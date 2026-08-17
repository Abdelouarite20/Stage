from datetime import datetime, timedelta, timezone


def test_admin_manages_reference_data_and_users(client, auth_headers):
    admin = auth_headers("admin@example.com")
    manager = auth_headers("manager@example.com")

    customer = client.post(
        "/api/customers",
        json={
            "company_name": "Synthetic Casablanca Services",
            "contact_name": "Test Contact",
            "email": "contact@example.com",
        },
        headers=manager,
    )
    assert customer.status_code == 201

    user = client.post(
        "/api/users",
        json={
            "first_name": "Portal",
            "last_name": "Tester",
            "email": "portal@example.com",
            "password": "Password123!",
            "role": "CLIENT",
            "customer_id": customer.json()["id"],
        },
        headers=admin,
    )
    assert user.status_code == 201, user.text
    assert user.json()["customer_id"] == customer.json()["id"]

    product = client.post(
        "/api/catalog/products",
        json={"name": "Synthetic ERP", "description": "Automated test data"},
        headers=admin,
    )
    assert product.status_code == 201
    module = client.post(
        "/api/catalog/modules",
        json={"product_id": product.json()["id"], "name": "Test Module"},
        headers=admin,
    )
    assert module.status_code == 201
    assert (
        client.post(
            "/api/catalog/categories",
            json={"name": "Manager must not configure"},
            headers=manager,
        ).status_code
        == 403
    )
    sla = client.put(
        "/api/catalog/sla/HIGH",
        json={"target_hours": 6, "warning_threshold_percent": 75, "is_active": True},
        headers=admin,
    )
    assert sla.status_code == 200
    assert sla.json()["target_hours"] == 6


def test_ticket_edit_comment_assignment_notification_and_sla_alert(
    client, auth_headers, seed_ids
):
    manager = auth_headers("manager@example.com")
    agent = auth_headers("agent@example.com")
    ticket = client.post(
        "/api/tickets",
        json={
            "customer_id": seed_ids["customer"],
            "subject": "Initial synthetic subject",
            "description": "Initial synthetic description for an integration test.",
            "category_id": seed_ids["category"],
            "module_id": seed_ids["module"],
            "priority": "HIGH",
        },
        headers=manager,
    ).json()

    edited = client.patch(
        f"/api/tickets/{ticket['id']}",
        json={"subject": "Updated synthetic subject"},
        headers=manager,
    )
    assert edited.status_code == 200
    assert edited.json()["subject"] == "Updated synthetic subject"

    client.post(
        f"/api/tickets/{ticket['id']}/assign",
        json={"assigned_user_id": seed_ids["agent"]},
        headers=manager,
    )
    comment = client.post(
        f"/api/tickets/{ticket['id']}/comments",
        json={"content": "Synthetic diagnostic note."},
        headers=agent,
    )
    assert comment.status_code == 201

    assignment_notifications = client.get("/api/notifications", headers=agent)
    assert assignment_notifications.status_code == 200
    assert any(item["type"] == "ASSIGNMENT" for item in assignment_notifications.json())

    from app.models import Ticket
    from conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        stored = db.get(Ticket, ticket["id"])
        stored.sla_deadline = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=5)
        db.commit()

    alerts = client.get("/api/notifications", headers=agent)
    assert any(item["type"] == "SLA_OVERDUE" for item in alerts.json())
    alerts_again = client.get("/api/notifications", headers=agent)
    assert sum(item["type"] == "SLA_OVERDUE" for item in alerts_again.json()) == 1


def test_health_and_password_change(client, auth_headers):
    assert client.get("/health").json() == {"status": "ok"}
    admin = auth_headers("admin@example.com")
    changed = client.post(
        "/api/auth/change-password",
        json={"current_password": "Password123!", "new_password": "NewPassword123!"},
        headers=admin,
    )
    assert changed.status_code == 200
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "NewPassword123!"},
        ).status_code
        == 200
    )


def test_literal_search_handles_unicode_and_sql_server_like_metacharacters(
    client, auth_headers
):
    manager = auth_headers("manager@example.com")
    company_name = "Unicode [SQL]%_ العربية 中文 🚀"
    created = client.post(
        "/api/customers",
        json={
            "company_name": company_name,
            "contact_name": "Élodie مثال 測試",
            "email": "unicode-search@example.com",
        },
        headers=manager,
    )
    assert created.status_code == 201, created.text

    searched = client.get(
        "/api/customers",
        params={"search": "[SQL]%_ العربية", "active_only": "false"},
        headers=manager,
    )
    assert searched.status_code == 200, searched.text
    assert any(item["company_name"] == company_name for item in searched.json())
