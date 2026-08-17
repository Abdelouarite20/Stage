# Initial technical architecture

## 1. Purpose and starting point

This document defines the target architecture for the Alias Informatique ticket-management and monitoring application. The workspace contained no frontend, backend, database schema, documentation, or tests when the initial design work began. The decisions below therefore form the project's technical foundation and must be refined only when implementation evidence or validated business feedback requires it.

The objective is not a distributed enterprise platform. It is a complete, understandable, testable, and demonstrable Licence 3 MIAGE application.

## 2. Architecture principles

- Angular provides the user interface.
- A FastAPI REST API, prefixed by `/api` by default, is the only application entry point to data.
- SQLAlchemy provides access to Microsoft SQL Server.
- The backend is a modular monolith: one deployed application organized by functional responsibility.
- Layers remain short and explicit: API route, Pydantic schema, business service where justified, and SQLAlchemy model/query.
- Workflow, authorization, and SLA rules are enforced by the backend.
- Authentication uses JWT and authorization uses role-based access control (RBAC).
- Configuration and secrets are supplied through environment variables.
- `database/schema.sql` versions the SQL Server schema and is kept consistent with the SQLAlchemy models.
- JSON is used at the API boundary, with ISO 8601 UTC date-time values.

Microservices, message brokers, Kubernetes, a BPM engine, and a generic repository layer are deliberately excluded. They would add complexity without proportional value for this project.

## 3. Business assumptions to validate

Every item in this section has the following status: **Assumption — to be validated with Alias Informatique.**

1. The application is a single installation for Alias Informatique; it is not a multi-tenant SaaS platform.
2. A `CLIENT` account is linked to one customer and may see only tickets created by that account for the linked customer. Extending access to every ticket for the company would require business validation.
3. Internal users (`ADMIN`, `MANAGER`, and `AGENT`) may create a ticket for any active customer.
4. A `MANAGER` validates and closes tickets. Clients follow progress and comment but do not directly change workflow status.
5. The MVP SLA target depends only on ticket priority. Customer-, category-, product-, and module-specific rules are possible future extensions.
6. SLA durations use continuous clock hours. Weekends, nights, holidays, and time spent in `WAITING` are not paused.
7. Reopening starts a new SLA cycle from the reopening action with the ticket's current priority. The former deadline remains available in ticket history.
8. Tasks are internal. A client sees overall ticket progress but not internal tasks.
9. Attachments are outside the implemented MVP. A storage and access-control policy must be validated before adding them.
10. Expected traffic is that of a small team. Pagination and a limited set of targeted indexes are sufficient; no distributed cache is needed.

These assumptions must not be presented as confirmed company rules.

## 4. System overview

```text
Browser
  |
  | HTTPS, JSON, Authorization: Bearer <JWT>
  v
Angular application
  - components and forms
  - typed HTTP services
  - route guard and authentication interceptor
  |
  | REST /api
  v
FastAPI modular monolith
  - routes and Pydantic validation
  - authentication and RBAC
  - ticket, workflow, task, SLA, audit, and notification logic
  - SQLAlchemy queries
  |
  | pyodbc / SQL transactions
  v
Microsoft SQL Server
```

Angular never receives SQL Server credentials and never communicates with the database directly. FastAPI owns input validation, authorization, transactions, and the public API contract.

## 5. Repository organization

The initial backend is intentionally compact; Angular can grow by feature as screens are implemented.

```text
frontend/
  src/app/
    core/                  # API, authentication, guards, interceptor, models
    features/              # feature screens as the UI grows
      auth/
      dashboard/
      tickets/
      customers/
      users/
      catalog/
      notifications/
    shared/                # reusable presentation components when needed

backend/
  app/
    main.py                # FastAPI application creation
    config.py              # environment configuration
    database.py            # SQLAlchemy engine, session factory, and base
    dependencies.py        # current user, role checks, and data scope
    security.py            # password hashing and JWT handling
    models.py              # enums and SQLAlchemy models
    schemas.py             # Pydantic request and response schemas
    routers/               # auth, users, customers, catalog, tickets, etc.
    services/              # workflow, SLA, audit, and notification rules
  tests/
  requirements.txt

database/
  schema.sql               # idempotent SQL Server schema creation
  seed.sql                 # entirely synthetic demonstration data

docs/
```

