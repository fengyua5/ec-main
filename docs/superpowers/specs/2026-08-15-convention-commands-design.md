# 按场景加载前端/后端规范的开源命令设计

日期:2026-08-15
状态:待评审

## 背景与目标

当前项目中,AI 生成页面/代码时缺少统一、可被 AI 遵循的前端与后端编码规范,而如果把完整规范常驻写入 AGENTS.md,每次会话都会为用不到的规范消耗 token。

本设计的目标:

1. **AI 生成页面时按前端/后端规范执行**,产出符合项目既定约定的代码。
2. **节省 token**:规范本体不常驻上下文,只在需要时按场景加载。
3. **场景区分**:前端开发任务、前端修 bug、后端开发任务、后端修 bug 各自加载不同的规范内容。
4. **精简 AGENTS.md**:只保留骨架,规范全部外置到按需加载的文档。

## 机制

基于 opencode 的斜杠命令功能。命令是 `.opencode/commands/<name>.md` 文件,模板正文中的 `@文件路径` 会被 opencode 在执行命令时自动读取并合并进 prompt。

因此:

- 规范正文只存放于 `docs/conventions/` 下的原子规范片段(markdown)。
- 命令模板本体非常轻(几行引用 + 任务说明),通过 `@` 引用点按场景组合加载片段。
- AGENTS.md 不再包含规范正文,只保留提示"按场景使用对应命令"。

## 文件布局

```
.opencode/commands/
  fe-dev.md           前端开发任务
  fe-bugfix.md        前端修 bug
  be-dev.md           后端开发任务
  be-bugfix.md        后端修 bug

docs/conventions/
  frontend/
    data-fetching.md      数据获取约定
    api-client.md         API 调用约定(@ec/sdk)
    components.md         UI 组件写法
    styling.md            样式与 design token
    error-loading-form.md 错误 / loading / 表单
    testing.md            前端测试约定
    debugging.md          修 bug 指引
  backend/
    layering.md           路由 / domain 分层
    models.md             数据模型与持久化
    schemas.md            Pydantic schema
    dependency-injection.md 依赖注入
    errors.md             错误与状态码
    testing.md            后端测试约定
    security.md           认证与安全
    debugging.md          修 bug 指引
```

每份片段控制在 20-40 行,只描述"必须做什么 / 禁止做什么 / 参考现有实现"。

## 命令 → 片段映射

| 命令 | 加载片段 |
|---|---|
| `/fe-dev` | `frontend/data-fetching.md`、`api-client.md`、`components.md`、`styling.md`、`error-loading-form.md`、`testing.md` |
| `/fe-bugfix` | `frontend/debugging.md`、`testing.md` |
| `/be-dev` | `backend/layering.md`、`models.md`、`schemas.md`、`dependency-injection.md`、`errors.md`、`testing.md`、`security.md` |
| `/be-bugfix` | `backend/debugging.md`、`testing.md` |

修 bug 场景刻意不整套加载开发规范(不加载样式 / schema / 分层等),只加载"如何定位、最小改动、保持现有模式"+ 测试约定,进一步省 token。

## 命令模板示例

`fe-dev.md`

```
---
description: 按前端开发规范完成前端页面/组件开发
---

按本项目前端规范完成任务: $ARGUMENTS

请严格遵循以下规范切片:

@docs/conventions/frontend/data-fetching.md
@docs/conventions/frontend/api-client.md
@docs/conventions/frontend/components.md
@docs/conventions/frontend/styling.md
@docs/conventions/frontend/error-loading-form.md
@docs/conventions/frontend/testing.md
```

## 规范片段内容大纲

### 前端片段

