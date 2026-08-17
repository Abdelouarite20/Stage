# Installation and operation

## 1. Prerequisites

Install:

- Python 3.12;
- Node.js `^24.15.0` (Angular 22 also supports the compatible Node versions listed by Angular);
- Microsoft SQL Server;
- Microsoft ODBC Driver 18 for SQL Server;
- optionally SQL Server Management Studio or `sqlcmd`.

The commands below use Windows PowerShell because that is the current development environment. Equivalent Python, npm, and SQL Server commands work on other supported systems.

### Verified local environment

The end-to-end technical validation was completed on this local environment:

- Windows 11 Pro 23H2 x64;
- SQL Server 2022 Developer RTM `16.0.1000.6`, default `MSSQLSERVER` instance;
- SQL Server service configured for automatic startup and running;
- Windows-only authentication, validated as `USER\abdel`;
- Shared Memory for local SQL transport; TCP disabled;
- Microsoft ODBC Driver 18 for SQL Server `18.6.2.1`;
- no SQL Server Management Studio or `sqlcmd` installation on the validated machine.

Shared Memory and Windows authentication are appropriate for this same-machine development setup. TCP must be configured before a separate application host can connect to this instance.

## 2. Database setup

Create an empty database. The schema deliberately does not create or drop a database.

```sql
CREATE DATABASE alias_ticketing;
```

Connect to `alias_ticketing`, then execute in this order:

1. `database/schema.sql`;
2. optionally `database/seed.sql`.

The seed is idempotent and contains only proposed reference values and fictional customers. It contains no user and no password.

On the verified environment, both scripts were executed successfully against `alias_ticketing` and their repeat execution was confirmed to be idempotent. The live database is `ONLINE`, uses compatibility level `160` and collation `French_CI_AS`, and contains 11 tables, 11 primary keys, 15 foreign keys, 31 check constraints, and 33 indexes. Post-installation integrity checks found zero violations.

With `sqlcmd`, an example using Windows authentication is:

```powershell
sqlcmd -S localhost -E -d alias_ticketing -i database\schema.sql
sqlcmd -S localhost -E -d alias_ticketing -i database\seed.sql
```

These `sqlcmd` commands are reproducible setup examples; `sqlcmd` and SSMS were not installed on the machine used for the completed ODBC validation.

Use a dedicated SQL login with only the permissions needed on `alias_ticketing` when SQL authentication is selected. Do not use an administrator account in the application connection string.

## 3. Environment configuration

From the repository root:

```powershell
Copy-Item .env.example .env
```

Set at least:

- `SECRET_KEY`: a random secret of 32 characters or more;
- `DATABASE_URL`: the SQLAlchemy SQL Server URL;
- `CORS_ORIGINS`: the Angular origin;
- `BOOTSTRAP_ADMIN_EMAIL` and a temporary `BOOTSTRAP_ADMIN_PASSWORD` for first use.

Generate a suitable secret with Python:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

The validated same-machine Windows-authentication URL is:

```text
mssql+pyodbc://@localhost/alias_ticketing?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes&trusted_connection=yes
```

This URL contains no database password: `trusted_connection=yes` uses the Windows identity running FastAPI, while `Encrypt=yes` makes transport encryption explicit. `TrustServerCertificate=yes` is accepted only for this local development environment. For a deployed or remote connection, enable and restrict TCP as required, use a certificate that the client validates, remove `TrustServerCertificate=yes`, and run the application under a dedicated least-privilege identity. If SQL authentication is selected instead, URL-encode special characters in the username or password.

## 4. Backend

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Calling the virtual-environment interpreter directly avoids depending on the
PowerShell script execution policy.

Useful URLs:

- health: `http://localhost:8000/health`;
- OpenAPI UI: `http://localhost:8000/docs`;
- OpenAPI JSON: `http://localhost:8000/openapi.json`.

If `BOOTSTRAP_ADMIN_PASSWORD` is non-empty and the email does not yet exist, startup creates one administrator with an Argon2 password hash. After a successful first login, clear the password value from `.env` and restart the API.

## 5. Frontend

```powershell
cd frontend
npm.cmd install
npm.cmd start
```

The Angular development server opens on `http://localhost:4200`. Its proxy forwards `/api` to FastAPI on port 8000.

For a production-style static build:

```powershell
npm.cmd run build
```

Deploy the resulting `frontend/dist/alias-support` files behind a web server that forwards `/api` to FastAPI.

## 6. Lightweight demonstration database

SQL Server is the target database. For a classroom demonstration or automated tests when SQL Server is unavailable, explicitly set:

```text
DATABASE_URL=sqlite:///./ticketing.db
AUTO_CREATE_TABLES=true
```

This mode is a convenience, not proof of SQL Server integration. It does not execute `database/schema.sql`, and it should not be presented as the final database platform.

## 7. Common problems

- `Data source name not found`: install ODBC Driver 18 and verify the driver name in `DATABASE_URL`.
- A remote connection cannot reach the validated default instance: the local validation instance has TCP disabled and accepts local Shared Memory connections only; enable and secure TCP deliberately before remote use.
- `sqlcmd` is not recognized: install the optional SQL Server command-line tools or execute the scripts with SSMS or another client that supports `GO` batch separators.
- Login fails before any account exists: configure the one-time bootstrap administrator and ensure the schema is already present.
- Browser receives a CORS error: add the exact frontend origin to `CORS_ORIGINS` and restart FastAPI.
- PowerShell reports that `npm.ps1` cannot be loaded because script execution is disabled: use `npm.cmd` as shown above; administrator rights and a machine-wide execution-policy change are not required.
- Angular API calls return 404 in development: start with `npm.cmd start` so `proxy.conf.json` is used.
- A transition returns 409 or 422: read the response detail; workflow state, reason, active assignment, resolution summary, or unfinished tasks may block it.
