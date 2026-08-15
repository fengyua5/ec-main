# 后端认证与安全规范

- 认证方案:JWT(HS256)+ HttpOnly cookie(token,24h)。
- 加解密/bcrypt/JWT 逻辑全部集中在 `backend/app/core/security.py`。
- 路由/domain 不得直接碰 jwt / passlib / bcrypt,统一调用 `backend/app/core/security.py` 提供的函数。

  参考:`backend/app/core/security.py`、`backend/app/api/web/auth.py`
