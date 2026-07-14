## 1. 路由重构

- [x] 1.1 创建 (main)/ 和 (auth)/ 路由群组目录结构
- [x] 1.2 移动现有页面到对应群组：/ → (main)/page，/login → (auth)/login/page，/register → (auth)/register/page
- [x] 1.3 创建 (auth)/layout.tsx（纯净布局，无底部 Tab 栏）
- [x] 1.4 更新根 layout.tsx（仅保留 html/body/globals.css）

## 2. 底部 Tab 栏组件

- [x] 2.1 创建 BottomTabBar 组件，固定在页面底部
- [x] 2.2 三个 Tab（首页 Home 图标、AI 客服 Bot 图标、账号 User 图标）使用 lucide-react
- [x] 2.3 Tab 路由跳转（next/navigation usePathname + Link）
- [x] 2.4 激活 Tab 高亮样式（当前路径匹配）

## 3. 布局整合

- [x] 3.1 创建 (main)/layout.tsx（包含 BottomTabBar）
- [x] 3.2 移除 AuthHeader 文件和引用
- [x] 3.3 响应式：内容区最大宽度限制，Tab 栏在不同视口宽度下表现一致

## 4. AI 客服占位页面

- [x] 4.1 创建 (main)/ai/page.tsx，显示\"AI 客服\"标题和\"即将上线\"提示

## 5. 账号页面

- [x] 5.1 创建 (main)/account/page.tsx，使用 SDK getMe 获取用户信息
- [x] 5.2 已登录状态：展示用户名/邮箱、角色、登出按钮
- [x] 5.3 未登录状态：展示登录入口和注册链接

## 6. 清理与验证

- [x] 6.1 验证三个 Tab 切换正常，路径和激活状态正确
- [x] 6.2 验证登录/注册页面无底部 Tab，布局正常
- [x] 6.3 验证账号页面登录/未登录状态正确
- [x] 6.4 TypeScript 编译检查通过
- [x] 6.5 旧 vitest 测试仍然通过
