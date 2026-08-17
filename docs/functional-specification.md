# Phase 2 — Functional Specification

## 1. Purpose and status

This document translates the Phase 1 requirements into observable application behaviour. It defines version 1 roles, permissions, data, ticket and task workflows, SLA behaviour, notifications, dashboards, use cases, validation rules, and acceptance criteria.

It must be read with `docs/requirements-analysis.md`. Requirement identifiers from that document are retained for traceability.

The specification is implementation-oriented but technology-neutral unless a project constraint requires otherwise. Angular, FastAPI, and SQL Server technical structure belongs to Phase 3.

The exact internal process of Alias Informatique has not yet been supplied. Consequently, every proposed company or process rule is marked with:

> Assumption — to be validated with Alias Informatique.

## 2. Functional boundaries

Version 1 contains these functional areas:

1. authentication and personal session;
2. users and roles;
3. customers;
4. products and modules;
5. ticket categories and priorities;
6. tickets, comments, optional attachment references, and chronological history;
7. ticket tasks;
8. configurable priority-based SLA targets;
9. in-application notifications;
10. ticket search, filters, and monitoring dashboard.

Email delivery, external-system integration, advanced SLA calendars, configurable workflows, complex reporting, and native mobile access are not part of version 1.

## 3. Shared terminology

| Term | Functional meaning |
|---|---|
| Active ticket | A ticket whose status is not `CLOSED` |
| Open ticket KPI | Any ticket not in `CLOSED`, including `RESOLVED` and `VALIDATED` while closure remains pending |
| Assigned employee | The one support employee currently responsible for coordinating a ticket |
| Contributor | An employee who participates through a task or comment but is not necessarily the ticket assignee |
| Resolution | The support answer/work result recorded when processing is believed complete |
| Validation | Formal acceptance of a recorded resolution by an authorized internal role |
| SLA target | Configured maximum continuous duration for a ticket at its priority |
| SLA deadline | Timestamp derived from ticket creation plus its configured SLA target |
| Client-visible | Information that a permitted client account may see |
| Internal-only | Information available only to permitted Alias Informatique users |

> Assumption — to be validated with Alias Informatique.

Terminology assumption FS-A01: “Validation” is an internal manager/administrator action; it is not customer acceptance or a contractual signature.

## 4. Roles and permission model

### 4.1 Role model

> Assumption — to be validated with Alias Informatique.

Role assumption FS-A02: Version 1 has exactly four code-level roles and one active user has exactly one role: `ADMIN`, `MANAGER`, `AGENT`, or `CLIENT`.

- **Administrator:** manages accounts, reference data, and configuration; can support operational correction.
- **Manager:** supervises the ticket queue, assignment, priority, validation, closure, reopening, and company-wide indicators.
- **Support Agent:** processes tickets assigned to them and performs the related task/comment work.
- **Client:** creates and follows only tickets created by that same client account.

The API is the authority for permissions. Hiding an Angular button is a usability measure, not an authorization control.

### 4.2 Permission matrix

The matrix is a proposed operating model rather than a confirmed description of current company responsibilities.

> Assumption — to be validated with Alias Informatique.

Permission assumption FS-A03: The entire role-permission matrix below is the version 1 working rule.

Legend: `All` = all records in the internal operational scope; `Assigned` = only tickets assigned to the agent; `Own` = only records created by that client account; `R` = read; `C` = create; `U` = update; `—` = not permitted.

| Capability | Administrator | Manager | Support Agent | Client |
|---|---:|---:|---:|---:|
| Log in, log out, view own profile | Yes | Yes | Yes | Yes |
| Manage users and activation | C/R/U/All | — | — | — |
| Reset another user's password | Yes | — | — | — |
| View customers | All | All | Needed for assigned work | Own linked company |
| Create/update/deactivate customers | C/R/U/All | C/R/U/All | — | — |
| Manage products and modules | C/R/U/All | R | R | R active values during creation |
| Manage categories | C/R/U/All | R | R | R active values during creation |
| Manage SLA configuration | C/R/U/All | R | R applicable ticket data | — |
| View ticket list/detail | All | All | Assigned | Own |
| Create a ticket | Yes | Yes | Yes | Yes, for linked customer |
| Edit core ticket data | All active tickets | All active tickets | — | — |
| Assign/reassign ticket | Yes | Yes | — | — |
| Change priority | Yes | Yes | — | — |
| Perform processing transitions | Yes | Yes | Assigned | — |
| Validate resolution | Yes | Yes | — | — |
| Close/reopen ticket | Yes | Yes | — | — |
| Create/update task | All active tickets | All active tickets | Assigned ticket, within limits | — |
| Assign task to any support agent | Yes | Yes | — | — |
| Assign new task to self | Yes | Yes | Yes, on assigned ticket | — |
| Add comment | Yes | Yes | Assigned | Own ticket |
| View comments | All | All | Assigned | Own |
| View full ticket history | All | All | Assigned | Own |
| View dashboard | Company | Company | Personal | Own-ticket summary |
| Read/mark notifications | Own notifications | Own notifications | Own notifications | Own notifications |

### 4.3 Data-scope rules

> Assumption — to be validated with Alias Informatique.

Permission assumption FS-A04: A support agent's normal data scope contains tickets currently assigned to them. A manager or administrator retains access after reassignment for supervision and audit.

> Assumption — to be validated with Alias Informatique.

Permission assumption FS-A05: A client user is linked to exactly one active customer and can access only tickets created by that same user account, even when several client accounts belong to the same customer company.

> Assumption — to be validated with Alias Informatique.

Permission assumption FS-A06: Version 1 has one comment stream and all comments/history are visible to a user who can view the ticket; tasks remain internal. A private-note flag and reduced client timeline are deferred until the company confirms that distinction is needed.

### 4.4 Account rules

- Email is the login identifier and must be unique case-insensitively.
- An inactive account cannot authenticate or receive a new assignment.
- A password is never returned by the API and is never displayed after submission.
- A role change affects subsequent authorization checks.
- Deactivation preserves authored tickets, comments, tasks, and history.

> Assumption — to be validated with Alias Informatique.

Account assumption FS-A07: An administrator creates accounts and supplies an initial password through an agreed manual channel; self-registration and forgotten-password email flows are outside version 1.

## 5. Functional data definitions

The fields below describe information visible to the business logic. Exact SQL types and table design belong to Phase 3.

### 5.1 User

| Field | Required | Rule |
|---|---:|---|
| Identifier | Yes | System-generated, immutable |
| First name / last name | Yes | Trimmed, non-empty |
| Email | Yes | Valid format, unique case-insensitively |
| Password hash | Yes | Never accepted as a client-provided hash or returned |
| Role | Yes | One of the four configured version 1 roles |
| Customer link | For client only | Active customer required for `CLIENT`; empty for internal roles |
| Active | Yes | Defaults to active on creation |
| Created / updated timestamps | Yes | System-managed |

### 5.2 Customer

| Field | Required | Rule |
|---|---:|---|
| Identifier | Yes | System-generated, immutable |
| Company name | Yes | Trimmed, non-empty |
| Contact name | No | Free text within configured length |
| Email / phone / address | No | Validated when supplied |
| Active | Yes | Inactive records remain visible on historical tickets |
| Created / updated timestamps | Yes | System-managed |

