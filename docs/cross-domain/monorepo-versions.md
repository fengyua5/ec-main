# Monorepo 版本管理规范

## 包范围

| 包 | 发布时机 |
|----|---------|
| `packages/sdk` | API 接口变更、新增功能时 |
| `packages/ui` | 组件 API 变更、breaking change 时 |
| `packages/config` | 配置项变更时（通常不需发布） |

---

## 版本策略

采用 [SemVer](https://semver.org/) 语义化版本：

| 变更类型 | 版本号变化 | 示例 |
|---------|-----------|------|
| Breaking change | `major` | `1.0.0` → `2.0.0` |
| 新功能（向下兼容） | `minor` | `1.1.0` → `1.2.0` |
| Bug 修复 | `patch` | `1.2.3` → `1.2.4` |

---

## 发布流程

```bash
# 1. 修改 package.json 中的 version
# 2. 更新 CHANGELOG.md
# 3. 提交并打 tag
git tag -a v1.2.0 -m "release: sdk v1.2.0"
git push origin v1.2.0

# 4. 其他包升级依赖时，运行 pnpm update 并检查 lockfile
```

---

## 依赖升级规范

- 同一 workspace 内包之间用 `workspace:*` 引用
- 升级内部包时，同步更新引用方的 `package.json` 中的版本号
- 不要手动修改 `pnpm-lock.yaml`
