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
│  存 cookie   │     Set-Cookie: token    │  2. 签发 JWT      │
│              │                          │  3. 返回用户信息   │
└──────┬───────┘                          └────────┬─────────┘
       │                                           │
       │  GET /auth/me (Authorization: Bearer)     │
       │  + Cookie auto-sent                       │
       │                                           │
       │  ← 200 { user } 或 401                    │
       │                                           ▼
       │                                    ┌──────────────┐
       │                                    │  SQLite      │
       │                                    │  users 表    │
       │                                    └──────────────┘
```

## Risks / Trade-offs

- [Risk] JWT 无法服务端主动吊销 → Mitigation：token 有效期 24h；后续可加黑名单表
- [Risk] 密码泄漏风险 → Mitigation：bcrypt 哈希、httpOnly cookie 防 XSS 窃取
- [Risk] 一期共享 users 表后续拆分成本 → Mitigation：role 字段隔离业务逻辑，拆表时只需按 role 迁移
- [Risk] Cookie SameSite 在跨域场景可能有问题 → Mitigation：开发环境 CORS 已配置 web/admin 域名

## Migration Plan

1. 安装 Python 依赖（python-jose、passlib、bcrypt）
2. 创建 User SQLAlchemy 模型和迁移
3. 实现 auth 路由（register/login/logout/me）
4. 实现 JWT 工具函数（签发 + 验证 + cookie 设置）
5. 实现密码哈希工具
6. SDK 新增 auth 方法
7. Web 端登录/注册页面
8. Admin 端登录/注册页面
9. 验证端到端流程

## Open Questions

- JWT 签名密钥通过环境变量配置，开发环境默认值如何约定？

## Implementation Divergence

### 路由分离：Web/Admin API 隔离

**设计文档原方案**：统一路由 `/api/v1/auth/*`，通过请求体参数 `role` 区分 buyer/admin。

**实现方案**：两组独立路由 `/api/v1/web/auth/*`（buyer）和 `/api/v1/admin/auth/*`（admin）。

**原因**：用户要求 API 按域隔离，避免前端与 admin 共享同一组 auth 端点。Web 注册自动设为 buyer 角色，Admin 注册自动设为 admin 角色，不需前端传递 role 参数。

**影响**：SDK auth 方法增加 `path: "/web" | "/admin"` 参数；业务逻辑与设计一致；路由隔离增强了安全性（admin 登录端点额外校验 role 字段）。

### shadcn/ui 前端 UI 框架

**设计文档原方案**：使用 `@ec/ui` 共享包（packages/ui）管理通用 UI 组件（Button 等），两端共用。

**实现方案**：两端独立使用 shadcn/ui（基于 `@base-ui/react` 的 Tailwind v4 组件库），`@ec/ui` 已废弃并移除依赖。

**原因**：shadcn/ui 按需安装到各端 `components/ui/` 目录，组件源码可各自定制样式和主题，不需要维护共享 UI 包。Tailwind v4 的 scanner 无法穿透 workspace 包解析编译后的类名，直接在各端使用 shadcn 组件避免了该问题。

**影响**：已安装的组件包括 `button`、`card`、`input`、`label`、`avatar`、`dropdown-menu`、`separator`。所有登录/注册表单使用 Card 包裹，Header 使用 Avatar + DropdownMenu 展示用户信息。后续添加新 UI 组件时直接在各端 `npx shadcn add <组件名>` 即可。

### Admin 认证拦截（proxy.ts + API 代理路由）

**设计文档原方案**：前端直接调用后端 API `/api/v1/admin/auth/*`，cookie 作用域为后端域（`localhost:8000`），前端页面加载时无法读取。

**实现方案**：
1. **Next.js 16 proxy.ts**（原 middleware）：检查所有页面请求的 `token` cookie，不存在则重定向到 `/login`；公开路径（`/login`、`/register`、`/api/*`、`/_next/*`）始终放行
2. **API 代理路由** `apps/admin/app/api/auth/*/route.ts`：前端登录/注册/登出/获取用户改为调用本地 `/api/auth/*` 代理，由代理转发到后端。Set-Cookie 作用域变为 Next.js 域（`localhost:3001`），proxy.ts 可读取

**原因**：httpOnly cookie 按 origin（host + port）隔离，后端 `localhost:8000` 设置的 cookie 不会发送到前端 `localhost:3001`，导致 proxy.ts 无法读取。API 代理路由使 cookie 作用域对齐，同时避免暴露后端地址给前端。

**影响**：新增文件 `apps/admin/proxy.ts`、`apps/admin/app/api/auth/login/register/logout/me/route.ts`；登录/注册页不再直接调用 `@ec/sdk` 的后端地址，改为 fetch 本地 `/api/auth/*`。退出登录和获取用户信息也走代理。前端需配置 `API_BASE_URL`（服务器端环境变量，非 `NEXT_PUBLIC_*`）。

### 前端测试框架（vitest）

**决策**：Admin 端使用 vitest + @testing-library/react + jsdom 编写前端测试。

**测试范围**：
- proxy.ts 拦截逻辑（未认证重定向、公开路由放行、已认证用户通过）
- API 代理路由（请求转发、cookie 传递）
- AuthHeader 组件渲染（未登录/已登录状态）
- Sidebar 组件渲染

**理由**：vitest 与 Next.js 生态兼容性好（vs 可选 Jest），@testing-library/react 是 React 组件测试标准。
