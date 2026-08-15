# 按场景加载前端/后端规范的 opencode 命令实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建 4 个 opencode 斜杠命令(`/fe-dev`、`/fe-bugfix`、`/be-dev`、`/be-bugfix`),按场景 `@` 引用加载前端/后端原子规范片段,并把 AGENTS.md 精简为只留骨架。

**Architecture:** 规范正文只存放于 `docs/conventions/{frontend,backend}/` 下的 markdown 片段;`.opencode/commands/` 下的命令模板正文通过 `@docs/conventions/...` 引用这些片段,由 opencode 在命令执行时自动把片段内容合并进 prompt。AGENTS.md 只保留文档语言要求 + 一行命令使用提示。

**Tech Stack:** opencode 命令(无需运行时、无新依赖)。

**设计文档:** `docs/superpowers/specs/2026-08-15-convention-commands-design.md`

---

### Task 1: 创建前端规范片段

**Files:**
- Create: `docs/conventions/frontend/data-fetching.md`
- Create: `docs/conventions/frontend/api-client.md`
- Create: `docs/conventions/frontend/components.md`
- Create: `docs/conventions/frontend/styling.md`
- Create: `docs/conventions/frontend/error-loading-form.md`
- Create: `docs/conventions/frontend/testing.md`
- Create: `docs/conventions/frontend/debugging.md`

- [ ] **Step 1: 创建 `data-fetching.md`**

```markdown
# 前端数据获取规范

## 两种允许的模式

1. **静态 / 非交互页面**:使用 Server Component,直接 `await` SDK 调用。

```tsx
export default async function HomePage() {
  const health = await checkHealth(getClient());
  return <div>...{health}...</div>;
}
```

  参考:`apps/web/app/(main)/page.tsx`

2. **交互页面**:`"use client"` + `useEffect` + `useState` + `useCallback`,统一命名为 `loadXxx`。

```tsx
"use client";
const [data, setData] = useState<T>([]);
const [loading, setLoading] = useState(false);

const loadOrders = useCallback(async () => {
  setLoading(true);
  try {
    setData(await getOrders(getClient()));
  } finally {
    setLoading(false);
  }
}, []);

useEffect(() => { void loadOrders(); }, [loadOrders]);
```

  参考:`apps/admin/app/(main)/orders/page.tsx`

## 禁止

- ❌ 引入 SWR / React Query / @tanstack(项目不采用)。
- ❌ 在组件内裸写业务 fetch 逻辑。
```

- [ ] **Step 2: 创建 `api-client.md`**

