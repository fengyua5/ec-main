## Context

底部 Tab 栏当前使用 `bg-background`（可能为透明/带透明度），选中状态仅靠 `text-primary` 文字颜色区分，视觉反馈不足。

## 改动

1. nav 背景色改为 `bg-white`，确保不透明白色
2. 选中 Tab 增加 `bg-primary/10` 浅色背景高亮，配合已有的 `text-primary` 文字颜色
3. Tab 圆角 `rounded-lg`，使高亮更自然
