from sqlalchemy.sql.elements import ColumnElement, SQLColumnExpression


def literal_contains(
    column: SQLColumnExpression[str | None], value: str
) -> ColumnElement[bool]:
    """Build a case-insensitive literal substring predicate for SQLite and SQL Server."""

    escaped = value.strip().replace("/", "//")
    for character in ("%", "_", "[", "]"):
        escaped = escaped.replace(character, f"/{character}")
    return column.ilike(f"%{escaped}%", escape="/")