```markdown
# 前端 API 调用规范

## 统一走 @ec/sdk

- 所有 API 调用一律通过 `packages/sdk` 的 `createApiClient` 创建 client,并调用 sdk 提供的一等函数。
- 函数签名以 `client: ApiClient` 为第一个参数。

```ts
// apps/web 或 apps/admin 中创建单例
const client = createApiClient({ baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000" });

// sdk 用法
const orders = await getOrders(client, { page, page_size });
```

  参考:`apps/web/app/(auth)/login/page.tsx`、`packages/sdk/src/client.ts`、`packages/sdk/src/orders.ts`

## 禁止

- ❌ 在页面/组件里裸 `fetch(BACKEND_URL...)` 直连后端。
- ❌ 在 app 业务代码中重复定义请求/响应类型(应加在 sdk 对应模块)。

## admin BFF 代理

- 需要隐藏后端 URL 或透传凭证时,在 `apps/admin/app/api/<域>/route.ts` 用 Next.js Route Handler 作为 BFF:转发浏览器的 `Cookie` 头、透传后端 status。

  参考:`apps/admin/app/api/auth/me/route.ts`
```

- [ ] **Step 3: 创建 `components.md`**

```markdown
# 前端 UI 组件规范

## 使用各 app 自带的 shadcn 副本

- 组件放在 `apps/web/components/ui/` 或 `apps/admin/components/ui/`(项目不共享 `@ec/ui`,已废弃)。
- 写法:`@base-ui/react` 无头原语 + `cva()` 声明 variants + `cn()`(twMerge + clsx)合并类名,导出组件与 `xxxVariants`。

  参考:`apps/web/components/ui/button.tsx`

## 组织方式

- 特定页面/功能的组件、hooks、workers 按功能就近内聚在路由目录下(如 `app/(main)/ai/components/`、`app/(main)/ai/hooks/`)。
- 跨页面共享的组件放 `app/components/`(如 `bottom-tab-bar.tsx`)。

## 禁止

- ❌ 新建组件时手写 clsx 拼接大段类名(应走 cva)。
- ❌ 把不需要的组件放到全局 `components/ui/`(就近内聚优先)。
```

- [ ] **Step 4: 创建 `styling.md`**

```markdown
# 前端样式规范

## 只使用 Tailwind v4 utility + design token

- 样式一律用 Tailwind utility 类,禁用内联 `style` 定义布局样式。
- 颜色/间距等静态值必须走 design token 语义类,不直接写十六进制/oklch 色值。

## 三层 design token 体系(app/design-tokens/)

1. `tokens.css`:根色板 `@theme`,唯一事实来源。
2. `semantic.css`:`@theme inline` 桥接层,把 `--font-size-*` 等桥到 Tailwind。
3. `enki.css`:`@layer components` 的 `.enki-*` 组合类(如 `enki-body-sm`)。

## 新颜色/品牌规范

- 需要新色值 → 在 `tokens.css` 加根 token,再在语义层映射,禁止在组件里硬编码色值。
- 参考 `apps/web/app/design-tokens/*.css`、`packages/config` 中两端的 token 约定。
```

- [ ] **Step 5: 创建 `error-loading-form.md`**

```markdown
# 前端错误 / loading / 表单规范

## 错误处理

- 页面本地 `useState<string | null>` 存错误,`catch` 里 `setError(...)`,渲染 `<p className="text-sm text-destructive">`。
- 复杂场景可用 `{ type: "success" | "error", message }` 对象。

## loading

- 独立 `useState` boolean,`loadXxx` 开头 `setLoading(true)`,`.finally` 里 `setLoading(false)`。
- 渲染用 `Loader2 className="animate-spin"`。
- 行级操作(删除等)用独立 state(如 `deletingId`),不与整页 loading 混用。

## 表单

- 受控 `useState` + `onSubmit` `preventDefault`,不引入表单库。
- 基础校验交给原生 `required`,业务校验手写。

  参考:`apps/web/app/(auth)/login/page.tsx`、`apps/web/app/(main)/account/page.tsx`、`apps/admin/app/(main)/faq/components/upload-form.tsx`
```

- [ ] **Step 6: 创建 `testing.md`**

```markdown
# 前端测试规范

## 框架

- Vitest + Testing Library(jsdom),配置见 `apps/web/vitest.config.ts` / `apps/admin/vitest.config.ts`。

## 要求

- 组件、hooks、Next.js API route handler 都要补测试。
- 测试文件放 `apps/<app>/__tests__/`,按被测模块镜像目录结构。

## 常用 mock 手法

- 路由:`vi.mock("next/navigation")`。
- SDK:`vi.mock("@ec/sdk")`。
- 后端请求:`vi.spyOn(globalThis, "fetch")`。
- 浏览器 API:`vi.stubGlobal`(如 Worker)。

  参考:`apps/web/__tests__/bottom-tab-bar.test.tsx`、`apps/web/__tests__/ai/use-sse-chat.test.ts`、`apps/admin/__tests__/api/auth/login.test.ts`
```

- [ ] **Step 7: 创建 `debugging.md`**

```markdown
# 前端修 bug 指引

## 定位

- 按功能就近定位:先在对应路由目录(`app/(main)/<feature>/`)内找页面、components、hooks。
- 数据流:`@ec/sdk` 函数 → 页面 `loadXxx` → 组件 props,沿这条链路排查。
- 样式问题:确认使用的是 token 语义类还是硬编码值,优先检查 `design-tokens/`。

## 最小改动

- 只修目标 bug,不做无关重构或样式重写。
- 保持现有命名、组件写法、数据获取模式,与相邻代码一致。

## 收尾

- 为修复补一条回归测试(前端组件/hook 测试)。
```

- [ ] **Step 8: 提交**

```bash
git add docs/conventions/frontend/
git commit -m "docs(conventions): 添加前端规范原子片段"
```

---

### Task 2: 创建后端规范片段

**Files:**
- Create: `docs/conventions/backend/layering.md`
- Create: `docs/conventions/backend/models.md`
- Create: `docs/conventions/backend/schemas.md`
- Create: `docs/conventions/backend/dependency-injection.md`
- Create: `docs/conventions/backend/errors.md`
- Create: `docs/conventions/backend/testing.md`
- Create: `docs/conventions/backend/security.md`
- Create: `docs/conventions/backend/debugging.md`

- [ ] **Step 1: 创建 `layering.md`**

```markdown
# 后端分层规范

## 铁律

- 路由函数体只做:参数解析 + 调 domain 函数 + `model_validate` 包装返回。
- 业务规则(状态机、权限、校验)必须写在 `domain/<域>/`。

```python
@router.get("/{order_no}", response_model=OrderOut)
def get_order_detail(order_no: str, db: Session = Depends(get_db)):
    order = domain_get_order(db, order_no)
    return OrderOut.model_validate(order)
```

  参考:`backend/app/api/admin/orders.py`(薄路由)、`backend/app/domain/orders/__init__.py`(状态机)

## 禁止

- ❌ 在路由文件里写业务逻辑(状态流转、权限判断、校验)。
- ❌ 在路由里直接读写 DB(应走 domain 或 repo)。
```

- [ ] **Step 2: 创建 `models.md`**

```markdown
# 后端数据模型规范

## SQLAlchemy 2.0 风格

- 使用类型注解写法:`Mapped[...]` + `mapped_column(...)`。
- 时间统一 `DateTime(timezone=True)`。
- 持久化默认值用 `server_default`(布尔用 `"1"`/`"0"`,不写在 Python 逻辑里翻转)。

```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    is_active: Mapped[bool] = mapped_column(server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

  参考:`backend/app/models/user.py`、`backend/app/models/buyer_memory.py`

## 其他

- 新模型必须加入 `backend/app/models/__init__.py`(保证 `create_all` 元数据完整)。
- 表结构变更遵循 `db/migrate.py` 的幂等 SQL 迁移方式,不使用 alembic。
```

- [ ] **Step 3: 创建 `schemas.md`**

```markdown
# 后端 Pydantic schema 规范

## 位置

- 请求/响应 schema 统一放 `domain/<域>/schemas.py`,禁止在路由文件内联定义。

```python
class OrderOut(BaseModel):
    model_config = {"from_attributes": True}
    order_no: str
    amount: str
    status: str
```

  参考:`backend/app/domain/orders/schemas.py`

## 禁止

- ❌ 在 `app/api/...` 路由文件里写 `class XxxIn(BaseModel)`(反例:历史 `api/web/ai.py`)。
```

- [ ] **Step 4: 创建 `dependency-injection.md`**

```markdown
# 后端依赖注入规范

## 形状

- 数据库:`db: Session = Depends(get_db)`,浅注入。
- 认证:嵌套依赖 `get_current_user`,路由通过 `Depends(get_current_user)` 引入。
  - 仅需"已登录"但不需要用户对象的参数,命名用 `_` 前缀(`_current_user`)。

```python
@router.get("/{order_no}")
def get_order(order_no: str, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    ...
```

  参考:`backend/app/db/deps.py`、`backend/app/domain/auth/deps.py`、`backend/app/api/admin/users.py`

## 禁止

- ❌ 路由里直接 new Session / 手动 close(统一走 `get_db`。
```

- [ ] **Step 5: 创建 `errors.md`**

```markdown
# 后端错误与状态码规范

- 统一抛出 `HTTPException(status_code=..., detail="中文消息")`,不加响应外壳(envelope)。
- 状态码语义:
  - `400` 业务非法(状态流转不允许、自禁用等)
  - `401` 未登录 / 凭证无效
  - `403` 账号禁用
  - `404` 资源不存在
  - `409` 唯一性冲突(如邮箱重复)
  - `422` Pydantic 校验失败
- 认证失败文案约定:"未登录"、"无效的认证凭证"、"用户不存在"。

  参考:`backend/app/domain/auth/__init__.py`、`backend/app/domain/orders/__init__.py`
```

- [ ] **Step 6: 创建 `testing.md`**

```markdown
# 后端测试规范

## 框架

- pytest + FastAPI `TestClient`(黑盒 API 测试)+ domain 单测。

## 结构约定

- `tests/conftest.py` 在导入任何 app 模块前设置 `DATABASE_URL` 为临时 sqlite(避免污染开发库)。
- 每个 API 测试文件:`Base.metadata.create_all(bind=engine)` + `client = TestClient(app)` + `@pytest.fixture(autouse=True)` 的 `_clean_db` 清空所有表。
- 断言 `response.status_code` + `response.json()`;覆盖非法输入 422、不存在 404、非法流转 400。

  参考:`backend/tests/test_order_api.py`、`backend/tests/conftest.py`

## 禁止

- ❌ mock 数据库(统一用真实 sqlite + 每次清表)。
- 运行:`cd backend && uv run pytest`
```

- [ ] **Step 7: 创建 `security.md`**

```markdown
# 后端认证与安全规范

- 认证方案:JWT(HS256)+ HttpOnly cookie(token,24h)。
- 加解密/bcrypt/JWT 逻辑全部集中在 `core/security.py`。
- 路由/domain 不得直接碰 jwt / passlib / bcrypt,统一调用 `core/security.py` 提供的函数。

  参考:`backend/app/core/security.py`、`backend/app/api/web/auth.py`
```

- [ ] **Step 8: 创建 `debugging.md`**

```markdown
# 后端修 bug 指引

## 定位

- 按分层排查:路由(`api/`)薄 → `domain/<域>/` 业务规则 → `models/` / repo。
- 先用测试复现:在 `backend/tests/` 加复现用例(黑盒 API 或 domain 单测),确认红后再修。

## 最小改动

- 只修目标 bug,保持分层(不把逻辑下沉进路由)。
- 修完补回归测试并跑 `uv run pytest`。
```

- [ ] **Step 9: 提交**

```bash
git add docs/conventions/backend/
git commit -m "docs(conventions): 添加后端规范原子片段"
```

---

### Task 3: 创建 4 个 opencode 命令

**Files:**
- Create: `.opencode/commands/fe-dev.md`
- Create: `.opencode/commands/fe-bugfix.md`
- Create: `.opencode/commands/be-dev.md`
- Create: `.opencode/commands/be-bugfix.md`

- [ ] **Step 1: 创建 `fe-dev.md`**

```markdown
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

- [ ] **Step 2: 创建 `fe-bugfix.md`**

```markdown
---
description: 定位并修复前端 bug,遵循项目修 bug 规范
---

修复以下前端问题: $ARGUMENTS

请遵循以下规范切片:

@docs/conventions/frontend/debugging.md
@docs/conventions/frontend/testing.md
```

- [ ] **Step 3: 创建 `be-dev.md`**

```markdown
---
description: 按后端开发规范完成后端接口/领域开发
---

按本项目后端规范完成任务: $ARGUMENTS

请严格遵循以下规范切片:

@docs/conventions/backend/layering.md
@docs/conventions/backend/models.md
@docs/conventions/backend/schemas.md
@docs/conventions/backend/dependency-injection.md
@docs/conventions/backend/errors.md
@docs/conventions/backend/testing.md
@docs/conventions/backend/security.md
```

- [ ] **Step 4: 创建 `be-bugfix.md`**

```markdown
---
description: 定位并修复后端 bug,遵循项目修 bug 规范
---

修复以下后端问题: $ARGUMENTS

请遵循以下规范切片:

@docs/conventions/backend/debugging.md
@docs/conventions/backend/testing.md
```

- [ ] **Step 5: 提交**

```bash
git add .opencode/commands/
git commit -m "feat(commands): 添加按场景加载规范的斜杠命令"
```

---

### Task 4: 精简 AGENTS.md 为骨架

**Files:**
- Modify: `AGENTS.md`(整文件替换)

- [ ] **Step 1: 替换 AGENTS.md 全文**

```
# AGENTS.md 指令

## 文档语言

本项目产出的文档必须使用中文,包括 OpenSpec 产物、Superpowers specs/plans、README、开发说明、设计文档、实施计划和验证报告。只有代码标识符、命令、文件路径、配置键、第三方专有名词或引用原文需要保留英文时,才使用英文。

## 开发规范

按场景加载对应规范,避免规范常驻上下文浪费 token:

- /fe-dev 前端开发任务 · /fe-bugfix 前端修 bug
- /be-dev 后端开发任务 · /be-bugfix 后端修 bug
```

- [ ] **Step 2: 提交**

```bash
git add AGENTS.md
git commit -m "docs(agents): 精简 AGENTS.md 为骨架,规范改为按场景命令加载"
```

---

### Task 5: 验证命令可用

- [ ] **Step 1: 在 opencode 中手动验证 4 个命令**

在 opencode 中分别执行 `/fe-dev`、`/fe-bugfix`、`/be-dev`、`/be-bugfix`,确认:
- prompt 中出现对应 `@docs/conventions/...` 片段全文;
- `/fe-bugfix` 与 `/be-bugfix` 明显轻(只 2 个片段);
- AGENTS.md 中无残留大段规范正文。

- [ ] **Step 2: 验证指定 `@` 路径解析正确**

确认命令引用的路径与 `docs/conventions/` 实际文件完全一致(大小写、位置),若 opencode 无法解析会提示文件不存在。

---

## 自检

- **Spec 覆盖**:设计文档各片段内容大纲 → Task 1(前端 6 片段,已删 sse-streaming)/ Task 2(后端 8 片段,已删 migration);命令映射 → Task 3;AGENTS.md 骨架 → Task 4;验证 → Task 5。全量覆盖。
- **无占位符**:每个片段/命令文件都含完整 final 内容,无 TBD。
- **类型一致**:命令引用的片段文件名与 Task 1 / Task 2 创建的文件名完全一致。