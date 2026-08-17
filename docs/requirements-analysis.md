# Phase 1 — Requirements Analysis

## 1. Document purpose

This document defines the business need, scope, stakeholders, actors, requirements, assumptions, use cases, and acceptance criteria for the Alias Informatique ticket-management and monitoring application. It is the baseline for functional design, implementation, testing, user acceptance, and the academic presentation.

The project starts from an empty workspace. At the time of this analysis there is no frontend, backend, database schema, test suite, or previous project documentation to preserve.

## 2. Requirement classification

This project distinguishes three kinds of statements:

- **Project requirement:** explicitly required by the supplied project brief.
- **Technical decision:** a design choice made to implement the project simply and coherently; it may change during technical design.
- **Unconfirmed business or process rule:** a proposed operating rule that requires company validation. Every such rule is labelled with the exact sentence below.

> Assumption — to be validated with Alias Informatique.

This label does not mean that the proposal is undesirable. It means that the company's current process has not yet been confirmed.

## 3. Confirmed project context

- The host company is Alias Informatique in Casablanca, Morocco.
- The company has approximately ten employees and works mainly with Moroccan businesses.
- Its activities include Sage solution integration, functional and technical assistance, customer support, interventions, maintenance, and evolution of implemented solutions.
- The exact internal support processes are not fully documented.
- The project title is **Development of a web application for ticket management and monitoring**.
- The application must centralize customer requests and internal support work.
- The required technology stack is Angular, FastAPI/Python, and Microsoft SQL Server.
- The expected result is a serious, understandable, testable, and defendable Licence 3 MIAGE project, not an enterprise-scale platform.

No confidential customer information is available or required for development. Development, demonstration, and automated tests must use synthetic data.

## 4. Business problem

Customer requests can concern technical incidents, functional incidents, Sage-related problems, assistance, configuration, information, interventions, maintenance, or product evolution. Without a central application, information can be fragmented and it becomes difficult to answer basic operational questions:

- Which tickets are open, waiting, overdue, resolved, or closed?
- Who currently owns each request?
- Which requests are urgent?
- What work remains on a ticket?
- Which deadlines are approaching or exceeded?
- What actions led to the current state?
- What is the current workload and SLA performance?

The application must provide one coherent record for each request, its assignments, tasks, discussion, deadlines, and history.

## 5. Project objectives and success criteria

The project succeeds when an authenticated and authorized user can complete a realistic end-to-end support scenario:

1. identify or create the customer;
2. create a categorized and prioritized ticket, with a product/module classification when known;
3. assign the ticket to an employee;
4. plan and complete one or more tasks;
5. exchange and retain ticket comments;
6. follow a controlled ticket lifecycle;
7. calculate and monitor the applicable SLA deadline;
8. receive in-application alerts for important events and deadlines;
9. resolve, validate, close, and, when permitted, reopen the ticket;
10. inspect the chronological history and management indicators.

Success also requires role-based access, secure password storage, validated inputs, meaningful tests of critical rules, and documentation that a Licence 3 student can explain.

## 6. Stakeholders

| Stakeholder | Interest in the project | Expected contribution |
|---|---|---|
| Alias Informatique management | Visibility over requests, delays, workload, and service quality | Confirm scope, rules, indicators, and acceptance |
| Internship supervisor / business representative | Coherent fit with actual work practices | Clarify workflows and validate demonstrations |
| Support employees / technicians | A practical queue, clear ownership, tasks, comments, and deadlines | Validate usability and daily processing scenarios |
| Functional consultants | Traceable functional assistance and Sage-related work | Validate categories, products/modules, and processing needs |
| Application administrator | Controlled users and configurable reference data | Validate administration and security needs |
| Customer contacts | Submission and follow-up of their own requests, if portal access is retained | Validate the usefulness and limits of client access |
| Student developer | A complete, maintainable, testable, and explainable internship deliverable | Analyze, design, implement, test, and document |
| Academic evaluator | Evidence of analysis, implementation, validation, and justified choices | Assess the project's academic quality |

