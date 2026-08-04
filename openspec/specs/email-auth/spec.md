# email-auth Specification

## Purpose
TBD - created by archiving change add-email-auth. Update Purpose after archive.
## Requirements
### Requirement: User can register with email and password

系统 MUST 允许新用户通过邮箱和密码注册账号。Web 端注册通过 `/api/v1/web/auth/register` 自动设为 buyer 角色，Admin 端注册通过 `/api/v1/admin/auth/register` 自动设为 admin 角色。

#### Scenario: Successful registration

- **WHEN** 用户提交有效的邮箱、密码和角色信息到注册接口
- **THEN** 系统创建新用户返回成功响应，密码以 bcrypt 哈希存储

#### Scenario: Duplicate email registration

- **WHEN** 用户使用已注册的邮箱再次提交注册
- **THEN** 系统返回 409 错误提示邮箱已被注册

#### Scenario: Invalid email format

- **WHEN** 用户提交格式不正确的邮箱地址
- **THEN** 系统返回 422 错误提示邮箱格式无效

### Requirement: User can login with email and password

系统 MUST 允许已注册用户通过邮箱和密码登录，登录成功后返回 JWT token。

#### Scenario: Successful login

- **WHEN** 已注册用户提交正确的邮箱和密码到登录接口
- **THEN** 系统返回 JWT token（设置在 httpOnly cookie 中）和用户基本信息

#### Scenario: Wrong password

- **WHEN** 已注册用户提交错误的密码
- **THEN** 系统返回 401 错误提示邮箱或密码不正确

#### Scenario: Non-existent email

- **WHEN** 用户提交未注册的邮箱地址
- **THEN** 系统返回 401 错误提示邮箱或密码不正确

### Requirement: User can view current session info

系统 MUST 允许已登录用户查看当前登录状态和用户信息。

#### Scenario: Authenticated user views profile

- **WHEN** 已登录用户请求当前用户信息接口
- **THEN** 系统返回用户 ID、邮箱、角色和注册时间

#### Scenario: Unauthenticated user views profile

- **WHEN** 未登录用户请求当前用户信息接口
- **THEN** 系统返回 401 未授权错误

### Requirement: User can logout

系统 MUST 允许已登录用户登出，清除登录状态。

#### Scenario: Successful logout

- **WHEN** 已登录用户请求登出接口
- **THEN** 系统清除登录 token，返回登出成功响应

### Requirement: Web端提供登录注册界面

系统 MUST 在买家端（apps/web）提供登录和注册页面。

#### Scenario: Web user can navigate to login

- **WHEN** 用户访问买家端并点击登录入口
- **THEN** 系统显示邮箱和密码输入框的登录表单

#### Scenario: Web user can register

- **WHEN** 用户访问买家端注册页面并提交注册信息
- **THEN** 注册成功后自动登录并跳转到首页

### Requirement: Admin端提供登录注册界面

系统 MUST 在 Admin 后台（apps/admin）提供登录和注册页面。

#### Scenario: Admin user can navigate to login

- **WHEN** 管理员访问 Admin 后台并点击登录入口
- **THEN** 系统显示邮箱和密码输入框的登录表单

#### Scenario: Admin user can register

- **WHEN** 管理员访问 Admin 注册页面并提交注册信息
- **THEN** 注册成功后自动登录并跳转到 Admin 首页

