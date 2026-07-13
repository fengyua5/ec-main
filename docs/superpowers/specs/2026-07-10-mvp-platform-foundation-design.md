---
comet_change: mvp-platform-foundation
role: technical-design
canonical_spec: openspec
---

# MVP 平台底座技术设计

## 上下文

本设计用于实现电商 MVP 的技术底座。OpenSpec 仍然是需求的 canonical source；本文档记录 `mvp-platform-foundation` change 已确认的实现架构、技术取舍、测试策略和构建指导。

当前仓库还是一个较薄的规划工作区，主要包含 OpenSpec/Comet 文件，尚无既有电商应用代码。因此本 change 可以直接建立应用结构，不需要迁移既有业务代码。

## 已确认架构

平台使用根目录 `pnpm` workspace 管理前端应用和共享 TypeScript packages；FastAPI 后端位于根目录 `backend/`，作为独立 Python 项目存在。

```text
ec-main/
  apps/
    web/                 # 买家端商城
    admin/               # Admin 后台
  backend/               # FastAPI API 服务
  packages/
    ui/                  # 共享前端 UI primitives
    sdk/                 # 共享 API client
    config/              # 共享 TS/Tailwind/lint 配置
  infra/
    sqlite/              # SQLite 说明、本地数据约定、迁移文档
```

根目录 `package.json` 应提供统一的开发入口，但不应把 Python 依赖管理变成 Node 体系内的职责。根脚本可以代理 `dev:backend`、`check:backend`、`test:backend` 等后端命令；后端仍保留自己的轻量 Python 依赖管理方式。

## 技术决策

### 根目录 `pnpm` 编排，`backend` 保持独立

使用 `pnpm-workspace.yaml` 覆盖：

```yaml
packages:
  - "apps/*"
  - "packages/*"
  - "backend"
```

即使 `backend` 被纳入 workspace 发现和根脚本编排，它仍然是 Python 服务边界。只有在脚本兼容需要时，`backend` 才需要最小化的 `package.json`；Python 依赖应声明在后端原生依赖文件中。

选择原因：这样可以为 MVP 提供统一命令入口，同时保持 FastAPI 打包、虚拟环境和运行时行为对 Python 工具链友好。

### 前端应用保持分离

`apps/web` 和 `apps/admin` 是两个独立的 Next.js 16 + Tailwind 应用。它们共享 `packages/ui`、`packages/sdk` 和 `packages/config`，但路由、布局、环境变量和后续认证边界保持独立。

选择原因：买家端和 Admin 后台在导航、权限、信息密度和部署形态上会快速分化。现在保持分离，可以避免后续再拆分时产生额外成本。

### 后端 API 是单体 FastAPI 服务

`backend/` 承载 MVP API 服务。它应提供健康检查端点和版本化 API 边界，例如：

```text
GET /health
/api/v1/*
```

服务内部建议按清晰后端层次组织：

```text
backend/
  app/
    main.py
    core/
    api/
      v1/
    services/
    repositories/
    db/
    schemas/
```

商品、认证、购物车、订单和 AI 智能客服等业务模块，应在后续各自的 OpenSpec changes 中加入该服务。

### `packages/sdk` 负责前端 API 访问

前端应用通过 `packages/sdk` 调用后端 API，初始能力从 health check client 开始。SDK 应集中处理 API base URL、请求错误和后续认证/session token 传递。

选择原因：这样可以避免 `fetch` 细节散落在 web/admin 页面里，也为未来升级为 OpenAPI 生成 client 留出单一演进路径。

### SQLite 本地优先，但必须迁移友好

SQLite 是一期关系型数据库。后端应从环境变量读取数据库位置，并提供文档化的本地默认值，例如 `backend/.data/ec-main.sqlite3`。

底座应建立迁移工具或可重复初始化机制。对后续业务 changes，推荐使用迁移方式演进商品、用户、购物车、订单和客服相关数据表。

## 数据流

```text
apps/web 或 apps/admin
        |
        v
packages/sdk
        |
        v
backend FastAPI /api/v1
        |
        v
service layer
        |
        v
repository / ORM
        |
        v
SQLite
```

后续 AI 智能客服必须通过 backend services 读取受控上下文，而不能直接读取前端状态或绕过权限的数据库访问。这样才能保证订单可见性和用户权限可执行。

## 实现边界

本 change 只实现平台底座：

- workspace 和 package 结构
- web/admin shell apps
- FastAPI shell service 和 health check
- SDK health check client
- 共享配置和 UI primitive 基线
- SQLite 配置和初始化/迁移约定
- 本地开发文档

本 change 不实现商品 CRUD、PDP 真实数据、购物车、结算、订单、登录、支付或 AI 对话行为。这些能力属于后续 OpenSpec changes。

## 风险与缓解

- SQLite 与生产数据库存在能力差异：通过后端抽象和迁移工具约束 schema 演进，让后续迁移 PostgreSQL 保持现实可行。
- Node/Python 双生态带来安装复杂度：根 `pnpm` 脚本保持开发入口顺手，同时清晰记录 backend Python setup。
- Next.js 16 依赖可用性需要确认：build 阶段确认可安装性，并在 lockfile 中锁定版本。
- SDK/API 类型可能漂移：先从小型集中 SDK 开始，API schema 稳定后再评估 OpenAPI 生成。
- 底座过度建设风险：本 change 限制在 health check、应用 shell、配置和持久化基线。

## 测试策略

### Workspace 检查

- 验证 `pnpm` 能识别 `apps/*`、`packages/*` 和 `backend`。
- 验证根脚本包含 web、admin、backend 和共享检查入口。

### 前端检查

- 验证 web 和 admin 应用可以启动，或通过对应框架检查。
- 验证两个应用都能导入共享配置和共享 UI primitive。
- 验证两个应用都能调用 SDK health check 路径。

### 后端检查

- 验证 FastAPI app 可以正常 import。
- 验证 `/health` 返回机器可判断的健康状态。
- 验证 SQLite 配置能解析本地路径，并能初始化连接。

### 集成检查

- 运行 backend health check。
- 通过 SDK 调用 backend health check。
- 记录后续 changes 可复用的本地启动顺序。

## Spec 补丁

无需回写 OpenSpec spec patch。当前 delta spec 已覆盖根目录 `backend`、workspace、应用边界、API 基线、SQLite 基线和后续 change 依赖边界。