> Assumption — to be validated with Alias Informatique.

Stakeholder assumption STK-A01: Alias Informatique will nominate at least one business representative who can answer process questions and participate in user acceptance testing.

> Assumption — to be validated with Alias Informatique.

Stakeholder assumption STK-A02: Customer contacts may receive application accounts. If this is not wanted, the `CLIENT` role and client portal functions can be disabled without changing the internal ticket workflow.

## 7. Actors

The project brief proposes four simple application roles. Their exact mapping to real job titles remains to be validated.

> Assumption — to be validated with Alias Informatique.

Actor assumption ACT-A01: Version 1 uses four code-level roles: `ADMIN`, `MANAGER`, `AGENT`, and `CLIENT`; one active user has exactly one role.

| Actor | Proposed responsibility |
|---|---|
| Administrator | Manage users and configurable reference data; retain broad operational access for support and verification |
| Manager / Supervisor | Monitor all tickets, assign work, adjust priority, validate resolutions, close/reopen tickets, and view team dashboards |
| Support Agent / Technician | Process assigned tickets, update status, add comments, create and complete tasks, and propose resolution |
| Client | Create a request and follow or comment on tickets belonging to the client's own company |
| System clock | Re-evaluate SLA and task deadlines and generate due/overdue notifications through a simple scheduled or on-access process |

The “system clock” is a logical actor used in use cases; it is not a human role.

## 8. Functional scope

### 8.1 In scope for version 1

- authentication, logout, protected routes, and role-based authorization;
- active/inactive users and basic profile information;
- customers and customer contacts;
- configurable products, modules, ticket categories, and SLA policies;
- ticket creation, viewing, modification, search, filtering, sorting, assignment, and lifecycle management;
- ticket comments and optional attachment references;
- tasks attached to a ticket, with assignment, status, and due-date tracking;
- chronological history of important ticket actions;
- priority-based SLA deadline calculation, warning, and overdue detection;
- in-application notifications;
- operational dashboard indicators;
- functional, permission, workflow, SLA, and key KPI tests;
- synthetic demonstration data and project documentation.

### 8.2 Explicitly outside the first-version scope

- mobile application;
- email, SMS, or push notifications;
- integration with Sage or another external business system;
- automated ticket ingestion from mailboxes;
- advanced file repository, antivirus pipeline, or document versioning;
- advanced business-hours, holiday-calendar, or multi-contract SLA engine;
- complex workflow designer or per-customer workflow;
- microservices, message brokers, Kubernetes, or distributed infrastructure;
- billing, contracts, inventory, remote-control tooling, or knowledge-base management;
- machine-learning classification or prediction;
- enterprise analytics, data warehouse, or customizable report builder;
- production hosting, high-availability infrastructure, and disaster-recovery automation.

These exclusions keep the deliverable coherent with a Licence 3 project. They may be considered as future improvements after the core workflow is validated.

## 9. Functional requirements

Priorities use **Must**, **Should**, and **Could**:

- **Must:** required for the coherent end-to-end version.
- **Should:** valuable and expected when it does not endanger the core version.
- **Could:** optional enhancement after all Must requirements pass.

### 9.1 Authentication and authorization

| ID | Requirement | Priority |
|---|---|---|
| FR-AUTH-01 | The system shall authenticate an active user with an email address and password. | Must |
| FR-AUTH-02 | The system shall reject invalid credentials without revealing whether an account exists. | Must |
| FR-AUTH-03 | The system shall allow the authenticated user to log out. | Must |
| FR-AUTH-04 | The frontend shall protect restricted routes and the API shall independently authorize every protected operation. | Must |
| FR-AUTH-05 | The system shall deny inactive users access. | Must |
| FR-AUTH-06 | The system shall apply role-based permissions and data-scope restrictions. | Must |
| FR-AUTH-07 | Passwords shall be stored only as secure hashes; secrets shall be supplied through configuration rather than source code. | Must |