- **data-fetching.md**:数据获取二选一 —— 静态/非交互页用 Server Component 直接 `await` SDK;交互页统一 `"use client"` + `useEffect` + `useState` + `useCallback` 的 `loadXxx` 模式。禁止引入 SWR / React Query。
- **api-client.md**:所有 API 调用一律走 `@ec/sdk` 的 `createApiClient` + 一等函数(如 `getOrders(client, ...)`),禁止在页面里裸 fetch。admin 的 Next.js API Routes 作为 BFF 转发给 FastAPI 并透传 Cookie。
- **components.md**:UI 组件用各 app 自带的 shadcn 副本(`components/ui/*`):`@base-ui/react` 无头原语 + `cva()` + `cn()`(twMerge + clsx)。组件与 hooks 按功能就近内聚在路由目录,跨页面共享放 `app/components/`。
- **styling.md**:只用 Tailwind v4 utility + design token 语义类。新颜色/品牌先补三层 token(根 token / semantic 桥接 / enki 组合类),禁止硬编码色值。禁止内联样式定义布局样式。
- **error-loading-form.md**:错误用 `useState<string|null>` + `catch` 设置 + 渲染 `text-destructive`;loading 用独立 `useState` boolean + `.finally` 收起,样式用 `Loader2 animate-spin`;表单用受控组件 + 手写校验,不用表单库。
- **testing.md**:Vitest + Testing Library(jsdom)。组件 / hooks / Next API route handler 都要有测试;mock `next/navigation`、`@ec/sdk`、`fetch`。
- **debugging.md**:在现有结构中按功能就近定位;最小改动、不重构;保持现有命名与模式;修完补回归测试。

### 后端片段

- **layering.md**:路由函数体只做参数解析 + 调 domain 函数 + `model_validate` 包装;业务规则(状态机、权限)必须放 `domain/<域>/`。
- **models.md**:SQLAlchemy 2.0 类型注解风格(`Mapped[]` + `mapped_column`);持久化默认值用 `server_default`;新模型加入 `models/__init__.py`。
- **schemas.md**:Pydantic schema 统一放 `domain/<域>/schemas.py` 并使用 `model_config = {"from_attributes": True}`;禁止在路由文件内联定义 schema。
- **dependency-injection.md**:`db: Session = Depends(get_db)` 浅注入;认证用嵌套依赖 `get_current_user`;仅需认证不需用户对象的参数用 `_` 前缀。
- **errors.md**:统一 `HTTPException(status_code, detail="中文")`;状态码语义 400 业务 / 401 未登录 / 403 禁用 / 404 不存在 / 409 重复 / 422 校验;不加响应外壳。
- **testing.md**:pytest + `TestClient`;每个测试文件 `autouse _clean_db` 清表;`conftest.py` 用临时 sqlite 隔离;不 mock 数据库。
- **security.md**:JWT(HS256)+ HttpOnly cookie,集中在 `core/security.py`;路由里不直接碰 jwt/passlib。
- **debugging.md**:先复现并用测试锁定;按分层定位(路由薄 → domain → repo);最小改动、保持分层;补回归测试。

## AGENTS.md 骨架(精简后)

```
# AGENTS.md 指令

## 文档语言
本项目产出的文档必须使用中文(OpenSpec / Superpowers / README / 设计文档 / 实施计划 / 验证报告)。代码标识符、命令、文件路径、配置键、第三方专有名词保留原文。

## 开发规范
按场景加载对应规范,避免常驻上下文浪费 token:
- /fe-dev 前端开发任务 · /fe-bugfix 前端修 bug
- /be-dev 后端开发任务 · /be-bugfix 后端修 bug
```

## 验证方式

1. 手动在 opencode 中执行 `/fe-dev`、`/fe-bugfix`、`/be-dev`、`/be-bugfix`,确认 prompt 中出现对应片段内容。
2. 检查 AGENTS.md 不再包含大段规范正文。
3. 检查前端与后端现有代码符合片段描述(参考调研证据:`apps/web` / `apps/admin` / `packages/sdk` / `backend/app` 现有实现已对齐约定)。

## 范围

- 本设计只创建命令文件与规范片段文档 + 精简 AGENTS.md。
- 不写任何运行时代码,不引入新依赖。
- 不重构现有与规范不一致的代码(如 `api/web/ai.py` 内联 schema)。