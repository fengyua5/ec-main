import os
import tempfile

# 在导入任何 app 模块前，将测试数据库指向独立的临时文件，
# 避免测试套件（含 _clean_db 清表）污染开发用的 backend/.data/ec-main.sqlite3。
_DATA_DIR = tempfile.mkdtemp(prefix="ec-test-data-")
os.environ["DATABASE_URL"] = f"sqlite:///{_DATA_DIR}/test.sqlite3"
