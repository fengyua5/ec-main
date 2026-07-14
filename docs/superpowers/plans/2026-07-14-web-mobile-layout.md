---
change: web-mobile-layout
design-doc: openspec/changes/web-mobile-layout/design.md
base-ref: 343b9f8c322c65467ae2e178f336e83a054e1b7b
archived-with: 2026-07-14-web-mobile-layout
---

# Web 端移动布局改造 — 实施计划

## 参考文档

- **Design Doc**: openspec/changes/web-mobile-layout/design.md
- **Spec**: openspec/changes/web-mobile-layout/specs/mobile-layout/spec.md
- **Tasks**: openspec/changes/web-mobile-layout/tasks.md

## 执行顺序（按依赖关系）

### Phase 1: 路由重构（Tasks 1）
1. 创建 `(main)/` 和 `(auth)/` 路由群组目录
2. 移动 `page.tsx` 到 `(main)/page.tsx`
3. 移动 `login/` 和 `register/` 到 `(auth)/` 下
4. 创建 `(auth)/layout.tsx`（纯净布局，无 Tab）
5. 简化根 `layout.tsx`

### Phase 2: 新建组件（Tasks 2, 4, 5）
1. 创建 `BottomTabBar` 组件（lucide-react 图标 + shadcn Button）
2. 创建 AI 客服占位页面 `(main)/ai/page.tsx`
3. 创建账号页面 `(main)/account/page.tsx`（登录/未登录双态）

### Phase 3: 布局整合（Tasks 3, 6）
1. 创建 `(main)/layout.tsx`（内容区 + BottomTabBar）
2. 移除 `AuthHeader` 文件与引用
3. 响应式宽度限制
4. 端到端验证

## 注意点

- 登录/注册页必须用 `(auth)` 群组，确保底部不显示 Tab
- 账号页用 SDK `getMe()` 获取用户信息（支持 credentials: "include"）
- 不要改动 Admin 端的代码
- 不要创建新的 shadcn 组件，复用已有 Button/Card/Input
