# 前端样式规范

## 只使用 Tailwind v4 utility + design token

- 样式一律用 Tailwind utility 类,禁用内联 `style` 定义布局样式。
- 颜色/间距等静态值必须走 design token 语义类,不直接写十六进制/oklch 色值。

## 三层 design token 体系(app/design-tokens/)

1. `tokens.css`:根色板 `@theme`,唯一事实来源。
2. `semantic.css`:`@theme inline` 桥接层,把 `--font-size-*` 等桥到 Tailwind。
3. `enki.css`:`@layer components` 的 `.enki-*` 组合类(如 `enki-body-sm`)。

## 新颜色/品牌规范

- 需要新色值 → 在 `tokens.css` 加根 token,再在语义层映射,禁止在组件里硬编码色值。
- 参考 `apps/web/app/design-tokens/*.css`、`packages/config` 中两端的 token 约定。