### 5.3 Product and module

| Object | Required fields | Relationship and rule |
|---|---|---|
| Product | Identifier, unique name, active flag | Parent configurable value |
| Module | Identifier, product, unique name within product, active flag | Belongs to exactly one product |

> Assumption — to be validated with Alias Informatique.

Catalogue assumption FS-A08: A ticket may select a module when the request is classified; the product is then derived from that module's parent. A temporarily unclassified ticket may have no module/product association.

### 5.4 Category and priority

- Category is configurable, uniquely named, and active/inactive.
- Existing tickets retain their category if it later becomes inactive.
- New tickets can select only active categories.

> Assumption — to be validated with Alias Informatique.

Priority assumption FS-A09: Priorities are the fixed ordered values `LOW`, `MEDIUM`, `HIGH`, and `CRITICAL`; the names are not administratively editable in version 1, while their SLA durations are configurable.

> Assumption — to be validated with Alias Informatique.

Priority assumption FS-A09b: An internal creator selects the initial priority. A `CLIENT` submission is forced to `MEDIUM`, regardless of a client-supplied value, until a manager or administrator evaluates it.

### 5.5 Ticket

| Field | Required | Functional rule |
|---|---:|---|
| Identifier | Yes | Internal system identifier |
| Reference | Yes | Unique, system-generated, immutable, human-readable |
| Customer | Yes | Active at creation; retained if later inactive |
| Subject | Yes | Trimmed, concise, non-empty |
| Description | Yes | Trimmed, non-empty |
| Category | Yes | Active at creation |
| Product | Derived | Not stored separately; obtained from the selected module |
| Module | No | If supplied, active; its parent determines the product |
| Priority | Yes | One of four ordered values |
| Status | Yes | Controlled by ticket workflow |
| Creator | Yes | Authenticated account |
| Assigned employee | Conditional | Active `AGENT` or `MANAGER` in assigned/processing states |
| Waiting reason | Conditional | Required in `WAITING` |
| Resolution summary | Conditional | Required from `RESOLVED` onward |
| Validation note | No | Optional note recorded during validation |
| Reopening reason | Conditional | Required for reopening |
| SLA deadline | Conditional | Calculated deadline for the current cycle; null only when no active SLA configuration exists |
| Created / updated timestamps | Yes | System-managed |
| Resolution / validation / closure timestamps | Conditional | Set by successful transitions |

> Assumption — to be validated with Alias Informatique.

Reference assumption FS-A10: A reference uses `TKT-YYYYMMDD-8HEX`, where the suffix is eight uppercase hexadecimal characters generated by the backend; the format has no company meaning until validated.

> Assumption — to be validated with Alias Informatique.

Assignment assumption FS-A11: A ticket has at most one current assigned employee. Other employees participate through assigned tasks and comments.

### 5.6 Task

| Field | Required | Functional rule |
|---|---:|---|
| Identifier | Yes | System-generated |
| Ticket | Yes | Existing ticket not in `CLOSED` |
| Title | Yes | Trimmed and non-empty |
| Description | No | Optional work detail |
| Assigned user | No | When supplied, an active internal support-capable user |
| Status | Yes | Controlled by task workflow; initially `TODO` |
| Due timestamp | No | When supplied, must be after task creation at submission time |
| Created / updated timestamps | Yes | System-managed |
| Completion timestamp | Conditional | Set only in `DONE` |

> Assumption — to be validated with Alias Informatique.

Task assumption FS-A12: A task may temporarily be unassigned and may omit a due timestamp; it can never be assigned to a client. Deadline alerts apply only when a due timestamp exists.

### 5.7 Comment

| Field | Required | Functional rule |
|---|---:|---|
| Identifier | Yes | System-generated |
| Ticket | Yes | Ticket visible to author |
| Author | Yes | Authenticated user |
| Content | Yes | Trimmed and non-empty |
| Creation timestamp | Yes | System-managed |

> Assumption — to be validated with Alias Informatique.

Comment assumption FS-A13: Comments cannot be edited or deleted through version 1; an incorrect comment is followed by a corrective comment.

> Assumption — to be validated with Alias Informatique.

Comment assumption FS-A13b: Version 1 does not distinguish private internal notes from client-visible comments; every comment follows the ticket's visibility scope.

### 5.8 Attachment reference

The brief makes attachments optional. Version 1 may retain an attachment's original name, stored name or external reference, media type, size, uploader, and upload timestamp when secure file handling is implemented.

> Assumption — to be validated with Alias Informatique.

Attachment assumption FS-A14: Attachment upload is a `Should` capability and does not block acceptance of the core lifecycle. Allowed formats, maximum size, storage location, download permission, antivirus handling, and retention require company and technical validation before upload is enabled.

### 5.9 Ticket history event

| Field | Required | Functional rule |
|---|---:|---|
| Identifier / ticket | Yes | System-generated event linked to one ticket |
| Event type | Yes | Controlled value such as created, assigned, status changed, or comment added |
| Actor | Conditional | Authenticated user, or empty with `SYSTEM` origin |
| Timestamp | Yes | Server-generated |
| Summary | Yes | Concise, human-readable explanation |
| Structured old/new values | No | Limited to values needed for clear display/testing |

History is append-only through ordinary application operations. Sensitive values such as passwords, tokens, or full confidential payloads must never be recorded.

## 6. Ticket workflow

### 6.1 Status model

> Assumption — to be validated with Alias Informatique.

Workflow assumption FS-A15: Version 1 uses the following strict lifecycle, including a correction path after rejected resolution:

```text
NEW → ASSIGNED → IN_PROGRESS ⇄ WAITING
                    │
                    ↓
                 RESOLVED → VALIDATED → CLOSED → REOPENED
                    │                              │
                    └─ resolution rejected ────────┴→ IN_PROGRESS
```

The normal forward path is `NEW → ASSIGNED → IN_PROGRESS → RESOLVED → VALIDATED → CLOSED`. `WAITING` is entered and left only from active processing. A rejected resolution returns to `IN_PROGRESS`. Reopening is explicit and recorded.

### 6.2 Transition table

Every row in this table is an unconfirmed process rule.

