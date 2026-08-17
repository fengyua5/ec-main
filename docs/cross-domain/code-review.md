# Code Review 规范

## 适用范围

所有 PR / 合并请求，无论大小。

---

## Review 优先级

| 优先级 | 类型 | 处理方式 |
|--------|------|---------|
| P0 | 安全漏洞、数据丢失风险 | 必须修复才能合并 |
| P1 | 违反项目规范（分层、api-client 等） | 必须修复才能合并 |
| P2 | 逻辑错误、边界情况遗漏 | 建议修复 |
| P3 | 代码风格、命名建议 | 可选 |

---

## 前端 Review 重点

### 规范合规性
- [ ] API 调用是否统一走 `@ec/sdk`，无裸 fetch
- [ ] 数据获取是否遵循 `data-fetching.md`（静态用 Server Component，交互用 `loadXxx` 模式）
- [ ] 样式是否走 Tailwind + design token，无硬编码色值
- [ ] 组件是否使用 `cva()` 声明 variants，无手写 clsx 拼接

### 质量检查
- [ ] 是否有未处理的 loading / error 状态
- [ ] 是否有内存泄漏风险（未清理的订阅、定时器）
- [ ] TypeScript 类型是否完整，无 `any` 滥用

---

## 后端 Review 重点

### 规范合规性
- [ ] 路由函数是否只做参数解析 + domain 调用 + `model_validate`
- [ ] 业务逻辑是否写在 `domain/<域>/` 中
- [ ] Pydantic schema 是否放在 `domain/<域>/schemas.py`
- [ ] 错误是否用 `HTTPException`，无裸 raise

### 质量检查
- [ ] 是否有 N+1 查询问题
- [ ] 事务边界是否清晰
- [ ] 权限校验是否到位

---

## Review 输出格式

```markdown
## 变更摘要
- 涉及文件：xxx
- 改动类型：feat / fix / refactor

## P0/P1 问题
1. ...

## P2 建议
1. ...

## P3 可选
1. ...
```

---

## 自动化工具辅助

- ESLint / Prettier：前端格式和规范检查
- ruff / mypy：后端类型和风格检查
- pytest：测试覆盖率检查

> **原则**：能由工具检查的，不要靠人工 review 发现。
