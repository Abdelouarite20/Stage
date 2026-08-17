from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select, true
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models import Customer, Role, User
from app.query_utils import literal_contains
from app.schemas import UserCreate, UserRead, UserUpdate
from app.security import hash_password


router = APIRouter(prefix="/users", tags=["Users"])


def _ensure_customer_link(db: Session, role: Role, customer_id: int | None) -> None:
    if role == Role.CLIENT:
        customer = db.get(Customer, customer_id) if customer_id is not None else None
        if customer is None or not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A client user must be linked to an active customer",
            )
    elif customer_id is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only client users may be linked to a customer",
        )


@router.get("", response_model=list[UserRead])
def list_users(
    search: str | None = Query(default=None, max_length=100),
    role: Role | None = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN, Role.MANAGER)),
) -> list[User]:
    query = select(User)
    if active_only:
        query = query.where(User.is_active == true())
    if role:
        query = query.where(User.role == role)
    if search:
        query = query.where(
            or_(
                literal_contains(User.first_name, search),
                literal_contains(User.last_name, search),
                literal_contains(User.email, search),
            )
        )
    return list(db.scalars(query.order_by(User.last_name, User.first_name)).all())


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN)),
) -> User:
    _ensure_customer_link(db, payload.role, payload.customer_id)
    user = User(
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        customer_id=payload.customer_id,
        is_active=payload.is_active,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN, Role.MANAGER)),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN)),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    updates = payload.model_dump(exclude_unset=True)
    final_role = updates.get("role", user.role)
    final_customer_id = updates.get("customer_id", user.customer_id)
    _ensure_customer_link(db, final_role, final_customer_id)
    if user.id == current_user.id and updates.get("is_active") is False:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You cannot deactivate your own account")
    if "email" in updates and updates["email"] is not None:
        updates["email"] = str(updates["email"]).lower()
    for field, value in updates.items():
        setattr(user, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    db.refresh(user)
    return user
