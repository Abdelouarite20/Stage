from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from app import models
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.models import Role, User
from app.routers import auth, catalog, customers, dashboard, notifications, tasks, tickets, users
from app.security import hash_password


settings = get_settings()


def bootstrap_administrator() -> None:
    """Create the first administrator only when an explicit local password is configured."""

    if not settings.bootstrap_admin_password:
        return
    with SessionLocal() as db:
        existing = db.scalar(
            select(User).where(func.lower(User.email) == settings.bootstrap_admin_email.lower())
        )
        if existing is not None:
            return
        db.add(
            User(
                first_name=settings.bootstrap_admin_first_name,
                last_name=settings.bootstrap_admin_last_name,
                email=settings.bootstrap_admin_email.lower(),
                password_hash=hash_password(settings.bootstrap_admin_password),
                role=Role.ADMIN,
                is_active=True,
            )
        )
        db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        if not settings.database_url.startswith("sqlite"):
            raise RuntimeError(
                "AUTO_CREATE_TABLES is supported only for the SQLite demonstration mode; "
                "use database/schema.sql for SQL Server"
            )
        Base.metadata.create_all(bind=engine)
    bootstrap_administrator()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Ticket management and monitoring API for Alias Informatique.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for api_router in (
    auth.router,
    users.router,
    customers.router,
    catalog.router,
    tickets.router,
    tasks.router,
    notifications.router,
    dashboard.router,
):
    app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