| From | To | Trigger / required data | Authorized actor | Additional effect | Validation status |
|---|---|---|---|---|---|
| — | `NEW` | Create valid ticket | Administrator, manager, support agent, or client within scope | Reference, SLA, timestamps, history | Assumption — to be validated with Alias Informatique. |
| `NEW` | `ASSIGNED` | Select active support assignee | Administrator or manager | Assignment notification and history | Assumption — to be validated with Alias Informatique. |
| `ASSIGNED` | `IN_PROGRESS` | Start work | Assigned agent, manager, or administrator | Status timestamp/history | Assumption — to be validated with Alias Informatique. |
| `IN_PROGRESS` | `WAITING` | Supply waiting reason | Assigned agent, manager, or administrator | SLA continues; history | Assumption — to be validated with Alias Informatique. |
| `WAITING` | `IN_PROGRESS` | Resume work | Assigned agent, manager, or administrator | Clear current waiting flag but retain history | Assumption — to be validated with Alias Informatique. |
| `IN_PROGRESS` | `RESOLVED` | Supply resolution summary | Assigned agent, manager, or administrator | Resolution time, SLA result, notification, history | Assumption — to be validated with Alias Informatique. |
| `RESOLVED` | `VALIDATED` | Accept resolution; optional note | Manager or administrator | Validation time, notification, history | Assumption — to be validated with Alias Informatique. |
| `RESOLVED` | `IN_PROGRESS` | Reject resolution with reason | Manager or administrator | Clear current resolution time, notify assignee, history | Assumption — to be validated with Alias Informatique. |
| `VALIDATED` | `CLOSED` | All non-cancelled tasks are done | Manager or administrator | Closure time, notification, history; normal edits locked | Assumption — to be validated with Alias Informatique. |
| `CLOSED` | `REOPENED` | Supply reopening reason and active assignee | Manager or administrator | Clear current closure/validation/resolution times, start new SLA cycle, history/notification | Assumption — to be validated with Alias Informatique. |
| `REOPENED` | `IN_PROGRESS` | Resume work | Assigned agent, manager, or administrator | Status history | Assumption — to be validated with Alias Informatique. |

All other status pairs are invalid and return a business-validation error without partial updates.

### 6.3 Assignment and field-edit rules

> Assumption — to be validated with Alias Informatique.

Workflow assumption FS-A16: Creating a ticket always results in `NEW`; creation does not silently auto-assign it.

> Assumption — to be validated with Alias Informatique.

Workflow assumption FS-A17: Reassignment is allowed in `ASSIGNED`, `IN_PROGRESS`, `WAITING`, and `REOPENED`; it does not by itself change status and always creates history plus a notification to the new assignee.

> Assumption — to be validated with Alias Informatique.

Workflow assumption FS-A18: Customer, category, product/module, subject, and description may be corrected by a manager or administrator before `VALIDATED`; after validation they are locked unless the ticket is reopened.

> Assumption — to be validated with Alias Informatique.

Workflow assumption FS-A19: Priority may be changed by a manager or administrator while the ticket is not `RESOLVED`, `VALIDATED`, or `CLOSED`; changing it recalculates the current deadline from the current SLA-cycle start and records old/new priority and deadline.

### 6.4 Resolution, validation, closure, and reopening

- Resolution summary is mandatory and whitespace-only text is invalid.
- Validation records who validated and when.
- Closure records who closed and when and makes operational fields read-only.
- History, comments, and prior timestamps remain available to permitted internal roles.
- Reopening never deletes or overwrites historical events.

> Assumption — to be validated with Alias Informatique.

Workflow assumption FS-A20: The same manager/administrator may validate and close a ticket; separation of duties is not required in version 1.

> Assumption — to be validated with Alias Informatique.

Workflow assumption FS-A21: All tasks except those explicitly `CANCELLED` must be `DONE` before closure, but not necessarily before resolution.

> Assumption — to be validated with Alias Informatique.

Workflow assumption FS-A22: Reopening starts a new SLA cycle at the reopening timestamp using the current priority; the previous deadline and result remain explainable through history, while dashboard compliance uses the latest cycle.

### 6.5 Atomic effects of a transition

A successful transition is one business transaction. It updates the ticket, relevant timestamps, history, and required notification records together. If any required update fails, none of those effects is committed.

The API returns the resulting ticket state. A stale or duplicate transition request that no longer matches the current state is rejected rather than silently applied.

## 7. Task workflow

### 7.1 Status model

> Assumption — to be validated with Alias Informatique.

Task-workflow assumption FS-A23: Task statuses are `TODO`, `IN_PROGRESS`, `BLOCKED`, `DONE`, and `CANCELLED` with these paths:

```text
TODO -> IN_PROGRESS -> DONE
          |     ^
          v     |
        BLOCKED

TODO / IN_PROGRESS / BLOCKED -> CANCELLED
```

### 7.2 Transition rules

Every row in this table is an unconfirmed process rule.

| From | To | Required information | Authorized actor | Effect | Validation status |
|---|---|---|---|---|---|
| — | `TODO` | Valid title; optional active assignee and future due timestamp | Administrator, manager, or assigned ticket agent within permission limits | Task creation and ticket history | Assumption — to be validated with Alias Informatique. |
| `TODO` | `IN_PROGRESS` | None | Task assignee, manager, administrator | Update and history | Assumption — to be validated with Alias Informatique. |
| `IN_PROGRESS` | `BLOCKED` | Blocking reason | Task assignee, manager, administrator | Update and history | Assumption — to be validated with Alias Informatique. |
| `BLOCKED` | `IN_PROGRESS` | Optional resume note | Task assignee, manager, administrator | Update and history | Assumption — to be validated with Alias Informatique. |
| `IN_PROGRESS` | `DONE` | Optional completion note | Task assignee, manager, administrator | Set completion timestamp and history | Assumption — to be validated with Alias Informatique. |
| `TODO` / `IN_PROGRESS` / `BLOCKED` | `CANCELLED` | Cancellation reason | Manager or administrator | No completion timestamp; history | Assumption — to be validated with Alias Informatique. |

`DONE` and `CANCELLED` are terminal in version 1. Correcting either terminal result requires a manager/administrator to create a replacement task; this avoids adding another task-reopening workflow.

> Assumption — to be validated with Alias Informatique.

Task-workflow assumption FS-A24: A support agent may update only tasks assigned to them on their currently assigned ticket; managers and administrators may update all active-ticket tasks.

> Assumption — to be validated with Alias Informatique.

Task-workflow assumption FS-A25: Changing task assignee or due date is allowed only before terminal status and is recorded in the ticket history.

## 8. SLA functional specification

### 8.1 Version 1 policy model

> Assumption — to be validated with Alias Informatique.

SLA assumption FS-A26: There is one configuration row for each priority. It contains a positive integer `target_hours`, an integer `warning_threshold_percent` from 1 through 100, and an active flag.

The priority is unique in SLA configuration, so two competing rows cannot exist. A configuration may be updated or deactivated but is not physically removed through the user interface.

Category-, customer-, product-, module-, support-calendar-, and contractual overrides are outside version 1. They may be added only if business validation identifies an essential case.

### 8.2 Deadline formula

For a newly created ticket:

```text
sla_cycle_start = ticket.created_at
sla_deadline = sla_cycle_start + configured_target_hours
```

For a reopened ticket:

```text
sla_cycle_start = timestamp of the latest STATUS_REOPENED history event
sla_deadline = sla_cycle_start + configured_target_hours
```

There is no `reopened_at` ticket column. The backend obtains the current cycle start from `ticket.created_at` when no reopening event exists, otherwise from the latest `STATUS_REOPENED` history event.

Only the calculated `sla_deadline` is persisted on the ticket. The configured target duration is not copied into a separate ticket field. Later edits to general SLA configuration do not silently change an already calculated deadline. A priority change is the explicit exception defined by FS-A19.

> Assumption — to be validated with Alias Informatique.

SLA assumption FS-A27: Durations use continuous elapsed clock time; weekends, public holidays, nights, and `WAITING` time are included.

### 8.3 Current SLA state

