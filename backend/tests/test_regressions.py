from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, true
from sqlalchemy.dialects import mssql

from app.models import (
    Notification,
    NotificationType,
    Priority,
    Product,
    ProductModule,
    SLAConfiguration,
    TaskStatus,
    Ticket,
    TicketHistory,
    TicketStatus,
    User,
    utc_now,
)
from app.services.notifications import refresh_deadline_notifications
from conftest import TestingSessionLocal


def _ticket_payload(ids: dict[str, int], *, subject: str = "Synthetic regression ticket") -> dict:
    return {
        "customer_id": ids["customer"],
        "subject": subject,
        "description": "Synthetic data used only by the backend regression suite.",
        "category_id": ids["category"],
        "module_id": ids["module"],
        "priority": "HIGH",
    }


def _create_ticket(client, headers: dict[str, str], ids: dict[str, int], **payload_overrides) -> dict:
    payload = _ticket_payload(ids)
    payload.update(payload_overrides)
    response = client.post("/api/tickets", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def _assign_ticket(client, manager: dict[str, str], ticket_id: int, assignee_id: int) -> None:
    response = client.post(
        f"/api/tickets/{ticket_id}/assign",
        json={"assigned_user_id": assignee_id},
        headers=manager,
    )
    assert response.status_code == 200, response.text


def _start_ticket(client, agent: dict[str, str], ticket_id: int) -> None:
    response = client.post(
        f"/api/tickets/{ticket_id}/status",
        json={"status": "IN_PROGRESS"},
        headers=agent,
    )
    assert response.status_code == 200, response.text


def _resolve_ticket(client, agent: dict[str, str], ticket_id: int) -> None:
    response = client.post(
        f"/api/tickets/{ticket_id}/status",
        json={"status": "RESOLVED", "resolution_summary": "Synthetic resolution."},
        headers=agent,
    )
    assert response.status_code == 200, response.text


def _create_assigned_started_ticket(client, manager, agent, ids) -> dict:
    ticket = _create_ticket(client, manager, ids)
    _assign_ticket(client, manager, ticket["id"], ids["agent"])
    _start_ticket(client, agent, ticket["id"])
    return ticket


def test_agent_cannot_reject_own_resolution(client, auth_headers, seed_ids):
    manager = auth_headers("manager@example.com")
    agent = auth_headers("agent@example.com")
    ticket = _create_assigned_started_ticket(client, manager, agent, seed_ids)
    _resolve_ticket(client, agent, ticket["id"])

    rejected_by_agent = client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "IN_PROGRESS", "note": "Resolution needs more work."},
        headers=agent,
    )
    assert rejected_by_agent.status_code == 403, rejected_by_agent.text

    unchanged = client.get(f"/api/tickets/{ticket['id']}", headers=manager).json()
    assert unchanged["status"] == "RESOLVED"
    assert unchanged["resolved_at"] is not None

    manager_rejection = client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "IN_PROGRESS", "note": "Manager-requested correction."},
        headers=manager,
    )
    assert manager_rejection.status_code == 200, manager_rejection.text


def test_agent_cannot_update_a_task_owned_by_another_agent(client, auth_headers, seed_ids):
    manager = auth_headers("manager@example.com")
    agent = auth_headers("agent@example.com")
    ticket = _create_ticket(client, manager, seed_ids)
    _assign_ticket(client, manager, ticket["id"], seed_ids["agent"])

    task = client.post(
        f"/api/tickets/{ticket['id']}/tasks",
        json={"title": "Work owned by agent two", "assigned_user_id": seed_ids["agent2"]},
        headers=manager,
    )
    assert task.status_code == 201, task.text

    forbidden = client.patch(
        f"/api/tasks/{task.json()['id']}",
        json={"title": "Unauthorized rewrite"},
        headers=agent,
    )
    assert forbidden.status_code == 403, forbidden.text

    detail = client.get(f"/api/tickets/{ticket['id']}", headers=manager).json()
    stored = next(item for item in detail["tasks"] if item["id"] == task.json()["id"])
    assert stored["title"] == "Work owned by agent two"


def test_terminal_task_is_immutable(client, auth_headers, seed_ids):
    manager = auth_headers("manager@example.com")
    agent = auth_headers("agent@example.com")
    ticket = _create_ticket(client, manager, seed_ids)
    _assign_ticket(client, manager, ticket["id"], seed_ids["agent"])

    task = client.post(
        f"/api/tickets/{ticket['id']}/tasks",
        json={"title": "Terminal work", "assigned_user_id": seed_ids["agent"]},
        headers=agent,
    ).json()
    assert (
        client.patch(
            f"/api/tasks/{task['id']}", json={"status": "IN_PROGRESS"}, headers=agent
        ).status_code
        == 200
    )
    completed = client.patch(
        f"/api/tasks/{task['id']}", json={"status": "DONE"}, headers=agent
    )
    assert completed.status_code == 200, completed.text
    completed_at = completed.json()["completed_at"]

    rewritten = client.patch(
        f"/api/tasks/{task['id']}", json={"title": "Rewritten terminal work"}, headers=manager
    )
    assert rewritten.status_code == 409, rewritten.text

    stored = client.get(f"/api/tickets/{ticket['id']}/tasks", headers=manager).json()[0]
    assert stored["title"] == "Terminal work"
    assert stored["completed_at"] == completed_at


def test_task_on_closed_ticket_is_immutable(client, auth_headers, seed_ids):
    manager = auth_headers("manager@example.com")
    ticket = _create_ticket(client, manager, seed_ids)
    task = client.post(
        f"/api/tickets/{ticket['id']}/tasks",
        json={"title": "Unexpected legacy task"},
        headers=manager,
    ).json()

    # Simulate legacy/inconsistent data so the route itself must enforce the closed-ticket lock.
    with TestingSessionLocal() as db:
        stored_ticket = db.get(Ticket, ticket["id"])
        stored_ticket.status = TicketStatus.CLOSED
        stored_ticket.closed_at = utc_now()
        db.commit()

    response = client.patch(
        f"/api/tasks/{task['id']}", json={"title": "Changed after closure"}, headers=manager
    )
    assert response.status_code == 409, response.text


def test_required_patch_fields_reject_explicit_null(client, auth_headers, seed_ids):
    admin = auth_headers("admin@example.com")
    manager = auth_headers("manager@example.com")
    ticket = _create_ticket(client, manager, seed_ids)
    task = client.post(
        f"/api/tickets/{ticket['id']}/tasks",
        json={"title": "Required field validation"},
        headers=manager,
    ).json()

    with TestingSessionLocal() as db:
        product_id = db.get(ProductModule, seed_ids["module"]).product_id

    cases = [
        (f"/api/users/{seed_ids['agent']}", {"email": None}, admin),
        (f"/api/customers/{seed_ids['customer']}", {"company_name": None}, manager),
        (f"/api/catalog/products/{product_id}", {"name": None}, admin),
        (f"/api/catalog/modules/{seed_ids['module']}", {"name": None}, admin),
        (f"/api/catalog/categories/{seed_ids['category']}", {"name": None}, admin),
        (f"/api/tickets/{ticket['id']}", {"subject": None}, manager),
        (f"/api/tasks/{task['id']}", {"title": None}, manager),
        (f"/api/tasks/{task['id']}", {"status": None}, manager),
    ]
    for path, payload, headers in cases:
        response = client.patch(path, json=payload, headers=headers)
        assert response.status_code == 422, f"{path} accepted {payload}: {response.text}"


def test_reopened_sla_cycle_creates_a_new_overdue_alert(client, auth_headers, seed_ids):
    manager = auth_headers("manager@example.com")
    agent = auth_headers("agent@example.com")
    ticket = _create_ticket(client, manager, seed_ids)
    _assign_ticket(client, manager, ticket["id"], seed_ids["agent"])

    with TestingSessionLocal() as db:
        stored = db.get(Ticket, ticket["id"])
        stored.sla_deadline = datetime(2026, 1, 1, 12, 0, 0)
        db.commit()

    first_cycle = client.get("/api/notifications", headers=agent)
    assert first_cycle.status_code == 200, first_cycle.text
    first_ids = {
        item["id"] for item in first_cycle.json() if item["type"] == "SLA_OVERDUE"
    }
    assert len(first_ids) == 1

    _start_ticket(client, agent, ticket["id"])
    _resolve_ticket(client, agent, ticket["id"])
    assert (
        client.post(
            f"/api/tickets/{ticket['id']}/status",
            json={"status": "VALIDATED"},
            headers=manager,
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/tickets/{ticket['id']}/status",
            json={"status": "CLOSED"},
            headers=manager,
        ).status_code
        == 200
    )
    reopened = client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "REOPENED", "note": "Synthetic recurrence."},
        headers=manager,
    )
    assert reopened.status_code == 200, reopened.text

    with TestingSessionLocal() as db:
        stored = db.get(Ticket, ticket["id"])
        stored.sla_deadline = datetime(2026, 2, 1, 12, 0, 0)
        db.commit()

    second_cycle = client.get("/api/notifications", headers=agent)
    assert second_cycle.status_code == 200, second_cycle.text
    overdue_ids = {
        item["id"] for item in second_cycle.json() if item["type"] == "SLA_OVERDUE"
    }
    assert len(overdue_ids) == 2
    assert first_ids < overdue_ids


