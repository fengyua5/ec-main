# Brainstorm Summary

- Change: mvp-platform-foundation
- Date: 2026-07-10

## 确认的技术方案

使用根目录 `pnpm` workspace 管理 `apps/web`、`apps/admin`、`packages/*`，并将 FastAPI 后端放在与 `apps` 平级的 `backend/` 目录。`backend` 保持独立 Python 项目形态，由根目录 `package.json` 脚本统一代理启动、检查和测试。

根 `pnpm` 负责统一开发入口和跨端编排；Python 依赖仍由 `backend` 自己的轻量依赖管理方式负责，避免把 FastAPI 项目强行塞进 Node workspace 模型。

## 候选方案

1. 推荐方案：`pnpm` 编排 + `backend` 独立 Python 项目。优点是前后端边界清晰，符合 `backend/` 平级目录要求，Python 依赖管理不被 Node workspace 扭曲；缺点是实现时需要同时维护 Node 和 Python 两套依赖安装说明。
2. 全部纳入 `pnpm` workspace 脚本的弱统一方案：`backend` 仍独立，但所有开发入口都只通过根目录 `pnpm` 脚本暴露。优点是开发者入口统一；缺点是 Python 环境问题仍需要后端自己的工具处理。
3. 单仓库但不统一编排方案：前端用 `pnpm`，后端完全独立命令。优点是简单；缺点是 MVP 多端联调体验差，不推荐。

## 关键取舍与风险

- 取舍：`backend/` 与 `apps/` 平级，而不是 `apps/api`，使后端职责更显式。
- 取舍：根 `pnpm` 负责 orchestration，不直接替代 Python dependency manager。
- 风险：Next.js 16 依赖安装可用性需要实现阶段确认。
- 风险：Python dependency manager 尚未最终指定，推荐实现阶段优先选择轻量方案，如 `uv` 或 `venv + requirements`，并在不增加复杂度的前提下保证可复现。
- 风险：手写 `packages/sdk` 类型可能与 FastAPI schema 漂移，后续可升级为 OpenAPI 生成。

## 测试策略

- workspace 级验证：`pnpm` 能识别 `apps/*`、`packages/*`，根脚本能代理 web/admin/backend。
- 前端验证：web/admin 基础页面可启动并能通过 `packages/sdk` 请求 health check。
- 后端验证：FastAPI health check 返回机器可判断状态；SQLite 路径配置和连接初始化可测试。
- 集成验证：本地环境变量配置后，前端 SDK 能访问 backend health check。

## Spec Patch

无。当前 OpenSpec delta spec 已覆盖 `backend` 平级目录、workspace、应用边界、API、SQLite 和后续 change 依赖。