Let `evaluation_time` be the current server time for an unresolved ticket, and `resolution_at` for a resolved/validated/closed ticket in the current cycle.

| Condition | Display state | Meaning |
|---|---|---|
| `sla_deadline` is null | `NOT_CONFIGURED` | No active SLA configuration was available when the deadline had to be calculated |
| Current cycle resolved and `resolution_at <= sla_deadline` | `MET` | Resolution target met |
| Current cycle resolved and `resolution_at > sla_deadline` | `BREACHED` | Resolution target missed |
| Not resolved and `evaluation_time > sla_deadline` | `OVERDUE` | Deadline exceeded |
| Otherwise | `ON_TRACK` | Active ticket has not exceeded its deadline |

`BREACHED` is retained for resolved records; `OVERDUE` describes an unresolved current condition. “Approaching deadline” is a separate warning condition and notification, not a `Ticket.sla_status` value.

For a ticket with a deadline, the warning instant is calculated as:

```text
warning_at = sla_cycle_start
             + (sla_deadline - sla_cycle_start)
               × warning_threshold_percent / 100
```

An unresolved ticket is approaching its deadline when `warning_at <= evaluation_time <= sla_deadline`. This produces an `SLA_WARNING` notification while the displayed ticket SLA status remains `ON_TRACK` until the deadline is exceeded.

> Assumption — to be validated with Alias Informatique.

SLA assumption FS-A28: Entering `WAITING` never pauses or extends the deadline in version 1.

### 8.4 Configuration validation

- Target hours must be a positive integer.
- Warning threshold percent must be an integer from 1 through 100.
- When an active configuration exists, ticket creation/reopening and eligible priority change calculate the deadline from it.
- SLA calculation uses server timestamps consistently; display converts them to the configured/local interface time zone.
- No user directly types a ticket deadline during normal ticket creation.

> Assumption — to be validated with Alias Informatique.

SLA assumption FS-A29: If no active configuration exists, ticket creation remains possible with a null deadline and `NOT_CONFIGURED` SLA state so configuration can be corrected without losing the request. Version 1 has no direct manual deadline-edit action.

### 8.5 SLA compliance rate

For tickets whose current/latest cycle has reached `RESOLVED`, `VALIDATED`, or `CLOSED` within the selected dashboard scope:

```text
compliance_rate = 100 × count(resolution_at <= sla_deadline)
                      / count(tickets with a resolved current/latest cycle)
```

If the denominator is zero, the interface displays “No resolved tickets” rather than `0%`, because no compliance observation exists.

## 9. Notification specification

### 9.1 General behaviour

- Notifications are in-application records only.
- Each notification has a recipient, event type, message, related ticket/task identifier, creation time, and read/unread state.
- A user can list newest notifications first, open the related authorized record, mark one as read, or mark all as read.
- A notification link is authorized again at access time; possessing the notification does not bypass current permissions.
- Deadline checks use a deduplication key so the same ticket/task threshold does not create repeated unread records on each evaluation.
- Notification failure must not make a valid ticket transition appear successful unless notification creation is part of the same transaction; implementation behaviour must be consistent and tested.

### 9.2 Event and recipient matrix

Every recipient rule below is an unconfirmed process rule.

| Event | Recipient | When created | Deduplication scope | Validation status |
|---|---|---|---|---|
| Ticket assigned/reassigned | New ticket assignee | Successful assignment | Assignment event/version | Assumption — to be validated with Alias Informatique. |
| SLA approaching | Ticket assignee | First evaluation at/after warning percentage and no later than deadline | Ticket + SLA cycle + `SLA_WARNING` | Assumption — to be validated with Alias Informatique. |
| SLA overdue | Ticket assignee | First evaluation after deadline while unresolved | Ticket + SLA cycle + `SLA_OVERDUE` | Assumption — to be validated with Alias Informatique. |
| Task approaching | Task assignee | First evaluation within task warning window | Task + due-date version + `TASK_WARNING` | Assumption — to be validated with Alias Informatique. |
| Task overdue | Task assignee | First evaluation after due time while non-terminal | Task + due-date version + `TASK_OVERDUE` | Assumption — to be validated with Alias Informatique. |
| Important ticket status update | Ticket creator, when different from actor | Successful status transition | Ticket + lifecycle version + `UPDATE` | Assumption — to be validated with Alias Informatique. |

> Assumption — to be validated with Alias Informatique.

Notification assumption FS-A30: A task enters its “approaching” window 24 continuous hours before its due timestamp; separate task rules and administrative configuration are outside version 1.

> Assumption — to be validated with Alias Informatique.

Notification assumption FS-A31: Notification records may be retained after they are read; version 1 has no user-facing deletion or retention purge.

### 9.3 Deadline evaluation

Functional correctness does not depend on an enterprise message broker. The backend must provide one deterministic deadline-evaluation operation that can be run periodically and invoked in automated tests. Dashboard/list reads must calculate current SLA state from timestamps even if a notification evaluation has not run recently.

The precise scheduling interval is a technical/deployment setting, not a contractual SLA promise.

## 10. Dashboard specification

### 10.1 Scope and filters

All dashboard queries apply the viewer's data scope before aggregation. Unauthorized records must neither appear in details nor influence totals.

Supported common filters are:

- creation-date range;
- customer;
- category;
- product/module;
- priority;
- status;
- assigned employee;
- SLA state.

Filters not permitted by role are omitted or fixed to the user's scope. Unless a date filter is selected, indicators cover all authorized records. A displayed “last refreshed” time distinguishes current calculations from cached interface state.

> Assumption — to be validated with Alias Informatique.

Dashboard assumption FS-A32: Administrators and managers receive company-wide scope; support agents receive tickets currently assigned to them; clients receive only tickets created by their own account.

### 10.2 KPI definitions

| KPI | Exact version 1 definition | Business purpose | Priority |
|---|---|---|---|
| Total tickets | Count of all authorized tickets matching filters | Establish selected activity volume | Must |
| Open tickets | Count where status is not `CLOSED` | Show remaining service responsibility | Must |
| In progress | Count where status is `IN_PROGRESS` | Show work actively being processed | Must |
| Waiting | Count where status is `WAITING` | Reveal dependency bottlenecks | Should |
| Resolved | Count where status is `RESOLVED` | Show items awaiting validation | Must |
| Closed | Count where status is `CLOSED` | Show completed lifecycle volume | Must |
| Currently overdue | Count of unresolved active tickets where current time is after SLA deadline | Focus urgent corrective action | Must |
| SLA compliance rate | Formula in section 8.5 for resolved current/latest cycles | Measure resolution against configured target | Must |
| Tickets by status | Grouped ticket count for each workflow status | Understand queue composition | Must |
| Tickets by priority | Grouped ticket count for each priority | Understand urgency mix | Must |
| Tickets by category | Grouped ticket count for each category | Understand request types | Should |
| Tickets by customer | Grouped ticket count for each customer, internal roles only | Identify customer demand | Should |
| Tickets by assignee | Grouped active-ticket count by assigned employee, including unassigned | Compare distribution | Should |
| Employee workload | Per employee: count of active assigned tickets plus separate count of unfinished assigned tasks | Support assignment decisions | Must for managers |
| Average resolution time | Average of `resolution_at - sla_cycle_start` for resolved current/latest cycles | Show elapsed time to resolution | Should |
| Average active-processing time | Average of `resolution_at - first IN_PROGRESS timestamp of current/latest cycle` where both exist | Approximate time after work started | Should |