def test_existing_ticket_warning_uses_its_persisted_cycle_duration(
    client, auth_headers, seed_ids, monkeypatch
):
    manager = auth_headers("manager@example.com")
    ticket = _create_ticket(client, manager, seed_ids)
    _assign_ticket(client, manager, ticket["id"], seed_ids["agent"])
    cycle_start = datetime(2026, 1, 1, 0, 0, 0)

    with TestingSessionLocal() as db:
        stored = db.get(Ticket, ticket["id"])
        stored.created_at = cycle_start
        stored.sla_deadline = cycle_start + timedelta(hours=10)
        configuration = db.scalar(
            select(SLAConfiguration).where(SLAConfiguration.priority == Priority.HIGH)
        )
        # A later policy edit must not make an existing ticket warn earlier.
        configuration.target_hours = 20
        configuration.warning_threshold_percent = 80
        db.commit()

    monkeypatch.setattr(
        "app.services.notifications.utc_now", lambda: cycle_start + timedelta(hours=7)
    )
    with TestingSessionLocal() as db:
        assert refresh_deadline_notifications(db) == 0
        assert db.scalar(
            select(Notification.id).where(
                Notification.ticket_id == ticket["id"],
                Notification.type == NotificationType.SLA_WARNING,
            )
        ) is None

    monkeypatch.setattr(
        "app.services.notifications.utc_now", lambda: cycle_start + timedelta(hours=9)
    )
    with TestingSessionLocal() as db:
        assert refresh_deadline_notifications(db) == 1
        assert db.scalar(
            select(Notification.id).where(
                Notification.ticket_id == ticket["id"],
                Notification.type == NotificationType.SLA_WARNING,
            )
        ) is not None


def test_inactive_module_is_rejected_for_new_ticket(client, auth_headers, seed_ids):
    admin = auth_headers("admin@example.com")
    manager = auth_headers("manager@example.com")
    deactivated = client.patch(
        f"/api/catalog/modules/{seed_ids['module']}",
        json={"is_active": False},
        headers=admin,
    )
    assert deactivated.status_code == 200, deactivated.text

    response = client.post(
        "/api/tickets", json=_ticket_payload(seed_ids), headers=manager
    )
    assert response.status_code == 422, response.text


def test_module_of_inactive_product_is_hidden_and_rejected(client, auth_headers, seed_ids):
    admin = auth_headers("admin@example.com")
    manager = auth_headers("manager@example.com")
    with TestingSessionLocal() as db:
        product_id = db.get(ProductModule, seed_ids["module"]).product_id

    deactivated = client.patch(
        f"/api/catalog/products/{product_id}",
        json={"is_active": False},
        headers=admin,
    )
    assert deactivated.status_code == 200, deactivated.text

    active_modules = client.get("/api/catalog/modules", headers=manager)
    assert active_modules.status_code == 200, active_modules.text
    assert seed_ids["module"] not in {item["id"] for item in active_modules.json()}

    response = client.post(
        "/api/tickets", json=_ticket_payload(seed_ids), headers=manager
    )
    assert response.status_code == 422, response.text


@pytest.mark.parametrize("final_status", ["RESOLVED", "VALIDATED"])
def test_priority_cannot_change_after_resolution(
    final_status, client, auth_headers, seed_ids
):
    manager = auth_headers("manager@example.com")
    agent = auth_headers("agent@example.com")
    ticket = _create_assigned_started_ticket(client, manager, agent, seed_ids)
    _resolve_ticket(client, agent, ticket["id"])
    if final_status == "VALIDATED":
        validation = client.post(
            f"/api/tickets/{ticket['id']}/status",
            json={"status": "VALIDATED"},
            headers=manager,
        )
        assert validation.status_code == 200, validation.text

    before = client.get(f"/api/tickets/{ticket['id']}", headers=manager).json()
    response = client.post(
        f"/api/tickets/{ticket['id']}/priority",
        json={"priority": "LOW"},
        headers=manager,
    )
    assert response.status_code == 409, response.text
    after = client.get(f"/api/tickets/{ticket['id']}", headers=manager).json()
    assert after["status"] == final_status
    assert after["priority"] == before["priority"]
    assert after["sla_deadline"] == before["sla_deadline"]


