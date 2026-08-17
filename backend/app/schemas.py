from datetime import datetime, timezone
from typing import Annotated

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    PlainSerializer,
    StringConstraints,
    model_validator,
)

from app.models import NotificationType, Priority, Role, TaskStatus, TicketStatus


def _serialize_utc(value: datetime) -> str:
    utc_value = (
        value.replace(tzinfo=timezone.utc)
        if value.tzinfo is None
        else value.astimezone(timezone.utc)
    )
    return utc_value.isoformat().replace("+00:00", "Z")


UTCDateTime = Annotated[
    datetime, PlainSerializer(_serialize_utc, return_type=str, when_used="json")
]
Name100 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Name150 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
Name200 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Title250 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=250)]
TicketSubject = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=3, max_length=250)
]
TicketText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=3, max_length=10000)
]
CommentText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)
]


def _reject_explicit_none(value):
    if value is None:
        raise ValueError("Field cannot be null")
    return value


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserSummary(ORMModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: Role


class UserCreate(BaseModel):
    first_name: Name100
    last_name: Name100
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    role: Role
    customer_id: int | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def client_must_have_customer(self):
        if self.role == Role.CLIENT and self.customer_id is None:
            raise ValueError("A client user must be linked to a customer")
        if self.role != Role.CLIENT and self.customer_id is not None:
            raise ValueError("Only client users may be linked to a customer")
        return self


class UserUpdate(BaseModel):
    first_name: Annotated[Name100 | None, BeforeValidator(_reject_explicit_none)] = None
    last_name: Annotated[Name100 | None, BeforeValidator(_reject_explicit_none)] = None
    email: Annotated[EmailStr | None, BeforeValidator(_reject_explicit_none)] = None
    role: Annotated[Role | None, BeforeValidator(_reject_explicit_none)] = None
    customer_id: int | None = None
    is_active: Annotated[bool | None, BeforeValidator(_reject_explicit_none)] = None


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)


class UserRead(UserSummary):
    customer_id: int | None
    is_active: bool
    created_at: UTCDateTime
    updated_at: UTCDateTime


class CustomerCreate(BaseModel):
    company_name: Name200
    contact_name: str | None = Field(default=None, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)


class CustomerUpdate(BaseModel):
    company_name: Annotated[Name200 | None, BeforeValidator(_reject_explicit_none)] = None
    contact_name: str | None = Field(default=None, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)
    is_active: Annotated[bool | None, BeforeValidator(_reject_explicit_none)] = None


class CustomerRead(ORMModel):
    id: int
    company_name: str
    contact_name: str | None
    email: EmailStr | None
    phone: str | None
    address: str | None
    is_active: bool
    created_at: UTCDateTime
    updated_at: UTCDateTime


class ProductCreate(BaseModel):
    name: Name150
    description: str | None = Field(default=None, max_length=500)


class ProductUpdate(BaseModel):
    name: Annotated[Name150 | None, BeforeValidator(_reject_explicit_none)] = None
    description: str | None = Field(default=None, max_length=500)
    is_active: Annotated[bool | None, BeforeValidator(_reject_explicit_none)] = None


class ProductRead(ORMModel):
    id: int
    name: str
    description: str | None
    is_active: bool


class ModuleCreate(BaseModel):
    product_id: int
    name: Name150
    description: str | None = Field(default=None, max_length=500)


class ModuleUpdate(BaseModel):
    name: Annotated[Name150 | None, BeforeValidator(_reject_explicit_none)] = None
    description: str | None = Field(default=None, max_length=500)
    is_active: Annotated[bool | None, BeforeValidator(_reject_explicit_none)] = None


class ModuleRead(ORMModel):
    id: int
    product_id: int
    name: str
    description: str | None
    is_active: bool


class CategoryCreate(BaseModel):
    name: Name150
    description: str | None = Field(default=None, max_length=500)


class CategoryUpdate(BaseModel):
    name: Annotated[Name150 | None, BeforeValidator(_reject_explicit_none)] = None
    description: str | None = Field(default=None, max_length=500)
    is_active: Annotated[bool | None, BeforeValidator(_reject_explicit_none)] = None


