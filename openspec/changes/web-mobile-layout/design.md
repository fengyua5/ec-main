## Context

Web 端（apps/web）当前使用桌面优先布局：顶部 AuthHeader（登录/注册/用户信息）+ 居中内容区。缺少移动端适配，没有底部导航 Tab。

本 change 将 Web 端改造为移动端友好的响应式布局，底部固定三个 Tab，移除顶部 AuthHeader。

## Goals / Non-Goals

**Goals:**
- Web 端新增响应式布局，移动端底部固定 Tab 栏
- 三个 Tab：首页（/）、AI 客服（/ai）、账号（/account）
- 移除 AuthHeader，导航由底部 Tab + 账号页面承载
- 登录/注册页面使用纯净布局（(auth) 路由群组）
- 账号页面显示用户信息和登录状态
- AI 客服为占位页面

**Non-Goals:**
- 不实现 AI 客服功能（仅占位）
- 不改变 Admin 端布局
- 不涉及后端 API 变更
- 不做 Desktop 专属布局（底部 Tab 在所有视口宽度展示）

## Decisions

### Decision: 底部 Tab 栏使用 shadcn + lucide-react 图标

底部 Tab 栏使用 shadcn Button 组件 + lucide-react 图标（Home、Bot、User）。
当前项目已安装这些依赖（shadcn init 时已引入 lucide-react）。

替代方案：
- 自建纯 CSS Tab 栏：可减少依赖，但与现有设计体系不一致
- 选择理由：复用现有 shadcn 组件体系，图标风格统一

### Decision: 路由结构 — 使用 (main) 和 (auth) 路由群组

参考 Admin 端的模式，Web 端也拆分为 (main) 和 (auth) 路由群组：
- `(main)/` — 首页、AI 客服、账号页面（含底部 Tab 栏）
- `(auth)/` — 登录、注册页面（纯净布局，无 Tab 栏）

替代方案：
- 条件渲染：在 layout 中用路径判断是否显示 Tab 栏
- 选择理由：路由群组更清晰，符合 Next.js 推荐模式

### Decision: 账号页用户信息获取

账号页面通过 `/api/auth/me` Next.js API 路由（注：这是 Admin 端的代理路由）或直接调用后端获取用户信息。

实际上是 **Web 端也需要创建类似的 API 代理路由**，或直接调用 SDK `getMe(client, "/web")`。

**选择**：由于 Web 端暂无 proxy.ts 拦截，账号页直接使用 SDK 调用后端 `/api/v1/web/auth/me`（当前 token cookie 作用域为后端域，但在浏览器中 SDK 请求使用 `credentials: "include"` 可携带 cookie）。

后续如需像 Admin 端一样添加认证拦截，可再补充 Web 端 proxy。

### Decision: 桌面端布局

底部 Tab 栏在桌面端（>=768px）同样展示，但内容区增加最大宽度限制，居中显示。

替代方案：
- 桌面端隐藏底部 Tab，保留顶部 Header
- 选择理由：统一体验，用户要求不保留顶部 Header

## Risks / Trade-offs

- [Risk] 底部 Tab 栏在桌面端可能浪费屏幕空间 → Mitigation：内容区保持最大宽度限制，Tab 栏在宽屏下不会显得过大
- [Risk] 登录/注册页无 Tab 栏，用户需自行通过 URL 返回主页 → Mitigation：表单内提供返回链接"已有账号/去注册"

## Migration Plan

1. 创建 (main) 和 (auth) 路由群组，移动现有页面
2. 新建底部 Tab 栏组件
3. 修改根布局，移除 AuthHeader，添加 Tab 栏
4. 新建 AI 客服占位页面
5. 新建账号页面
6. 验证端到端流程
