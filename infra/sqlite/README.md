# SQLite 本地开发约定

一期使用 SQLite 作为本地关系型数据库。默认数据库路径为 `backend/.data/ec-main.sqlite3`，可通过 `DATABASE_URL` 覆盖。

后续业务表必须通过迁移或可重复初始化机制演进，避免散落一次性 SQL 脚本。商品、用户、购物车、订单和 AI 客服上下文相关表应在各自 OpenSpec change 中定义。
