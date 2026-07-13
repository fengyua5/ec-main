# Comet Design Handoff

- Change: mvp-platform-foundation
- Phase: design
- Mode: compact
- Context hash: ea07e4d8a5cb1b7ffeb0eafd39c50daab3600b063e527c64d137af5d071fcb63

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/mvp-platform-foundation/proposal.md

- Source: openspec/changes/mvp-platform-foundation/proposal.md
- Lines: 1-27
- SHA256: 90dcd570624d02039f9eefbee9b222af6e44247536d93b6662df304d6fda5137

```md
## Why

电商 MVP 在实现商品、结算、登录、后台和 AI 客服之前，需要先建立稳定的技术底座。提前明确 monorepo、应用边界、后端服务形态、数据库策略和共享契约，可以降低后续业务能力落地时的返工成本。

## What Changes

- 引入面向电商系统的 `pnpm` workspace 架构。
- 定义两个前端应用入口和一个独立后端入口：买家商城、Admin 后台、`backend` API 服务。
- 建立共享包边界，包括 UI 基础组件、API client 和跨项目配置。
- 明确本地 SQLite 开发数据库策略和迁移预期。
- 定义基础前后端集成契约，包括 health check 和环境变量配置。
- 记录后续 MVP changes 的依赖边界：商品与后台、登录账号、购物车结算订单、AI 智能客服。

## Capabilities

### New Capabilities

- `platform-foundation`：覆盖 monorepo workspace、前端应用边界、独立 `backend` 后端边界、共享包、FastAPI 服务基线、SQLite 持久化基线，以及后续业务 change 依赖的前端/API 集成契约。

### Modified Capabilities

- 无。

## Impact

- 影响仓库结构、包管理方式、本地开发命令、前后端应用职责、共享包边界、API 约定和数据库初始化/迁移方式。
- 后续 changes 应基于此底座扩展业务能力，而不是重新定义 workspace 结构、环境契约或应用边界。
```

## openspec/changes/mvp-platform-foundation/design.md

- Source: openspec/changes/mvp-platform-foundation/design.md
- Lines: 1-138
- SHA256: 5eec9cc5decaf4d6623816cd9e09dab2c923d21e5fcc9c1d63eb775dc12975b1

[TRUNCATED]

```md
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

```

Full source: openspec/changes/mvp-platform-foundation/design.md

## openspec/changes/mvp-platform-foundation/tasks.md

- Source: openspec/changes/mvp-platform-foundation/tasks.md
- Lines: 1-41
- SHA256: 0af0b6037b3121787b306356c1303ca99d557848d13220016eb111c16cb5af8c

```md
## 1. Workspace 基础

- [ ] 1.1 创建根目录 `pnpm-workspace.yaml`，覆盖 `apps/*`、`packages/*` 和 `backend`
- [ ] 1.2 创建根目录 `package.json`，提供 web/admin/backend 的开发、检查和构建脚本入口
- [ ] 1.3 建立基础目录结构：`apps/web`、`apps/admin`、`backend`、`packages/ui`、`packages/sdk`、`packages/config`、`infra/sqlite`

## 2. 前端应用骨架

- [ ] 2.1 初始化 `apps/web` 为 Next.js 16 + Tailwind 买家端应用，并提供基础首页
- [ ] 2.2 初始化 `apps/admin` 为 Next.js 16 + Tailwind Admin 应用，并提供基础后台入口页
- [ ] 2.3 配置 web/admin 复用共享 TypeScript、Tailwind 或 lint 配置

## 3. 共享 Packages

- [ ] 3.1 创建 `packages/ui`，提供至少一个可被 web/admin 引用的基础 UI primitive
- [ ] 3.2 创建 `packages/sdk`，封装 API base URL 和 health check 调用
- [ ] 3.3 创建 `packages/config`，承载共享 TypeScript/Tailwind/lint 配置或配置约定

## 4. FastAPI 服务基线

- [ ] 4.1 初始化 `backend` FastAPI 应用结构
- [ ] 4.2 实现 `/health` 或等价健康检查端点
- [ ] 4.3 定义 `/api/v1` API 前缀、配置加载方式和 CORS 本地开发策略

## 5. SQLite 持久化基线

- [ ] 5.1 定义 SQLite 数据库路径环境变量和本地默认值
- [ ] 5.2 建立数据库连接/session 管理基础代码
- [ ] 5.3 建立 schema 迁移或可重复初始化策略，并记录后续业务表接入方式

## 6. 集成与文档

- [ ] 6.1 让 web/admin 通过 `packages/sdk` 调用 API health check
- [ ] 6.2 编写本地开发文档，说明安装、启动、环境变量和目录职责
- [ ] 6.3 记录后续 changes 的依赖顺序：商品与后台、登录账号、购物车结算订单、AI 智能客服

## 7. 验证

- [ ] 7.1 验证 `pnpm` workspace 能识别 apps 和 packages
- [ ] 7.2 验证 web/admin/backend 可以按文档启动或通过基础检查
- [ ] 7.3 验证 API health check 和前端 SDK health check 调用路径可用
```

## openspec/changes/mvp-platform-foundation/specs/platform-foundation/spec.md

- Source: openspec/changes/mvp-platform-foundation/specs/platform-foundation/spec.md
- Lines: 1-71
- SHA256: f4f16a229005c2111f59f31e090ac29adf24b08737978813a62d9277a701203b

```md
## ADDED Requirements

### Requirement: Monorepo workspace baseline
系统 MUST 使用 `pnpm` workspace 组织电商 MVP 的前端、后台、独立 `backend` 后端和共享包，并提供一致的本地开发入口。

#### Scenario: Workspace can be installed and inspected
- **WHEN** 开发者在仓库根目录执行 workspace 安装和脚本查看命令
- **THEN** 系统必须识别买家端、Admin 后台、`backend` API 服务和共享 packages

#### Scenario: Workspace scripts expose core app entrypoints
- **WHEN** 开发者查看根目录脚本
- **THEN** 系统必须提供启动、检查或代理启动 `web`、`admin`、`backend` 的基础命令

### Requirement: Application boundaries
系统 MUST 将买家商城、Admin 后台和 `backend` API 服务定义为独立边界，并明确每个边界的一期职责。

#### Scenario: Buyer storefront boundary is defined
- **WHEN** 后续 change 实现首页、PDP、购物车、结算、订单确认或订单详情
- **THEN** 这些买家体验必须归属到 `apps/web` 或等价买家端应用边界内

#### Scenario: Admin boundary is defined
- **WHEN** 后续 change 实现商品维护、上下架、价格或库存基础维护
- **THEN** 这些后台操作必须归属到 `apps/admin` 或等价 Admin 应用边界内

#### Scenario: API boundary is defined
- **WHEN** 前端或后台需要业务数据、认证、订单或 AI 客服能力
- **THEN** 这些能力必须通过根目录 `backend` 或等价 FastAPI 服务边界提供

### Requirement: Shared package boundaries
系统 MUST 定义共享 UI、API client 和配置 packages，避免应用之间直接复制基础能力。

#### Scenario: Shared UI is reusable
- **WHEN** 买家端和 Admin 后台需要基础 UI primitives
- **THEN** 系统必须提供共享 UI package 作为复用边界

#### Scenario: API client is centralized
- **WHEN** 买家端或 Admin 后台调用后端 API
- **THEN** 系统必须通过共享 SDK/API client package 或明确的统一调用层发起请求

#### Scenario: Shared configuration is centralized
- **WHEN** 多个 TypeScript/Next.js package 需要基础配置
- **THEN** 系统必须提供共享配置 package 或根级配置约定

### Requirement: API service baseline
系统 MUST 提供 FastAPI 服务基线，包含健康检查、版本化 API 边界和可供前端配置的基础地址约定。

#### Scenario: Health check is available
- **WHEN** 开发者或前端请求 API 健康检查端点
- **THEN** API 服务必须返回可机器判断的健康状态

#### Scenario: API base URL is configurable
- **WHEN** 买家端或 Admin 后台在本地开发环境调用 API
- **THEN** API 地址必须通过环境变量或集中配置进行设置

### Requirement: SQLite persistence baseline
系统 MUST 明确 SQLite 作为一期关系型数据库的使用方式，并为后续业务表和迁移保留路径。

#### Scenario: Local database location is defined
- **WHEN** 开发者启动本地 API 服务
- **THEN** 系统必须有明确的 SQLite 数据库路径或环境变量约定

#### Scenario: Migrations can evolve business schema
- **WHEN** 后续 change 增加商品、用户、购物车、订单或客服相关数据表
- **THEN** 系统必须通过迁移或可重复初始化机制演进 schema

### Requirement: Future capability dependency boundaries
系统 MUST 记录后续商品与后台、登录账号、购物车结算订单、AI 智能客服 changes 对平台底座的依赖关系。

#### Scenario: Later changes can depend on foundation
- **WHEN** 后续 OpenSpec change 开始设计业务能力
- **THEN** 该 change 必须能够引用已定义的 app、package、API 和数据库边界，而无需重新定义底座架构
```

