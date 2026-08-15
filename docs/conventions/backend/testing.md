# 后端测试规范

## 框架

- pytest + FastAPI `TestClient`(黑盒 API 测试)+ domain 单测。

## 结构约定

- `tests/conftest.py` 在导入任何 app 模块前设置 `DATABASE_URL` 为临时 sqlite(避免污染开发库)。
- 每个 API 测试文件:`Base.metadata.create_all(bind=engine)` + `client = TestClient(app)` + `@pytest.fixture(autouse=True)` 的 `_clean_db` 清空所有表。
- 断言 `response.status_code` + `response.json()`;覆盖非法输入 422、不存在 404、非法流转 400。

  参考:`backend/tests/test_order_api.py`、`backend/tests/conftest.py`

## 禁止

- ❌ mock 数据库(统一用真实 sqlite + 每次清表)。
- 运行:`cd backend && uv run pytest`
