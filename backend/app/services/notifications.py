from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Notification,
    NotificationType,
    SLAConfiguration,
    TaskStatus,
    Ticket,
    TicketStatus,
    TicketTask,
    utc_now,
)
from app.services.sla import get_sla_cycle_marker, get_sla_cycle_start, is_sla_warning


def create_notification(
    db: Session,
    recipient_id: int,
    notification_type: NotificationType,
    title: str,
    message: str,
    ticket_id: int | None = None,
) -> Notification:
    notification = Notification(
        recipient_id=recipient_id,
        ticket_id=ticket_id,
        type=notification_type,
        title=title,
        message=message,
    )
    db.add(notification)
    return notification


def notify_assignment(db: Session, ticket: Ticket) -> None:
    if ticket.assigned_user_id is None:
        return
    create_notification(
        db,
        recipient_id=ticket.assigned_user_id,
        notification_type=NotificationType.ASSIGNMENT,
        title="Ticket assigned",
        message=f"Ticket {ticket.reference} has been assigned to you.",
        ticket_id=ticket.id,
    )


def _notification_exists(
    db: Session,
    recipient_id: int,
    notification_type: NotificationType,
    ticket_id: int,
    title: str,
    message: str,
) -> bool:
    return db.scalar(
        select(Notification.id).where(
            Notification.recipient_id == recipient_id,
            Notification.type == notification_type,
            Notification.ticket_id == ticket_id,
            Notification.title == title,
            Notification.message == message,
        )
    ) is not None


def refresh_deadline_notifications(db: Session) -> int:
    """Create missing in-app SLA/task alerts; returns the number created."""

    created = 0
    now = utc_now()
    active_statuses = {
        TicketStatus.NEW,
        TicketStatus.ASSIGNED,
        TicketStatus.IN_PROGRESS,
        TicketStatus.WAITING,
        TicketStatus.REOPENED,
    }
    tickets = db.scalars(
        select(Ticket).where(
            Ticket.assigned_user_id.is_not(None),
            Ticket.status.in_(active_statuses),
            Ticket.sla_deadline.is_not(None),
        )
    ).all()
    configurations = {
        item.priority: item
        for item in db.scalars(
            select(SLAConfiguration)
        ).all()
    }

    for ticket in tickets:
        deadline_label = ticket.sla_deadline.isoformat(timespec="seconds")
        message = (
            f"Ticket {ticket.reference}: {ticket.subject} "
            f"(SLA cycle {get_sla_cycle_marker(db, ticket)}, deadline {deadline_label} UTC)"
        )
        if ticket.sla_deadline is not None and now > ticket.sla_deadline:
            notification_type = NotificationType.SLA_OVERDUE
            title = "SLA deadline exceeded"
        else:
            configuration = configurations.get(ticket.priority)
            if configuration is None or not is_sla_warning(
                ticket,
                configuration.warning_threshold_percent,
                get_sla_cycle_start(db, ticket),
                now,
            ):
                continue
            notification_type = NotificationType.SLA_WARNING
            title = "SLA deadline approaching"
        if not _notification_exists(
            db, ticket.assigned_user_id, notification_type, ticket.id, title, message
        ):
            create_notification(
                db,
                ticket.assigned_user_id,
                notification_type,
                title,
                message,
                ticket.id,
            )
            created += 1

    unfinished = {TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED}
    tasks = db.scalars(
        select(TicketTask).where(
            TicketTask.assigned_user_id.is_not(None),
            TicketTask.status.in_(unfinished),
            TicketTask.due_date.is_not(None),
            TicketTask.due_date <= now + timedelta(hours=24),
        )
    ).all()
    for task in tasks:
        overdue = task.due_date is not None and task.due_date < now
        notification_type = NotificationType.TASK_OVERDUE if overdue else NotificationType.TASK_WARNING
        title = f"Task {'overdue' if overdue else 'deadline approaching'} #{task.id}"
        due_label = task.due_date.isoformat(timespec="seconds")
        message = f"{task.title} (due {due_label} UTC)"
        if not _notification_exists(
            db, task.assigned_user_id, notification_type, task.ticket_id, title, message
        ):
            create_notification(
                db,
                task.assigned_user_id,
                notification_type,
                title,
                message,
                task.ticket_id,
            )
            created += 1

    if created:
        db.commit()
    return created
