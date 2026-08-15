# 后端数据模型规范

## SQLAlchemy 2.0 风格

- 使用类型注解写法:`Mapped[...]` + `mapped_column(...)`。
- 时间统一 `DateTime(timezone=True)`。
- 持久化默认值用 `server_default`(布尔用 `"1"`/`"0"`,不写在 Python 逻辑里翻转)。

```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    is_active: Mapped[bool] = mapped_column(server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

  参考:`backend/app/models/user.py`、`backend/app/models/buyer_memory.py`

## 其他

- 新模型必须加入 `backend/app/models/__init__.py`(保证 `create_all` 元数据完整)。
- 表结构变更遵循 `backend/app/db/migrate.py` 的幂等 SQL 迁移方式,不使用 alembic。
