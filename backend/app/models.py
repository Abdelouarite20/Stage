from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Unicode,
    UniqueConstraint,
)
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    """Return a database-portable naive UTC timestamp."""

    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(value: datetime) -> datetime:
    """Normalize an API datetime for storage in SQL Server DATETIME2."""

    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


class Role(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    AGENT = "AGENT"
    CLIENT = "CLIENT"


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TicketStatus(str, Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING = "WAITING"
    RESOLVED = "RESOLVED"
    VALIDATED = "VALIDATED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class NotificationType(str, Enum):
    ASSIGNMENT = "ASSIGNMENT"
    SLA_WARNING = "SLA_WARNING"
    SLA_OVERDUE = "SLA_OVERDUE"
    TASK_WARNING = "TASK_WARNING"
    TASK_OVERDUE = "TASK_OVERDUE"
    UPDATE = "UPDATE"


role_enum = SqlEnum(Role, native_enum=False, length=20)
priority_enum = SqlEnum(Priority, native_enum=False, length=20)
ticket_status_enum = SqlEnum(TicketStatus, native_enum=False, length=20)
task_status_enum = SqlEnum(TaskStatus, native_enum=False, length=20)
notification_type_enum = SqlEnum(NotificationType, native_enum=False, length=30)
sql_datetime = DateTime().with_variant(DATETIME2(precision=0), "mssql")


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(sql_datetime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        sql_datetime, default=utc_now, onupdate=utc_now, nullable=False
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    last_name: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    email: Mapped[str] = mapped_column(Unicode(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    role: Mapped[Role] = mapped_column(role_enum, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True)

    customer: Mapped[Customer | None] = relationship(back_populates="portal_users")

    __table_args__ = (
        Index("ix_users_active_role", "is_active", "role"),
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[str] = mapped_column(Unicode(200), nullable=False, index=True)
    contact_name: Mapped[str | None] = mapped_column(Unicode(200))
    email: Mapped[str | None] = mapped_column(Unicode(255))
    phone: Mapped[str | None] = mapped_column(Unicode(50))
    address: Mapped[str | None] = mapped_column(Unicode(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    portal_users: Mapped[list[User]] = relationship(back_populates="customer")
    tickets: Mapped[list[Ticket]] = relationship(back_populates="customer")


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Unicode(150), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Unicode(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    modules: Mapped[list[ProductModule]] = relationship(back_populates="product")


class ProductModule(TimestampMixin, Base):
    __tablename__ = "product_modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    name: Mapped[str] = mapped_column(Unicode(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Unicode(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product: Mapped[Product] = relationship(back_populates="modules")
    tickets: Mapped[list[Ticket]] = relationship(back_populates="module")

    __table_args__ = (UniqueConstraint("product_id", "name", name="uq_module_product_name"),)


class TicketCategory(TimestampMixin, Base):
    __tablename__ = "ticket_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Unicode(150), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Unicode(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tickets: Mapped[list[Ticket]] = relationship(back_populates="category")


class SLAConfiguration(TimestampMixin, Base):
    __tablename__ = "sla_configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    priority: Mapped[Priority] = mapped_column(priority_enum, unique=True, nullable=False)
    target_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    warning_threshold_percent: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        CheckConstraint("target_hours > 0", name="ck_sla_target_positive"),
        CheckConstraint(
            "warning_threshold_percent BETWEEN 1 AND 100",
            name="ck_sla_warning_percent",
        ),
    )


class Ticket(TimestampMixin, Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(Unicode(40), unique=True, index=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(Unicode(250), nullable=False)
    description: Mapped[str] = mapped_column(Unicode(), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("ticket_categories.id"), nullable=False)
    module_id: Mapped[int | None] = mapped_column(ForeignKey("product_modules.id"))
    priority: Mapped[Priority] = mapped_column(priority_enum, nullable=False, index=True)
    status: Mapped[TicketStatus] = mapped_column(
        ticket_status_enum, default=TicketStatus.NEW, nullable=False, index=True
    )
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    resolution_summary: Mapped[str | None] = mapped_column(Unicode())
    sla_deadline: Mapped[datetime | None] = mapped_column(sql_datetime, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(sql_datetime)
    validated_at: Mapped[datetime | None] = mapped_column(sql_datetime)
    closed_at: Mapped[datetime | None] = mapped_column(sql_datetime)

    customer: Mapped[Customer] = relationship(back_populates="tickets")
    category: Mapped[TicketCategory] = relationship(back_populates="tickets")
    module: Mapped[ProductModule | None] = relationship(back_populates="tickets")
    creator: Mapped[User] = relationship(foreign_keys=[creator_id])
    assigned_user: Mapped[User | None] = relationship(foreign_keys=[assigned_user_id])
    tasks: Mapped[list[TicketTask]] = relationship(back_populates="ticket")
    comments: Mapped[list[TicketComment]] = relationship(back_populates="ticket")
    history: Mapped[list[TicketHistory]] = relationship(back_populates="ticket")

    __table_args__ = (
        Index("ix_tickets_status_priority", "status", "priority"),
        Index("ix_tickets_customer_created", "customer_id", "created_at"),
    )

    @property
    def sla_status(self) -> str:
        if self.sla_deadline is None:
            return "NOT_CONFIGURED"
        comparison_time = self.resolved_at or utc_now()
        if self.resolved_at is not None:
            return "MET" if comparison_time <= self.sla_deadline else "BREACHED"
        return "OVERDUE" if comparison_time > self.sla_deadline else "ON_TRACK"

    @property
    def sla_remaining_minutes(self) -> int | None:
        if self.sla_deadline is None:
            return None
        return int((self.sla_deadline - (self.resolved_at or utc_now())).total_seconds() // 60)

    @property
    def assigned_user_name(self) -> str | None:
        return self.assigned_user.full_name if self.assigned_user is not None else None


class TicketTask(TimestampMixin, Base):
    __tablename__ = "ticket_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Unicode(250), nullable=False)
    description: Mapped[str | None] = mapped_column(Unicode())
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[TaskStatus] = mapped_column(
        task_status_enum, default=TaskStatus.TODO, nullable=False, index=True
    )
    due_date: Mapped[datetime | None] = mapped_column(sql_datetime, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(sql_datetime)

    ticket: Mapped[Ticket] = relationship(back_populates="tasks")
    assigned_user: Mapped[User | None] = relationship()

    @property
    def assigned_user_name(self) -> str | None:
        return self.assigned_user.full_name if self.assigned_user is not None else None


class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Unicode(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(sql_datetime, default=utc_now, nullable=False)

    ticket: Mapped[Ticket] = relationship(back_populates="comments")
    author: Mapped[User] = relationship()

    @property
    def author_name(self) -> str:
        return self.author.full_name


class TicketHistory(Base):
    __tablename__ = "ticket_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False, index=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    details: Mapped[str | None] = mapped_column(Unicode())
    created_at: Mapped[datetime] = mapped_column(sql_datetime, default=utc_now, nullable=False)

    ticket: Mapped[Ticket] = relationship(back_populates="history")
    actor: Mapped[User | None] = relationship()

    __table_args__ = (Index("ix_history_ticket_created", "ticket_id", "created_at"),)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    ticket_id: Mapped[int | None] = mapped_column(ForeignKey("tickets.id"), index=True)
    type: Mapped[NotificationType] = mapped_column(notification_type_enum, nullable=False)
    title: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    message: Mapped[str] = mapped_column(Unicode(1000), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(sql_datetime, default=utc_now, nullable=False)

    recipient: Mapped[User] = relationship()
    ticket: Mapped[Ticket | None] = relationship()

    __table_args__ = (Index("ix_notifications_recipient_read", "recipient_id", "is_read"),)