The design does not require one class per operation. Routers coordinate dependencies, permissions, and the SQLAlchemy transaction. Reused or sensitive rules live in short services (`workflow`, `sla`, `audit`, and `notifications`); straightforward CRUD remains readable in its router. A repository abstraction should be introduced only if actual duplication justifies it.

## 6. Layer responsibilities

### Angular

- displays pages and components;
- uses reactive forms for immediate user feedback;
- calls only `/api` through typed HTTP services;
- adds the JWT through an HTTP interceptor;
- protects navigation with authentication and role guards;
- presents API errors without exposing technical details.

Angular guards improve the user experience but are not a security boundary. FastAPI repeats every authorization check.

### FastAPI routes and Pydantic schemas

- declare URLs, parameters, response codes, and request/response schemas;
- reject malformed input;
- obtain the current user and SQLAlchemy session through dependencies;
- apply role and data-scope restrictions;
- coordinate `commit`/`rollback` and delegate cross-cutting rules to services.

### Business services

- apply the ticket workflow; the small task transition graph remains local to the task router;
- calculate SLA deadlines and warning conditions;
- construct history events and notifications inside the route's transaction;
- prevent important rules from being duplicated across endpoints.

### SQLAlchemy and SQL Server

- SQLAlchemy 2.x is used synchronously, which is simple to explain and sufficient for the expected load.
- `pyodbc` and Microsoft ODBC Driver for SQL Server provide connectivity.
- primary keys, foreign keys, unique constraints, checks, and targeted indexes enforce data integrity.
- SQLAlchemy parameter binding prevents SQL injection caused by string-built queries.
- `database/schema.sql` is the normal SQL Server creation mechanism; `AUTO_CREATE_TABLES` is an explicitly disabled-by-default classroom/demo convenience.

## 7. Modules in the monolith

| Module | Main responsibility |
|---|---|
| Authentication | Login, current user, password change, JWT issue and validation |
| Users | Accounts, one role per user, activation/deactivation, optional customer link |
| Customers | Customer-company contact information and active status |
| Catalog | Configurable products, modules, and ticket categories |
| SLA | Configurable target per priority and deadline calculation |
| Tickets | Creation, scoped search, permitted updates, and detail retrieval |
| Workflow | Assignment, processing, resolution, validation, closure, and reopening |
| Tasks | Internal work planning and tracking within a ticket |
| Comments | Immutable chronological discussion |
| History | Backend-generated ticket events, exposed read-only |
| Notifications | In-application alerts and read/unread state |
| Dashboard | SQL aggregates restricted to the current user's ticket scope |

All modules run in one FastAPI process and share one database while retaining clear responsibilities.

## 8. Authentication and authorization

### 8.1 JWT authentication

1. The browser sends a normalized email and password to `POST /api/auth/login`.
2. The backend compares the password with an Argon2 hash. Unknown email, wrong password, and inactive account return the same generic error.
3. The backend issues an `HS256` JWT with a configurable short lifetime (60 minutes by default).
4. Angular stores it for the browser session and sends `Authorization: Bearer ...`.
5. For every protected request, FastAPI verifies the signature and expiry, then reloads the user from the database. The current database role and `is_active` state remain authoritative.
6. Logout is an Angular action that removes the local token. The MVP has no logout endpoint, token revocation list, or refresh token.

The JWT contains `sub` (user identifier), `iat`, and `exp`. It never contains a password or confidential business data.

### 8.2 Roles and resource scope

Each user has exactly one role: `ADMIN`, `MANAGER`, `AGENT`, or `CLIENT`. Permissions are centralized in code and covered by tests; dynamic permission administration would be unnecessary complexity in the MVP.

| Action | ADMIN | MANAGER | AGENT | CLIENT |
|---|:---:|:---:|:---:|:---:|
| Manage users and configuration | yes | no | no | no |
| Manage customers | yes | yes | read | linked customer only |
| View tickets | all | all | assigned | created by this account |
| Create a ticket | yes | yes | yes | for linked customer |
| Assign, validate, close, or reopen | yes | yes | no | no |
| Process or resolve | yes | yes | assigned ticket | no |
| Manage tasks | yes | yes | assigned ticket | no |
| Add comments | accessible tickets | accessible tickets | assigned ticket | own ticket |
| View dashboard | global | global | personal | own-ticket summary |

