import logging
from sqlalchemy import Engine, text

logger = logging.getLogger(__name__)

# 轻量幂等迁移：为已存在的 users 表补充 is_active 列（SQLite）
_USER_IS_ACTIVE_SQL = "ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1 NOT NULL"
_HOME_MODULE_DESCRIPTION_SQL = "ALTER TABLE home_modules ADD COLUMN description VARCHAR(200) DEFAULT '' NOT NULL"
_HOME_MODULE_IS_STATIC_SQL = "ALTER TABLE home_modules ADD COLUMN is_static INTEGER DEFAULT 0 NOT NULL"
_BANNER_DESCRIPTION_SQL = "ALTER TABLE banner_items ADD COLUMN description VARCHAR(200) DEFAULT '' NOT NULL"


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


def ensure_home_module_columns(engine: Engine) -> None:
    if not _column_exists(engine, "home_modules", "description"):
        with engine.begin() as conn:
            conn.execute(text(_HOME_MODULE_DESCRIPTION_SQL))
        logger.info("迁移: home_modules 表已新增 description 列")
    if not _column_exists(engine, "home_modules", "is_static"):
        with engine.begin() as conn:
            conn.execute(text(_HOME_MODULE_IS_STATIC_SQL))
        logger.info("迁移: home_modules 表已新增 is_static 列")


def ensure_banner_description_column(engine: Engine) -> None:
    if _column_exists(engine, "banner_items", "description"):
        return
    with engine.begin() as conn:
        conn.execute(text(_BANNER_DESCRIPTION_SQL))
    logger.info("迁移: banner_items 表已新增 description 列")
