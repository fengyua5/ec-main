# 后端依赖注入规范

## 形状

- 数据库:`db: Session = Depends(get_db)`,浅注入。
- 认证:嵌套依赖 `get_current_user`,路由通过 `Depends(get_current_user)` 引入。
  - 仅需"已登录"但不需要用户对象的参数,命名用 `_` 前缀(`_current_user`)。

```python
@router.get("/{order_no}")
def get_order(order_no: str, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    ...
```

  参考:`backend/app/db/deps.py`、`backend/app/domain/auth/deps.py`、`backend/app/api/admin/users.py`

## 禁止

- ❌ 路由里直接 new Session / 手动 close(统一走 `get_db`)。