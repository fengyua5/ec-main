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
