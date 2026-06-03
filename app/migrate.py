
from sqlalchemy import inspect, text

from .database import engine
from .utils.slug import slugify

def _column_names(table: str) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {row[1] for row in rows}

def _add_column(conn, table: str, column: str, ddl: str) -> None:
    cols = _column_names(table)
    if column not in cols:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))

def _backfill_slugs(conn, table: str, source_column: str) -> None:
    rows = conn.execute(
        text(f"SELECT id, {source_column} AS label FROM {table} WHERE slug IS NULL OR slug = ''")
    ).fetchall()
    used: set[str] = set()
    existing = conn.execute(text(f"SELECT slug FROM {table} WHERE slug IS NOT NULL")).fetchall()
    for (slug,) in existing:
        if slug:
            used.add(slug)

    for row_id, label in rows:
        base = slugify(str(label or ""), fallback=f"{table}-{row_id}")
        candidate = base
        suffix = 2
        while candidate in used:
            candidate = f"{base}-{suffix}"
            suffix += 1
        used.add(candidate)
        conn.execute(
            text(f"UPDATE {table} SET slug = :slug WHERE id = :id"),
            {"slug": candidate, "id": row_id},
        )

def run_migrations() -> None:
    if engine.dialect.name != "sqlite":
        return

    tables = inspect(engine).get_table_names()

    with engine.begin() as conn:
        if "users" in tables:
            _add_column(conn, "users", "role", "role VARCHAR(16) NOT NULL DEFAULT 'member'")
            _add_column(conn, "users", "member_id", "member_id INTEGER")
            _add_column(conn, "users", "password_hash", "password_hash VARCHAR(128)")

        if "members" in tables:
            _add_column(conn, "members", "slug", "slug VARCHAR(128)")
            _add_column(conn, "members", "points_total", "points_total INTEGER NOT NULL DEFAULT 0")
            conn.execute(text("UPDATE members SET points_total = 0 WHERE points_total IS NULL"))
            _backfill_slugs(conn, "members", "name")

        if "projects" in tables:
            _add_column(conn, "projects", "slug", "slug VARCHAR(128)")
            _backfill_slugs(conn, "projects", "name")

        if "articles" in tables:
            _add_column(conn, "articles", "slug", "slug VARCHAR(128)")
            _add_column(conn, "articles", "member_names", "member_names TEXT DEFAULT '[]'")
            _add_column(conn, "articles", "completed_at", "completed_at DATETIME")
            _backfill_slugs(conn, "articles", "title")

        if "article_revisions" in tables:
            _add_column(conn, "article_revisions", "member_names", "member_names TEXT DEFAULT '[]'")
            _add_column(conn, "article_revisions", "completed_at", "completed_at DATETIME")

        if "point_transactions" not in tables:
            conn.execute(
                text(
                    """
                    CREATE TABLE point_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        member_id INTEGER NOT NULL,
                        delta INTEGER NOT NULL,
                        balance_after INTEGER NOT NULL,
                        reason VARCHAR(256) DEFAULT '',
                        granted_by VARCHAR(64) NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(member_id) REFERENCES members(id)
                    )
                    """
                )
            )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_point_transactions_member_id ON point_transactions (member_id)")
            )
