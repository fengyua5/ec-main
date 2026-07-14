# Brainstorm Summary

- Change: add-email-auth
- Date: 2026-07-13

## 确认的技术方案

邮箱+密码登录注册，共享 users 表（role 区分 buyer/admin），JWT 存 httpOnly cookie + Authorization header，passlib+bcrypt 密码哈希，FastAPI 依赖注入认证保护。

API 路由分两组：
- `/api/v1/web/auth/*` — Web（买家端）注册/登录/登出/当前用户
- `/api/v1/admin/auth/*` — Admin 后台注册/登录/登出/当前用户

前端 Web/Admin 各一套登录注册页面，SDK 封装 auth 调用。

## 关键取舍与风险

- 共享 users 表一期简单，后续可按 role 拆分
- JWT 无法服务端主动吊销，24h 过期
- httpOnly cookie 防 XSS，SameSite=Lax 防 CSRF

## 测试策略

- 后端 pytest 测试各 auth 端点（正常流程 + 错误边界）
- 前端 TypeScript 编译验证

## Spec Patch

API 路由从统一的 `/api/v1/auth/*` 改为 `/api/v1/web/auth/*` 和 `/api/v1/admin/auth/*` 两组，对应 delta spec 场景需补充分离路由描述。
