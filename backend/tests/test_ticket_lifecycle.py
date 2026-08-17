from datetime import datetime, timedelta, timezone


def _ticket_payload(ids, priority="HIGH"):
    return {
        "customer_id": ids["customer"],
        "subject": "Synthetic accounting export failure",
        "description": "The fictional customer cannot export an accounting journal.",
        "category_id": ids["category"],
        "module_id": ids["module"],
        "priority": priority,
    }


def test_complete_ticket_workflow_and_audit(client, auth_headers, seed_ids):
    manager = auth_headers("manager@example.com")
    agent = auth_headers("agent@example.com")

    created = client.post("/api/tickets", json=_ticket_payload(seed_ids), headers=manager)
    assert created.status_code == 201, created.text
    ticket = created.json()
    assert ticket["status"] == "NEW"
    assert ticket["reference"].startswith("TKT-")
    assert ticket["sla_deadline"] is not None

    assigned = client.post(
        f"/api/tickets/{ticket['id']}/assign",
        json={"assigned_user_id": seed_ids["agent"]},
        headers=manager,
    )
    assert assigned.status_code == 200
    assert assigned.json()["status"] == "ASSIGNED"

    changed_priority = client.post(
        f"/api/tickets/{ticket['id']}/priority",
        json={"priority": "CRITICAL"},
        headers=manager,
    )
    assert changed_priority.status_code == 200
    assert changed_priority.json()["priority"] == "CRITICAL"

    in_progress = client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "IN_PROGRESS"},
        headers=agent,
    )
    assert in_progress.status_code == 200

    resolved = client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "RESOLVED", "resolution_summary": "Synthetic correction applied."},
        headers=agent,
    )
    assert resolved.status_code == 200
    assert resolved.json()["resolved_at"] is not None

    validated = client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "VALIDATED"},
        headers=manager,
    )
    assert validated.status_code == 200
    closed = client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "CLOSED"},
        headers=manager,
    )
    assert closed.status_code == 200

    reopened = client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "REOPENED", "note": "Synthetic issue recurred."},
        headers=manager,
    )
    assert reopened.status_code == 200
    assert reopened.json()["sla_deadline"] > closed.json()["sla_deadline"]

    history = client.get(f"/api/tickets/{ticket['id']}/history", headers=manager)
    assert history.status_code == 200
    event_types = [item["event_type"] for item in history.json()]
    assert event_types == [
        "TICKET_CREATED",
        "TICKET_ASSIGNED",
        "PRIORITY_CHANGED",
        "STATUS_IN_PROGRESS",
        "STATUS_RESOLVED",
        "STATUS_VALIDATED",
        "STATUS_CLOSED",
        "STATUS_REOPENED",
    ]


def test_invalid_workflow_transition_is_rejected(client, auth_headers, seed_ids):
    manager = auth_headers("manager@example.com")
    ticket = client.post("/api/tickets", json=_ticket_payload(seed_ids), headers=manager).json()
    response = client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "CLOSED"},
        headers=manager,
    )
    assert response.status_code == 409


def test_waiting_transition_requires_a_reason(client, auth_headers, seed_ids):
    manager = auth_headers("manager@example.com")
    agent = auth_headers("agent@example.com")
    ticket = client.post("/api/tickets", json=_ticket_payload(seed_ids), headers=manager).json()
    client.post(
        f"/api/tickets/{ticket['id']}/assign",
        json={"assigned_user_id": seed_ids["agent"]},
        headers=manager,
    )
    client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "IN_PROGRESS"},
        headers=agent,
    )
    missing_reason = client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "WAITING"},
        headers=agent,
    )
    assert missing_reason.status_code == 422
    accepted = client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "WAITING", "note": "Awaiting synthetic customer input."},
        headers=agent,
    )
    assert accepted.status_code == 200


def test_sla_deadline_and_overdue_filter(client, auth_headers, seed_ids):
    manager = auth_headers("manager@example.com")
    ticket = client.post(
        "/api/tickets", json=_ticket_payload(seed_ids, "CRITICAL"), headers=manager
    ).json()
    created = datetime.fromisoformat(ticket["created_at"])
    deadline = datetime.fromisoformat(ticket["sla_deadline"])
    assert timedelta(hours=3, minutes=59) <= deadline - created <= timedelta(hours=4, minutes=1)

    from app.models import Ticket
    from conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        stored = db.get(Ticket, ticket["id"])
        stored.sla_deadline = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
        db.commit()

    overdue = client.get("/api/tickets?sla_status=OVERDUE", headers=manager)
    assert overdue.status_code == 200
    assert overdue.json()["total"] == 1
    assert overdue.json()["items"][0]["sla_status"] == "OVERDUE"
