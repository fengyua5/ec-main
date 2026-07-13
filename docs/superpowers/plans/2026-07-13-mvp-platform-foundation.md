---
change: mvp-platform-foundation
design-doc: docs/superpowers/specs/2026-07-10-mvp-platform-foundation-design.md
base-ref: unborn-main-no-head
---

# MVP 平台底座实施计划

> **给 agentic workers：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐项执行。本计划使用 checkbox（`- [ ]`）追踪进度。

**目标：** 搭建电商 MVP 的技术底座，包括 `pnpm` workspace、买家端、Admin、独立 `backend` FastAPI 服务、共享 packages、SQLite 基线和本地开发文档。

**架构：** 根目录 `pnpm` 负责统一编排 `apps/web`、`apps/admin`、`packages/*` 和 `backend`。`backend/` 与 `apps/` 平级，保持独立 Python 项目形态；前端通过 `packages/sdk` 调用 backend API。

**技术栈：** pnpm workspace、Next.js 16、Tailwind、TypeScript、FastAPI、SQLite、Python backend-native dependency management。

**基线说明：** 当前仓库尚无初始 commit，`git rev-parse HEAD` 返回 `fatal: ambiguous argument 'HEAD'`。因此 `base-ref` 记录为 `unborn-main-no-head`，不得伪造提交 hash。进入真实实现和提交流前，建议先创建初始提交或在执行阶段明确处理 unborn HEAD。

## 全局约束

- 项目产出的文档必须使用中文；代码标识符、命令、文件路径、配置键、第三方专有名词可保留英文。
- `apps/` 只包含前端应用：`apps/web` 和 `apps/admin`。
- FastAPI 后端必须位于根目录 `backend/`，不得回退为 `apps/api`。
- 根目录 `pnpm` 负责统一开发入口，但不替代 Python 原生依赖管理。
- 本 change 只实现平台底座，不实现商品、购物车、结算、订单、登录、支付或 AI 对话业务。
- 每个任务完成后必须运行该任务列出的验证命令，并更新 `openspec/changes/mvp-platform-foundation/tasks.md` 中对应 checkbox。

## 文件结构规划

- 创建：`pnpm-workspace.yaml`，定义 workspace 覆盖范围。
- 修改：`package.json`，补充根脚本和 workspace 元数据。
- 创建：`apps/web/*`，买家端 Next.js 16 + Tailwind shell。
- 创建：`apps/admin/*`，Admin Next.js 16 + Tailwind shell。
- 创建：`packages/ui/*`，共享 UI primitive。
- 创建：`packages/sdk/*`，共享 API client 与 health check 调用。
- 创建：`packages/config/*`，共享 TypeScript/Tailwind/lint 配置或配置约定。
- 创建：`backend/*`，FastAPI app、health check、配置加载、SQLite 连接基线。
- 创建：`infra/sqlite/README.md`，SQLite 路径、初始化和迁移说明。
- 创建或修改：`README.md`，记录本地开发、环境变量和后续 changes 顺序。
- 修改：`openspec/changes/mvp-platform-foundation/tasks.md`，按完成情况勾选任务。

---

### 任务 1：建立 workspace 和根脚本

**Files:**
- Create: `pnpm-workspace.yaml`
- Modify: `package.json`
- Create: `apps/.gitkeep`
- Create: `packages/.gitkeep`
- Create: `infra/sqlite/.gitkeep`

**Interfaces:**
- Produces: 根目录 workspace 发现 `apps/*`、`packages/*` 和 `backend`。
- Produces: 根脚本 `dev:web`、`dev:admin`、`dev:backend`、`check`、`check:backend`。

- [x] **Step 1: 创建 workspace 配置**

写入 `pnpm-workspace.yaml`：

```yaml
packages:
  - "apps/*"
  - "packages/*"
  - "backend"
```

- [x] **Step 2: 修改根目录 package.json**

将 `package.json` 调整为至少包含：

