## 1. Workspace 基础

- [x] 1.1 创建根目录 `pnpm-workspace.yaml`，覆盖 `apps/*`、`packages/*` 和 `backend`
- [x] 1.2 创建根目录 `package.json`，提供 web/admin/backend 的开发、检查和构建脚本入口
- [x] 1.3 建立基础目录结构：`apps/web`、`apps/admin`、`backend`、`packages/ui`、`packages/sdk`、`packages/config`、`infra/sqlite`

## 2. 前端应用骨架

- [x] 2.1 初始化 `apps/web` 为 Next.js 16 + Tailwind 买家端应用，并提供基础首页
- [x] 2.2 初始化 `apps/admin` 为 Next.js 16 + Tailwind Admin 应用，并提供基础后台入口页
- [x] 2.3 配置 web/admin 复用共享 TypeScript、Tailwind 或 lint 配置

## 3. 共享 Packages

- [x] 3.1 创建 `packages/ui`，提供至少一个可被 web/admin 引用的基础 UI primitive
- [x] 3.2 创建 `packages/sdk`，封装 API base URL 和 health check 调用
- [x] 3.3 创建 `packages/config`，承载共享 TypeScript/Tailwind/lint 配置或配置约定

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
