# 意图识别与规范路由

本文档定义 AI 如何根据用户输入自动识别场景并加载对应规范。

---

## 一、场景识别规则

### 1. Bug 修复场景

**触发关键词**：bug、坏了、不显示、报错、异常、失效、无法、不能、错误、问题

**判断条件**：
- 用户描述现有功能出现问题
- 不涉及新能力、新架构
- 改动范围可预估

**路由结果**：

| 目标模块 | 场景 | 规范切片 |
|---------|------|---------|
| 前端 | `/fe-bugfix` | `debugging.md` + `testing.md` |
| 后端 | `/be-bugfix` | `debugging.md` + `testing.md` |
| 不确定 | 询问用户 | — |

---

### 2. 小改动场景（Tweak）

**触发关键词**：小改动、调整、改文案、修改配置、优化 prompt、更新说明

**判断条件**：
- 不新增 capability
- 不改变架构
- 不涉及接口变化
- 通常 ≤ 3 个 tasks

**路由结果**：`/comet-tweak`

---

### 3. 新功能开发场景

**触发关键词**：新功能、实现、开发、添加、新建、创建、设计

**判断条件**：
- 需要新增 capability
- 或涉及架构/接口变更
- 或改动范围超出 hotfix/tweak

**路由结果**：

| 目标模块 | 场景 |
|---------|------|
| 前端 | 加载「前端核心规范」 |
| 后端 | 加载「后端核心规范」 |
| 跨域/大型 | `/comet` 完整五阶段流程 |
| 不确定 | 询问用户 |

---

## 二、技术栈判断

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

## 三、规范加载协议

### 核心规范（每次场景必加载）

| 场景 | 规范 |
|------|------|
| **前端（统一）** | `data-fetching.md` + `api-client.md` + `components.md` + `styling.md`<br>`+ error-loading-form.md` + `debugging.md` |
| **后端（统一）** | `layering.md` + `models.md` + `schemas.md` + `errors.md`<br>`+ security.md` + `debugging.md` |
| **跨域开发** | **前端核心 + 后端核心全部加载** |

### 条件规范（按任务类型追加）

| 任务类型 | 追加规范 |
|---------|---------|
| 新建页面/组件/路由 | `directory-structure.md` |
| 新建 API 接口 | `api-responses.md` |
| 涉及依赖注入 | `dependency-injection.md` |
| 需要写测试 | `testing.md` |

### 跨领域规范（按需引用）

| 规范 | 使用时机 |
|------|---------|
| `code-review.md` | PR/合并前 review 时 |
| `commit-convention.md` | 执行 commit 时 |
| `monorepo-versions.md` | 发布包时 |

---

## 四、用户交互原则

### ❌ 不要问的问题

- 「你想用哪个命令？」
- 「需要加载哪些规范？」
- 「这是前端还是后端？」（除非真的无法判断）
- 「要我创建 /comet 还是直接用自然语言？」
- 「这个需求涉及前后端吗？」（看到关键词就自动合并，不需要问）

### ✅ 应该做的事

1. **自动识别**：根据用户描述判断场景
2. **加载规范**：按上述规则加载对应规范切片
3. **执行开发**：在规范约束下完成工作
4. **告知进度**：完成时说明已遵守的规范

### 示例对话

```
用户：登录页的验证码输入框不显示

AI：[检测到前端 Bug 修复场景]
    [加载规范：debugging.md, testing.md]
    开始排查...
```

```
用户：帮我在订单列表页加一个导出 Excel 功能

AI：[检测到前端开发场景]
    [加载规范：data-fetching.md, api-client.md, 
              components.md, styling.md, 
              error-loading-form.md, directory-structure.md]
    开始实现...
```

```
用户：给订单列表加导出功能

AI：[检测到跨域开发场景 — 前端加按钮 + 后端出接口]
    [加载规范：
      前端核心：data-fetching.md, api-client.md, components.md, 
                styling.md, error-loading-form.md, directory-structure.md
      后端核心：layering.md, models.md, schemas.md, errors.md, security.md, api-responses.md
     ]
    开始实现...
```

---

## 五、Comet 工作流集成

当用户使用 `/comet` 相关命令时，遵循 `.codex/skills/comet/` 中的定义：

| 命令 | 触发条件 | 行为 |
|------|---------|------|
| `/comet` | 无描述或有大段需求 | 自动检测阶段，分发到子命令 |
| `/comet-hotfix` | 明确是 bug 修复 | 快速五阶段流程 |
| `/comet-tweak` | 小改动 | 精简流程 |

**注意**：即使用户使用了 `/comet` 命令，也要根据描述内容加载对应的技术规范切片。