def test_task_due_date_cannot_be_changed_to_the_past(client, auth_headers, seed_ids):
    manager = auth_headers("manager@example.com")
    ticket = _create_ticket(client, manager, seed_ids)
    future_due = datetime.now(timezone.utc) + timedelta(hours=2)
    task = client.post(
        f"/api/tickets/{ticket['id']}/tasks",
        json={"title": "Future work", "due_date": future_due.isoformat()},
        headers=manager,
    )
    assert task.status_code == 201, task.text

    past_due = datetime.now(timezone.utc) - timedelta(minutes=1)
    rejected = client.patch(
        f"/api/tasks/{task.json()['id']}",
        json={"due_date": past_due.isoformat()},
        headers=manager,
    )
    assert rejected.status_code == 422, rejected.text

    stored = client.get(f"/api/tickets/{ticket['id']}/tasks", headers=manager).json()[0]
    assert stored["due_date"] == task.json()["due_date"]


def test_task_reassignment_notifies_the_new_assignee(client, auth_headers, seed_ids):
    manager = auth_headers("manager@example.com")
    agent_two = auth_headers("agent2@example.com")
    ticket = _create_ticket(client, manager, seed_ids)
    task = client.post(
        f"/api/tickets/{ticket['id']}/tasks",
        json={"title": "Reassigned work"},
        headers=manager,
    )
    assert task.status_code == 201, task.text

    reassigned = client.patch(
        f"/api/tasks/{task.json()['id']}",
        json={"assigned_user_id": seed_ids["agent2"]},
        headers=manager,
    )
    assert reassigned.status_code == 200, reassigned.text

    notifications = client.get("/api/notifications", headers=agent_two)
    assert notifications.status_code == 200, notifications.text
    assignment_alerts = [
        item
        for item in notifications.json()
        if item["title"] == "Task assigned" and item["ticket_id"] == ticket["id"]
    ]
    assert len(assignment_alerts) == 1
    assert f"Task #{task.json()['id']}" in assignment_alerts[0]["message"]


def test_history_uses_id_as_tie_breaker(client, auth_headers, seed_ids):
    manager = auth_headers("manager@example.com")
    ticket = _create_ticket(client, manager, seed_ids)
    _assign_ticket(client, manager, ticket["id"], seed_ids["agent"])
    tied_timestamp = datetime(2026, 1, 1, 12, 0, 0)

    with TestingSessionLocal() as db:
        events = list(
            db.scalars(
                select(TicketHistory).where(TicketHistory.ticket_id == ticket["id"])
            ).all()
        )
        assert len(events) >= 2
        for event in events:
            event.created_at = tied_timestamp
        db.commit()

    history = client.get(f"/api/tickets/{ticket['id']}/history", headers=manager)
    assert history.status_code == 200, history.text
    history_ids = [item["id"] for item in history.json()]
    assert history_ids == sorted(history_ids)

    detail = client.get(f"/api/tickets/{ticket['id']}", headers=manager)
    assert detail.status_code == 200, detail.text
    detail_ids = [item["id"] for item in detail.json()["history"]]
    assert detail_ids == sorted(detail_ids)


def test_openapi_describes_http_bearer_authentication(client):
    schema = client.get("/openapi.json").json()
    security_schemes = schema["components"]["securitySchemes"]
    bearer_schemes = [
        value
        for value in security_schemes.values()
        if value.get("type") == "http" and value.get("scheme", "").lower() == "bearer"
    ]
    assert bearer_schemes
    assert all(value.get("type") != "oauth2" for value in security_schemes.values())


def test_mssql_boolean_unicode_and_datetime_mappings_match_the_live_schema():
    dialect = mssql.dialect()
    boolean_sql = str(
        select(Product.id)
        .where(Product.is_active == true())
        .compile(dialect=dialect, compile_kwargs={"literal_binds": True})
    )

    assert "products.is_active = 1" in boolean_sql
    assert "products.is_active IS 1" not in boolean_sql
    assert User.first_name.type.compile(dialect=dialect) == "NVARCHAR(100)"
    assert Ticket.description.type.compile(dialect=dialect) == "NVARCHAR(max)"
    assert Ticket.created_at.type.compile(dialect=dialect) == "DATETIME2(0)"
