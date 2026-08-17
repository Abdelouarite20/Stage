from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Role, Ticket, User
from app.security import decode_access_token


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    user_id = decode_access_token(token)
    user = db.get(User, user_id) if user_id is not None else None
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(*roles: Role) -> Callable:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return dependency


def apply_ticket_scope(query: Select, current_user: User) -> Select:
    if current_user.role in {Role.ADMIN, Role.MANAGER}:
        return query
    if current_user.role == Role.AGENT:
        return query.where(Ticket.assigned_user_id == current_user.id)
    if current_user.customer_id is None:
        return query.where(Ticket.id == -1)
    return query.where(
        Ticket.customer_id == current_user.customer_id,
        Ticket.creator_id == current_user.id,
    )


def get_visible_ticket(db: Session, ticket_id: int, current_user: User) -> Ticket:
    from sqlalchemy import select

    ticket = db.scalar(apply_ticket_scope(select(Ticket), current_user).where(Ticket.id == ticket_id))
    if ticket is None:
        # Returning 404 avoids revealing tickets outside the user's scope.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket
