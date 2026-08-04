# Comet Design Handoff

- Change: add-email-auth
- Phase: design
- Mode: compact
- Context hash: 3166969159c978d19a0385104fb3d272a6383dc9888705a4480662991b4407ea

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/add-email-auth/proposal.md

- Source: openspec/changes/add-email-auth/proposal.md
- Lines: 1-29
- SHA256: cdfc1259f24f6aa69ac72f5fd71925b68f3ff7a661041cebf53017614a2d1338

```md
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
```

## openspec/changes/add-email-auth/design.md

- Source: openspec/changes/add-email-auth/design.md
- Lines: 1-117
- SHA256: 46a86ae2b656404f2dbf4d3d94740c2b54f8d2078038d9be1d88d6911f58ffaf

[TRUNCATED]

```md
## Context

当前系统已有 FastAPI 底座、SQLAlchemy + SQLite、CORS 配置和 API v1 路由前缀。Web 和 Admin 端可以访问 SDK，但没有任何用户认证机制。

本 change 在现有底座上叠加邮箱认证层：后端新增 users 表和 JWT 认证，前端新增登录注册页面和 SDK auth 方法。

## Goals / Non-Goals

**Goals:**
- 后端提供用户注册、登录、登出、当前用户信息 API
- 用户数据存入 SQLite（users 表），密码使用 bcrypt 哈希
- 使用 JWT 维护登录状态（token 存 cookie + 请求时带 Authorization header）
- Web 端和 Admin 端提供登录/注册界面
- SDK 封装 auth 接口调用

**Non-Goals:**
- 不实现忘记密码/重置密码
- 不做邮箱验证
- 不做第三方 OAuth 登录
- 不涉及购物车、订单等业务层面的权限控制

## Decisions

### Decision: 用户模型 — 共享 users 表 + role 字段

一期 buyer 和 admin 使用同一张 users 表，通过 `role` 字段区分。

```python
class User(Base):
    id: int (PK, auto)
    email: str (unique, indexed)
    password_hash: str
    role: str  # "buyer" | "admin"
    created_at: datetime
```

替代方案：
- 分开两张表：边界清晰，但一期登录注册逻辑冗余
- 选择理由：一期角色少、逻辑接近，共享表更简单；后续有独立权限诉求时再拆分

### Decision: JWT 认证方式

Token 使用 `python-jose` 库签发和验证 RS256/HS256，存于 httpOnly cookie（自动随请求发送），同时 SDK 层在 Authorization header 中携带。

- Token 内容：`sub`（user_id）、`email`、`role`、`exp`（过期时间）
- Token 过期：24 小时
- Cookie 配置：httpOnly、SameSite=Lax、Secure（生产）

替代方案：
- Session + Cookie：服务端有状态，不适合水平扩展
- 纯 JWT：前端无状态，但 CSRF 防护成本高
- 选择理由：JWT + httpOnly cookie 兼顾无状态和安全性

### Decision: 密码哈希使用 passlib + bcrypt

```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"])
```

替代方案：
- 直接用 hashlib：缺乏盐值和迭代轮数管理
- 选择理由：passlib 是 FastAPI 社区标准，bcrypt 强度足够

### Decision: API 路由设计

```
POST   /api/v1/auth/register  → 注册（email, password, role）
POST   /api/v1/auth/login      → 登录（email, password）→ 返回 token
POST   /api/v1/auth/logout     → 登出（清除 cookie）
GET    /api/v1/auth/me         → 当前登录用户信息（需认证）
```

## Data Flow

```
┌──────────────┐     POST /auth/login     ┌──────────────────┐
│  Web/Admin   │ ──────────────────────▶  │  FastAPI Backend │
│  Login Page  │                          │                  │
│              │ ◀────────────────────── │  1. 验证邮箱密码   │
```

Full source: openspec/changes/add-email-auth/design.md

## openspec/changes/add-email-auth/tasks.md

- Source: openspec/changes/add-email-auth/tasks.md
- Lines: 1-32
- SHA256: 21b6390ab1a39f3df0d222a73585e4cebae93eb9fb7858fcd18e3cd33aa5752e

```md
## 1. 后端认证基础设施

- [ ] 1.1 安装 Python 依赖（python-jose、passlib、bcrypt）
- [ ] 1.2 创建 User SQLAlchemy 模型
- [ ] 1.3 创建密码哈希工具函数
- [ ] 1.4 创建 JWT 工具函数（签发、验证、cookie 设置）

## 2. 后端 Auth API

- [ ] 2.1 实现 POST /api/v1/auth/register 注册端点
- [ ] 2.2 实现 POST /api/v1/auth/login 登录端点
- [ ] 2.3 实现 POST /api/v1/auth/logout 登出端点
- [ ] 2.4 实现 GET /api/v1/auth/me 当前用户端点
- [ ] 2.5 实现认证依赖注入（获取当前用户）

## 3. SDK Auth 方法

- [ ] 3.1 SDK 新增 auth 方法（register、login、logout、getMe）
- [ ] 3.2 SDK 导出 auth 类型和函数

## 4. 前端登录注册页面

- [ ] 4.1 Web 端注册页面
- [ ] 4.2 Web 端登录页面
- [ ] 4.3 Admin 端注册页面
- [ ] 4.4 Admin 端登录页面
- [ ] 4.5 Web/Admin 端登录状态管理（token 处理、受保护路由）

## 5. 验证

- [ ] 5.1 后端 auth API 测试通过
- [ ] 5.2 前端登录注册流程端到端验证
```

## openspec/changes/add-email-auth/specs/email-auth/spec.md

- Source: openspec/changes/add-email-auth/specs/email-auth/spec.md
- Lines: 1-90
- SHA256: cccf4dc6a25340152ea6349c2280b9106755da924b6194bd563c342644a8bb9b

[TRUNCATED]

```md
## ADDED Requirements

### Requirement: User can register with email and password

系统 MUST 允许新用户通过邮箱和密码注册账号。Web 端注册通过 `/api/v1/web/auth/register` 自动设为 buyer 角色，Admin 端注册通过 `/api/v1/admin/auth/register` 自动设为 admin 角色。

#### Scenario: Successful registration

- **WHEN** 用户提交有效的邮箱、密码和角色信息到注册接口
- **THEN** 系统创建新用户返回成功响应，密码以 bcrypt 哈希存储

#### Scenario: Duplicate email registration

- **WHEN** 用户使用已注册的邮箱再次提交注册
- **THEN** 系统返回 409 错误提示邮箱已被注册

#### Scenario: Invalid email format

- **WHEN** 用户提交格式不正确的邮箱地址
- **THEN** 系统返回 422 错误提示邮箱格式无效

### Requirement: User can login with email and password

系统 MUST 允许已注册用户通过邮箱和密码登录，登录成功后返回 JWT token。

#### Scenario: Successful login

- **WHEN** 已注册用户提交正确的邮箱和密码到登录接口
- **THEN** 系统返回 JWT token（设置在 httpOnly cookie 中）和用户基本信息

#### Scenario: Wrong password

- **WHEN** 已注册用户提交错误的密码
- **THEN** 系统返回 401 错误提示邮箱或密码不正确

#### Scenario: Non-existent email

- **WHEN** 用户提交未注册的邮箱地址
- **THEN** 系统返回 401 错误提示邮箱或密码不正确

### Requirement: User can view current session info

系统 MUST 允许已登录用户查看当前登录状态和用户信息。

#### Scenario: Authenticated user views profile

- **WHEN** 已登录用户请求当前用户信息接口
- **THEN** 系统返回用户 ID、邮箱、角色和注册时间

#### Scenario: Unauthenticated user views profile

- **WHEN** 未登录用户请求当前用户信息接口
- **THEN** 系统返回 401 未授权错误

### Requirement: User can logout

系统 MUST 允许已登录用户登出，清除登录状态。

#### Scenario: Successful logout

- **WHEN** 已登录用户请求登出接口
- **THEN** 系统清除登录 token，返回登出成功响应

### Requirement: Web端提供登录注册界面

系统 MUST 在买家端（apps/web）提供登录和注册页面。

#### Scenario: Web user can navigate to login

- **WHEN** 用户访问买家端并点击登录入口
- **THEN** 系统显示邮箱和密码输入框的登录表单

#### Scenario: Web user can register

- **WHEN** 用户访问买家端注册页面并提交注册信息
- **THEN** 注册成功后自动登录并跳转到首页

### Requirement: Admin端提供登录注册界面

系统 MUST 在 Admin 后台（apps/admin）提供登录和注册页面。
```

Full source: openspec/changes/add-email-auth/specs/email-auth/spec.md

