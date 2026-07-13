# EC Main

EC Main 是一个电商 MVP（最小可行产品）平台，采用 monorepo 架构管理多个前端应用、共享包和后端服务。

## 架构概览

```
┌──────────────────────────────────────────────────┐
│                  前端应用层                        │
│  ┌────────────────┐  ┌────────────────────────┐  │
│  │  apps/web      │  │  apps/admin             │  │
│  │  买家端商城     │  │  Admin 后台             │  │
│  │  Next.js +     │  │  Next.js +             │  │
│  │  Tailwind      │  │  Tailwind              │  │
│  └───────┬────────┘  └───────────┬────────────┘  │
│          │                      │                 │
│  ┌───────┴──────────────────────┴────────────┐   │
│  │          共享包层                          │   │
│  │  packages/sdk (API client)                │   │
│  │  packages/ui (UI primitives)              │   │
│  │  packages/config (TS/Tailwind 配置)       │   │
│  └───────────────────────┬───────────────────┘   │
└──────────────────────────┼───────────────────────┘
                           │ HTTP /api/v1
┌──────────────────────────┼───────────────────────┐
│                  后端 API 服务层                  │
│  ┌───────────────────────┴───────────────────┐   │
│  │  backend/ (FastAPI)                      │   │
│  │  - CORS 中间件 → 配置加载                  │   │
│  │  - /api/v1 路由 → 业务模块                │   │
│  └───────────────────────┬───────────────────┘   │
│                          │                       │
│  ┌───────────────────────┴───────────────────┐   │
│  │          数据持久化层                      │   │
│  │  SQLite (本地开发) → SQLAlchemy ORM       │   │
│  │  环境变量: DATABASE_URL                   │   │
│  └───────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

**技术栈：** pnpm workspace · Next.js 16 · Tailwind · FastAPI · SQLAlchemy · SQLite

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