### 9.2 Users and reference data

| ID | Requirement | Priority |
|---|---|---|
| FR-ADM-01 | An authorized user shall create, view, edit, search, activate, and deactivate users. | Must |
| FR-ADM-02 | A user record shall include identifier, first name, last name, unique email, role, active status, and creation/update timestamps. | Must |
| FR-ADM-03 | An authorized user shall create, view, edit, search, activate, and deactivate customers. | Must |
| FR-ADM-04 | A customer shall include identifier, company name, contact name, email, phone, address, status, and creation timestamp as applicable. | Must |
| FR-ADM-05 | An authorized user shall manage configurable products and modules. | Must |
| FR-ADM-06 | An authorized user shall manage configurable ticket categories. | Must |
| FR-ADM-07 | The system shall preserve historical references when reference data is deactivated. | Must |

> Assumption — to be validated with Alias Informatique.

Business assumption ADM-A01: Deactivation, rather than physical deletion, is the normal operation for users, customers, products, modules, and categories that have already been referenced.

### 9.3 Tickets

| ID | Requirement | Priority |
|---|---|---|
| FR-TKT-01 | An authorized user shall create a ticket with customer, subject, description, category, and priority, plus a product/module classification when known. | Must |
| FR-TKT-02 | The system shall generate a unique human-readable ticket reference. | Must |
| FR-TKT-03 | The system shall record creator, creation timestamp, update timestamp, status, assignment, SLA deadline, resolution timestamp, and closure timestamp as applicable. | Must |
| FR-TKT-04 | Authorized users shall view ticket details including tasks, comments, SLA state, and history. | Must |
| FR-TKT-05 | Authorized users shall edit permitted ticket fields according to role and current status. | Must |
| FR-TKT-06 | Authorized users shall assign or reassign a ticket to an active support employee. | Must |
| FR-TKT-07 | Authorized users shall change ticket priority and lifecycle status only through valid transitions. | Must |
| FR-TKT-08 | Authorized users shall resolve, validate, close, and reopen tickets when transition preconditions are met. | Must |
| FR-TKT-09 | Users shall search and filter tickets by reference, customer, status, priority, category, product/module, assignee, date, and SLA state. | Must |
| FR-TKT-10 | The ticket list shall support sorting and paginated results. | Should |
| FR-TKT-11 | Authorized users shall add comments to a ticket. | Must |
| FR-TKT-12 | The system shall optionally associate attachment metadata or references with tickets. | Should |
| FR-TKT-13 | Client users, if enabled, shall only see and act on tickets within their authorized customer scope. | Must |

> Assumption — to be validated with Alias Informatique.

Business assumption TKT-A01: The application generates the ticket reference automatically; users do not choose or edit it.

> Assumption — to be validated with Alias Informatique.

Business assumption TKT-A02: Only managers and administrators may assign/reassign tickets and change priority after creation; support agents may update processing fields on tickets assigned to them.

> Assumption — to be validated with Alias Informatique.

Business assumption TKT-A03: A client account, if enabled, is linked to exactly one customer company and can see only the tickets that account created; it cannot see internal-only information or another user's tickets.

> Assumption — to be validated with Alias Informatique.

Business assumption TKT-A04: Comments are immutable after submission in version 1; correction is made by adding a new comment, which preserves traceability.

> Assumption — to be validated with Alias Informatique.

Business assumption TKT-A05: A ticket created by a client starts at `MEDIUM` priority; only a manager or administrator may subsequently assess and change that priority.

### 9.4 Tasks

| ID | Requirement | Priority |
|---|---|---|
| FR-TSK-01 | An authorized user shall create one or more tasks within a ticket. | Must |
| FR-TSK-02 | A task shall include identifier, ticket, title, description, assignee, status, due date, creation timestamp, and completion timestamp as applicable. | Must |
| FR-TSK-03 | Authorized users shall edit, assign, change status, complete, or cancel a task under valid transition rules. | Must |
| FR-TSK-04 | The ticket detail shall display all tasks belonging to that ticket and their deadline state. | Must |
| FR-TSK-05 | Users shall identify tasks approaching or exceeding their due dates. | Must |

