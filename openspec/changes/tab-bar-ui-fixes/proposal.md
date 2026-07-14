## Why

Web 端底部 Tab 栏背景色半透明，选中 Tab 高亮不够明显，需要改善视觉效果。

## What Changes

- Tab 栏背景色改为不透明白色（bg-white）
- 选中 Tab 增加背景色高亮（bg-primary/10），不仅靠文字颜色区分

## Impact

- `apps/web/app/components/bottom-tab-bar.tsx`
