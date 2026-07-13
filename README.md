# EC Main

## 本地开发

- `pnpm install` 安装前端 workspace 依赖。
- `pnpm dev:web` 启动买家端。
- `pnpm dev:admin` 启动 Admin 后台。
- `pnpm dev:backend` 启动 FastAPI backend。

## 目录职责

- `apps/web`：买家端商城。
- `apps/admin`：Admin 后台。
- `backend`：FastAPI API 服务。
- `packages/ui`：共享 UI primitives。
- `packages/sdk`：共享 API client。
- `packages/config`：共享配置。
- `infra/sqlite`：SQLite 本地开发约定。

## 后续 OpenSpec changes 顺序

1. 商品与 Admin 维护。
2. 登录与账号。
3. 购物车、结算和订单。
4. AI 智能客服。