```json
{
  "name": "ec-main",
  "private": true,
  "packageManager": "pnpm@10.11.0",
  "scripts": {
    "dev:web": "pnpm --filter @ec/web dev",
    "dev:admin": "pnpm --filter @ec/admin dev",
    "dev:backend": "pnpm --filter @ec/backend dev",
    "check": "pnpm -r check",
    "check:backend": "pnpm --filter @ec/backend check"
  },
  "dependencies": {
    "@fission-ai/openspec": "^1.5.0"
  }
}
```

- [x] **Step 3: 创建基础目录占位**

创建 `apps/`、`packages/`、`infra/sqlite/`。如果目录暂时为空，添加 `.gitkeep` 让结构可见。

- [x] **Step 4: 验证 workspace**

Run:

```bash
pnpm -r list --depth -1
```

Expected: 命令能运行；在后续任务创建具体 package 后，应能列出 web/admin/backend/packages。

- [x] **Step 5: 更新 OpenSpec 任务**

勾选 `openspec/changes/mvp-platform-foundation/tasks.md` 中 1.1、1.2、1.3。

---

### 任务 2：创建共享配置和 UI 基线

**Files:**
- Create: `packages/config/package.json`
- Create: `packages/config/tsconfig/base.json`
- Create: `packages/config/tailwind/base.ts`
- Create: `packages/ui/package.json`
- Create: `packages/ui/src/button.tsx`
- Create: `packages/ui/src/index.ts`
- Create: `packages/ui/tsconfig.json`

**Interfaces:**
- Produces: `@ec/config/tsconfig/base.json`
- Produces: `@ec/ui` export `Button`
- Consumes: 根 workspace。

- [x] **Step 1: 创建共享 config package**

创建 `packages/config/package.json`：

```json
{
  "name": "@ec/config",
  "private": true,
  "version": "0.0.0",
  "exports": {
    "./tsconfig/base.json": "./tsconfig/base.json",
    "./tailwind/base": "./tailwind/base.ts"
  }
}
```

- [x] **Step 2: 创建基础 TypeScript 配置**

创建 `packages/config/tsconfig/base.json`：

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "es2022"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve"
  }
}
```

- [x] **Step 3: 创建共享 Tailwind 配置约定**

创建 `packages/config/tailwind/base.ts`：

```ts
import type { Config } from "tailwindcss";

export const baseTailwindConfig = {
  theme: {
    extend: {}
  },
  plugins: []
} satisfies Partial<Config>;
```

- [x] **Step 4: 创建 UI package**

创建 `packages/ui/package.json`：

```json
{
  "name": "@ec/ui",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "exports": {
    ".": "./src/index.ts"
  },
  "scripts": {
    "check": "tsc --noEmit"
  },
  "dependencies": {
    "clsx": "^2.1.1",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@ec/config": "workspace:*",
    "typescript": "^5.7.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0"
  }
}
```

- [x] **Step 5: 创建 Button primitive**

创建 `packages/ui/src/button.tsx`：

```tsx
import { clsx } from "clsx";
import type { ButtonHTMLAttributes } from "react";

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary";
};