> Assumption — to be validated with Alias Informatique.

Business assumption TSK-A01: Managers, administrators, and the assigned support agent may create tasks; managers and administrators may assign them to any active support employee, while an agent may assign a newly created task to themself.

> Assumption — to be validated with Alias Informatique.

Business assumption TSK-A02: Closing a ticket requires all non-cancelled tasks to be `DONE`.

### 9.5 History and traceability

| ID | Requirement | Priority |
|---|---|---|
| FR-HIS-01 | The system shall append a chronological history event for ticket creation, assignment/reassignment, priority change, status change, resolution, validation, closure, and reopening. | Must |
| FR-HIS-02 | The system shall record task creation/completion and comment addition in the ticket history. | Must |
| FR-HIS-03 | Each history event shall identify the ticket, event type, actor or system origin, timestamp, and a concise description of the change. | Must |
| FR-HIS-04 | Ordinary users shall not edit or delete history events through the application. | Must |

### 9.6 SLA management

| ID | Requirement | Priority |
|---|---|---|
| FR-SLA-01 | An authorized administrator shall configure SLA target durations rather than relying on hard-coded company values. | Must |
| FR-SLA-02 | The system shall select an applicable SLA rule and calculate a deadline for each ticket. | Must |
| FR-SLA-03 | The system shall expose remaining time and a state of `NOT_CONFIGURED`, `ON_TRACK`, `OVERDUE`, `MET`, or `BREACHED`. | Must |
| FR-SLA-04 | The system shall identify tickets approaching or exceeding their SLA deadline. | Must |
| FR-SLA-05 | The system shall retain the deadline used for a ticket so its processing can be explained later. | Must |
| FR-SLA-06 | The dashboard shall calculate SLA compliance using a documented formula. | Must |

> Assumption — to be validated with Alias Informatique.

Business assumption SLA-A01: Version 1 selects one configurable resolution target by priority; category-, customer-, product-, and module-specific policies are future extensions unless company validation makes one of them essential.

> Assumption — to be validated with Alias Informatique.

Business assumption SLA-A02: SLA time is measured in continuous clock hours, including nights, weekends, and holidays; no business-calendar pause is implemented in version 1.

> Assumption — to be validated with Alias Informatique.

Business assumption SLA-A03: SLA compliance is measured at `RESOLVED`, not at `VALIDATED` or `CLOSED`.

> Assumption — to be validated with Alias Informatique.

Business assumption SLA-A04: Moving a ticket to `WAITING` does not pause the SLA clock in version 1.

### 9.7 Notifications

| ID | Requirement | Priority |
|---|---|---|
| FR-NOT-01 | The system shall create in-application notifications for assignment, approaching SLA, overdue SLA, approaching task due date, overdue task, and important ticket updates. | Must |
| FR-NOT-02 | A notification shall include recipient, type, concise message, related object, creation timestamp, and read/unread state. | Must |
| FR-NOT-03 | A user shall list their notifications and mark one or all as read. | Must |
| FR-NOT-04 | Repeated deadline evaluation shall not create uncontrolled duplicate notifications for the same event threshold. | Must |
| FR-NOT-05 | The interface shall show an unread-notification count. | Should |

> Assumption — to be validated with Alias Informatique.

Business assumption NOT-A01: In-application notifications are sufficient for version 1; no email, SMS, or external messaging channel is required.

### 9.8 Dashboard and reporting

