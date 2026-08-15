# 后端错误与状态码规范

- 统一抛出 `HTTPException(status_code=..., detail="中文消息")`,不加响应外壳(envelope)。
- 状态码语义:
  - `400` 业务非法(状态流转不允许、自禁用等)
  - `401` 未登录 / 凭证无效
  - `403` 账号禁用
  - `404` 资源不存在
  - `409` 唯一性冲突(如邮箱重复)
  - `422` Pydantic 校验失败
- 认证失败文案约定:"未登录"、"无效的认证凭证"、"用户不存在"。

  参考:`backend/app/domain/auth/__init__.py`、`backend/app/domain/orders/__init__.py`