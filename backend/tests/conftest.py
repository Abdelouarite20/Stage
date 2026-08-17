import os
from collections.abc import Generator

os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-jwt-signing"
os.environ["DATABASE_URL"] = "sqlite+pysqlite://"
os.environ["AUTO_CREATE_TABLES"] = "false"
os.environ["BOOTSTRAP_ADMIN_PASSWORD"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import (
    Customer,
    Priority,
    Product,
    ProductModule,
    Role,
    SLAConfiguration,
    TicketCategory,
    User,
)
from app.security import hash_password


TEST_DATABASE_URL = "sqlite+pysqlite://"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    with TestingSessionLocal() as db:
        customer = Customer(company_name="Atlas Demo SARL", contact_name="Nadia Test")
        second_customer = Customer(company_name="Rif Demo SA", contact_name="Karim Test")
        db.add_all([customer, second_customer])
        db.flush()
        password_hash = hash_password("Password123!")
        db.add_all(
            [
                User(
                    first_name="Amine",
                    last_name="Admin",
                    email="admin@example.com",
                    password_hash=password_hash,
                    role=Role.ADMIN,
                ),
                User(
                    first_name="Meryem",
                    last_name="Manager",
                    email="manager@example.com",
                    password_hash=password_hash,
                    role=Role.MANAGER,
                ),
                User(
                    first_name="Youssef",
                    last_name="Agent",
                    email="agent@example.com",
                    password_hash=password_hash,
                    role=Role.AGENT,
                ),
                User(
                    first_name="Salma",
                    last_name="Agent",
                    email="agent2@example.com",
                    password_hash=password_hash,
                    role=Role.AGENT,
                ),
                User(
                    first_name="Nadia",
                    last_name="Client",
                    email="client@example.com",
                    password_hash=password_hash,
                    role=Role.CLIENT,
                    customer_id=customer.id,
                ),
                User(
                    first_name="Omar",
                    last_name="Client",
                    email="client2@example.com",
                    password_hash=password_hash,
                    role=Role.CLIENT,
                    customer_id=customer.id,
                ),
            ]
        )
        product = Product(name="Sage Demo", description="Synthetic test product")
        category = TicketCategory(name="Technical Incident")
        db.add_all([product, category])
        db.flush()
        db.add(ProductModule(product_id=product.id, name="Accounting Demo"))
        db.add_all(
            [
                SLAConfiguration(priority=Priority.LOW, target_hours=72),
                SLAConfiguration(priority=Priority.MEDIUM, target_hours=24),
                SLAConfiguration(priority=Priority.HIGH, target_hours=8),
                SLAConfiguration(priority=Priority.CRITICAL, target_hours=4),
            ]
        )
        db.commit()
    yield


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient):
    def factory(email: str) -> dict[str, str]:
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": "Password123!"},
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return factory


@pytest.fixture
def seed_ids() -> dict[str, int]:
    with TestingSessionLocal() as db:
        return {
            "customer": db.query(Customer).filter_by(company_name="Atlas Demo SARL").one().id,
            "category": db.query(TicketCategory).filter_by(name="Technical Incident").one().id,
            "module": db.query(ProductModule).filter_by(name="Accounting Demo").one().id,
            "agent": db.query(User).filter_by(email="agent@example.com").one().id,
            "agent2": db.query(User).filter_by(email="agent2@example.com").one().id,
        }
