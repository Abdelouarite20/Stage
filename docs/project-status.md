# Project status

## Current phase

Phase 10 — local technical validation completed; business user acceptance pending.

The repository began empty. It now contains a coherent requirements baseline, functional specification, architecture, SQL Server design, FastAPI backend, Angular frontend, automated tests, and operating documentation.

## Completed

- [x] Requirements, actors, scope, assumptions, use cases, and acceptance criteria
- [x] Role-permission and ticket/task workflow specification
- [x] Modular Angular → REST → FastAPI → SQLAlchemy → SQL Server architecture
- [x] SQL Server tables, constraints, indexes, and synthetic idempotent seed
- [x] Secure authentication, password hashing, JWT validation, and role/data scoping
- [x] Users, customers, configurable catalogue, and SLA configuration
- [x] Tickets, assignment, workflow guards, comments, tasks, history, and reopening
- [x] In-application deadline/assignment/update notifications
- [x] Role-scoped dashboard KPIs
- [x] Angular operational screens and protected navigation
- [x] Backend integration tests, SQL Server DDL compilation, and live SQL Server execution
- [x] End-to-end API and Angular development-proxy validation against SQL Server
- [x] Requirements, architecture, database, API, installation, testing, and UAT documentation

## Validation evidence

- Backend: 30 tests pass with warnings treated as errors.
- SQL Server host: Windows 11 Pro 23H2 x64 with SQL Server 2022 Developer RTM `16.0.1000.6`; the default `MSSQLSERVER` service is automatic and running under Windows-only authentication.
- SQL Server transport/tooling: local Shared Memory succeeded through ODBC Driver 18 `18.6.2.1`; TCP is disabled, and neither SSMS nor `sqlcmd` is installed.
- Live database: `alias_ticketing` is `ONLINE`, at compatibility level `160`, with `French_CI_AS` collation.
- Live schema: `schema.sql` and `seed.sql` executed successfully and idempotently; verification found 11 tables, 11 primary keys, 15 foreign keys, 31 check constraints, 33 indexes, and zero constraint violations.
- Live API: authentication, RBAC, customers, users, tickets, assignment, priority changes, SLA handling, tasks, comments, history, notifications, dashboard data, deactivation, and a controlled overdue case passed against SQL Server.
- SQL Server compatibility fixes verified during this run: SQLAlchemy Boolean predicates no longer emit incompatible `IS 1`; Unicode columns map to `NVARCHAR`/`NVARCHAR(MAX)`; timestamps map to `DATETIME2(0)`; and literal `%`, `_`, and escape characters are handled safely in `LIKE` searches.
- Frontend: 3 Vitest files and 6 tests pass; the Angular production build passes with a 351.83 kB raw initial bundle (96.51 kB estimated transfer).
- Browser/API chain: the Angular development proxy successfully forwarded `/api` requests to FastAPI backed by the live SQL Server database.
- Dependency audit: npm reports 0 known vulnerabilities in the installed Angular dependency tree.

Technical validation completed. Business user acceptance testing with Alias Informatique remains to be performed.

## Known bugs

No confirmed blocking application defect is open after the automated suite and completed local SQL Server/browser-path validation. Business UAT and a future production-like environment can still reveal defects and must be recorded here if found.

## Technical decisions

- A modular monolith keeps the code understandable and the transaction boundaries simple.
- Roles are four constrained values instead of a configurable permission engine.
- A product is derived from the optional selected module; temporarily unclassified tickets may omit it.
- SLA version 1 uses continuous elapsed hours per priority and persists the calculated deadline.
- Reopening starts a new SLA cycle; prior dates/deadline remain in JSON history details.
- Notifications are generated in the application when the notification endpoints evaluate deadlines; there is no background scheduler.
- Ticket comments use one shared stream. Internal/private comments require a validated future rule.
- SQL Server is the target; SQLite exists only for automated tests and lightweight demonstrations.

## Remaining external validation

- Conduct UAT with an authorized Alias Informatique representative.
- Validate the proposed catalogue, SLA durations, warning percentage, roles, notification recipients, and comment visibility.
- Replace every demonstration credential/value in the local environment before real use.

## Known limitations

- no email notifications or background scheduling;
- no attachment storage;
- no forgotten-password flow, refresh token, or server-side logout/revocation list;
- no business-hours/holiday SLA calendar or customer/product/category overrides;
- no advanced exports, saved reports, or external Sage integration;
- no comment editing/deletion or private internal-note channel;
- no production deployment/backup/monitoring automation;
- the validated SQL Server installation is the RTM `16.0.1000.6` build with no cumulative update applied;
- the validated instance is local-only because TCP is disabled, and SSMS and `sqlcmd` are not installed.

These limitations are deliberate to keep the project realistic, maintainable, and explainable at Licence 3 level.

## Next steps

1. Execute the documented UAT scenarios with synthetic data and an authorized Alias Informatique representative.
2. Apply only company-validated adjustments to assumptions and reference values.
3. Before production, apply an approved current SQL Server cumulative update and define TCP, certificate, service-account, backup, and monitoring policies for the chosen host.
