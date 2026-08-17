from fastapi import APIRouter, Depends, HTTPException, status
from enum import Enum

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_visible_ticket
from app.models import (
    NotificationType,
    Role,
    TaskStatus,
    TicketStatus,
    TicketTask,
    User,
    to_naive_utc,
    utc_now,
)
from app.schemas import TaskCreate, TaskRead, TaskUpdate
from app.services.audit import record_history
from app.services.notifications import create_notification


router = APIRouter(tags=["Tasks"])

TASK_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.TODO: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
    TaskStatus.IN_PROGRESS: {TaskStatus.BLOCKED, TaskStatus.DONE, TaskStatus.CANCELLED},
    TaskStatus.BLOCKED: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
    TaskStatus.DONE: set(),
    TaskStatus.CANCELLED: set(),
}


def _validate_assignee(db: Session, assignee_id: int | None, current_user: User) -> User | None:
    if assignee_id is None:
        return None
    assignee = db.get(User, assignee_id)
    if assignee is None or not assignee.is_active or assignee.role not in {Role.AGENT, Role.MANAGER}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Task assignee must be an active agent or manager",
        )
    if current_user.role == Role.AGENT and assignee.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agents can only assign tasks to themselves",
        )
    return assignee


def _get_visible_task(db: Session, task_id: int, current_user: User):
    task = db.get(TicketTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    ticket = get_visible_ticket(db, task.ticket_id, current_user)
    return task, ticket


def _history_value(value):
    return value.value if isinstance(value, Enum) else value


@router.get("/tickets/{ticket_id}/tasks", response_model=list[TaskRead])
def list_tasks(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketTask]:
    if current_user.role == Role.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clients cannot view internal tasks")
    get_visible_ticket(db, ticket_id, current_user)
    return list(
        db.scalars(
            select(TicketTask)
            .where(TicketTask.ticket_id == ticket_id)
            .order_by(TicketTask.created_at, TicketTask.id)
        ).all()
    )


@router.post(
    "/tickets/{ticket_id}/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED
)
def create_task(
    ticket_id: int,
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketTask:
    if current_user.role == Role.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clients cannot manage tasks")
    ticket = get_visible_ticket(db, ticket_id, current_user)
    if ticket.status in {TicketStatus.VALIDATED, TicketStatus.CLOSED}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ticket is completed")
    task_data = payload.model_dump()
    if current_user.role == Role.AGENT and task_data["assigned_user_id"] is None:
        task_data["assigned_user_id"] = current_user.id
    assignee = _validate_assignee(db, task_data["assigned_user_id"], current_user)
    if task_data["due_date"] is not None:
        task_data["due_date"] = to_naive_utc(task_data["due_date"])
        if task_data["due_date"] <= utc_now():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Task due date must be in the future",
            )
    task = TicketTask(ticket_id=ticket.id, **task_data)
    db.add(task)
    db.flush()
    record_history(
        db,
        ticket.id,
        "TASK_CREATED",
        current_user.id,
        {"task_id": task.id, "title": task.title},
    )
    if assignee is not None and assignee.id != current_user.id:
        create_notification(
            db,
            assignee.id,
            NotificationType.UPDATE,
            "Task assigned",
            f"Task #{task.id} on ticket {ticket.reference}: {task.title}",
            ticket.id,
        )
    db.commit()
    db.refresh(task)
    return task


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketTask:
    if current_user.role == Role.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clients cannot manage tasks")
    task, ticket = _get_visible_task(db, task_id, current_user)
    if ticket.status == TicketStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Closed-ticket tasks are immutable")
    if task.status in {TaskStatus.DONE, TaskStatus.CANCELLED}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Completed tasks are immutable")
    if current_user.role == Role.AGENT and task.assigned_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agents can update only tasks assigned to themselves",
        )
    updates = payload.model_dump(exclude_unset=True)
    note = updates.pop("note", None)
    if "assigned_user_id" in updates:
        if current_user.role == Role.AGENT and updates["assigned_user_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Agents cannot reassign or unassign tasks",
            )
        _validate_assignee(db, updates["assigned_user_id"], current_user)
    if updates.get("due_date") is not None:
        updates["due_date"] = to_naive_utc(updates["due_date"])
        if updates["due_date"] <= utc_now():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Task due date must be in the future",
            )
    new_status = updates.get("status")
    if new_status is not None and new_status != task.status:
        if new_status in {TaskStatus.BLOCKED, TaskStatus.CANCELLED} and (
            note is None or not note.strip()
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A reason is required to block or cancel a task",
            )
        if new_status == TaskStatus.CANCELLED and current_user.role == Role.AGENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Task cancellation requires a manager",
            )
        if new_status not in TASK_TRANSITIONS[task.status]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Task transition from {task.status.value} to {new_status.value} is not allowed",
            )
        if new_status == TaskStatus.DONE:
            task.completed_at = utc_now()
    changes: dict[str, dict[str, object]] = {}
    for field, value in updates.items():
        previous_value = getattr(task, field)
        if previous_value != value:
            setattr(task, field, value)
            changes[field] = {
                "from": _history_value(previous_value),
                "to": _history_value(value),
            }
    if changes:
        event_type = "TASK_COMPLETED" if new_status == TaskStatus.DONE else "TASK_UPDATED"
        if new_status == TaskStatus.DONE:
            changes["completed_at"] = {"from": None, "to": task.completed_at}
        record_history(
            db,
            task.ticket_id,
            event_type,
            current_user.id,
            {
                "task_id": task.id,
                "changes": changes,
                **({"note": note.strip()} if note and note.strip() else {}),
            },
        )
        new_assignee_id = updates.get("assigned_user_id")
        if (
            "assigned_user_id" in changes
            and new_assignee_id is not None
            and new_assignee_id != current_user.id
        ):
            create_notification(
                db,
                new_assignee_id,
                NotificationType.UPDATE,
                "Task assigned",
                f"Task #{task.id} on ticket {ticket.reference}: {task.title}",
                ticket.id,
            )
        db.commit()
        db.refresh(task)
    return task