Date range applies to ticket `created_at` for ticket-volume indicators. For duration and SLA indicators, it applies to the current/latest cycle's `resolution_at`. The interface states the basis beside the filter so users do not compare different populations unknowingly.

> Assumption — to be validated with Alias Informatique.

Dashboard assumption FS-A33: `RESOLVED` and `VALIDATED` tickets remain “open” until explicitly `CLOSED`.

> Assumption — to be validated with Alias Informatique.

Dashboard assumption FS-A34: Employee workload is a descriptive count, not an automatic performance score; cancelled tasks and closed tickets are excluded.

> Assumption — to be validated with Alias Informatique.

Dashboard assumption FS-A35: Customer and employee comparisons are visible only to administrators and managers; support agents and clients receive personal summaries rather than rankings.

### 10.3 Display rules

- Each KPI shows its label, value, active filter context, and empty state.
- Distribution charts must show the same values as an accessible textual legend or table.
- A zero denominator displays “No data” rather than a misleading percentage.
- Counts are whole numbers; durations use a consistent human-readable hours/days format; SLA rate uses at most one decimal place.
- Where practical, selecting a count opens the ticket list with equivalent filters.
- `CRITICAL`, approaching, and overdue indicators are visually prominent but not dependent on colour alone.

## 11. Ticket search and list specification

### 11.1 Search/filter behaviour

The ticket list supports these query inputs:

| Input | Behaviour |
|---|---|
| Reference | Exact or partial case-insensitive match |
| Free text | Partial case-insensitive match on subject; full description search is optional |
| Customer | Exact identifier selection |
| Status / priority / category | One or multiple selected values where interface complexity remains reasonable |
| Product/module | Exact identifier selection; module choices depend on product |
| Assignee | Exact employee, plus an `Unassigned` option |
| Creation date | Inclusive start/end date interpreted in interface time zone |
| SLA state | `NOT_CONFIGURED`, `ON_TRACK`, `OVERDUE`, `MET`, or `BREACHED` |

Filters are combined with logical AND; multiple values inside one filter use logical OR. Clearing filters returns the permitted unfiltered scope. Pagination, filter, and sort parameters are validated server-side.

### 11.2 Sort behaviour

Supported sort fields are reference, creation date, update date, priority, status, SLA deadline, and customer. Default sort is newest creation first. A deterministic secondary sort by ticket identifier prevents records from jumping between pages when primary values are equal.

The interface shows an empty result message distinct from a loading or error state.

## 12. Screen-level functional specification

| Screen | Main content | Main actions | Access |
|---|---|---|---|
| Login | Email, password, generic error | Log in | Public |
| Dashboard | Authorized KPIs, filters, drill-down | Filter, open ticket list | All authenticated, scoped |
| Ticket list | Search, filters, sort, pagination, SLA/priority/status badges | Open ticket; create if permitted | All authenticated, scoped |
| Create ticket | Customer, subject, description, category, product/module, priority | Validate and submit | All roles within scope |
| Ticket detail | Identity, state, SLA, assignment, discussion, tasks, history | Permission-dependent ticket actions | Authorized scope |
| Ticket edit | Editable core fields | Save/cancel | Administrator/manager on eligible states |
| Customers | Searchable customer list/detail/form | Create, update, deactivate | Administrator/manager write; permitted reads |
| Tasks | Ticket-context task list/form | Create, assign, transition | Internal authorized roles |
| Users | Searchable account list/detail/form | Create, update role/status, password reset | Administrator |
| Products/modules | Hierarchical active/inactive lists/forms | Create, update, deactivate | Administrator write |
| Categories | Active/inactive list/form | Create, update, deactivate | Administrator write |
| SLA configuration | One rule per priority, target hours/warning percentage | Create/update/activate/deactivate with validation | Administrator write; manager read |
| Notifications | Newest-first list and unread count | Open link, mark read/all read | Own records |
| Profile | Own identity/role information | Change own password if implemented | Authenticated user |

> Assumption — to be validated with Alias Informatique.

Interface assumption FS-A36: One responsive desktop-first Angular interface is sufficient; no separate branded client portal or native mobile design is required.

### 12.1 Ticket detail layout

The detail screen presents:

1. reference, subject, customer, category, product/module, priority, and status;
2. creator, assignee, creation/update dates, and permitted workflow actions;
3. SLA deadline, remaining/elapsed state, and warning/overdue label;
4. description and current resolution/waiting/reopening information as applicable;
5. tasks with assignee, status, due date, and deadline state;
6. one chronological comment stream;
7. chronological history for permitted ticket viewers.

Available actions come from current state plus role; the UI must not display impossible transitions. The API still rejects invalid calls.

## 13. Detailed use cases

### UC-F01 — Authenticate

- **Primary actor:** active user.
- **Trigger:** user submits email and password.
- **Preconditions:** login page is reachable; account exists and is active for the success path.
- **Main flow:**
  1. User enters credentials.
  2. Frontend validates required fields.
  3. API verifies the password hash and account status.
  4. API returns the authenticated session/token information without password data.
  5. Frontend navigates to the authorized dashboard or start page.
- **Alternative flows:** invalid format is rejected before submission; incorrect credentials or inactive account returns the same generic failure; an expired/invalid session on later request returns unauthorized and leads back to login.
- **Postcondition:** a successful user can call only operations permitted by role and scope.
- **Related requirements:** FR-AUTH-01 through FR-AUTH-07.

### UC-F02 — Create a ticket

- **Primary actor:** administrator, manager, support agent, or client.
- **Preconditions:** actor is authenticated; required reference data is active; a client actor has an active customer link.
- **Main flow:**
  1. Actor opens Create ticket.
  2. System supplies only selectable customers/reference values within permission.
  3. Actor enters required content, selects category, optionally classifies the ticket with a module/product, and—if internal—selects priority. A client submission receives `MEDIUM` priority server-side.
  4. Frontend checks obvious required/relationship rules.
  5. API repeats full validation and authorization.
  6. System generates the reference, stores status `NEW`, calculates the deadline when an active SLA rule exists, and writes creation history atomically.
  7. System returns the created ticket detail.
- **Alternative flows:** missing/invalid field, inactive reference, invalid module/product, or unauthorized customer is rejected with no partial business record. If SLA configuration is absent, creation succeeds with `NOT_CONFIGURED` and a null deadline.
- **Postconditions:** exactly one `NEW` ticket and its history exist.
- **Related requirements:** FR-TKT-01 through FR-TKT-04, FR-SLA-01/02, FR-HIS-01/03.

### UC-F03 — Assign and start ticket

- **Primary actor:** manager/administrator for assignment, then assigned support agent.
- **Preconditions:** ticket is `NEW`; chosen employee is active and support-capable.
- **Main flow:**
  1. Manager selects employee and confirms assignment.
  2. System changes `NEW → ASSIGNED`, stores assignee, adds history, and notifies employee.
  3. Assignee opens the ticket and selects Start work.
  4. System verifies ownership and changes `ASSIGNED → IN_PROGRESS` with history.
