## Why

电商 MVP 的买家端和 Admin 后台目前没有任何用户认证机制。在进入商品浏览、下单和后台管理之前，需要先建立基础的邮箱+密码登录注册体系，为用户身份识别和权限控制奠定基础。

## What Changes

- 后端新增 `users` 表（SQLite），存储邮箱、密码哈希、角色等用户信息
- 后端新增 auth API 端点：注册、登录、登出、当前用户信息
- 后端实现 JWT 令牌认证（token 存 cookie + Authorization header）
- Web 端（买家端）新增登录和注册页面
- Admin 端新增登录和注册页面
- SDK 新增 auth 相关方法（登录、注册、登出、获取当前用户）

## Capabilities

### New Capabilities

- `email-auth`: 覆盖用户注册、邮箱+密码登录、JWT 令牌管理、登录状态保持、role-based 用户区分

### Modified Capabilities

- 无

## Impact

- `backend`：新增 `app/api/v1/auth/` 路由模块、`app/models/` 用户模型、`app/services/` 认证服务、`pyproject.toml` 新增 JWT 和密码哈希依赖
- `apps/web`：新增登录/注册页面和路由
- `apps/admin`：新增登录/注册页面和路由
- `packages/sdk`：新增 auth 客户端方法