export function Button({ className, variant = "primary", ...props }: ButtonProps) {
  return (
    <button
      className={clsx(
        "inline-flex h-10 items-center justify-center rounded-md px-4 text-sm font-medium transition-colors",
        variant === "primary" && "bg-zinc-950 text-white hover:bg-zinc-800",
        variant === "secondary" && "border border-zinc-300 bg-white text-zinc-950 hover:bg-zinc-50",
        className
      )}
      {...props}
    />
  );
}
```

- [x] **Step 6: 导出 UI primitive**

创建 `packages/ui/src/index.ts`：

```ts
export { Button } from "./button";
export type { ButtonProps } from "./button";
```

- [x] **Step 7: 创建 UI tsconfig**

创建 `packages/ui/tsconfig.json`：

```json
{
  "extends": "@ec/config/tsconfig/base.json",
  "include": ["src/**/*.ts", "src/**/*.tsx"]
}
```

- [x] **Step 8: 验证共享 packages**

Run:

```bash
pnpm --filter @ec/ui check
```

Expected: TypeScript 检查通过。

- [x] **Step 9: 更新 OpenSpec 任务**

勾选 `tasks.md` 中 2.3、3.1、3.3。

---

### 任务 3：创建 SDK health check client

**Files:**
- Create: `packages/sdk/package.json`
- Create: `packages/sdk/src/client.ts`
- Create: `packages/sdk/src/health.ts`
- Create: `packages/sdk/src/index.ts`
- Create: `packages/sdk/tsconfig.json`

**Interfaces:**
- Produces: `createApiClient(options: { baseUrl: string }): ApiClient`
- Produces: `checkHealth(client: ApiClient): Promise<HealthResponse>`
- Consumes: backend `/health` endpoint。

- [x] **Step 1: 创建 SDK package**

创建 `packages/sdk/package.json`：

```json
{
  "name": "@ec/sdk",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "exports": {
    ".": "./src/index.ts"
  },
  "scripts": {
    "check": "tsc --noEmit"
  },
  "devDependencies": {
    "typescript": "^5.7.0"
  }
}
```

- [x] **Step 2: 创建 API client**

创建 `packages/sdk/src/client.ts`：

```ts
export type ApiClient = {
  baseUrl: string;
  request<T>(path: string, init?: RequestInit): Promise<T>;
};

export function createApiClient(options: { baseUrl: string }): ApiClient {
  const baseUrl = options.baseUrl.replace(/\/$/, "");

  return {
    baseUrl,
    async request<T>(path, init) {
      const response = await fetch(`${baseUrl}${path}`, init);

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      return response.json() as Promise<T>;
    }
  };
}
```

- [x] **Step 3: 创建 health check 方法**

创建 `packages/sdk/src/health.ts`：

```ts
import type { ApiClient } from "./client";

export type HealthResponse = {
  status: "ok";
  service: "ec-backend";
};

