from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import apply_ticket_scope, get_current_user
from app.models import Customer, Ticket, TicketCategory, TicketStatus, User, utc_now
from app.schemas import DashboardCount, DashboardSummary
from app.services.sla import get_sla_cycle_start


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _count(db: Session, query) -> int:
    return db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardSummary:
    visible = apply_ticket_scope(select(Ticket), current_user)
    total = _count(db, visible)
    closed = _count(db, visible.where(Ticket.status == TicketStatus.CLOSED))
    in_progress = _count(db, visible.where(Ticket.status == TicketStatus.IN_PROGRESS))
    resolved = _count(db, visible.where(Ticket.status == TicketStatus.RESOLVED))
    overdue = _count(
        db,
        visible.where(
            Ticket.resolved_at.is_(None),
            Ticket.sla_deadline.is_not(None),
            Ticket.sla_deadline < utc_now(),
        ),
    )

    status_rows = db.execute(
        apply_ticket_scope(
            select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status), current_user
        )
    ).all()
    priority_rows = db.execute(
        apply_ticket_scope(
            select(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority), current_user
        )
    ).all()
    category_rows = db.execute(
        apply_ticket_scope(
            select(TicketCategory.name, func.count(Ticket.id))
            .join(Ticket, Ticket.category_id == TicketCategory.id)
            .group_by(TicketCategory.name),
            current_user,
        )
    ).all()
    customer_rows = db.execute(
        apply_ticket_scope(
            select(Customer.company_name, func.count(Ticket.id))
            .join(Ticket, Ticket.customer_id == Customer.id)
            .group_by(Customer.company_name),
            current_user,
        )
    ).all()
    assignee_rows = db.execute(
        apply_ticket_scope(
            select(Ticket.assigned_user_id, func.count(Ticket.id))
            .where(Ticket.status != TicketStatus.CLOSED)
            .group_by(Ticket.assigned_user_id),
            current_user,
        )
    ).all()
    assignee_ids = [row[0] for row in assignee_rows if row[0] is not None]
    users = {
        user.id: f"{user.first_name} {user.last_name}"
        for user in db.scalars(select(User).where(User.id.in_(assignee_ids))).all()
    } if assignee_ids else {}

    completed_tickets = list(
        db.scalars(
            apply_ticket_scope(
                select(Ticket).where(Ticket.resolved_at.is_not(None)), current_user
            )
        ).all()
    )
    resolution_hours = [
        (ticket.resolved_at - get_sla_cycle_start(db, ticket)).total_seconds() / 3600
        for ticket in completed_tickets
        if ticket.resolved_at is not None
    ]
    sla_measurable = [
        ticket
        for ticket in completed_tickets
        if ticket.sla_deadline is not None and ticket.resolved_at is not None
    ]
    sla_met = sum(
        1 for ticket in sla_measurable if ticket.resolved_at <= ticket.sla_deadline
    )

    return DashboardSummary(
        total_tickets=total,
        open_tickets=total - closed,
        in_progress_tickets=in_progress,
        resolved_tickets=resolved,
        closed_tickets=closed,
        overdue_tickets=overdue,
        sla_compliance_rate=round(sla_met * 100 / len(sla_measurable), 2)
        if sla_measurable
        else None,
        average_resolution_hours=round(sum(resolution_hours) / len(resolution_hours), 2)
        if resolution_hours
        else None,
        by_status=[DashboardCount(label=row[0].value, count=row[1]) for row in status_rows],
        by_priority=[DashboardCount(label=row[0].value, count=row[1]) for row in priority_rows],
        by_category=[DashboardCount(label=row[0], count=row[1]) for row in category_rows],
        by_customer=[DashboardCount(label=row[0], count=row[1]) for row in customer_rows],
        by_assignee=[
            DashboardCount(label=users.get(row[0], "Unassigned"), count=row[1])
            for row in assignee_rows
        ],
    )