| ID | Requirement | Priority |
|---|---|---|
| FR-DSH-01 | The dashboard shall show total, open, in-progress, resolved, closed, and overdue ticket counts. | Must |
| FR-DSH-02 | The dashboard shall show distributions by status and priority. | Must |
| FR-DSH-03 | The dashboard shall show SLA compliance rate and current employee workload. | Must |
| FR-DSH-04 | The dashboard should show distributions by category, customer, and assignee. | Should |
| FR-DSH-05 | The dashboard should show average processing and resolution times using documented formulas. | Should |
| FR-DSH-06 | Dashboard indicators shall respect the viewer's authorization and data scope. | Must |
| FR-DSH-07 | A user shall be able to open the filtered ticket list supporting an actionable indicator. | Should |

> Assumption — to be validated with Alias Informatique.

Business assumption DSH-A01: Managers and administrators may view company-wide indicators; support agents see their own workload and assigned tickets; clients see only indicators for their authorized customer scope.

## 10. Non-functional requirements

| ID | Category | Requirement / acceptance target | Priority |
|---|---|---|---|
| NFR-SEC-01 | Security | Passwords shall use a current adaptive password hash; passwords and secrets shall never appear in source code, API responses, or logs. | Must |
| NFR-SEC-02 | Security | The API shall enforce authentication and authorization independently of the Angular user interface. | Must |
| NFR-SEC-03 | Security | All incoming API data shall be schema-validated; database access shall use parameterized ORM/driver operations. | Must |
| NFR-SEC-04 | Security | Error responses shall be useful without exposing stack traces, credentials, SQL text, or sensitive internal data. | Must |
| NFR-SEC-05 | Security | Production-like deployment shall use HTTPS; local development may use HTTP. | Must |
| NFR-DAT-01 | Data integrity | Primary keys, foreign keys, uniqueness, nullability, and valid-value constraints shall protect the relational data. | Must |
| NFR-DAT-02 | Data integrity | A failed multi-record business operation shall roll back atomically. | Must |
| NFR-AUD-01 | Auditability | Important ticket changes shall be attributable and chronologically ordered. | Must |
| NFR-PER-01 | Performance | Under the small-team demonstration workload, ordinary list/detail API requests should complete within two seconds excluding network latency. | Should |
| NFR-USA-01 | Usability | Main workflows shall use clear French-ready labels, visible validation messages, and consistent status/priority indicators. | Must |
| NFR-USA-02 | Usability | A trained user should create a complete ticket without consulting technical documentation. | Should |
| NFR-ACC-01 | Accessibility | Forms shall have labels, keyboard-usable controls, and status information that is not conveyed by colour alone. | Should |
| NFR-MNT-01 | Maintainability | Frontend, API routing, validation, business logic, and persistence concerns shall remain separated and understandable. | Must |
| NFR-MNT-02 | Maintainability | Configurable business values shall not be duplicated as unexplained constants. | Must |
| NFR-TST-01 | Testability | Automated tests shall cover authentication, permissions, ticket/task transitions, SLA calculation, and critical KPI formulas. | Must |
| NFR-CMP-01 | Compatibility | The web interface shall support a current desktop version of a major standards-based browser. | Must |
| NFR-OPS-01 | Operability | Application errors shall be logged with enough context to diagnose them without logging passwords or tokens. | Must |
| NFR-PRV-01 | Privacy | Only synthetic data shall be committed or distributed with the project. | Must |
| NFR-SCL-01 | Scale | The design shall suit approximately ten internal employees and realistic demonstration data; high-volume enterprise scaling is not an objective. | Must |

The two-second response target is a technical acceptance target for a local or representative test environment, not a confirmed contractual commitment by Alias Informatique.

> Assumption — to be validated with Alias Informatique.

Business assumption NFR-A01: The initial user interface may use French as its primary display language while code and technical identifiers remain in English.

## 11. Cross-cutting business rules

Confirmed project rules from the brief:

- A ticket belongs to a customer and may contain multiple tasks and comments.
- Products, modules, categories, priorities, statuses, users, and SLA configuration support ticket processing.
- Ticket workflow transitions must be validated; state cannot be changed arbitrarily.
- A resolved ticket must contain resolution information.
- Closing and reopening must be controlled and recorded in history.
- Access must depend on role, and client access must be limited to appropriate records.
- Exact SLA durations must be configurable.
- Important actions must be traceable.

