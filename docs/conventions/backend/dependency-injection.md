# 后端依赖注入规范

## 形状

- 数据库:`db: Session = Depends(get_db)`,浅注入。
- 认证:嵌套依赖 `get_current_user`,路由通过 `Depends(get_current_user)` 引入。
- 仅需"已登录"但不需要用户对象的参数,命名用 `_` 前缀(`_current_user`);需要用户对象时用 `current_user`。

```python
@router.get("/{user_id}", response_model=AdminUserResponse)
def user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return AdminUserResponse.model_validate(get_user(db, user_id))
```

  参考:`backend/app/api/admin/users.py` 的 `user_detail`(仅认证)与 `change_user_active`(使用 current_user)

## 禁止

- ❌ 路由里直接 new Session / 手动 close(统一走 `get_db`)。
