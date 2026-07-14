## Why

Web 端目前是桌面优先布局（顶部 Header + 宽屏居中内容），在移动端体验差。需要改为移动端友好的响应式布局，底部固定 Tab 导航替代顶部 Header，使买家在手机上能方便地在首页、AI 客服和账号之间切换。

## What Changes

- 修改 Web 端根布局为响应式设计（移动端底部 Tab，桌面端保留合理布局）
- 新增底部 Tab 导航组件，固定在页面底部
- 移除当前顶部 AuthHeader 组件
- 新增"AI 客服"占位页面（/ai）
- 新增"账号"页面（/account），展示用户信息和登录状态
- 登录/注册页面使用纯净布局（不显示底部 Tab），使用路由群组 `(auth)/` 隔离
- 支持 Tab 切换时保持页面状态

## Capabilities

### New Capabilities
- `mobile-layout`: Web 端响应式底部 Tab 导航布局，含 Tab 组件、路由结构、响应式断点

### Modified Capabilities

（无 — 不涉及已有 spec 的行为变更）

## Impact

- `apps/web/app/layout.tsx` — 修改根布局，移除 AuthHeader，添加底部 Tab
- `apps/web/app/components/` — 新建 `bottom-tab-bar.tsx`、`account-page.tsx`
- `apps/web/app/ai/` — 新建 AI 客服占位页面
- `apps/web/app/account/` — 新建账号页面
- `apps/web/app/login/`、`apps/web/app/register/` — 移至 `(auth)/` 路由群组
- `apps/web/app/components/auth-header.tsx` — 移除
