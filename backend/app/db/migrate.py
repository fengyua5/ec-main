import logging
from sqlalchemy import Engine, text

logger = logging.getLogger(__name__)

# 轻量幂等迁移：为已存在的 users 表补充 is_active 列（SQLite）
_USER_IS_ACTIVE_SQL = "ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1 NOT NULL"


def _column_exists(engine: Engine, table: str, column: str) -> bool:
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(row[1] == column for row in rows)


def ensure_user_is_active_column(engine: Engine) -> None:
    if _column_exists(engine, "users", "is_active"):
        return
    with engine.begin() as conn:
        conn.execute(text(_USER_IS_ACTIVE_SQL))
    logger.info("迁移: users 表已新增 is_active 列")