- **Alternative flows:** inactive user, stale state, or unauthorized actor is rejected without a partial assignment/transition.
- **Postcondition:** ticket is `IN_PROGRESS` with one current assignee.
- **Related requirements:** FR-TKT-06/07, FR-NOT-01/02, FR-HIS-01/03.

### UC-F04 — Put ticket on hold and resume

- **Primary actor:** assigned support agent, manager, or administrator.
- **Preconditions:** ticket is `IN_PROGRESS` for hold or `WAITING` for resume.
- **Main flow:** actor provides waiting reason; system transitions to `WAITING`, retains the unchanged SLA deadline, and records history. When dependency ends, actor resumes to `IN_PROGRESS`.
- **Alternative:** empty waiting reason or invalid state is rejected.
- **Postcondition:** state reflects work availability and history explains the waiting period.
- **Related requirements:** FR-TKT-07, FR-HIS-01, FR-SLA-02/03.

### UC-F05 — Create and complete task

- **Primary actor:** manager, administrator, or assigned ticket agent within matrix limits.
- **Preconditions:** ticket is not closed; any supplied assignee is active and any supplied due timestamp is in the future.
- **Main flow:**
  1. Actor supplies a title and may supply description, assignee, and future due timestamp.
  2. System creates `TODO` task and ticket history event.
  3. Task assignee changes it to `IN_PROGRESS`.
  4. If blocked, assignee supplies a reason and later resumes.
  5. Assignee marks work `DONE`; system records completion time and history.
- **Alternative:** manager cancels an unfinished task with a reason; invalid/unauthorized transition is rejected.
- **Postcondition:** ticket detail reflects task state and deadline condition.
- **Related requirements:** FR-TSK-01 through FR-TSK-05, FR-HIS-02.

### UC-F06 — Add comment

- **Primary actor:** authorized internal user or client ticket creator.
- **Preconditions:** actor can view the ticket.
- **Main flow:** actor enters non-empty content; system stores author/time and records a ticket history event.
- **Alternative:** empty content or a ticket outside the actor's scope is rejected.
- **Postcondition:** permitted viewers see the immutable comment.
- **Related requirements:** FR-TKT-11, FR-HIS-02/03.

### UC-F07 — Resolve, validate, and close

- **Primary actors:** assigned support agent, manager/administrator.
- **Preconditions:** ticket is `IN_PROGRESS`; closure task condition can eventually be satisfied.
- **Main flow:**
  1. Agent supplies resolution summary and requests resolution.
  2. System transitions to `RESOLVED`, records resolution time and SLA result, history, and notifications.
  3. Manager reviews resolution and validates it.
  4. System transitions to `VALIDATED` and records validator/time.
  5. Manager closes the ticket when all non-cancelled tasks are `DONE`.
  6. System transitions to `CLOSED`, records closure, locks ordinary edits, writes history, and notifies relevant users.
- **Alternative:** manager rejects resolution with a reason, returning it to `IN_PROGRESS`; missing resolution or unfinished closure-blocking task causes rejection without partial transition.
- **Postcondition:** closed lifecycle, timestamps, SLA outcome, and history are consistent.
- **Related requirements:** FR-TKT-07/08, FR-HIS-01/03, FR-SLA-03/06, FR-NOT-01/02.

### UC-F08 — Reopen ticket

- **Primary actor:** manager/administrator.
- **Preconditions:** ticket is `CLOSED`; an active assignee exists or is selected.
- **Main flow:**
  1. Actor enters reopening reason and confirms assignee.
  2. System changes to `REOPENED`, starts a new SLA cycle, persists its newly calculated deadline only, clears current-cycle terminal timestamps, records cycle information in history, and notifies recipients.
  3. Assigned agent resumes `REOPENED → IN_PROGRESS`.
- **Alternative:** missing reason/assignee, unauthorized actor, or stale status is rejected.
- **Postcondition:** prior lifecycle remains auditable and a new active processing cycle exists.
- **Related requirements:** FR-TKT-08, FR-HIS-01, FR-SLA-02/05, FR-NOT-01/02.

### UC-F09 — Evaluate deadlines

- **Primary actor:** system clock.
- **Preconditions:** active tickets/tasks have deadlines.
- **Main flow:** system compares server time to deadline/warning threshold, derives state, and creates any missing deduplicated notification for newly crossed thresholds.
- **Alternative:** a recipient is inactive; notification is omitted or routed per validated rule without preventing state calculation.
- **Postcondition:** lists/dashboard derive correct current states and recipients have no duplicate threshold event.
- **Related requirements:** FR-SLA-03/04, FR-NOT-01/02/04.

### UC-F10 — Monitor dashboard

- **Primary actor:** authenticated user.
- **Preconditions:** dashboard permission.
- **Main flow:** API applies actor scope and selected filters, computes defined indicators, frontend displays values and empty states, actor drills down to a consistent filtered ticket list.
- **Alternative:** invalid filter returns validation error; no eligible data produces zero/“No data” states without calculation failure.
- **Postcondition:** no inaccessible ticket influences or appears in output.
- **Related requirements:** FR-DSH-01 through FR-DSH-07.

## 14. Business validation and error behaviour

### 14.1 Validation principles

- Required text is trimmed; whitespace-only content is invalid.
- Enumerated statuses/priorities/roles must use supported values.
- Identifiers must reference records that exist and are allowed within actor scope.
- Inactive reference values cannot be selected for a new relationship, but remain readable historically.
- Product/module relationship is validated server-side.
- Conditional fields are enforced for waiting, resolution, cancellation, validation, closure, and reopening operations.
- A workflow action accepts the expected current state; stale state is rejected clearly.
- Client-submitted customer, creator, role, assignee, status, SLA, and timestamp fields are ignored or rejected rather than trusted.
- Empty lists return a successful empty result, not a not-found error.

### 14.2 Error categories

| Situation | Expected API category | User-facing behaviour |
|---|---|---|
| Missing/invalid input | Validation error | Field-level or concise form message |
| No authenticated session | Unauthorized | Return to login when appropriate |
| Authenticated but forbidden | Forbidden | Clear access-denied message, no data leak |
| Record not found within authorized scope | Not found | Generic missing/unavailable message |
| Duplicate email/reference/name | Conflict | Explain conflicting business field safely |
| Invalid workflow/stale state | Conflict or business validation | Refresh current state and explain allowed action |
| Unexpected server/database failure | Server error | Generic retry/report message; diagnostic detail only in safe logs |

The API must not disclose whether an inaccessible record exists. For client and restricted-agent lookups, “not found” may intentionally cover both nonexistent and out-of-scope identifiers.

## 15. History event catalogue

At minimum, the following actions create a ticket history event:

| Event type | Summary content |
|---|---|
| `TICKET_CREATED` | Creator and initial priority/category/product |
| `ASSIGNEE_CHANGED` | Previous and new assignee |
| `PRIORITY_CHANGED` | Previous/new priority and previous/new deadline |
| `STATUS_CHANGED` | Previous/new status and reason when required |
| `CORE_FIELDS_UPDATED` | Names of changed fields; concise old/new values where safe |
| `COMMENT_ADDED` | Author and comment identifier, without duplicating full content |
| `TASK_CREATED` | Task identifier/title and assignee |
| `TASK_UPDATED` | Assignee, due date, or status change as relevant |
| `TASK_COMPLETED` | Task identifier/title and completion actor |
| `TICKET_RESOLVED` | Resolver, resolution timestamp, and SLA result |
| `TICKET_VALIDATED` | Validator and validation timestamp |
| `TICKET_CLOSED` | Closer and closure timestamp |
| `STATUS_REOPENED` | Actor, reason, assignee, previous/new SLA cycle information |
| `SLA_DEADLINE_CORRECTED` | Actor, reason, previous/new deadline |

History ordering uses event timestamp and identifier as a deterministic tie-breaker.

## 16. Acceptance criteria and test traceability

### 16.1 Role and permission acceptance

| ID | Given / When / Then | Requirement trace |
|---|---|---|
| FS-AC-001 | Given an inactive user, when correct credentials are submitted, then login fails with the same generic response used for invalid credentials. | FR-AUTH-01/02/05 |
| FS-AC-002 | Given a support agent, when the agent requests an unassigned or another agent's ticket directly through the API, then no ticket data is returned. | FR-AUTH-04/06, FR-TKT-13 |
| FS-AC-003 | Given client A, when client A requests a ticket created by client B or an internal user, then access is denied as unavailable even if both accounts link to the same customer. | FR-AUTH-06, FR-TKT-13 |
| FS-AC-003b | Given a client sends another customer identifier while creating a ticket, when the API processes it, then the ticket is linked only to the authenticated client's configured customer and cannot escape that scope. | FR-AUTH-06, FR-TKT-01/13 |
| FS-AC-004 | Given a client, when an assignment, priority, administration, or transition endpoint is called, then the API rejects it and data remains unchanged. | FR-AUTH-04/06 |
| FS-AC-005 | Given an agent assigned to a ticket, when the agent submits a permitted processing transition, then it succeeds; a manager-only action remains forbidden. | FR-AUTH-06, FR-TKT-07/08 |
| FS-AC-006 | Given a client submits any priority value, when its ticket is created, then stored priority is `MEDIUM`; a manager/administrator can later change it through the authorized action. | FR-TKT-01/07 |

### 16.2 Ticket workflow acceptance

| ID | Given / When / Then | Requirement trace |
|---|---|---|
| FS-AC-010 | Given valid ticket input and active SLA policy, when ticket creation succeeds, then one `NEW` ticket, unique reference matching `TKT-YYYYMMDD-8HEX`, calculated `sla_deadline`, and creation event exist; no target-duration copy exists on the ticket. | FR-TKT-01/02/03, FR-SLA-02, FR-HIS-01 |
| FS-AC-011 | Given no active SLA policy for selected priority, when ticket creation succeeds, then its deadline is null and SLA state is `NOT_CONFIGURED`; the request itself is not lost. | FR-SLA-01/02/03 |
| FS-AC-012 | Given `NEW`, when a manager assigns an active agent, then state becomes `ASSIGNED`, assignee/history are stored, and one assignment notification exists. | FR-TKT-06/07, FR-HIS-01, FR-NOT-01 |
| FS-AC-013 | Given `IN_PROGRESS`, when an authorized actor enters `WAITING` without a non-empty reason, then transition fails and deadline/state remain unchanged. | FR-TKT-07, FR-SLA-05 |
| FS-AC-014 | Given `IN_PROGRESS`, when resolution is requested without a summary, then state remains `IN_PROGRESS` and no resolution timestamp/event exists. | FR-TKT-08, FR-HIS-01 |
| FS-AC-015 | Given `RESOLVED`, when manager rejects with reason, then state becomes `IN_PROGRESS`, assigned agent is notified, and rejection remains in history. | FR-TKT-07/08, FR-NOT-01, FR-HIS-01 |
| FS-AC-016 | Given `VALIDATED` with an unfinished non-cancelled task, when closure is requested, then closure is rejected without a closure timestamp. | FR-TKT-08, FR-TSK-03 |
| FS-AC-017 | Given `CLOSED`, when ordinary field update is requested, then update fails; when authorized reopening includes reason/assignee, a new SLA cycle and history event are created. | FR-TKT-05/08, FR-SLA-02/05, FR-HIS-01 |
| FS-AC-018 | Given any disallowed status pair, when it is submitted directly, then the API rejects it and creates no history/notification side effect. | FR-TKT-07, FR-HIS-01 |

### 16.3 Task, comment, and history acceptance

| ID | Given / When / Then | Requirement trace |
|---|---|---|
| FS-AC-020 | Given a valid active ticket, when an authorized actor creates a task, then it begins `TODO`, appears only under that ticket, and creates history. | FR-TSK-01/02/04, FR-HIS-02 |
| FS-AC-021 | Given `DONE`, when another transition is requested, then it is rejected as terminal and completion time remains unchanged. | FR-TSK-03 |
| FS-AC-022 | Given an unfinished task past due time, when evaluation runs, then overdue state is true and the same threshold evaluation does not duplicate notifications. | FR-TSK-05, FR-NOT-01/04 |
| FS-AC-023 | Given a client-created ticket, when its client creator adds a non-empty comment, then author/content/time are stored in the single ticket comment stream. | FR-TKT-11/13 |
| FS-AC-024 | Given another client account, when it requests that comment through a ticket it did not create, then neither the ticket nor comment is returned. | FR-AUTH-06, FR-TKT-13 |
| FS-AC-025 | Given an important action, when history is read, then actor/system origin, event type, time, and meaningful summary are present in stable chronological order. | FR-HIS-01/02/03/04 |

### 16.4 SLA, notification, and dashboard acceptance

| ID | Given / When / Then | Requirement trace |
|---|---|---|
| FS-AC-030 | Given cycle start `S` and target `H`, when deadline is calculated, then it equals `S + H` continuous hours, including time spent waiting. | FR-SLA-02/05 |
| FS-AC-031 | Given an unresolved ticket before the warning instant, after the warning percentage but before its deadline, and after its deadline, when evaluated at each controlled test time, then SLA states are `ON_TRACK`, `ON_TRACK`, and `OVERDUE`; only the middle evaluation creates the approaching `SLA_WARNING`. | FR-SLA-03/04 |
| FS-AC-032 | Given resolution at exactly the deadline, when compliance is evaluated, then it is `MET`; one instant later is `BREACHED`. | FR-SLA-03/06 |
| FS-AC-033 | Given repeated evaluation after one threshold crossing, when no SLA cycle/deadline version changed, then only one notification exists for that recipient/event key. | FR-NOT-01/02/04 |
| FS-AC-034 | Given priority change on an eligible ticket, when saved, then deadline is recomputed from the current cycle start, only the new deadline is persisted on the ticket, and old/new priority and deadline are in history. | FR-TKT-07, FR-SLA-02/05, FR-HIS-01 |
| FS-AC-035 | Given a fixed synthetic dataset, when KPI endpoints run, then each count, duration, workload, and SLA result matches section 10 definitions. | FR-DSH-01 through FR-DSH-06 |
| FS-AC-036 | Given no resolved ticket in scope, when compliance is displayed, then “No data” is shown and no divide-by-zero error occurs. | FR-DSH-03/06 |
| FS-AC-037 | Given client scope, when dashboard aggregates execute, then tickets created by other accounts contribute to none of the values. | FR-DSH-06 |