export function checkHealth(client: ApiClient): Promise<HealthResponse> {
  return client.request<HealthResponse>("/health");
}
```

- [x] **Step 4: 导出 SDK 接口**

创建 `packages/sdk/src/index.ts`：

```ts
export { createApiClient } from "./client";
export type { ApiClient } from "./client";
export { checkHealth } from "./health";
export type { HealthResponse } from "./health";
```

- [x] **Step 5: 创建 SDK tsconfig**

创建 `packages/sdk/tsconfig.json`：

```json
{
  "extends": "@ec/config/tsconfig/base.json",
  "include": ["src/**/*.ts"]
}
```

- [x] **Step 6: 验证 SDK**

Run:

```bash
pnpm --filter @ec/sdk check
```

Expected: TypeScript 检查通过。

- [x] **Step 7: 更新 OpenSpec 任务**

勾选 `tasks.md` 中 3.2。

---

### 任务 4：创建 web/admin Next.js shell apps

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/app/page.tsx`
- Create: `apps/web/app/layout.tsx`
- Create: `apps/web/app/globals.css`
- Create: `apps/web/next.config.ts`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/postcss.config.mjs`
- Create: `apps/admin/package.json`
- Create: `apps/admin/app/page.tsx`
- Create: `apps/admin/app/layout.tsx`
- Create: `apps/admin/app/globals.css`
- Create: `apps/admin/next.config.ts`
- Create: `apps/admin/tsconfig.json`
- Create: `apps/admin/postcss.config.mjs`

**Interfaces:**
- Consumes: `@ec/ui` Button。
- Consumes: `@ec/sdk` createApiClient/checkHealth in a server component or utility path.
- Produces: `@ec/web` and `@ec/admin` apps with `dev` and `check` scripts.

- [x] **Step 1: 创建 web package**

创建 `apps/web/package.json`，依赖 Next.js 16、React 19、Tailwind 和共享包：

```json
{
  "name": "@ec/web",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "next dev --port 3000",
    "check": "next lint || true && tsc --noEmit",
    "build": "next build"
  },
  "dependencies": {
    "@ec/sdk": "workspace:*",
    "@ec/ui": "workspace:*",
    "next": "^16.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@ec/config": "workspace:*",
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.7.0"
  }
}
```

- [x] **Step 2: 创建 web 页面**

`apps/web/app/page.tsx` 使用 `Button` 并显示买家端 shell。页面只展示底座状态，不实现商品业务。

- [x] **Step 3: 创建 web layout、CSS 和配置**

添加 `layout.tsx`、`globals.css`、`next.config.ts`、`postcss.config.mjs`、`tsconfig.json`，确保 `tsconfig` extends `@ec/config/tsconfig/base.json`。

- [x] **Step 4: 创建 admin package**

创建 `apps/admin/package.json`，结构与 web 类似，但 `dev` 端口使用 3001，package name 为 `@ec/admin`。

- [x] **Step 5: 创建 admin 页面**

`apps/admin/app/page.tsx` 使用 `Button` 并显示 Admin shell。页面只展示后台入口，不实现商品维护业务。

- [x] **Step 6: 创建 admin layout、CSS 和配置**

添加 `layout.tsx`、`globals.css`、`next.config.ts`、`postcss.config.mjs`、`tsconfig.json`，确保与 web 共用配置模式。

- [x] **Step 7: 验证前端应用**

Run:

```bash
pnpm --filter @ec/web check
pnpm --filter @ec/admin check
```

Expected: 两个应用 TypeScript 检查通过；如 Next.js 16 当前 lint 命令不可用，保留 `tsc --noEmit` 作为基础检查。

- [x] **Step 8: 更新 OpenSpec 任务**

勾选 `tasks.md` 中 2.1、2.2。

---

### 任务 5：创建 backend FastAPI 和 SQLite 基线

**Files:**
- Create: `backend/package.json`
- Create: `backend/pyproject.toml`
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/api/v1/router.py`
- Create: `backend/app/__init__.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/v1/__init__.py`
- Create: `backend/tests/test_health.py`

**Interfaces:**
- Produces: `GET /health` returns `{"status":"ok","service":"ec-backend"}`。
- Produces: `settings.database_url` from env `DATABASE_URL` with local SQLite default.
- Produces: backend root scripts `dev` and `check` callable via root `pnpm`.

- [ ] **Step 1: 创建 backend package script wrapper**

创建 `backend/package.json`：

```json
{
  "name": "@ec/backend",
  "private": true,
  "version": "0.0.0",
  "scripts": {
    "dev": "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000",
    "check": "python3.11 -m pytest"
  }
}
```

- [ ] **Step 2: 创建 Python 项目配置**

创建 `backend/pyproject.toml`：

```toml
[project]
name = "ec-backend"
version = "0.0.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.30.0",
  "pydantic-settings>=2.6.0",
  "sqlalchemy>=2.0.0"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
  "httpx>=0.27.0"
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 3: 创建配置加载**

创建 `backend/app/core/config.py`：

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./.data/ec-main.sqlite3"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    model_config = SettingsConfigDict(env_file=".env", env_prefix="")


settings = Settings()
```

- [ ] **Step 4: 创建数据库 session 基线**

创建 `backend/app/db/session.py`：

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

- [ ] **Step 5: 创建 API router**

创建 `backend/app/api/v1/router.py`：

```python
from fastapi import APIRouter

router = APIRouter()
```

- [ ] **Step 6: 创建 FastAPI app 和 health check**

创建 `backend/app/main.py`：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.core.config import settings

app = FastAPI(title="EC Main API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ec-backend"}


app.include_router(api_v1_router, prefix="/api/v1")
```

- [ ] **Step 7: 创建 health 测试**

创建 `backend/tests/test_health.py`：

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_check() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ec-backend"}
```

