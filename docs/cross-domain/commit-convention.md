# 提交信息规范

## 格式

```
<type>(<scope>): <subject>

<body>（可选）

<footer>（可选）
```

---

## Type 列表

| type | 适用场景 |
|------|---------|
| `feat` | 新功能 |
| `fix` | bug 修复 |
| `refactor` | 重构（不改变行为） |
| `style` | 代码格式（不影响逻辑） |
| `docs` | 文档变更 |
| `test` | 测试相关 |
| `chore` | 构建、CI、依赖等 |
| `tweak` | 小改动（文案、配置） |
| `hotfix` | 紧急修复 |

---

## Scope 示例

| scope | 适用模块 |
|-------|---------|
| `web` | `apps/web` |
| `admin` | `apps/admin` |
| `backend` | `backend` |
| `sdk` | `packages/sdk` |
| `ui` | `packages/ui` |
| `auth` | 认证相关 |
| `order` | 订单相关 |
| `ai` | AI 相关功能 |

---

## 示例

```
feat(web): 添加首页 CMS 模块配置

- 新增 HomeModule 模型
- 添加管理后台配置页面
- 前端新增 CMS 编辑组件

Closes: #123
```

```
fix(backend): 修复订单状态流转权限校验

- 补充 admin 角色的权限检查
- 修复 domain/orders/__init__.py 中的边界情况

Refs: #456
```

```
tweak(web): 更新注册弹窗文案

- 修改 terms 协议文本
- 调整 CTA 按钮文案
```

---

## 禁止事项

- ❌ 不要只写 "fix bug" 或 "update" 等无意义描述
- ❌ 不要混用英文和中文（主体用中文，代码标识符除外）
- ❌ 不要在 commit message 中描述无关内容
