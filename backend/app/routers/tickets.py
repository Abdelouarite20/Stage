from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import apply_ticket_scope, get_current_user, get_visible_ticket, require_roles
from app.models import (
    Customer,
    NotificationType,
    Priority,
    Product,
    ProductModule,
    Role,
    TaskStatus,
    Ticket,
    TicketCategory,
    TicketComment,
    TicketHistory,
    TicketStatus,
    TicketTask,
    User,
    to_naive_utc,
    utc_now,
)
from app.query_utils import literal_contains
from app.schemas import (
    CommentCreate,
    CommentRead,
    HistoryRead,
    TicketAssignment,
    TicketCreate,
    TicketDetail,
    TicketPage,
    TicketPriorityChange,
    TicketRead,
    TicketStatusChange,
    TicketUpdate,
)
from app.services.audit import record_history
from app.services.notifications import create_notification, notify_assignment
from app.services.sla import calculate_sla_deadline, get_sla_cycle_start
from app.services.workflow import transition_ticket


router = APIRouter(prefix="/tickets", tags=["Tickets"])


def _reference() -> str:
    return f"TKT-{utc_now():%Y%m%d}-{uuid4().hex[:8].upper()}"


def _validate_catalog(
    db: Session, customer_id: int, category_id: int, module_id: int | None
) -> None:
    customer = db.get(Customer, customer_id)
    if customer is None or not customer.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="An active customer is required",
        )
    category = db.get(TicketCategory, category_id)
    if category is None or not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="An active category is required",
        )
    if module_id is not None:
        module = db.get(ProductModule, module_id)
        product = db.get(Product, module.product_id) if module is not None else None
        if module is None or not module.is_active or product is None or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The selected module and its product must be active",
            )


def _can_edit(ticket: Ticket, user: User) -> bool:
    return user.role in {Role.ADMIN, Role.MANAGER} or (
        user.role == Role.AGENT and ticket.assigned_user_id == user.id
    )