### 16.5 Non-functional acceptance

| ID | Acceptance check | Requirement trace |
|---|---|---|
| FS-AC-040 | Inspect stored users and API payloads/logs to confirm no plaintext password, password hash response, secret, or token leakage. | NFR-SEC-01/04 |
| FS-AC-041 | Exercise protected endpoints without token and with each wrong role to confirm backend enforcement. | NFR-SEC-02/03 |
| FS-AC-042 | Force a failure during a transition transaction and confirm ticket/history/notification remain mutually consistent. | NFR-DAT-02 |
| FS-AC-043 | Run core list/detail performance checks on representative synthetic small-team data and record whether the two-second technical target is met. | NFR-PER-01 |
| FS-AC-044 | Navigate core forms with keyboard and confirm labels, validation, and non-colour status text are available. | NFR-USA-01, NFR-ACC-01 |

## 17. User acceptance scenarios

### UAT-01 — Complete normal lifecycle

Using synthetic data, an administrator creates reference data and users; a client or employee creates a `HIGH` ticket; a manager assigns it; the agent starts work, creates/completes a task, and comments; the agent resolves it before deadline; a manager validates and closes it. Acceptance requires coherent permissions, states, timestamps, notifications, SLA result, and history throughout.

### UAT-02 — Waiting and overdue SLA

An agent puts an `IN_PROGRESS` ticket into `WAITING` with a reason. Controlled test time passes the warning threshold and deadline. Acceptance requires unchanged deadline, approaching/overdue indicators, deduplicated alerts, and successful return to `IN_PROGRESS`.

### UAT-03 — Task delay

An agent owns a task with a controlled due timestamp, starts it, becomes blocked, then exceeds the due time. Acceptance requires blocked reason/history, overdue display, and task-recipient notification without changing the parent ticket status automatically.

> Assumption — to be validated with Alias Informatique.

Task automation assumption FS-A37: A task becoming blocked or overdue does not automatically change the parent ticket status or priority.

### UAT-04 — Resolution rejection

An agent resolves a ticket with a summary; a manager rejects it with a reason; the ticket returns to `IN_PROGRESS`; the agent corrects work and resolves again; manager validates and closes. Acceptance requires both attempts in history and the final/current SLA result calculated coherently.

### UAT-05 — Reopening

A manager reopens a closed ticket with a reason and active assignee. Acceptance requires retained prior events, new SLA cycle/deadline, notification, restricted actor, and resumption through `REOPENED → IN_PROGRESS`.

### UAT-06 — Permission isolation

Two agents and two client accounts each have tickets. Direct API calls and UI navigation are attempted across scopes. Acceptance requires no unauthorized details, comments, history, dashboard contribution, or mutation.

### UAT-07 — Configuration deactivation

An administrator deactivates a used category/product/customer/user. Acceptance requires old tickets to remain readable, inactive values to disappear from new selection where applicable, and assignment/login to reject inactive users.

## 18. Requirement-to-feature traceability summary

| Feature | Main requirements | Main acceptance evidence |
|---|---|---|
| Authentication and authorization | FR-AUTH-01–07 | FS-AC-001–005, 040–041 |
| Administration/reference data | FR-ADM-01–07 | UAT-01, UAT-07 |
| Ticket CRUD/search | FR-TKT-01–13 | FS-AC-010–018 |
| Tasks | FR-TSK-01–05 | FS-AC-020–022, UAT-03 |
| History | FR-HIS-01–04 | FS-AC-012–018, 020, 025 |
| SLA | FR-SLA-01–06 | FS-AC-030–034, UAT-02/05 |
| Notifications | FR-NOT-01–05 | FS-AC-012, 015, 022, 033 |
| Dashboard | FR-DSH-01–07 | FS-AC-035–037 |

## 19. Licence 3 implementation limits

The following boundaries are deliberate, not hidden deficiencies:

- one deployable Angular frontend and one FastAPI backend;
- one relational SQL Server database;
- one role per user rather than arbitrary user-specific permission composition;
- one current ticket assignee;
- fixed, coded ticket/task state machines rather than a workflow designer;
- one priority-based continuous-hours SLA target per priority;
- one current/latest SLA cycle represented on the ticket, with previous cycle explanation retained in history rather than a contract-grade SLA ledger;
- in-application notifications with a deterministic evaluator, no email infrastructure;
- useful fixed dashboards rather than a report builder;
- simple chronological audit history, not a tamper-evident enterprise audit platform;
- synthetic demo/test data only;
- no promise of high availability, horizontal scaling, multi-tenancy, or external integration.

These limits keep the solution implementable, testable, and explainable while preserving the core business value.

## 20. Known limitations and future candidates

Only validated needs should move from this list into scope:

- business-hours and Moroccan holiday-aware SLA calendars;
- pause/restart rules for customer waiting time;
- SLA overrides by customer, category, product/module, or support contract;
- separate response and resolution SLA targets;
- email/SMS notification and escalation chains;
- richer client portal, customer-level shared visibility, and customer validation;
- secure managed file storage, scanning, preview, and retention;
- multiple assignees or team queues;
- reusable ticket templates and knowledge base;
- Sage or mailbox integration;
- advanced audit retention/export and regulatory controls;
- configurable reports and trend analytics;
- localized interface beyond the selected primary language;
- password-reset delivery, multi-factor authentication, and centralized identity;
- production backup, monitoring, high availability, and disaster recovery.

## 21. Business decisions still required

Before calling the functional specification company-approved, Alias Informatique should explicitly decide:

1. whether the four roles and the complete permission matrix match real responsibilities;
2. whether clients receive accounts, and whether visibility is per creator, company, or contact group;
3. whether client-visible versus internal comments are required;
4. the exact ticket/task states, transitions, and authorized actors;
5. whether the manager may both validate and close;
6. whether all non-cancelled tasks must be done before closure;
7. actual product, module, category, and priority lists;
8. actual SLA durations, business-hour calendar, waiting pause, priority-change, and reopening rules;
9. notification recipients and acceptable evaluation frequency;
10. KPI definitions, audience, default date range, and most useful drill-downs;
11. attachment need, formats, size, storage, security, and retention;
12. interface language, account provisioning, password policy, hosting, backup, and data retention.

Until those answers are obtained, every labelled statement remains a reversible working assumption for the academic version.

## 22. Phase 2 exit criteria

Phase 2 is complete enough to begin technical design when:

- each Must requirement has an observable rule and acceptance check;
- role and data-scope enforcement is unambiguous;
- every permitted ticket/task transition and its preconditions are enumerated;
- SLA states, formulas, persisted deadlines, cycle-start derivation, and edge conditions are deterministic;
- notification recipients and deduplication behaviour are testable;
- dashboard formulas use defined populations and zero-data behaviour;
- unresolved company rules remain labelled rather than presented as fact;
- planned implementation remains inside the Licence 3 boundaries in section 19.