- [ ] **Step 8: 创建 Python package init 文件**

创建空文件：`backend/app/__init__.py`、`backend/app/core/__init__.py`、`backend/app/db/__init__.py`、`backend/app/api/__init__.py`、`backend/app/api/v1/__init__.py`。

- [ ] **Step 9: 验证 backend**

Run:

```bash
cd backend
python3.11 -m pytest
```

Expected: `test_health_check` 通过。

- [ ] **Step 10: 更新 OpenSpec 任务**

勾选 `tasks.md` 中 4.1、4.2、4.3、5.1、5.2。

---

### 任务 6：补齐 SQLite 说明、集成说明和 README

**Files:**
- Create: `infra/sqlite/README.md`
- Create or Modify: `README.md`
- Create: `backend/.env.example`
- Create: `apps/web/.env.example`
- Create: `apps/admin/.env.example`

**Interfaces:**
- Produces: 文档化环境变量 `DATABASE_URL`、`NEXT_PUBLIC_API_BASE_URL`。
- Produces: 后续 changes 的依赖顺序说明。

- [ ] **Step 1: 创建 backend env 示例**

创建 `backend/.env.example`：

```env
DATABASE_URL=sqlite:///./.data/ec-main.sqlite3
```

- [ ] **Step 2: 创建前端 env 示例**

创建 `apps/web/.env.example` 和 `apps/admin/.env.example`：

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

- [ ] **Step 3: 创建 SQLite 文档**

创建 `infra/sqlite/README.md`，说明：

```md
# SQLite 本地开发约定

一期使用 SQLite 作为本地关系型数据库。默认数据库路径为 `backend/.data/ec-main.sqlite3`，可通过 `DATABASE_URL` 覆盖。

后续业务表必须通过迁移或可重复初始化机制演进，避免散落一次性 SQL 脚本。商品、用户、购物车、订单和 AI 客服上下文相关表应在各自 OpenSpec change 中定义。
```

- [ ] **Step 4: 创建根 README**

创建或更新 `README.md`，至少包含：

```md
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
```

- [ ] **Step 5: 更新 OpenSpec 任务**

勾选 `tasks.md` 中 5.3、6.2、6.3。

---

### 任务 7：完成端到端基础验证

**Files:**
- Modify: `openspec/changes/mvp-platform-foundation/tasks.md`
- Create: `docs/superpowers/reports/2026-07-13-mvp-platform-foundation-verification.md`

**Interfaces:**
- Consumes: 所有前序任务产物。
- Produces: 中文验证报告。

- [ ] **Step 1: 安装依赖**

Run:

```bash
pnpm install
```

Expected: lockfile 更新且 workspace dependencies 可解析。

- [ ] **Step 2: 验证 workspace**

Run:

```bash
pnpm -r list --depth -1
```

Expected: 输出包含 `@ec/web`、`@ec/admin`、`@ec/backend`、`@ec/ui`、`@ec/sdk`、`@ec/config`。

- [ ] **Step 3: 验证 TypeScript packages 和前端 app**

Run:

```bash
pnpm --filter @ec/ui check
pnpm --filter @ec/sdk check
pnpm --filter @ec/web check
pnpm --filter @ec/admin check
```

Expected: 所有检查通过。

- [ ] **Step 4: 验证 backend**

Run:

```bash
cd backend
python3.11 -m pytest
```

Expected: health check 测试通过。

- [ ] **Step 5: 记录验证报告**

创建 `docs/superpowers/reports/2026-07-13-mvp-platform-foundation-verification.md`，记录每条命令、结果和任何已知限制。报告必须使用中文。

- [ ] **Step 6: 更新 OpenSpec 任务**

勾选 `tasks.md` 中 6.1、7.1、7.2、7.3。

- [ ] **Step 7: 最终确认**

Run:

```bash
openspec validate mvp-platform-foundation --strict
```

Expected: OpenSpec change 仍然有效。
