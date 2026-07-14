## ADDED Requirements

### Requirement: System SHALL provide responsive mobile-first layout with bottom tab navigation

Web 端 SHALL 提供响应式移动优先布局，页面底部固定显示三个 Tab：首页、AI 客服、账号。

#### Scenario: Mobile viewport shows bottom tab bar

- **WHEN** 用户使用移动设备（视口宽度 < 768px）访问 Web 端
- **THEN** 页面底部固定显示三个 Tab（首页、AI 客服、账号），Tab 图标+文字居中排列

#### Scenario: Desktop viewport adapts layout

- **WHEN** 用户使用桌面设备（视口宽度 >= 768px）访问 Web 端
- **THEN** 底部 Tab 栏依旧显示，内容区域最大宽度受限制，整体布局居中

### Requirement: System SHALL remove top AuthHeader

Web 端 SHALL 移除现有 AuthHeader 组件，导航功能由底部 Tab 和账号页面承载。

#### Scenario: No AuthHeader rendered

- **WHEN** 用户访问 Web 端任何页面
- **THEN** 顶部不显示登录/注册链接或用户信息栏

### Requirement: System SHALL provide bottom tab bar with three tabs

系统 SHALL 提供固定底部 Tab 栏，包含首页（/）、AI 客服（/ai）、账号（/account）三个入口。

#### Scenario: Tabs navigate to correct routes

- **WHEN** 用户点击首页 Tab
- **THEN** 页面跳转到 /
- **WHEN** 用户点击 AI 客服 Tab
- **THEN** 页面跳转到 /ai
- **WHEN** 用户点击账号 Tab
- **THEN** 页面跳转到 /account

#### Scenario: Active tab is highlighted

- **WHEN** 用户当前在某个 Tab 对应的页面
- **THEN** 该 Tab 呈激活状态（高亮样式）

### Requirement: System SHALL provide AI 客服 placeholder page

系统 SHALL 在 /ai 路径提供 AI 客服占位页面。

#### Scenario: AI page shows placeholder

- **WHEN** 用户访问 /ai
- **THEN** 页面显示"AI 客服"标题和"即将上线"提示文字

### Requirement: System SHALL provide 账号 page

系统 SHALL 在 /account 路径提供账号页面，展示用户信息和登录状态。

#### Scenario: Authenticated user sees profile

- **WHEN** 已登录用户访问 /account
- **THEN** 页面显示用户的用户名（或邮箱）、角色和登出按钮

#### Scenario: Unauthenticated user sees login prompt

- **WHEN** 未登录用户访问 /account
- **THEN** 页面显示登录入口和注册链接

### Requirement: Login/register pages SHALL use clean layout without bottom tab

登录和注册页面 SHALL 使用纯净布局（(auth) 路由群组），不显示底部 Tab 栏，居中展示表单。

#### Scenario: Login page renders without bottom tab

- **WHEN** 用户访问 /login
- **THEN** 页面不显示底部 Tab 栏，仅居中显示登录表单

#### Scenario: Register page renders without bottom tab

- **WHEN** 用户访问 /register
- **THEN** 页面不显示底部 Tab 栏，仅居中显示注册表单
