# Alias Ticketing

Alias Ticketing is a web application for centralizing customer requests and monitoring support work at Alias Informatique. It is intentionally designed as a clear, defendable Licence 3 MIAGE project: one Angular frontend, one FastAPI REST API, and one Microsoft SQL Server database.

> Assumption — to be validated with Alias Informatique.
>
> The proposed roles, workflow, catalogue, SLA values, and notification recipients are working rules because the company's detailed internal process has not yet been confirmed.

## What is implemented

- JWT login, logout on the client, protected routes, Argon2 password hashing, and role-based authorization;
- four roles: `ADMIN`, `MANAGER`, `AGENT`, and `CLIENT`;
- users, customers, products, modules, categories, and priority-based SLA configuration;
- ticket creation, search, filters, assignment, priority changes, comments, history, and guarded workflow transitions;
- internal ticket tasks with assignment, deadlines, status workflow, and completion tracking;
- SLA deadlines, on-track/overdue/met/breached states, approaching/overdue in-app alerts, and task alerts;
- role-scoped dashboard KPIs and workload summaries;
- responsive Angular screens for the operational workflow;
- a normalized SQL Server schema and entirely synthetic seed data;
- automated backend and frontend tests plus detailed acceptance scenarios.

The ticket workflow is:

```text
NEW -> ASSIGNED -> IN_PROGRESS -> WAITING -> IN_PROGRESS
                              \-> RESOLVED -> VALIDATED -> CLOSED
                                                        \-> REOPENED -> IN_PROGRESS
```

Only valid transitions are accepted. Resolving requires a summary; waiting, rejecting a resolution, and reopening require a reason; closing requires every task to be `DONE` or `CANCELLED`.

## Repository layout

```text
backend/    FastAPI application and pytest suite
database/   SQL Server schema and synthetic reference seed
frontend/   Angular application and unit tests
docs/       Requirements, specification, architecture, API, setup, and status
```

## Quick start

Prerequisites:

- Python 3.12;
- Node.js 24.15 or later in the Node 24 line;
- Microsoft SQL Server and ODBC Driver 18 for SQL Server;
- optional: SQL Server Management Studio or `sqlcmd`.

This local path has been validated against a live SQL Server 2022 Developer default instance (`MSSQLSERVER`) through Microsoft ODBC Driver 18 x64, using Windows Authentication. See [Installation and operation](docs/installation.md) for the fuller database procedure and operational notes.

1. Create an empty SQL Server database named `alias_ticketing`.
2. Run [schema.sql](database/schema.sql), then optionally [seed.sql](database/seed.sql), against that database.
3. Copy `.env.example` to `.env`, generate a local `SECRET_KEY`, and set a one-time `BOOTSTRAP_ADMIN_PASSWORD` locally:

```powershell
Copy-Item .env.example .env
```

The primary example uses the current Windows identity and the local default SQL Server instance, so it contains no database password:

```text
DATABASE_URL=mssql+pyodbc://@localhost/alias_ticketing?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes&trusted_connection=yes
```

With no user name or password in this URL, `trusted_connection=yes` uses the current Windows identity. `Encrypt=yes` makes encryption explicit. `TrustServerCertificate=yes` permits the self-signed certificate commonly presented by a local development instance, but it disables certificate-chain and host-name validation. Keep it local-only; for a shared, remote, or production database, install a trusted certificate and remove that option.

4. Start the API:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Calling the virtual-environment interpreter directly avoids relying on PowerShell script activation.

5. Start Angular in another terminal:

```powershell
cd frontend
npm.cmd install
npm.cmd start
```

Open `http://localhost:4200`. The API documentation is available at `http://localhost:8000/docs`.

No deployable user credential is committed or inserted by the seed script; automated tests use isolated synthetic fixtures only. On the first API start, a bootstrap administrator is created only if `BOOTSTRAP_ADMIN_PASSWORD` is non-empty. Remove that value from the local `.env` after the account exists.

The Windows Authentication URL is the validated local default; `.env.example` also documents an opt-in SQL-login alternative without embedding credentials. See [Installation and operation](docs/installation.md) for SQL Server and demonstration-database details.

## Verification

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
```

Frontend:

```powershell
cd frontend
npm.cmd test
npm.cmd run build
```

See [Testing](docs/testing.md) for the complete automated and manual test scope, and [Project status](docs/project-status.md) for the wider delivery checklist.

## Documentation

- [Requirements analysis](docs/requirements-analysis.md)
- [Functional specification](docs/functional-specification.md)
- [Technical architecture](docs/architecture.md)
- [Database design](docs/database-design.md)
- [API overview](docs/api-overview.md)
- [Installation and operation](docs/installation.md)
- [Testing and UAT](docs/testing.md)
- [Project status](docs/project-status.md)

## Security decisions

- Secrets and database credentials come from environment variables and `.env` is ignored by Git.
- Passwords are stored only as Argon2 hashes.
- SQLAlchemy parameterizes database access.
- Every protected endpoint authenticates the user; sensitive actions also check role and ticket scope.
- A client account can see only tickets created by that same account and cannot see internal tasks.
- Closed tickets cannot be edited directly, and important actions are written to ticket history.

This is a serious educational MVP, not production infrastructure. Rate limiting, refresh-token revocation, password recovery, attachment storage, email delivery, a business-hours SLA calendar, scheduled workers, and external-system integration remain explicit future improvements.
