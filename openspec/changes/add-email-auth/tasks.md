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
- [ ] 5.2 前端登录注册流程端到端验证（手动验证）
