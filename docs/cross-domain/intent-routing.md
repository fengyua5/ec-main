# 意图识别与规范路由

本文档定义 AI 如何根据用户输入自动识别场景并加载对应规范。

---

## 场景分类与规范加载

### 场景 1：Tweak（小改动）

**触发条件**：
- 只修改已有内容，不新增功能/接口
- 例如：改文案、改样式、改配置、改文档

**判断关键词**：改文案、调整、优化 prompt、更新说明、修改配置

**流程**：`/comet-tweak`

**规范加载规则**：**只加载与任务最相关的 1-2 个规范**

| 任务类型 | 加载规范 | 理由 |
|---------|---------|------|
| 改文案/文字 | `@docs/conventions/frontend/components.md` 或 `@docs/conventions/backend/layering.md` | 了解组件/接口结构 |
| 改样式 | `@docs/conventions/frontend/styling.md` | 确保使用 design token |
| 改配置 | 不需要规范 | 纯配置修改 |
| 不明确 | 先问用户需要改什么 | — |

**示例**：
```
用户：把注册弹窗的文案改成新的
AI：[检测到 Tweak 场景]
    [加载规范：components.md（了解弹窗结构）]
    开始修改...

用户：首页按钮颜色不对
AI：[检测到 Tweak 场景]
    [加载规范：styling.md（确保用 token 改色）]
    开始修改...
```

---

### 场景 2：Bug 修复

**触发条件**：
- 已有功能出现问题
- 不涉及新功能
- 改动范围可预估

**判断关键词**：bug、坏了、不显示、报错、异常、失效

**流程**：
- 明确小范围（≤2 文件）→ `/comet-hotfix`
- 不确定范围 → `/fe-dev` 或 `/be-dev`（统一入口）

**规范加载规则**：**加载全部核心规范**

| 目标模块 | 加载规范 |
|---------|---------|
| 前端 | 6 个核心规范全部加载 |
| 后端 | 6 个核心规范全部加载 |
| 跨域 | 前后端核心规范全部加载 |

> **为什么 bugfix 也要加载全部核心规范？**
> - `data-fetching.md` — 理解现有数据获取模式，避免引入错误写法
> - `api-client.md` — 调用方式不变，bug 可能在调用侧
> - `components.md` — 组件写法不变，保持一致性
> - `styling.md` — 样式规范不变
> - `error-loading-form.md` — 状态处理模式不变
> - `debugging.md` — 修复方法和验证

---

### 场景 3：新功能开发

**触发条件**：
- 需要新增 capability
- 或涉及架构/接口变更
- 或改动范围超出 hotfix/tweak

**判断关键词**：新功能、实现、开发、添加、新建、创建

**流程**：`/comet`（完整五阶段）或 `/fe-dev` / `/be-dev`

**规范加载规则**：**加载全部核心规范 + 条件规范**

| 目标模块 | 核心规范 | 条件规范（按任务追加） |
|---------|---------|---------------------|
| 前端 | 6 个核心 | directory-structure（新建）、testing（写测试） |
| 后端 | 6 个核心 | api-responses（新建接口）、dependency-injection（DI）、testing（写测试） |
| 跨域 | 前后端核心 | 两侧条件规范合并 |

---

## 三、技术栈判断

### 前端关键词

```
页面、组件、样式、交互、路由、状态、hook、表单、列表、弹窗、按钮、布局、
Next.js、React、Tailwind、shadcn、设计 token、SDK、api-client、loadXxx
```

### 后端关键词

```
API、接口、路由函数、数据库、模型、schema、domain、Pydantic、SQLAlchemy、
JWT、认证、权限、MCP、FastAPI、session、事务
```

### 模糊情况处理

当前端和后端关键词同时出现时，判定为跨域开发：
- 不询问，直接合并加载两侧核心规范
- 条件规范按实际子任务追加

跨域常见模式：
```
用户描述示例：
  - 「给订单列表加导出按钮」（前端加按钮 + 后端出接口）
  - 「实现 AI 客服功能」（前端聊天 UI + 后端 MCP 接口）
  - 「搭建用户积分系统」（前端展示 + 后端计算 + 数据库）
```

---

## 四、规范加载规则汇总

### 核心规范（每次 dev/bugfix 必加载）

**前端核心（6 个）**：
```
data-fetching.md       — 数据获取模式
api-client.md          — API 调用规范
components.md          — 组件写法
styling.md             — 样式规范
error-loading-form.md  — 状态处理
debugging.md           — 调试方法
```

**后端核心（6 个）**：
```
layering.md            — 分层规范
models.md              — 数据模型
schemas.md             — Pydantic schema
errors.md              — 错误处理
security.md            — 安全规范
debugging.md           — 调试方法
```

### 条件规范（按任务类型追加）

| 任务类型 | 追加规范 |
|---------|---------|
| 新建页面/组件/路由 | `directory-structure.md` |
| 新建 API 接口 | `api-responses.md` |
| 涉及依赖注入 | `dependency-injection.md` |
| 需要写测试 | `testing.md` |

### Tweak 规范（小改动按需加载）

| 任务类型 | 加载规范 |
|---------|---------|
| 改文案 | `components.md`（前端）或 `layering.md`（后端） |
| 改样式 | `styling.md` |
| 改配置 | 不加载 |

---

## 五、跨领域规范（按需引用）

| 规范 | 使用时机 |
|------|---------|
| `code-review.md` | PR/合并前 review 时 |
| `commit-convention.md` | 执行 commit 时 |
| `monorepo-versions.md` | 发布包时 |

---

## 六、用户交互原则

### ❌ 不要问的问题

- 「你想用哪个命令？」
- 「需要加载哪些规范？」
- 「这是前端还是后端？」（除非真的无法判断）
- 「要我创建 /comet 还是直接用自然语言？」
- 「这个需求涉及前后端吗？」（看到关键词就自动合并，不需要问）

### ✅ 应该做的事

1. **自动识别**：根据用户描述判断场景（Tweak / Bugfix / Dev）
2. **按需加载**：
   - Tweak → 只加载 1-2 个相关规范
   - Bugfix → 加载全部核心规范
   - Dev → 加载全部核心 + 条件规范
3. **执行开发**：在规范约束下完成工作
4. **告知进度**：完成时说明已遵守的规范

---

## 七、示例对话

```
用户：登录页的验证码输入框不显示

AI：[检测到 Bug 修复场景]
    [加载规范：前端核心 6 个全部]
    开始排查...
```

```
用户：把注册弹窗的文案改成新的

AI：[检测到 Tweak 场景]
    [加载规范：components.md（了解弹窗结构）]
    开始修改...
```

```
用户：给订单列表加导出功能

AI：[检测到跨域开发场景]
    [加载规范：
      前端核心 6 个 + directory-structure.md
      后端核心 6 个 + api-responses.md
     ]
    开始实现...
```

```
用户：实现 AI 客服功能

AI：[检测到跨域开发场景]
    [加载规范：
      前端核心 6 个 + components.md（新建聊天组件）
      后端核心 6 个 + api-responses.md + dependency-injection.md
     ]
    开始实现...
```
