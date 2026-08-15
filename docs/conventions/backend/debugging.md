# 后端修 bug 指引

## 定位

- 按分层排查:路由(`api/`)薄 → `domain/<域>/` 业务规则 → `models/` 数据定义。
- 先用测试复现:在 `backend/tests/` 加复现用例(黑盒 API 或 domain 单测),确认红后再修。

## 最小改动

- 只修目标 bug,保持分层(不把逻辑下沉进路由)。
- 修完补回归测试并跑 `uv run pytest`。