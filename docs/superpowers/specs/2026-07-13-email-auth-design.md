---
comet_change: add-email-auth
role: technical-design
canonical_spec: openspec
---

# 邮箱登录认证设计

## 目标

为 EC Main 平台的买家端（Web）和 Admin 后台分别提供邮箱+密码的登录注册能力，建立基础用户认证体系。

## 架构

```
┌──────────────────────────────────────────────────┐
│                  前端应用层                        │
│  ┌────────────────┐  ┌────────────────────────┐  │
│  │  apps/web      │  │  apps/admin            │  │
│  │  登录/注册页   │  │  登录/注册页           │  │
│  └───────┬────────┘  └───────────┬────────────┘  │
│          │                      │                 │
│  ┌───────┴──────────────────────┴────────────┐   │
│  │  packages/sdk (auth 方法)                  │   │
│  └───────────────────────┬───────────────────┘   │
└──────────────────────────┼───────────────────────┘
                           │
┌──────────────────────────┼───────────────────────┐
│                  后端 API 层                      │
│  /api/v1/web/auth/*  ────┼─── buyer 认证         │
│  /api/v1/admin/auth/* ───┼─── admin 认证         │
│                          ▼                       │
│              auth 路由模块（复用逻辑）              │
│                          │                       │
│  ┌───────────────────────┴───────────────────┐   │
│  │  app/services/auth.py                     │   │
│  │  - 密码验证 (passlib+bcrypt)              │   │
│  │  - JWT 签发/验证 (python-jose)            │   │
│  │  - Cookie 设置/清除                       │   │
│  └───────────────────────┬───────────────────┘   │
│                          │                       │
│  ┌───────────────────────┴───────────────────┐   │
│  │  app/models/user.py                      │   │
│  │  User: id, email, password_hash,         │   │
│  │        role (buyer|admin), created_at     │   │
│  └───────────────────────┬───────────────────┘   │
│                          │                       │
│  ┌───────────────────────┴───────────────────┐   │
│  │  SQLite (SQLAlchemy)                     │   │
│  └───────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

## API 端点

### Web（买家端）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/web/auth/register` | 注册 buyer 账号 |
| POST | `/api/v1/web/auth/login` | buyer 登录 |
| POST | `/api/v1/web/auth/logout` | buyer 登出 |
| GET | `/api/v1/web/auth/me` | 获取当前 buyer 信息 |

### Admin 后台

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/admin/auth/register` | 注册 admin 账号 |
| POST | `/api/v1/admin/auth/login` | admin 登录 |
| POST | `/api/v1/admin/auth/logout` | admin 登出 |
| GET | `/api/v1/admin/auth/me` | 获取当前 admin 信息 |

## 数据模型

```python
class User(Base):
    __tablename__ = "users"

    id: int          # PK, autoincrement
    email: str       # unique, indexed
    password_hash: str  # bcrypt hash
    role: str        # "buyer" | "admin"
    created_at: datetime  # auto
```

## 认证流程

```
登录请求
  │
  ├→ 验证 email + password
  │     │
  │     ├→ 不匹配 → 401
  │     │
  │     └→ 匹配 → 签发 JWT
  │               ├→ payload: { sub, email, role, exp }
  │               ├→ httpOnly cookie: token=<jwt>
  │               └→ response: { user }
  │
登出请求 → 清除 cookie → 200

受保护请求
  │
  ├→ 读取 cookie / Authorization header 中的 JWT
  ├→ 验证签名 + 过期时间
  │     ├→ 无效 → 401
  │     └→ 有效 → 注入当前用户到 request
```

## 关键技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 密码哈希 | passlib + bcrypt | FastAPI 社区标准，自动盐值 |
| JWT | python-jose | 成熟的 JWT 库 |
| Token 存储 | httpOnly cookie | 防 XSS 窃取 |
| Token 传输 | Authorization: Bearer | SDK 请求 header 携带 |
| Token 过期 | 24 小时 | 一期够用，后续可加刷新 |

## 风险与缓解

- **JWT 无法服务端吊销** → 24h 有效期；后续可加黑名单
- **密码泄漏** → bcrypt 哈希 + httpOnly cookie
- **共享 users 表后续拆分** → role 字段隔离，拆表只需按 role 迁移

## 前端 UI 框架

两端独立使用 **shadcn/ui**（基于 `@base-ui/react` 的 Tailwind v4 组件库），组件安装在各端 `components/ui/` 目录，源码可控、样式可定制的。已安装的组件：

- `button`、`card`、`input`、`label` — 登录/注册表单
- `avatar`、`dropdown-menu` — Header 用户信息展示
- `separator` — 侧边栏分割装饰

添加新组件时在各端运行 `npx shadcn add <组件名>` 即可。

## 测试策略

- `tests/test_auth.py`：注册成功、重复邮箱、密码错误、未认证访问、登出
- SDK TypeScript 编译检查
- 前端页面手动验证登录注册流程