class CategoryRead(ORMModel):
    id: int
    name: str
    description: str | None
    is_active: bool


class SLAConfigurationUpdate(BaseModel):
    target_hours: int = Field(gt=0, le=8760)
    warning_threshold_percent: int = Field(default=80, ge=1, le=100)
    is_active: bool = True


class SLAConfigurationRead(ORMModel):
    id: int
    priority: Priority
    target_hours: int
    warning_threshold_percent: int
    is_active: bool


class TicketCreate(BaseModel):
    customer_id: int
    subject: TicketSubject
    description: TicketText
    category_id: int
    module_id: int | None = None
    priority: Priority = Priority.MEDIUM


class TicketUpdate(BaseModel):
    subject: Annotated[TicketSubject | None, BeforeValidator(_reject_explicit_none)] = None
    description: Annotated[TicketText | None, BeforeValidator(_reject_explicit_none)] = None
    category_id: Annotated[int | None, BeforeValidator(_reject_explicit_none)] = None
    module_id: int | None = None


class TicketAssignment(BaseModel):
    assigned_user_id: int


class TicketPriorityChange(BaseModel):
    priority: Priority


class TicketStatusChange(BaseModel):
    status: TicketStatus
    resolution_summary: str | None = Field(default=None, max_length=10000)
    note: str | None = Field(default=None, max_length=2000)


class TicketRead(ORMModel):
    id: int
    reference: str
    customer_id: int
    subject: str
    description: str
    category_id: int
    module_id: int | None
    priority: Priority
    status: TicketStatus
    creator_id: int
    assigned_user_id: int | None
    assigned_user_name: str | None
    resolution_summary: str | None
    sla_deadline: UTCDateTime | None
    sla_status: str
    sla_remaining_minutes: int | None
    resolved_at: UTCDateTime | None
    validated_at: UTCDateTime | None
    closed_at: UTCDateTime | None
    created_at: UTCDateTime
    updated_at: UTCDateTime


class TicketPage(BaseModel):
    items: list[TicketRead]
    total: int
    page: int
    page_size: int


class TaskCreate(BaseModel):
    title: Title250
    description: str | None = Field(default=None, max_length=10000)
    assigned_user_id: int | None = None
    due_date: UTCDateTime | None = None


class TaskUpdate(BaseModel):
    title: Annotated[Title250 | None, BeforeValidator(_reject_explicit_none)] = None
    description: str | None = Field(default=None, max_length=10000)
    assigned_user_id: int | None = None
    due_date: UTCDateTime | None = None
    status: Annotated[TaskStatus | None, BeforeValidator(_reject_explicit_none)] = None
    note: str | None = Field(default=None, max_length=2000)


class TaskRead(ORMModel):
    id: int
    ticket_id: int
    title: str
    description: str | None
    assigned_user_id: int | None
    assigned_user_name: str | None
    status: TaskStatus
    due_date: UTCDateTime | None
    completed_at: UTCDateTime | None
    created_at: UTCDateTime
    updated_at: UTCDateTime


class CommentCreate(BaseModel):
    content: CommentText


class CommentRead(ORMModel):
    id: int
    ticket_id: int
    author_id: int
    author_name: str
    content: str
    created_at: UTCDateTime


class HistoryRead(ORMModel):
    id: int
    ticket_id: int
    actor_id: int | None
    event_type: str
    details: str | None
    created_at: UTCDateTime


class TicketDetail(TicketRead):
    tasks: list[TaskRead]
    comments: list[CommentRead]
    history: list[HistoryRead]


class NotificationRead(ORMModel):
    id: int
    recipient_id: int
    ticket_id: int | None
    type: NotificationType
    title: str
    message: str
    is_read: bool
    created_at: UTCDateTime


class DashboardCount(BaseModel):
    label: str
    count: int


class DashboardSummary(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    overdue_tickets: int
    sla_compliance_rate: float | None
    average_resolution_hours: float | None
    by_status: list[DashboardCount]
    by_priority: list[DashboardCount]
    by_category: list[DashboardCount]
    by_customer: list[DashboardCount]
    by_assignee: list[DashboardCount]