The following operating details are proposals rather than confirmed company facts:

> Assumption — to be validated with Alias Informatique.

Business assumption BR-A01: Ticket priorities are `LOW`, `MEDIUM`, `HIGH`, and `CRITICAL`.

> Assumption — to be validated with Alias Informatique.

Business assumption BR-A02: Ticket statuses are `NEW`, `ASSIGNED`, `IN_PROGRESS`, `WAITING`, `RESOLVED`, `VALIDATED`, `CLOSED`, and `REOPENED`.

> Assumption — to be validated with Alias Informatique.

Business assumption BR-A03: Task statuses are `TODO`, `IN_PROGRESS`, `BLOCKED`, `DONE`, and `CANCELLED`.

> Assumption — to be validated with Alias Informatique.

Business assumption BR-A04: Only an administrator or manager may validate a resolution and close or reopen a ticket; the same person may both validate and close it.

> Assumption — to be validated with Alias Informatique.

Business assumption BR-A05: A support agent may process only a ticket assigned to them, while administrators and managers may inspect and operate on all internal tickets.

> Assumption — to be validated with Alias Informatique.

Business assumption BR-A06: A ticket may have at most one current assigned employee, while multiple employees may contribute through tasks and comments.

> Assumption — to be validated with Alias Informatique.

Business assumption BR-A07: `WAITING` represents a temporary dependency on information or an external action; a reason is mandatory when entering it.

> Assumption — to be validated with Alias Informatique.

Business assumption BR-A08: Reopening requires a reason and returns the ticket through `REOPENED` to active processing while preserving prior resolution and closure history.

> Assumption — to be validated with Alias Informatique.

Business assumption BR-A09: Physical deletion of tickets, comments, tasks, and history is unavailable through version 1 user interfaces.

## 12. High-level use cases

### UC-01 — Log in

- **Primary actor:** any active user.
- **Precondition:** the user has an active account.
- **Main result:** valid credentials create an authenticated session/token and lead to the permitted home/dashboard view.
- **Alternative:** invalid credentials produce a generic error and no authenticated session.

### UC-02 — Administer users and reference data

- **Primary actor:** administrator.
- **Precondition:** authenticated administrator.
- **Main result:** user/customer/product/module/category/SLA data is created or updated with validation and timestamps.
- **Alternative:** duplicate or referenced invalid values are rejected with a safe message.

### UC-03 — Create a customer ticket

- **Primary actor:** authorized internal user or enabled client.
- **Precondition:** active customer and selectable reference data exist.
- **Main result:** a ticket receives a unique reference, initial status, SLA deadline, creator, timestamps, and history entry.
- **Alternative:** incomplete or unauthorized input is rejected without partial creation.

### UC-04 — Search and review tickets

- **Primary actor:** any authorized user.
- **Precondition:** authenticated session.
- **Main result:** the actor sees only authorized tickets and can combine supported filters, sorting, and pagination before opening details.

### UC-05 — Assign and process a ticket

- **Primary actor:** manager/administrator for assignment; assigned agent for processing.
- **Precondition:** ticket and assignee are active and the transition is valid.
- **Main result:** the assignment and status changes are persisted, notified, and recorded in history.

### UC-06 — Manage ticket tasks

- **Primary actor:** authorized manager, administrator, or assigned support agent.
- **Precondition:** the ticket is not closed.
- **Main result:** tasks are created, assigned, progressed, completed/cancelled, displayed on the ticket, and recorded where required.

### UC-07 — Comment on a ticket

- **Primary actor:** authorized internal user or authorized client.
- **Precondition:** actor can view the ticket.
- **Main result:** non-empty comment is stored with author and timestamp and becomes visible to users authorized to view the ticket.

> Assumption — to be validated with Alias Informatique.

Use-case assumption UC-A01: Version 1 has one simple comment stream with no internal/private audience flag; all comments are visible to users authorized to view the ticket. Private internal notes are a possible future improvement.