Deactivation preserves historical references but immediately blocks login and protected requests.

## 9. Ticket and task workflows

Ticket statuses are stable code-level values rather than administrator-managed catalogue data.

```text
NEW --assignment--> ASSIGNED --> IN_PROGRESS <--> WAITING
                                      ^  |
                                      |  +----> RESOLVED
                                      |            |
                                      +------------+ (resolution rejected)
                                                   |
                                               VALIDATED
                                                   |
                                                CLOSED
                                                   |
                                               REOPENED
                                                   |
                                              IN_PROGRESS
```

Initial rules:

- assigning a `NEW` ticket to an active support user changes it to `ASSIGNED`;
- only the assigned agent, a manager, or an administrator performs processing transitions;
- every transition into `IN_PROGRESS` requires the ticket to have an active assignee;
- entering `WAITING` requires a non-blank reason stored in history;
- `RESOLVED` requires a non-blank resolution summary and sets `resolved_at`;
- a manager or administrator may return `RESOLVED` to `IN_PROGRESS`, but must provide a non-blank rejection reason;
- `VALIDATED`, `CLOSED`, and `REOPENED` are restricted to manager/administrator actions;
- closure is rejected until every ticket task is either `DONE` or `CANCELLED`;
- ordinary updates are blocked after closure;
- reopening requires a non-blank reason, clears the current `resolved_at`, `validated_at`, and `closed_at`, recalculates the deadline from the transition time, and records former values in history;
- every assignment, priority change, and status transition creates a history event;
- an invalid transition returns `409 Conflict`, while an unauthorized valid action returns `403 Forbidden`.

Tasks have an independent, smaller workflow:

```text
TODO        -> IN_PROGRESS | CANCELLED
IN_PROGRESS -> BLOCKED | DONE | CANCELLED
BLOCKED     -> IN_PROGRESS | CANCELLED
DONE        -> terminal
CANCELLED   -> terminal
```

Moving a task to `DONE` sets `completed_at`.

`BLOCKED` and `CANCELLED` require a non-blank note, which is stored in ticket history. An `AGENT` cannot cancel a task; cancellation is restricted to `MANAGER` and `ADMIN`. `TaskUpdate.note` is contextual transition information and is not stored as a mutable task field.

## 10. SLA and in-application alerts

### 10.1 SLA calculation

For each priority (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), an administrator configures a positive target in hours and the elapsed percentage at which a warning begins.

```text
sla_deadline = cycle_start UTC + target_hours
sla_warning_at = cycle_start UTC
                 + (target_hours × warning_threshold_percent / 100)
```

The first cycle starts at `created_at`. A reopened cycle starts at the latest `STATUS_REOPENED` history timestamp; no duplicate `reopened_at` column is required. Changing priority recalculates the deadline from the current cycle start and records the change.

The API exposes these SLA states:

- `NOT_CONFIGURED`: no active rule was available when the deadline was calculated;
- `ON_TRACK`: unresolved and the deadline has not passed;
- `OVERDUE`: unresolved and the deadline has passed;
- `MET`: resolved at or before the deadline;
- `BREACHED`: resolved after the deadline.

Approaching the deadline is not a sixth state. The percentage threshold creates an `SLA_WARNING` notification while the ticket remains `ON_TRACK`.

Exact durations and warning percentages are unknown. Seed values are synthetic demonstration values, not confirmed company commitments.

### 10.2 Notification generation

Two simple mechanisms are implemented:

- business actions create their immediate notifications, including assignment, status update, and task assignment, inside the same transaction;
- a deterministic service scans for tickets and tasks that are approaching or past a deadline before the notification list or unread count is returned.

Deduplication uses recipient, ticket, type, and title. No message broker or separate service is required. However, this read-triggered refresh is not continuous scheduling: no deadline alert is created in the background while nobody calls the notification endpoints. An externally scheduled command or controlled background job is a future improvement.

## 11. Transactions and history

Important business operations are atomic. Resolving a ticket, for example, performs the following work in one database transaction:

1. validate the transition and actor;
2. update status, summary, and `resolved_at`;
3. add a ticket-history event;
4. add any related notifications;
5. commit the transaction.

