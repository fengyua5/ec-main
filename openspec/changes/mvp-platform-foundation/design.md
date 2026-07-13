## Context

当前仓库还没有成型的电商业务应用，适合先建立架构底座，再逐步加入商品、认证、购物车、结算、订单和 AI 客服等能力。一期技术选型已明确：整体使用 `pnpm` workspace，前端使用 Next.js 16 + Tailwind，后端使用 FastAPI，关系型数据库先使用 SQLite。

本 change 聚焦“系统骨架和边界”，不把业务功能提前混入底座实现。后续业务 changes 应复用这里定义的 app、package、API 和数据持久化约定。

建议目标结构：

```text
ec-main/
  apps/
    web/                 # 买家端：首页、PDP、购物车、结算、订单相关页面
    admin/               # Admin 后台：商品维护和后续运营入口
  backend/               # FastAPI：业务 API、认证、订单、AI 客服接口
  packages/
    ui/                  # 前端共享 UI primitives
    sdk/                 # 前端调用 API 的 typed client
    config/              # 共享 tsconfig、eslint、tailwind 等配置
  infra/
    sqlite/              # 本地 SQLite 数据、初始化和迁移说明
  openspec/
    changes/
```

## Goals / Non-Goals

**Goals:**

- 建立可扩展的 monorepo 架构，让买家端、Admin 和 `backend` API 可以独立开发、启动和部署。
- 明确共享包边界，避免 web/admin 重复实现 UI、API 调用和基础配置。
- 建立 FastAPI 服务基线，提供健康检查、版本化 API 前缀和环境配置约定。
- 明确 SQLite 的本地开发使用方式，以及后续 schema 演进路径。
- 为后续 OpenSpec changes 提供清晰依赖边界。

**Non-Goals:**

- 不实现完整商品 CRUD、PDP 真实数据、购物车、结算、订单、登录或 AI 客服业务逻辑。
- 不接入真实支付网关、复杂库存锁定、促销、物流、ERP/WMS 或客服工单系统。
- 不在一期底座中引入微服务、消息队列、缓存集群或多数据库部署。

## Decisions

### Decision: 使用 `pnpm` monorepo 管理前后端与共享包

采用根目录 `pnpm-workspace.yaml` 管理 `apps/*`、`packages/*` 和 `backend`。根目录脚本负责代理常用开发命令，例如启动 web/admin/backend、运行 lint/typecheck/test。

替代方案：
- 多仓库：边界清晰，但 MVP 阶段协作和共享类型成本更高。
- 单一 Next.js 应用内包含后台和 API：启动简单，但 FastAPI、Admin 权限和后续部署边界会变模糊。

选择理由：MVP 需要速度，但也要为后续拆分业务能力留出清晰边界；monorepo 能在两者之间取得平衡。

### Decision: `apps/web` 和 `apps/admin` 都使用 Next.js 16 + Tailwind

买家端和 Admin 分成两个 Next.js 应用。两者共享 `packages/ui`、`packages/sdk` 和 `packages/config`，但页面路由、鉴权入口和部署边界独立。

替代方案：
- 一个 Next.js 应用内用路由分区 `/admin`：更省启动成本，但 Admin 依赖、权限和布局会污染买家端。
- Admin 使用纯 SPA：可以更轻，但与 Next.js 配置和共享组件一致性较差。

选择理由：Admin 与买家端面向不同用户和安全边界，拆成独立 app 更利于后续演进。

### Decision: 根目录 `backend` 使用 FastAPI 作为业务 API 单体

FastAPI 作为一期唯一后端服务，放在与 `apps` 平级的 `backend/` 目录，建议提供 `/health` 和 `/api/v1/*` API 前缀。商品、认证、购物车、订单和 AI 客服都先以模块形式存在于同一个服务内，后续有明确压力后再评估拆分。

替代方案：
- Next.js route handlers 承担后端：减少服务数量，但不符合用户指定的 FastAPI 方向。
- 多个后端服务：边界更细，但 MVP 阶段运维和本地开发成本过高。

选择理由：FastAPI 单体足够支撑 MVP，并能自然组织 service/router/schema/repository 层。

### Decision: 前端通过 `packages/sdk` 访问 API

`packages/sdk` 作为 web/admin 的统一 API client 层，负责 base URL、请求封装、错误类型和后续认证 token/session 传递。业务页面不直接散落 `fetch` 细节。

替代方案：
- 每个 app 内部单独封装请求：短期简单，但错误处理和认证逻辑会重复。
- 立即引入完整 OpenAPI 代码生成：类型契约强，但底座阶段可能增加工具链复杂度。

选择理由：先建立稳定调用边界，后续可以在 `sdk` 内演进为 OpenAPI 生成或更强类型客户端。

### Decision: SQLite 作为一期本地关系型数据库

API 通过环境变量配置 SQLite 数据库路径。建议后端采用 SQLAlchemy + Alembic 或等价迁移机制管理 schema，避免用一次性脚本堆叠业务表。

替代方案：
- 直接使用裸 SQL 初始化：启动快，但后续 schema 演进和回滚较弱。
- 一期直接上 PostgreSQL：更接近生产，但当前用户明确希望暂用 SQLite。

选择理由：SQLite 适合 MVP 本地迭代；只要迁移边界先定好，后续切换 PostgreSQL 的成本可控。

## Data Flow

```text
Buyer/Admin UI
      |
      v
packages/sdk
      |
      v
FastAPI /api/v1
      |
      v
Service layer
      |
      v
Repository / ORM
      |
      v
SQLite
```

后续 AI 客服的数据流应通过 API 服务读取受控上下文，例如商品摘要和当前登录用户可访问的订单摘要；AI 服务不得直接连接前端或绕过权限检查读取数据库。

## Risks / Trade-offs

- [Risk] SQLite 与未来生产数据库能力不完全一致 → Mitigation：通过 ORM 和迁移工具约束 SQL 使用，避免依赖 SQLite 特有行为。
- [Risk] web/admin 两个 Next.js app 带来重复配置 → Mitigation：把 TypeScript、Tailwind、lint 和 UI primitives 下沉到共享 packages。
- [Risk] `packages/sdk` 初期手写类型可能与 FastAPI schema 漂移 → Mitigation：先集中封装，后续在 API 稳定后评估 OpenAPI 生成。
- [Risk] 底座 change 过度实现业务 → Mitigation：仅提供边界、health check、配置和最小可运行骨架，业务能力放到后续 changes。

## Migration Plan

1. 创建或整理根目录 `pnpm` workspace 配置。
2. 建立 `apps/web`、`apps/admin`、`backend` 和 `packages/*` 的基础目录。
3. 为 web/admin 配置 Next.js 16、Tailwind 和共享配置引用。
4. 为 `backend` 配置 FastAPI app、health check、环境变量读取和 SQLite 连接策略。
5. 为 sdk 提供 API base URL 和 health check 调用示例。
6. 在 README 或等价开发文档中记录本地启动方式和后续 change 依赖边界。

Rollback 策略：如果底座实现出现问题，可以回退本 change 引入的 workspace 和 app/package 目录；由于本 change 不迁移生产数据，回滚不涉及数据兼容处理。

## Open Questions

- Next.js 16 是否在当前环境中已有稳定模板和依赖锁定策略，还是需要在实现阶段确认具体版本可安装性？
- Admin 和买家端是否需要共享同一认证域名/session，还是一期允许独立登录入口？
- SQLite 数据文件默认放在 `backend/.data/`、`infra/sqlite/`，还是使用统一环境变量指向仓库外路径？