@router.get("", response_model=TicketPage)
def list_tickets(
    search: str | None = Query(default=None, max_length=150),
    customer_id: int | None = None,
    ticket_status: TicketStatus | None = Query(default=None, alias="status"),
    priority: Priority | None = None,
    category_id: int | None = None,
    product_id: int | None = None,
    module_id: int | None = None,
    assigned_user_id: int | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    sla_status: str | None = Query(
        default=None, pattern="^(ON_TRACK|OVERDUE|NOT_CONFIGURED|MET|BREACHED)$"
    ),
    sort_by: str = Query(default="created_at", pattern="^(reference|created_at|updated_at|sla_deadline|priority)$"),
    sort_direction: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketPage:
    query = apply_ticket_scope(select(Ticket), current_user)
    if search:
        query = query.where(
            or_(
                literal_contains(Ticket.reference, search),
                literal_contains(Ticket.subject, search),
            )
        )
    if customer_id is not None:
        query = query.where(Ticket.customer_id == customer_id)
    if ticket_status is not None:
        query = query.where(Ticket.status == ticket_status)
    if priority is not None:
        query = query.where(Ticket.priority == priority)
    if category_id is not None:
        query = query.where(Ticket.category_id == category_id)
    if module_id is not None:
        query = query.where(Ticket.module_id == module_id)
    if product_id is not None:
        query = query.join(ProductModule, Ticket.module_id == ProductModule.id).where(
            ProductModule.product_id == product_id
        )
    if assigned_user_id is not None:
        query = query.where(Ticket.assigned_user_id == assigned_user_id)
    if created_from is not None:
        query = query.where(Ticket.created_at >= to_naive_utc(created_from))
    if created_to is not None:
        query = query.where(Ticket.created_at <= to_naive_utc(created_to))
    now = utc_now()
    if sla_status == "OVERDUE":
        query = query.where(
            Ticket.resolved_at.is_(None),
            Ticket.sla_deadline.is_not(None),
            Ticket.sla_deadline < now,
        )
    elif sla_status == "ON_TRACK":
        query = query.where(
            Ticket.resolved_at.is_(None),
            Ticket.sla_deadline.is_not(None),
            Ticket.sla_deadline >= now,
        )
    elif sla_status == "NOT_CONFIGURED":
        query = query.where(Ticket.sla_deadline.is_(None))
    elif sla_status == "MET":
        query = query.where(
            Ticket.resolved_at.is_not(None),
            Ticket.sla_deadline.is_not(None),
            Ticket.resolved_at <= Ticket.sla_deadline,
        )
    elif sla_status == "BREACHED":
        query = query.where(
            Ticket.resolved_at.is_not(None),
            Ticket.sla_deadline.is_not(None),
            Ticket.resolved_at > Ticket.sla_deadline,
        )

    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    sort_column = getattr(Ticket, sort_by)
    direction = sort_column.asc() if sort_direction == "asc" else sort_column.desc()
    id_direction = Ticket.id.asc() if sort_direction == "asc" else Ticket.id.desc()
    query = query.order_by(direction, id_direction)
    items = list(
        db.scalars(
            query.options(selectinload(Ticket.assigned_user))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return TicketPage(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Ticket:
    customer_id = payload.customer_id
    priority = payload.priority
    if current_user.role == Role.CLIENT:
        if current_user.customer_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is not linked to a customer",
            )
        customer_id = current_user.customer_id
        priority = Priority.MEDIUM
    _validate_catalog(db, customer_id, payload.category_id, payload.module_id)
    ticket = Ticket(
        reference=_reference(),
        customer_id=customer_id,
        subject=payload.subject.strip(),
        description=payload.description.strip(),
        category_id=payload.category_id,
        module_id=payload.module_id,
        priority=priority,
        status=TicketStatus.NEW,
        creator_id=current_user.id,
    )
    db.add(ticket)
    db.flush()
    ticket.sla_deadline = calculate_sla_deadline(db, priority, ticket.created_at)
    record_history(
        db,
        ticket.id,
        "TICKET_CREATED",
        current_user.id,
        {"reference": ticket.reference, "priority": priority.value},
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/{ticket_id}", response_model=TicketDetail)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Ticket | TicketDetail:
    query = (
        apply_ticket_scope(select(Ticket), current_user)
        .where(Ticket.id == ticket_id)
        .options(
            selectinload(Ticket.tasks).selectinload(TicketTask.assigned_user),
            selectinload(Ticket.comments).selectinload(TicketComment.author),
            selectinload(Ticket.history),
            selectinload(Ticket.assigned_user),
        )
    )
    ticket = db.scalar(query)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    ticket.tasks.sort(key=lambda item: (item.created_at, item.id))
    ticket.comments.sort(key=lambda item: (item.created_at, item.id))
    ticket.history.sort(key=lambda item: (item.created_at, item.id))
    if current_user.role == Role.CLIENT:
        response = TicketDetail.model_validate(ticket)
        response.tasks = []
        return response
    return ticket


@router.patch("/{ticket_id}", response_model=TicketRead)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Ticket:
    ticket = get_visible_ticket(db, ticket_id, current_user)
    if not _can_edit(ticket, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ticket cannot be edited")
    if ticket.status in {TicketStatus.RESOLVED, TicketStatus.VALIDATED, TicketStatus.CLOSED}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Completed tickets cannot be edited")
    updates = payload.model_dump(exclude_unset=True)
    category_id = updates.get("category_id", ticket.category_id)
    module_id = updates.get("module_id", ticket.module_id)
    _validate_catalog(db, ticket.customer_id, category_id, module_id)
    changed_fields: list[str] = []
    for field, value in updates.items():
        if getattr(ticket, field) != value:
            setattr(ticket, field, value)
            changed_fields.append(field)
    if changed_fields:
        record_history(
            db, ticket.id, "TICKET_UPDATED", current_user.id, {"fields": changed_fields}
        )
        db.commit()
        db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/assign", response_model=TicketRead)
def assign_ticket(
    ticket_id: int,
    payload: TicketAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER)),
) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if ticket.status in {TicketStatus.CLOSED, TicketStatus.VALIDATED}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Completed tickets cannot be assigned")
    assignee = db.get(User, payload.assigned_user_id)
    if assignee is None or not assignee.is_active or assignee.role not in {Role.AGENT, Role.MANAGER}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Assignee must be an active agent or manager",
        )
    previous_id = ticket.assigned_user_id
    ticket.assigned_user_id = assignee.id
    if ticket.status == TicketStatus.NEW:
        ticket.status = TicketStatus.ASSIGNED
    record_history(
        db,
        ticket.id,
        "TICKET_ASSIGNED",
        current_user.id,
        {"from_user_id": previous_id, "to_user_id": assignee.id},
    )
    notify_assignment(db, ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/priority", response_model=TicketRead)
def change_priority(
    ticket_id: int,
    payload: TicketPriorityChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN, Role.MANAGER)),
) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if ticket.status in {TicketStatus.RESOLVED, TicketStatus.VALIDATED, TicketStatus.CLOSED}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resolved, validated, or closed ticket priority cannot be changed",
        )
    previous = ticket.priority
    previous_deadline = ticket.sla_deadline
    if previous == payload.priority:
        return ticket
    ticket.priority = payload.priority
    ticket.sla_deadline = calculate_sla_deadline(
        db, payload.priority, get_sla_cycle_start(db, ticket)
    )
    record_history(
        db,
        ticket.id,
        "PRIORITY_CHANGED",
        current_user.id,
        {
            "from": previous.value,
            "to": payload.priority.value,
            "previous_sla_deadline": previous_deadline,
            "new_sla_deadline": ticket.sla_deadline,
        },
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/status", response_model=TicketRead)
def change_status(
    ticket_id: int,
    payload: TicketStatusChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Ticket:
    ticket = get_visible_ticket(db, ticket_id, current_user)
    previous = ticket.status
    reason_required = payload.status in {TicketStatus.WAITING, TicketStatus.REOPENED} or (
        previous == TicketStatus.RESOLVED and payload.status == TicketStatus.IN_PROGRESS
    )
    if reason_required and (payload.note is None or not payload.note.strip()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A reason is required for this workflow transition",
        )
    if payload.status == TicketStatus.IN_PROGRESS:
        assignee = db.get(User, ticket.assigned_user_id) if ticket.assigned_user_id else None
        if assignee is None or not assignee.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Assign the ticket to an active user before starting work",
            )
    if payload.status == TicketStatus.CLOSED:
        unfinished_tasks = db.scalar(
            select(func.count(TicketTask.id)).where(
                TicketTask.ticket_id == ticket.id,
                TicketTask.status.not_in({TaskStatus.DONE, TaskStatus.CANCELLED}),
            )
        )
        if unfinished_tasks:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Complete or cancel all ticket tasks before closure",
            )
    old_sla_deadline = ticket.sla_deadline
    old_lifecycle_dates = {
        "previous_resolution_summary": ticket.resolution_summary,
        "previous_resolved_at": ticket.resolved_at,
        "previous_validated_at": ticket.validated_at,
        "previous_closed_at": ticket.closed_at,
    }
    transition_ticket(ticket, payload.status, current_user, payload.resolution_summary)
    if payload.status == TicketStatus.REOPENED:
        ticket.sla_deadline = calculate_sla_deadline(db, ticket.priority, utc_now())
    history_details = {"from": previous.value, "to": payload.status.value}
    if payload.note and payload.note.strip():
        history_details["note"] = payload.note.strip()
    if payload.status == TicketStatus.REOPENED:
        history_details.update(
            {
                "previous_sla_deadline": old_sla_deadline,
                "new_sla_deadline": ticket.sla_deadline,
                **old_lifecycle_dates,
            }
        )
    if payload.status in {TicketStatus.RESOLVED, TicketStatus.IN_PROGRESS, TicketStatus.REOPENED}:
        history_details.update(old_lifecycle_dates)
        history_details.update(
            {
                "resolution_summary": ticket.resolution_summary,
                "resolved_at": ticket.resolved_at,
                "sla_result": ticket.sla_status if payload.status == TicketStatus.RESOLVED else None,
            }
        )
    record_history(
        db,
        ticket.id,
        f"STATUS_{payload.status.value}",
        current_user.id,
        history_details,
    )
    notification_recipient_ids = {
        recipient_id
        for recipient_id in (ticket.creator_id, ticket.assigned_user_id)
        if recipient_id is not None and recipient_id != current_user.id
    }
    for recipient_id in notification_recipient_ids:
        create_notification(
            db,
            recipient_id,
            NotificationType.UPDATE,
            "Ticket status updated",
            f"{ticket.reference} is now {payload.status.value.replace('_', ' ')}.",
            ticket.id,
        )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/{ticket_id}/comments", response_model=list[CommentRead])
def list_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketComment]:
    get_visible_ticket(db, ticket_id, current_user)
    return list(
        db.scalars(
            select(TicketComment)
            .where(TicketComment.ticket_id == ticket_id)
            .order_by(TicketComment.created_at, TicketComment.id)
        ).all()
    )


@router.post("/{ticket_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
def add_comment(
    ticket_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketComment:
    ticket = get_visible_ticket(db, ticket_id, current_user)
    comment = TicketComment(
        ticket_id=ticket.id, author_id=current_user.id, content=payload.content.strip()
    )
    db.add(comment)
    db.flush()
    record_history(
        db, ticket.id, "COMMENT_ADDED", current_user.id, {"comment_id": comment.id}
    )
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/{ticket_id}/history", response_model=list[HistoryRead])
def list_history(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketHistory]:
    get_visible_ticket(db, ticket_id, current_user)
    return list(
        db.scalars(
            select(TicketHistory)
            .where(TicketHistory.ticket_id == ticket_id)
            .order_by(TicketHistory.created_at, TicketHistory.id)
        ).all()
    )