On failure, the transaction is rolled back. The frontend cannot create, edit, or delete history entries. Each event stores a readable type and a small JSON details value when old/new values help explain the change.

## 12. Environment configuration

Secrets remain backend-only. `.env.example` documents variable names without working credentials, while the local `.env` file must not be committed.

| Backend variable | Purpose |
|---|---|
| `APP_ENV` | `development`, `test`, or `production` label |
| `APP_NAME` | public API name |
| `API_PREFIX` | route prefix, `/api` by default |
| `DATABASE_URL` | complete SQLAlchemy SQL Server/ODBC connection URL |
| `SECRET_KEY` | random signing secret of at least 32 characters |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT lifetime |
| `CORS_ORIGINS` | explicitly allowed Angular origins |
| `AUTO_CREATE_TABLES` | demo helper, disabled for normal SQL Server setup |
| `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD` | optional first-administrator bootstrap |
| `BOOTSTRAP_ADMIN_FIRST_NAME`, `BOOTSTRAP_ADMIN_LAST_NAME` | bootstrap administrator identity |

The frontend receives only public configuration such as its API base URL. Angular build-time configuration is visible to users and must never contain a secret.

## 13. Proportionate security controls

- Argon2 password hashes; passwords are never logged or returned;
- Pydantic validation and explicit field length limits;
- SQLAlchemy parameter binding rather than concatenated SQL;
- HTTPS required in a real hosted environment;
- CORS restricted to configured origins;
- role and resource-scope checks on protected endpoints;
- generic login errors and no raw exception details exposed to users;
- Angular's standard output escaping, with no rendering of untrusted HTML;
- functional history without passwords or JWT values;
- FastAPI interactive documentation is currently available; deployment may restrict it if the hosting context requires this.

JWT revocation, multi-factor authentication, an external identity provider, and a WAF are outside the initial scope.

## 14. API contract and errors

Application routes use `/api` with the default configuration. [api-overview.md](api-overview.md) documents the implemented contract, which FastAPI also exposes through OpenAPI.

The backend mainly uses `200`, `201`, `400`, `401`, `403`, `404`, `409`, and `422`. Current business errors use FastAPI's standard shape:

```json
{"detail": "Transition from CLOSED to IN_PROGRESS is not allowed"}
```

The ticket list is paginated and filtered in SQL Server. Small catalogues and resources attached to a detail response remain non-paginated arrays in the MVP.

## 15. Testing strategy

### Backend

- unit tests cover authentication helpers, ticket/task transition rules, SLA calculations, and permissions;
- API tests use `pytest` and FastAPI's test client for response codes, schemas, scopes, and complete workflows;
- fast automated tests use an in-memory SQLite database for repeatable business tests;
- `database/schema.sql` and important queries also require validation against a separate SQL Server test database because SQLite cannot prove SQL Server compatibility;
- fixtures create fresh synthetic data for each test.

Priority scenarios are valid/invalid login, unauthorized access, client isolation, complete ticket workflow, task transitions, history, overdue SLA behavior, notifications, and main dashboard indicators.

### Frontend

- focused unit tests cover authentication services, guards, interceptors, and components with logic;
- form tests cover required fields and API error presentation;
- a small number of navigation/integration tests cover role-dependent access with the test runner configured by Angular CLI.

### Functional acceptance

Postman and documented manual scenarios cover login, creation, assignment, processing, tasks, comments, resolution, validation, closure, reopening, and access denial. The goal is meaningful business-risk coverage rather than an artificial 100% coverage target.

## 16. Simple runtime and deployment

During development:

- Angular uses its development server and proxy configuration;
- FastAPI runs with Uvicorn;
- SQL Server may be local or company-provided;
- CORS allows only the configured Angular origin.

For a simple internal delivery, Angular can be built as static files and FastAPI can run as one service connected to SQL Server. HTTPS certificates, database backups, and service accounts depend on the chosen host and must be documented for the real deployment environment.

## 17. Known limitations and future work

The initial version does not include email delivery, a mobile application, business-hour SLA calendars, attachments, cloud storage, SSO, advanced analytics, multi-tenancy, distributed processing, or Sage integration. These capabilities must not be presented as implemented.

Reasonable future improvements are customer/product/category SLA overrides, email notifications, a working-day calendar, validated attachment storage, exportable reports, a richer client portal, and a true scheduled deadline job.
