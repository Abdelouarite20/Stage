from fastapi import HTTPException, status

from app.models import Role, Ticket, TicketStatus, User, utc_now


ALLOWED_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.NEW: {TicketStatus.ASSIGNED},
    TicketStatus.ASSIGNED: {TicketStatus.IN_PROGRESS},
    TicketStatus.IN_PROGRESS: {TicketStatus.WAITING, TicketStatus.RESOLVED},
    TicketStatus.WAITING: {TicketStatus.IN_PROGRESS},
    TicketStatus.RESOLVED: {TicketStatus.VALIDATED, TicketStatus.IN_PROGRESS},
    TicketStatus.VALIDATED: {TicketStatus.CLOSED},
    TicketStatus.CLOSED: {TicketStatus.REOPENED},
    TicketStatus.REOPENED: {TicketStatus.IN_PROGRESS},
}


def transition_ticket(
    ticket: Ticket,
    target_status: TicketStatus,
    actor: User,
    resolution_summary: str | None = None,
) -> None:
    if target_status not in ALLOWED_TRANSITIONS.get(ticket.status, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Transition from {ticket.status.value} to {target_status.value} is not allowed",
        )

    if actor.role == Role.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clients cannot change ticket status")

    if actor.role == Role.AGENT:
        if ticket.assigned_user_id != actor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ticket is not assigned to you")
        if target_status not in {
            TicketStatus.IN_PROGRESS,
            TicketStatus.WAITING,
            TicketStatus.RESOLVED,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This workflow step requires a manager",
            )
        if ticket.status == TicketStatus.RESOLVED and target_status == TicketStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Resolution rejection requires a manager",
            )

    if target_status == TicketStatus.ASSIGNED and ticket.assigned_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A ticket must have an assignee before entering ASSIGNED",
        )

    if target_status == TicketStatus.RESOLVED:
        if not resolution_summary or not resolution_summary.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A resolution summary is required to resolve a ticket",
            )
        ticket.resolution_summary = resolution_summary.strip()
        ticket.resolved_at = utc_now()

    if target_status == TicketStatus.IN_PROGRESS and ticket.status == TicketStatus.RESOLVED:
        ticket.resolved_at = None
        ticket.resolution_summary = None

    if target_status == TicketStatus.VALIDATED:
        ticket.validated_at = utc_now()

    if target_status == TicketStatus.CLOSED:
        ticket.closed_at = utc_now()

    if target_status == TicketStatus.REOPENED:
        ticket.resolution_summary = None
        ticket.resolved_at = None
        ticket.validated_at = None
        ticket.closed_at = None

    ticket.status = target_status
