# platform-foundation Specification

## Purpose
TBD - created by archiving change mvp-platform-foundation. Update Purpose after archive.
## Requirements
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

