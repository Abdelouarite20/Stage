/*
    Alias Informatique ticket management application
    Initial Microsoft SQL Server schema

    Run this script while connected to an empty application database.
    It deliberately does not create or drop the database.

    All DATETIME2 values are UTC. SQL Server cannot attach a time-zone marker to
    DATETIME2, so the FastAPI application is responsible for consistently writing
    and reading UTC values.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

IF OBJECT_ID(N'dbo.customers', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.customers
    (
        id           INT IDENTITY(1, 1) NOT NULL,
        company_name NVARCHAR(200) NOT NULL,
        contact_name NVARCHAR(200) NULL,
        email        NVARCHAR(255) NULL,
        phone        NVARCHAR(50) NULL,
        address      NVARCHAR(500) NULL,
        is_active    BIT NOT NULL CONSTRAINT DF_customers_is_active DEFAULT (1),
        created_at   DATETIME2(0) NOT NULL CONSTRAINT DF_customers_created_at DEFAULT (SYSUTCDATETIME()),
        updated_at   DATETIME2(0) NOT NULL CONSTRAINT DF_customers_updated_at DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_customers PRIMARY KEY CLUSTERED (id),
        CONSTRAINT CK_customers_company_name_not_blank
            CHECK (LEN(LTRIM(RTRIM(company_name))) > 0),
        CONSTRAINT CK_customers_dates
            CHECK (updated_at >= created_at)
    );
END;
GO

IF OBJECT_ID(N'dbo.users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.users
    (
        id            INT IDENTITY(1, 1) NOT NULL,
        first_name    NVARCHAR(100) NOT NULL,
        last_name     NVARCHAR(100) NOT NULL,
        email         NVARCHAR(255) NOT NULL,
        password_hash NVARCHAR(255) NOT NULL,
        role          VARCHAR(20) NOT NULL,
        is_active     BIT NOT NULL CONSTRAINT DF_users_is_active DEFAULT (1),
        customer_id   INT NULL,
        created_at    DATETIME2(0) NOT NULL CONSTRAINT DF_users_created_at DEFAULT (SYSUTCDATETIME()),
        updated_at    DATETIME2(0) NOT NULL CONSTRAINT DF_users_updated_at DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_users PRIMARY KEY CLUSTERED (id),
        CONSTRAINT UQ_users_email UNIQUE (email),
        CONSTRAINT FK_users_customer
            FOREIGN KEY (customer_id) REFERENCES dbo.customers (id),
        CONSTRAINT CK_users_role
            CHECK (role IN ('ADMIN', 'MANAGER', 'AGENT', 'CLIENT')),
        CONSTRAINT CK_users_names_not_blank
            CHECK (
                LEN(LTRIM(RTRIM(first_name))) > 0
                AND LEN(LTRIM(RTRIM(last_name))) > 0
            ),
        CONSTRAINT CK_users_email_not_blank
            CHECK (LEN(LTRIM(RTRIM(email))) > 0),
        CONSTRAINT CK_users_password_hash_not_blank
            CHECK (LEN(LTRIM(RTRIM(password_hash))) > 0),
        CONSTRAINT CK_users_dates
            CHECK (updated_at >= created_at)
    );
END;
GO

IF OBJECT_ID(N'dbo.products', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.products
    (
        id          INT IDENTITY(1, 1) NOT NULL,
        name        NVARCHAR(150) NOT NULL,
        description NVARCHAR(500) NULL,
        is_active   BIT NOT NULL CONSTRAINT DF_products_is_active DEFAULT (1),
        created_at  DATETIME2(0) NOT NULL CONSTRAINT DF_products_created_at DEFAULT (SYSUTCDATETIME()),
        updated_at  DATETIME2(0) NOT NULL CONSTRAINT DF_products_updated_at DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_products PRIMARY KEY CLUSTERED (id),
        CONSTRAINT UQ_products_name UNIQUE (name),
        CONSTRAINT CK_products_name_not_blank
            CHECK (LEN(LTRIM(RTRIM(name))) > 0),
        CONSTRAINT CK_products_dates
            CHECK (updated_at >= created_at)
    );
END;
GO

IF OBJECT_ID(N'dbo.product_modules', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.product_modules
    (
        id          INT IDENTITY(1, 1) NOT NULL,
        product_id  INT NOT NULL,
        name        NVARCHAR(150) NOT NULL,
        description NVARCHAR(500) NULL,
        is_active   BIT NOT NULL CONSTRAINT DF_product_modules_is_active DEFAULT (1),
        created_at  DATETIME2(0) NOT NULL CONSTRAINT DF_product_modules_created_at DEFAULT (SYSUTCDATETIME()),
        updated_at  DATETIME2(0) NOT NULL CONSTRAINT DF_product_modules_updated_at DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_product_modules PRIMARY KEY CLUSTERED (id),
        CONSTRAINT UQ_module_product_name UNIQUE (product_id, name),
        CONSTRAINT FK_product_modules_product
            FOREIGN KEY (product_id) REFERENCES dbo.products (id),
        CONSTRAINT CK_product_modules_name_not_blank
            CHECK (LEN(LTRIM(RTRIM(name))) > 0),
        CONSTRAINT CK_product_modules_dates
            CHECK (updated_at >= created_at)
    );
END;
GO

IF OBJECT_ID(N'dbo.ticket_categories', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.ticket_categories
    (
        id          INT IDENTITY(1, 1) NOT NULL,
        name        NVARCHAR(150) NOT NULL,
        description NVARCHAR(500) NULL,
        is_active   BIT NOT NULL CONSTRAINT DF_ticket_categories_is_active DEFAULT (1),
        created_at  DATETIME2(0) NOT NULL CONSTRAINT DF_ticket_categories_created_at DEFAULT (SYSUTCDATETIME()),
        updated_at  DATETIME2(0) NOT NULL CONSTRAINT DF_ticket_categories_updated_at DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_ticket_categories PRIMARY KEY CLUSTERED (id),
        CONSTRAINT UQ_ticket_categories_name UNIQUE (name),
        CONSTRAINT CK_ticket_categories_name_not_blank
            CHECK (LEN(LTRIM(RTRIM(name))) > 0),
        CONSTRAINT CK_ticket_categories_dates
            CHECK (updated_at >= created_at)
    );
END;
GO

IF OBJECT_ID(N'dbo.sla_configurations', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sla_configurations
    (
        id                        INT IDENTITY(1, 1) NOT NULL,
        priority                  VARCHAR(20) NOT NULL,
        target_hours              INT NOT NULL,
        warning_threshold_percent INT NOT NULL CONSTRAINT DF_sla_warning_threshold DEFAULT (80),
        is_active                 BIT NOT NULL CONSTRAINT DF_sla_is_active DEFAULT (1),
        created_at                DATETIME2(0) NOT NULL CONSTRAINT DF_sla_created_at DEFAULT (SYSUTCDATETIME()),
        updated_at                DATETIME2(0) NOT NULL CONSTRAINT DF_sla_updated_at DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_sla_configurations PRIMARY KEY CLUSTERED (id),
        CONSTRAINT UQ_sla_configurations_priority UNIQUE (priority),
        CONSTRAINT CK_sla_priority
            CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
        CONSTRAINT CK_sla_target_positive
            CHECK (target_hours > 0),
        CONSTRAINT CK_sla_warning_percent
            CHECK (warning_threshold_percent BETWEEN 1 AND 100),
        CONSTRAINT CK_sla_dates
            CHECK (updated_at >= created_at)
    );
END;
GO

IF OBJECT_ID(N'dbo.tickets', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.tickets
    (
        id                  INT IDENTITY(1, 1) NOT NULL,
        reference           NVARCHAR(40) NOT NULL,
        customer_id         INT NOT NULL,
        subject             NVARCHAR(250) NOT NULL,
        description         NVARCHAR(MAX) NOT NULL,
        category_id         INT NOT NULL,
        module_id           INT NULL,
        priority            VARCHAR(20) NOT NULL,
        status              VARCHAR(20) NOT NULL CONSTRAINT DF_tickets_status DEFAULT ('NEW'),
        creator_id          INT NOT NULL,
        assigned_user_id    INT NULL,
        resolution_summary  NVARCHAR(MAX) NULL,
        sla_deadline        DATETIME2(0) NULL,
        resolved_at         DATETIME2(0) NULL,
        validated_at        DATETIME2(0) NULL,
        closed_at           DATETIME2(0) NULL,
        created_at          DATETIME2(0) NOT NULL CONSTRAINT DF_tickets_created_at DEFAULT (SYSUTCDATETIME()),
        updated_at          DATETIME2(0) NOT NULL CONSTRAINT DF_tickets_updated_at DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_tickets PRIMARY KEY CLUSTERED (id),
        CONSTRAINT UQ_tickets_reference UNIQUE (reference),
        CONSTRAINT FK_tickets_customer
            FOREIGN KEY (customer_id) REFERENCES dbo.customers (id),
        CONSTRAINT FK_tickets_category
            FOREIGN KEY (category_id) REFERENCES dbo.ticket_categories (id),
        CONSTRAINT FK_tickets_module
            FOREIGN KEY (module_id) REFERENCES dbo.product_modules (id),
        CONSTRAINT FK_tickets_creator
            FOREIGN KEY (creator_id) REFERENCES dbo.users (id),
        CONSTRAINT FK_tickets_assigned_user
            FOREIGN KEY (assigned_user_id) REFERENCES dbo.users (id),
        CONSTRAINT CK_tickets_reference_not_blank
            CHECK (LEN(LTRIM(RTRIM(reference))) > 0),
        CONSTRAINT CK_tickets_subject_not_blank
            CHECK (LEN(LTRIM(RTRIM(subject))) > 0),
        CONSTRAINT CK_tickets_description_not_blank
            CHECK (LEN(LTRIM(RTRIM(description))) > 0),
        CONSTRAINT CK_tickets_priority
            CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
        CONSTRAINT CK_tickets_status
            CHECK (
                status IN (
                    'NEW', 'ASSIGNED', 'IN_PROGRESS', 'WAITING',
                    'RESOLVED', 'VALIDATED', 'CLOSED', 'REOPENED'
                )
            ),
        CONSTRAINT CK_tickets_dates
            CHECK (
                updated_at >= created_at
                AND (resolved_at IS NULL OR resolved_at >= created_at)
                AND (validated_at IS NULL OR resolved_at IS NULL OR validated_at >= resolved_at)
                AND (closed_at IS NULL OR validated_at IS NULL OR closed_at >= validated_at)
            )
    );
END;
GO

IF OBJECT_ID(N'dbo.ticket_tasks', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.ticket_tasks
    (
        id               INT IDENTITY(1, 1) NOT NULL,
        ticket_id        INT NOT NULL,
        title            NVARCHAR(250) NOT NULL,
        description      NVARCHAR(MAX) NULL,
        assigned_user_id INT NULL,
        status           VARCHAR(20) NOT NULL CONSTRAINT DF_ticket_tasks_status DEFAULT ('TODO'),
        due_date         DATETIME2(0) NULL,
        completed_at     DATETIME2(0) NULL,
        created_at       DATETIME2(0) NOT NULL CONSTRAINT DF_ticket_tasks_created_at DEFAULT (SYSUTCDATETIME()),
        updated_at       DATETIME2(0) NOT NULL CONSTRAINT DF_ticket_tasks_updated_at DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_ticket_tasks PRIMARY KEY CLUSTERED (id),
        CONSTRAINT FK_ticket_tasks_ticket
            FOREIGN KEY (ticket_id) REFERENCES dbo.tickets (id),
        CONSTRAINT FK_ticket_tasks_assigned_user
            FOREIGN KEY (assigned_user_id) REFERENCES dbo.users (id),
        CONSTRAINT CK_ticket_tasks_title_not_blank
            CHECK (LEN(LTRIM(RTRIM(title))) > 0),
        CONSTRAINT CK_ticket_tasks_status
            CHECK (status IN ('TODO', 'IN_PROGRESS', 'BLOCKED', 'DONE', 'CANCELLED')),
        CONSTRAINT CK_ticket_tasks_dates
            CHECK (
                updated_at >= created_at
                AND (completed_at IS NULL OR completed_at >= created_at)
            )
    );
END;
GO

IF OBJECT_ID(N'dbo.ticket_comments', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.ticket_comments
    (
        id         INT IDENTITY(1, 1) NOT NULL,
        ticket_id  INT NOT NULL,
        author_id  INT NOT NULL,
        content    NVARCHAR(MAX) NOT NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_ticket_comments_created_at DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_ticket_comments PRIMARY KEY CLUSTERED (id),
        CONSTRAINT FK_ticket_comments_ticket
            FOREIGN KEY (ticket_id) REFERENCES dbo.tickets (id),
        CONSTRAINT FK_ticket_comments_author
            FOREIGN KEY (author_id) REFERENCES dbo.users (id),
        CONSTRAINT CK_ticket_comments_content_not_blank
            CHECK (LEN(LTRIM(RTRIM(content))) > 0)
    );
END;
GO

IF OBJECT_ID(N'dbo.ticket_history', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.ticket_history
    (
        id         INT IDENTITY(1, 1) NOT NULL,
        ticket_id  INT NOT NULL,
        actor_id   INT NULL,
        event_type VARCHAR(60) NOT NULL,
        details    NVARCHAR(MAX) NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_ticket_history_created_at DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_ticket_history PRIMARY KEY CLUSTERED (id),
        CONSTRAINT FK_ticket_history_ticket
            FOREIGN KEY (ticket_id) REFERENCES dbo.tickets (id),
        CONSTRAINT FK_ticket_history_actor
            FOREIGN KEY (actor_id) REFERENCES dbo.users (id),
        CONSTRAINT CK_ticket_history_event_type_not_blank
            CHECK (LEN(LTRIM(RTRIM(event_type))) > 0)
    );
END;
GO

IF OBJECT_ID(N'dbo.notifications', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.notifications
    (
        id           INT IDENTITY(1, 1) NOT NULL,
        recipient_id INT NOT NULL,
        ticket_id    INT NULL,
        type         VARCHAR(30) NOT NULL,
        title        NVARCHAR(200) NOT NULL,
        message      NVARCHAR(1000) NOT NULL,
        is_read      BIT NOT NULL CONSTRAINT DF_notifications_is_read DEFAULT (0),
        created_at   DATETIME2(0) NOT NULL CONSTRAINT DF_notifications_created_at DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_notifications PRIMARY KEY CLUSTERED (id),
        CONSTRAINT FK_notifications_recipient
            FOREIGN KEY (recipient_id) REFERENCES dbo.users (id),
        CONSTRAINT FK_notifications_ticket
            FOREIGN KEY (ticket_id) REFERENCES dbo.tickets (id),
        CONSTRAINT CK_notifications_type
            CHECK (type IN ('ASSIGNMENT', 'SLA_WARNING', 'SLA_OVERDUE', 'TASK_WARNING', 'TASK_OVERDUE', 'UPDATE')),
        CONSTRAINT CK_notifications_title_not_blank
            CHECK (LEN(LTRIM(RTRIM(title))) > 0),
        CONSTRAINT CK_notifications_message_not_blank
            CHECK (LEN(LTRIM(RTRIM(message))) > 0)
    );
END;
GO

/* SQL Server does not automatically index foreign keys. These indexes support
   the application's frequent filters, joins, chronological views and alerts. */

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.customers') AND name = N'IX_customers_company_name')
    CREATE INDEX IX_customers_company_name ON dbo.customers (company_name);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.users') AND name = N'IX_users_active_role')
    CREATE INDEX IX_users_active_role ON dbo.users (is_active, role);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.users') AND name = N'IX_users_customer_id')
    CREATE INDEX IX_users_customer_id ON dbo.users (customer_id);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.product_modules') AND name = N'IX_product_modules_active_product')
    CREATE INDEX IX_product_modules_active_product ON dbo.product_modules (is_active, product_id);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.ticket_categories') AND name = N'IX_ticket_categories_is_active')
    CREATE INDEX IX_ticket_categories_is_active ON dbo.ticket_categories (is_active);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.tickets') AND name = N'IX_tickets_status_priority')
    CREATE INDEX IX_tickets_status_priority ON dbo.tickets (status, priority);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.tickets') AND name = N'IX_tickets_customer_created')
    CREATE INDEX IX_tickets_customer_created ON dbo.tickets (customer_id, created_at DESC);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.tickets') AND name = N'IX_tickets_assignee_status')
    CREATE INDEX IX_tickets_assignee_status ON dbo.tickets (assigned_user_id, status, updated_at DESC);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.tickets') AND name = N'IX_tickets_category_id')
    CREATE INDEX IX_tickets_category_id ON dbo.tickets (category_id);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.tickets') AND name = N'IX_tickets_module_id')
    CREATE INDEX IX_tickets_module_id ON dbo.tickets (module_id);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.tickets') AND name = N'IX_tickets_status_sla_deadline')
    CREATE INDEX IX_tickets_status_sla_deadline ON dbo.tickets (status, sla_deadline);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.ticket_tasks') AND name = N'IX_ticket_tasks_ticket_status')
    CREATE INDEX IX_ticket_tasks_ticket_status ON dbo.ticket_tasks (ticket_id, status);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.ticket_tasks') AND name = N'IX_ticket_tasks_assignee_status_due')
    CREATE INDEX IX_ticket_tasks_assignee_status_due ON dbo.ticket_tasks (assigned_user_id, status, due_date);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.ticket_comments') AND name = N'IX_ticket_comments_ticket_created')
    CREATE INDEX IX_ticket_comments_ticket_created ON dbo.ticket_comments (ticket_id, created_at);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.ticket_history') AND name = N'IX_history_ticket_created')
    CREATE INDEX IX_history_ticket_created ON dbo.ticket_history (ticket_id, created_at);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.notifications') AND name = N'IX_notifications_recipient_read')
    CREATE INDEX IX_notifications_recipient_read ON dbo.notifications (recipient_id, is_read, created_at DESC);
GO

