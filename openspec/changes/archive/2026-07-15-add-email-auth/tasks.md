## 1. 后端认证基础设施

- [x] 1.1 安装 Python 依赖（python-jose、passlib、bcrypt）
- [x] 1.2 创建 User SQLAlchemy 模型
- [x] 1.3 创建密码哈希工具函数
- [x] 1.4 创建 JWT 工具函数（签发、验证、cookie 设置）

## 2. 后端 Auth API

- [x] 2.1 实现 POST /api/v1/web/auth/register 和 /api/v1/admin/auth/register 注册端点
- [x] 2.2 实现 POST /api/v1/web/auth/login 和 /api/v1/admin/auth/login 登录端点
- [x] 2.3 实现 POST /api/v1/web/auth/logout 和 /api/v1/admin/auth/logout 登出端点
- [x] 2.4 实现 GET /api/v1/web/auth/me 和 /api/v1/admin/auth/me 当前用户端点
- [x] 2.5 实现认证依赖注入（获取当前用户）

## 3. SDK Auth 方法

- [x] 3.1 SDK 新增 auth 方法（register、login、logout、getMe）
- [x] 3.2 SDK 导出 auth 类型和函数

## 4. 前端登录注册页面

- [x] 4.1 Web 端注册页面
- [x] 4.2 Web 端登录页面
- [x] 4.3 Admin 端注册页面
- [x] 4.4 Admin 端登录页面
- [x] 4.5 Web/Admin 端登录状态管理（token 处理、受保护路由）

## 5. 验证

- [x] 5.1 后端 auth API 测试通过
- [x] 5.2 前端登录注册流程端到端验证（手动验证）

## 6. shadcn/ui 前端组件迁移

- [x] 6.1 Admin + Web 初始化 shadcn/ui（button、card、input、label、avatar、dropdown-menu、separator）
- [x] 6.2 替换所有 `@ec/ui` Button 引用为本地 shadcn Button
- [x] 6.3 清理 `@ec/ui` 依赖和 `next.config.ts` 引用

## 7. Admin 认证拦截

- [x] 7.1 创建 API 代理路由（/api/auth/login、/api/auth/register、/api/auth/logout、/api/auth/me）
- [x] 7.2 创建 proxy.ts（Next.js 16 proxy），未登录重定向到 /login
- [x] 7.3 Admin 登录/注册页改用本地 API 代理路由（使 httpOnly cookie 作用域一致）
- [x] 7.4 Admin AuthHeader 改用 /api/auth/me 获取用户、/api/auth/logout 登出

## 8. Admin 路由结构

- [x] 8.1 创建 (main)/ 和 (auth)/ 路由群组分离公共页面和受保护页面
- [x] 8.2 (main)/layout 含 Header + Sidebar，(auth)/layout 纯净布局
- [x] 8.3 Sidebar 使用 shadcn 语义色和 Separator
- [x] 8.4 登录/注册页面表单使用 Card 包裹

## 9. 前端测试（vitest）

- [x] 9.1 Admin 安装 vitest + @testing-library/react + jsdom，配置 vitest.config.ts
- [x] 9.2 Admin proxy.ts 测试：未认证重定向、公开路由放行、已认证通过
- [x] 9.3 Admin API 代理路由测试：转发请求和响应、传递 cookie 到后端
- [x] 9.4 Admin AuthHeader 组件渲染测试：未登录显示登录/注册链接，已登录显示用户信息
- [x] 9.5 Admin Sidebar 组件渲染测试
