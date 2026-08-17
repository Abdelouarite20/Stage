import json
from typing import Any

from sqlalchemy.orm import Session

from app.models import TicketHistory


def record_history(
    db: Session,
    ticket_id: int,
    event_type: str,
    actor_id: int | None,
    details: dict[str, Any] | None = None,
) -> TicketHistory:
    event = TicketHistory(
        ticket_id=ticket_id,
        actor_id=actor_id,
        event_type=event_type,
        details=json.dumps(details, ensure_ascii=False, default=str) if details else None,
    )
    db.add(event)
    return event