### UC-08 — Resolve, validate, and close a ticket

- **Primary actors:** support agent, then manager/administrator.
- **Precondition:** valid current state; resolution details supplied; closure conditions satisfied.
- **Main result:** timestamps, status, SLA result, history, and notifications are updated consistently.

### UC-09 — Reopen a ticket

- **Primary actor:** manager/administrator.
- **Precondition:** ticket is closed and a reason is supplied.
- **Main result:** the ticket becomes active again, prior history remains intact, and the reassigned employee is notified.

### UC-10 — Monitor deadlines and notifications

- **Primary actors:** system clock and authenticated users.
- **Precondition:** active tickets/tasks with deadlines exist.
- **Main result:** deadline states are updated or derived, deduplicated notifications are created, and recipients can read them.

### UC-11 — View dashboard

- **Primary actor:** authenticated user.
- **Precondition:** actor has dashboard permission.
- **Main result:** the system returns authorized, consistently calculated KPIs for the selected supported filters.

## 13. Acceptance criteria

### AC-01 — Security and scope

- Given valid credentials for an active user, when the user logs in, then protected content becomes accessible within that user's permissions.
- Given invalid credentials or an inactive account, when login is attempted, then access is denied with a generic error.
- Given a user without a required permission, when a protected API operation is called directly, then the API returns an authorization error and does not change data.
- Given a client account, when tickets are listed or opened, then no ticket outside the authorized customer scope is returned.

### AC-02 — Ticket creation and retrieval

- Given valid required data, when an authorized user creates a ticket, then exactly one ticket with a unique reference, initial status, calculated SLA deadline, timestamps, and creation-history event is stored.
- Given missing or invalid required data, when creation is attempted, then validation explains the relevant fields and no partial ticket is stored.
- Given supported filters, when the ticket list is queried, then every returned ticket satisfies both authorization scope and filter conditions.

### AC-03 — Workflow and assignment

- Given a valid transition and an authorized actor, when the transition is requested, then status, relevant timestamps, history, and notifications are updated in one transaction.
- Given an invalid transition or unauthorized actor, when a transition is requested, then it is rejected and the ticket remains unchanged.
- Given a ticket moved to `RESOLVED`, when resolution information is absent, then the transition is rejected.
- Given a closed ticket, when an ordinary edit is attempted, then the edit is rejected; an authorized reopen action with a reason remains available.

### AC-04 — Tasks and comments

- Given a viewable, non-closed ticket, when an authorized user creates a valid task, then the task appears on that ticket with its assignee, state, and deadline.
- Given a task moved to `DONE`, when the operation succeeds, then completion time is recorded.
- Given an overdue unfinished task, when deadlines are evaluated, then the task is shown as overdue and one relevant notification threshold event is available to recipients.
- Given a non-empty comment from an authorized actor, when it is submitted, then author, content, and timestamp are retained and a history event is added.

### AC-05 — SLA

- Given an active SLA configuration for the selected priority, when a ticket is created, then its deadline equals the documented base timestamp plus the configured target duration.
- Given a time before the warning threshold, when SLA state is requested, then it is `ON_TRACK`.
- Given a time after the configured warning percentage and before the deadline, when the ticket is evaluated, then its SLA state remains `ON_TRACK` and its approaching-deadline warning condition is true.
- Given an unresolved ticket after its deadline, when SLA state is requested, then it is `OVERDUE`.
- Given a ticket resolved no later than its deadline, when compliance is calculated, then it counts as met; a later resolution counts as breached.

### AC-06 — Dashboard and auditability

- Given a known synthetic dataset, when dashboard KPIs are requested, then counts, workload, averages, and SLA rate equal the documented formulas and authorization scope.
- Given an important ticket action, when the ticket history is viewed, then it shows the correct actor/system origin, action, timestamp, and concise change information in chronological order.
- Given a dashboard indicator with a drill-down link, when it is selected, then the ticket list opens with filters consistent with that indicator.

