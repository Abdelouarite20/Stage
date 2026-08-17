# Testing and user acceptance

## 1. Automated backend tests

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
```

The suite uses a temporary in-memory SQLite database so business logic can be tested without changing a developer's SQL Server data. It covers:

- valid login, invalid login, profile lookup, password change, and anonymous rejection;
- administrator reference-data and user management permissions;
- manager, agent, and client role restrictions and client ticket isolation;
- ticket creation, modification, assignment, priority change, filtering, and audit history;
- guarded transitions through resolution, validation, closure, and reopening;
- mandatory waiting/reopening reasons and prevention of invalid transitions;
- comments and assignment/status notifications;
- task creation, assignment, start, block validation, completion, cancellation, and the unfinished-task closure guard;
- SLA deadline calculation, priority recalculation, overdue filtering, deduplicated overdue alerts, and a new cycle after reopening;
- role-scoped dashboard totals and workload information.

Current result: **30 tests pass with Python warnings treated as errors**. The suite now also checks the SQL Server dialect mappings used for `BIT`, `NVARCHAR`, `NVARCHAR(MAX)`, and `DATETIME2(0)`, plus literal search values containing SQL Server `LIKE` metacharacters.

SQLite tests validate application behaviour, not Microsoft SQL Server itself. Before formal acceptance, execute both SQL scripts against the intended SQL Server instance and repeat the main API workflow there.

## 2. Automated frontend checks

Run:

```powershell
cd frontend
npm.cmd test
npm.cmd run build
```

Frontend unit tests focus on authentication state/guards and representative component behaviour. The production build is also required because strict TypeScript and Angular template checking detect integration mistakes that unit tests may not reach.

## 3. API smoke test

With both database and API running:

1. open `/health` and expect `{"status":"ok"}`;
2. log in through `/api/auth/login`;
3. read `/api/auth/me` with the bearer token;
4. create a synthetic ticket;
5. assign it, process a task, comment, resolve, validate, and close it;
6. verify chronological history, notifications, and dashboard totals.

Do not use confidential customer data for testing.

## 4. Live SQL Server integration result

The technical integration was executed on the local SQL Server 2022 Developer instance `MSSQLSERVER` through Microsoft ODBC Driver 18.6.2.1 and Windows Authentication. This is separate from the SQLite automated suite.

Validated results:

- `database/schema.sql` and `database/seed.sql` execute successfully and are idempotent;
- 11 tables, 11 primary keys, 15 foreign keys, 31 check constraints, and 33 indexes/index-backed constraints are present;
- every foreign key is enabled and trusted, and `DBCC CHECKCONSTRAINTS` reports zero violations;
- raw `pyodbc` and application-level SQLAlchemy connections reach `alias_ticketing`;
- FastAPI starts without a database error and `/health`, `/docs`, and `/openapi.json` return successfully;
- a real API flow created a customer and role-scoped users, created and edited a ticket, assigned it, recalculated its SLA after a priority change, completed a task, stored a comment, resolved, validated, and closed the ticket;
- direct SQL queries confirmed the persisted ticket, completed task, comment, 12 history records, assignment/update notifications, and Argon2 password hash;
- a controlled past SLA timestamp generated one `SLA_OVERDUE` notification and appeared in the dashboard overdue count;
- Unicode outside the Windows code page and literal `[`, `]`, `%`, and `_` search characters survive the API/ODBC/database round trip;
- the Angular development proxy successfully authenticated and loaded the SQL-backed dashboard through `http://localhost:4200/api`.

Current frontend result: **3 Vitest files / 6 tests pass**, and the production build succeeds at 351.83 kB raw initial bundle (96.51 kB estimated transfer).

## 5. User acceptance scenarios

### UAT-01 — Normal lifecycle

A manager creates a fictional customer request, selects catalogue values and priority, assigns an agent, and verifies the calculated SLA. The agent starts work, creates and completes a task, adds a comment, and resolves with a summary. The manager validates and closes. Expected result: every state, actor, and important action appears chronologically and dashboard totals change coherently.

### UAT-02 — Waiting and overdue SLA

An assigned agent enters `WAITING` with a reason. Controlled time passes the warning threshold and deadline. Expected result: the deadline remains unchanged, one approaching and then one overdue in-app alert is created without duplicates, and the manager sees the overdue ticket.

### UAT-03 — Task deadline

An internal task is assigned with a due timestamp. Expected result: only internal roles see it; approaching/overdue alerts go to its assignee; the parent ticket does not change status automatically.

### UAT-04 — Permission boundaries

Attempt administrator configuration as an agent, access an unassigned ticket as an agent, access another account's ticket as a client, and request internal tasks as a client. Expected result: each action is denied without disclosing protected data.

### UAT-05 — Reopening

A manager reopens a closed ticket with a reason. Expected result: prior terminal timestamps and deadline remain in history, current terminal timestamps clear, a new SLA deadline is calculated, and processing resumes only with an active assignee.

### UAT-06 — Invalid closure

Try to close a validated ticket that has a `TODO`, `IN_PROGRESS`, or `BLOCKED` task. Expected result: closure fails with no partial state change. Complete or manager-cancel every task, then close successfully.

The functional specification contains the fuller acceptance catalogue and traceability mapping.

## 6. Evidence to retain

For an academic demonstration, retain:

- backend test summary and coverage output;
- frontend test and production-build output;
- the SQL Server script execution result;
- screenshots of the main lifecycle, role denial, overdue alert, history, and dashboard;
- signed or commented UAT results from the authorized company representative when available.

Technical validation completed. Business user acceptance testing with Alias Informatique remains to be performed.
