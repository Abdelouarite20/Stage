from datetime import datetime, timedelta

from sqlalchemy import select, true
from sqlalchemy.orm import Session

from app.models import Priority, SLAConfiguration, Ticket, TicketHistory, utc_now


def get_sla_configuration(db: Session, priority: Priority) -> SLAConfiguration | None:
    return db.scalar(
        select(SLAConfiguration).where(
            SLAConfiguration.priority == priority,
            SLAConfiguration.is_active == true(),
        )
    )


def calculate_sla_deadline(
    db: Session, priority: Priority, start_at: datetime | None = None
) -> datetime | None:
    configuration = get_sla_configuration(db, priority)
    if configuration is None:
        return None
    return (start_at or utc_now()) + timedelta(hours=configuration.target_hours)


def get_sla_cycle_start(db: Session, ticket: Ticket) -> datetime:
    latest_reopen = db.scalar(
        select(TicketHistory.created_at)
        .where(
            TicketHistory.ticket_id == ticket.id,
            TicketHistory.event_type == "STATUS_REOPENED",
        )
        .order_by(TicketHistory.created_at.desc(), TicketHistory.id.desc())
        .limit(1)
    )
    return latest_reopen or ticket.created_at


def get_sla_cycle_marker(db: Session, ticket: Ticket) -> str:
    latest_reopen_id = db.scalar(
        select(TicketHistory.id)
        .where(
            TicketHistory.ticket_id == ticket.id,
            TicketHistory.event_type == "STATUS_REOPENED",
        )
        .order_by(TicketHistory.created_at.desc(), TicketHistory.id.desc())
        .limit(1)
    )
    return f"reopen-{latest_reopen_id}" if latest_reopen_id is not None else "initial"


def is_sla_warning(
    ticket: Ticket,
    warning_threshold_percent: int,
    cycle_start: datetime,
    now: datetime | None = None,
) -> bool:
    if ticket.sla_deadline is None or ticket.resolved_at is not None:
        return False
    current_time = now or utc_now()
    cycle_duration = ticket.sla_deadline - cycle_start
    if cycle_duration.total_seconds() <= 0:
        return False
    warning_time = cycle_start + cycle_duration * (warning_threshold_percent / 100)
    return warning_time <= current_time <= ticket.sla_deadline
