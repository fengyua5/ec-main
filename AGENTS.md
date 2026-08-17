# AGENTS.md 指令

## 项目定位

**全栈 SaaS 平台**，采用 Monorepo 架构：

| 模块 | 技术栈 | 职责 |
|------|--------|------|
| `apps/web` | Next.js 16 + React 19 + TypeScript + Tailwind + shadcn/ui | 用户端应用 |
| `apps/admin` | Next.js + React + TypeScript | 管理后台 |
| `backend` | Python 3.11+ + FastAPI + SQLAlchemy + Pydantic | API 服务 |
| `packages/sdk` | TypeScript | 前端 API 调用 SDK（统一入口） |
| `packages/config` | TypeScript | 共享配置（TSConfig、ESLint 等） |

---

## 文档语言

本项目产出的文档必须使用中文，包括 OpenSpec 产物、Superpowers specs/plans、README、开发说明、设计文档、实施计划和验证报告。只有代码标识符、命令、文件路径、配置键、第三方专有名词或引用原文需要保留英文时，才使用英文。

---

## 核心工作流

本项目的开发工作流基于 **Comet（OpenSpec + Superpowers 双星系统）**：

```
OpenSpec 负责 WHAT — 大纲、提案、spec 生命周期、归档
Superpowers 负责 HOW — 技术设计、计划、执行、收尾
```

### 三种工作路径

| 路径 | 适用场景 | 流程 |
|------|---------|------|
| `/comet` | 新功能开发 | open → design → build → verify → archive |
| `/comet-hotfix` | 明确 Bug 修复（≤2 文件） | open → build → verify → archive |
| `/comet-tweak` | 小改动（文案/配置/文档） | open → lightweight build → light verify → archive |

**核心原则**：brainstorming 不可跳过（hotfix/tweak 除外）。

---

## 意图识别与规范路由

AI 自动识别用户意图并加载对应规范，**用户无需手动选择**。

### 识别规则

```
1. 用户描述包含「改文案」「调整样式」「修改配置」「优化 prompt」等小改动
   → 自动判定为 Tweak 场景（comet-tweak）→ 只加载 1-2 个相关规范

2. 用户描述包含「bug」「坏了」「不显示」「报错」等 + 涉及已有功能
   → 自动判定为 Bug 修复场景 → 加载全部核心规范

3. 用户描述包含「新功能」「实现」「开发」「添加」等
   → 自动判定为开发场景 → 加载全部核心规范 + 条件规范

4. 无法判断时
   → 询问：「这是新功能开发、Bug 修复还是小改动？」
```

### 技术栈判断

| 用户描述关键词 | 目标模块 |
|--------------|---------|
| 页面、组件、样式、交互、路由、状态、hook | `apps/web` 或 `apps/admin`（前端） |
| API、接口、数据库、模型、domain、路由函数 | `backend`（后端） |
| 不明确 | 先询问，或检查最近修改的文件 |

### 规范加载规则

#### 核心规范（dev/bugfix 场景必加载）

这些规则影响所有代码，必须始终遵守：

| 场景 | 规范 |
|------|------|
| **前端（统一）** | `@docs/conventions/frontend/data-fetching.md`<br>`@docs/conventions/frontend/api-client.md`<br>`@docs/conventions/frontend/components.md`<br>`@docs/conventions/frontend/styling.md`<br>`@docs/conventions/frontend/error-loading-form.md`<br>`@docs/conventions/frontend/debugging.md` |
| **后端（统一）** | `@docs/conventions/backend/layering.md`<br>`@docs/conventions/backend/models.md`<br>`@docs/conventions/backend/schemas.md`<br>`@docs/conventions/backend/errors.md`<br>`@docs/conventions/backend/security.md`<br>`@docs/conventions/backend/debugging.md` |
| **跨域开发** | **前端核心 + 后端核心全部加载** |

#### 条件规范（按任务类型追加加载）

| 任务类型 | 追加规范 |
|---------|---------|
| 新建页面/组件/路由 | `@docs/conventions/frontend/directory-structure.md` |
| 新建 API 接口 | `@docs/conventions/backend/api-responses.md` |
| 涉及依赖注入 | `@docs/conventions/backend/dependency-injection.md` |
| 需要写测试 | `@docs/conventions/frontend/testing.md` 或 `@docs/conventions/backend/testing.md` |

#### Tweak 规范（小改动按需加载）

| 任务类型 | 加载规范 |
|---------|---------|
| 改文案/文字 | `components.md`（前端）或 `layering.md`（后端） |
| 改样式 | `styling.md` |
| 改配置 | 不加载 |

> **跨领域规范**（`docs/cross-domain/`）不在启动时加载，按需要在执行过程中引用：
> - `code-review.md` — PR/合并前 review 时
> - `commit-convention.md` — 执行 commit 时
> - `monorepo-versions.md` — 发布包时

---

## 提交纪律

除非用户明确要求，否则不要自动创建 git commit。实现、修复、文档同步等所有改动都只暂存(stage)，等用户确认后再提交。

---

## 禁止事项

- 不得修改 `node_modules/`、`.pnpm-lock.yaml`、`uv.lock` 等依赖锁文件
- 不得直接修改 `.comet.yaml` 状态文件（由工具链管理）
- 不得跳过 brainstorming 阶段直接进入实现（hotfix/tweak 除外）
- 不得在路由文件中写业务逻辑（违反分层规范）
- 不得在组件里裸写 fetch（必须走 `@ec/sdk`）
- 不得硬编码颜色值（必须走 design token）

---

## 快速参考

```bash
# 启动开发服务
pnpm dev:web          # 用户端 Next.js
pnpm dev:admin        # 管理后台
pnpm dev:backend      # 后端 FastAPI

# 类型检查
pnpm check            # 全量检查
pnpm check:backend    # 仅后端

# 测试
cd backend && pytest  # 后端测试
cd apps/web && npx vitest run  # 前端测试
```
