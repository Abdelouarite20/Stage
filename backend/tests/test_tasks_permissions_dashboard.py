def _create_and_assign(client, manager, ids):
    ticket = client.post(
        "/api/tickets",
        json={
            "customer_id": ids["customer"],
            "subject": "Synthetic payroll configuration question",
            "description": "A test request used only by the automated suite.",
            "category_id": ids["category"],
            "module_id": ids["module"],
            "priority": "MEDIUM",
        },
        headers=manager,
    ).json()
    client.post(
        f"/api/tickets/{ticket['id']}/assign",
        json={"assigned_user_id": ids["agent"]},
        headers=manager,
    )
    return ticket


def test_task_creation_assignment_and_completion(client, auth_headers, seed_ids):
    manager = auth_headers("manager@example.com")
    agent = auth_headers("agent@example.com")
    ticket = _create_and_assign(client, manager, seed_ids)

    created = client.post(
        f"/api/tickets/{ticket['id']}/tasks",
        json={
            "title": "Reproduce the synthetic issue",
            "assigned_user_id": seed_ids["agent"],
        },
        headers=agent,
    )
    assert created.status_code == 201, created.text
    task = created.json()
    started = client.patch(
        f"/api/tasks/{task['id']}", json={"status": "IN_PROGRESS"}, headers=agent
    )
    assert started.status_code == 200
    blocked_without_reason = client.patch(
        f"/api/tasks/{task['id']}", json={"status": "BLOCKED"}, headers=agent
    )
    assert blocked_without_reason.status_code == 422
    completed = client.patch(
        f"/api/tasks/{task['id']}", json={"status": "DONE"}, headers=agent
    )
    assert completed.status_code == 200
    assert completed.json()["completed_at"] is not None

    pending = client.post(
        f"/api/tickets/{ticket['id']}/tasks",
        json={"title": "Pending closure check", "assigned_user_id": seed_ids["agent"]},
        headers=agent,
    ).json()
    client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "IN_PROGRESS"},
        headers=agent,
    )
    client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "RESOLVED", "resolution_summary": "Synthetic fix."},
        headers=agent,
    )
    client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "VALIDATED"},
        headers=manager,
    )
    blocked_close = client.post(
        f"/api/tickets/{ticket['id']}/status",
        json={"status": "CLOSED"},
        headers=manager,
    )
    assert blocked_close.status_code == 409
    cancelled = client.patch(
        f"/api/tasks/{pending['id']}",
        json={"status": "CANCELLED", "note": "No longer required after validation."},
        headers=manager,
    )
    assert cancelled.status_code == 200
    assert (
        client.post(
            f"/api/tickets/{ticket['id']}/status",
            json={"status": "CLOSED"},
            headers=manager,
        ).status_code
        == 200
    )


def test_role_permissions_and_client_ticket_isolation(client, auth_headers, seed_ids):
    client_one = auth_headers("client@example.com")
    client_two = auth_headers("client2@example.com")
    agent = auth_headers("agent@example.com")

    forbidden_user_create = client.post(
        "/api/users",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": "new@example.com",
            "password": "Password123!",
            "role": "AGENT",
        },
        headers=agent,
    )
    assert forbidden_user_create.status_code == 403

    ticket = client.post(
        "/api/tickets",
        json={
            "customer_id": 999999,
            "subject": "Client-created synthetic ticket",
            "description": "Customer id and priority are intentionally overridden.",
            "category_id": seed_ids["category"],
            "module_id": seed_ids["module"],
            "priority": "CRITICAL",
        },
        headers=client_one,
    )
    assert ticket.status_code == 201, ticket.text
    assert ticket.json()["customer_id"] == seed_ids["customer"]
    assert ticket.json()["priority"] == "MEDIUM"
    assert client.get(f"/api/tickets/{ticket.json()['id']}", headers=client_two).status_code == 404
    assert client.get(f"/api/tickets/{ticket.json()['id']}", headers=agent).status_code == 404
    own_detail = client.get(f"/api/tickets/{ticket.json()['id']}", headers=client_one)
    assert own_detail.status_code == 200
    assert own_detail.json()["tasks"] == []
    assert (
        client.get(f"/api/tickets/{ticket.json()['id']}/tasks", headers=client_one).status_code
        == 403
    )


def test_dashboard_kpis_are_role_scoped(client, auth_headers, seed_ids):
    manager = auth_headers("manager@example.com")
    agent = auth_headers("agent@example.com")
    _create_and_assign(client, manager, seed_ids)

    manager_dashboard = client.get("/api/dashboard/summary", headers=manager)
    assert manager_dashboard.status_code == 200, manager_dashboard.text
    assert manager_dashboard.json()["total_tickets"] == 1
    assert manager_dashboard.json()["open_tickets"] == 1

    agent_dashboard = client.get("/api/dashboard/summary", headers=agent)
    assert agent_dashboard.status_code == 200
    assert agent_dashboard.json()["total_tickets"] == 1