### AC-07 — End-to-end user acceptance

- Given a synthetic customer, product/module, category, users, and SLA policy, when the complete scenario create → assign → start → task work → comment → resolve → validate → close is performed, then every state and history event is coherent and no unauthorized operation succeeds.
- Given a closed ticket, when an authorized user reopens it with a reason and resumes processing, then the prior lifecycle remains visible and the active workflow continues according to the specified transition rules.

## 14. Dependencies and constraints

- Angular must communicate only with the FastAPI REST API, never directly with SQL Server.
- FastAPI is responsible for validation, authorization, business rules, and database access.
- SQL Server availability and connection details are environment prerequisites, not values committed in source control.
- The final solution must remain locally demonstrable and understandable without complex infrastructure.
- Tests must use isolated synthetic data and must not depend on confidential company data.
- The exact supported browser versions, deployment server, identity policy, backup policy, and data-retention policy are not supplied by the project brief.

## 15. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Company workflow remains unvalidated | Rework of statuses, permissions, or closure rules | Keep workflow rules centralized and validate the marked assumptions early |
| Exact SLA rules are unknown | Incorrect deadline or compliance figures | Store configurable durations and document the simple initial formula |
| Scope becomes too broad | Core lifecycle remains incomplete | Deliver Must requirements first and defer advanced integrations/reporting |
| Client portal is not actually needed | Unnecessary access-control complexity | Keep client role separable and confirm STK-A02 before polishing it |
| SQL Server environment differs between machines | Setup and test delays | Use documented environment variables, migration/schema scripts, and synthetic seed data |
| Attachment handling expands unexpectedly | Security and storage complexity | Limit version 1 to explicitly validated formats/size or metadata references |
| Dashboard definitions are ambiguous | Misleading KPIs | Define every formula and verify it on a fixed acceptance dataset |
| Permission checks exist only in UI | Data exposure | Test authorization at API level for every protected capability |

## 16. Limitations of this analysis

- It is based on the supplied project brief, not interviews or observation of Alias Informatique's current ticket process.
- No real users, customers, contracts, SLA schedules, categories, product catalogue, or support statistics were supplied.
- Roles and lifecycle rules therefore remain proposals wherever explicitly marked.
- Performance targets cover a small-team academic deployment and are not production service guarantees.
- Legal, retention, backup, and hosting policies require organizational input and are not invented here.

## 17. Validation questions for Alias Informatique

1. Which employees create, assign, validate, close, and reopen tickets today?
2. Is direct customer portal access required, or will only employees create tickets?
3. Can one ticket have one assignee or several co-owners?
4. Which real categories, products, and modules should seed the configurable lists?
5. Are the proposed ticket and task statuses understandable and sufficient?
6. What exactly does `WAITING` mean, and should it pause an SLA?
7. Which priority levels are used and who may change them?
8. Are SLA targets measured in clock hours or business hours? Which event stops the clock?
9. Should changing priority recalculate an existing deadline?
10. Who receives each assignment, deadline, resolution, closure, and reopening alert?
11. May client users see comments, attachments, assigned employees, and history? Are internal notes required?
12. Are attachments required in version 1? If so, which types, maximum size, and retention rule apply?
13. Must all tasks be completed before resolution or only before closure?
14. Which dashboard indicators are actually used for management decisions?
15. What language should the user interface use?
16. What backup, retention, and account/password rules apply in the intended environment?

## 18. Phase 1 exit criteria

Phase 1 is ready to support design and implementation when:

- all Must requirements are traceable to functional specifications and tests;
- each unconfirmed process rule remains visibly marked;
- critical validation questions have an answer or a configurable/reversible default;
- the product owner/business representative accepts the in-scope/out-of-scope boundary;
- the core end-to-end acceptance scenario is understood by developer and representative.

Until company validation occurs, the marked assumptions are working defaults for an academic prototype, not statements of Alias Informatique's established practice.
