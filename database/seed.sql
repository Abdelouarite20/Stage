/*
    Alias Informatique ticket management application
    Idempotent development/reference seed for Microsoft SQL Server

    IMPORTANT: every catalogue item, SLA value and customer below is synthetic
    or proposed for demonstration. Nothing in this file is confidential company
    or customer data. Business owners must validate the catalogue and SLA values.

    This script deliberately creates no user. In particular, it never stores a
    plaintext or shared demonstration password. Create the first administrator
    through the FastAPI bootstrap described in docs/database-design.md.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

BEGIN TRY
    BEGIN TRANSACTION;

    /* Assumption — to be validated with Alias Informatique.
       The proposed categories below are demonstration values. */
    INSERT INTO dbo.ticket_categories (name, description, is_active)
    SELECT source.name, source.description, 1
    FROM
    (
        VALUES
            (N'Incident technique',   N'Incident lié au fonctionnement technique d''une solution.'),
            (N'Incident fonctionnel', N'Difficulté rencontrée dans l''utilisation fonctionnelle d''une solution.'),
            (N'Demande d''assistance', N'Besoin d''accompagnement ou d''aide utilisateur.'),
            (N'Configuration',        N'Demande de paramétrage ou d''ajustement de configuration.'),
            (N'Demande d''information', N'Question ne nécessitant pas nécessairement une intervention.'),
            (N'Intervention',         N'Demande d''intervention fonctionnelle ou technique.'),
            (N'Évolution',            N'Demande d''évolution d''une solution existante.')
    ) AS source (name, description)
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.ticket_categories AS existing
        WHERE existing.name = source.name
    );

    /* Assumption — to be validated with Alias Informatique.
       The product catalogue below is illustrative. */
    INSERT INTO dbo.products (name, description, is_active)
    SELECT source.name, source.description, 1
    FROM
    (
        VALUES
            (N'Sage 100', N'Produit de démonstration pour regrouper des modules Sage 100.'),
            (N'Autre solution', N'Produit générique de démonstration pour une solution non encore cataloguée.')
    ) AS source (name, description)
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.products AS existing
        WHERE existing.name = source.name
    );

    /* Assumption — to be validated with Alias Informatique.
       The module catalogue below is illustrative. */
    INSERT INTO dbo.product_modules (product_id, name, description, is_active)
    SELECT product.id, source.module_name, source.description, 1
    FROM
    (
        VALUES
            (N'Sage 100', N'Comptabilité',        N'Module de comptabilité utilisé uniquement comme donnée de démonstration.'),
            (N'Sage 100', N'Paie',                N'Module de paie utilisé uniquement comme donnée de démonstration.'),
            (N'Sage 100', N'Gestion commerciale', N'Module de gestion commerciale utilisé uniquement comme donnée de démonstration.'),
            (N'Autre solution', N'Module générique', N'Module générique à remplacer par le catalogue validé.')
    ) AS source (product_name, module_name, description)
    INNER JOIN dbo.products AS product
        ON product.name = source.product_name
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.product_modules AS existing
        WHERE existing.product_id = product.id
          AND existing.name = source.module_name
    );

    /*
       Assumption — to be validated with Alias Informatique.
       Continuous elapsed-hour targets and warning
       at 80% of elapsed target time. These are demonstration values, not an
       Alias Informatique commitment or contractual SLA.
    */
    INSERT INTO dbo.sla_configurations
        (priority, target_hours, warning_threshold_percent, is_active)
    SELECT source.priority, source.target_hours, source.warning_threshold_percent, 1
    FROM
    (
        VALUES
            ('LOW',      72, 80),
            ('MEDIUM',   48, 80),
            ('HIGH',     24, 80),
            ('CRITICAL',  8, 80)
    ) AS source (priority, target_hours, warning_threshold_percent)
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.sla_configurations AS existing
        WHERE existing.priority = source.priority
    );

    /* Entirely fictional customers; example.com is reserved for documentation. */
    INSERT INTO dbo.customers
        (company_name, contact_name, email, phone, address, is_active)
    SELECT source.company_name, source.contact_name, source.email, source.phone, source.address, 1
    FROM
    (
        VALUES
            (
                N'Entreprise Démo Atlas SARL',
                N'Nadia Exemple',
                N'atlas-demo@example.com',
                N'+212 5 00 00 00 01',
                N'Adresse fictive, Casablanca'
            ),
            (
                N'Société Test Horizon SA',
                N'Youssef Exemple',
                N'horizon-test@example.com',
                N'+212 5 00 00 00 02',
                N'Adresse fictive, Casablanca'
            )
    ) AS source (company_name, contact_name, email, phone, address)
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.customers AS existing
        WHERE existing.company_name = source.company_name
    );

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO
