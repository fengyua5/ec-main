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
