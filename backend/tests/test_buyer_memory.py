import pytest
from app.domain.ai.memory.memory_repo import get_by_buyer, upsert, list_all
from app.models.user import Base
from app.db.session import engine, SessionLocal

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


def test_get_by_buyer_returns_none_when_missing() -> None:
    db = SessionLocal()
    try:
        result = get_by_buyer(db, buyer_id=999)
        assert result is None
    finally:
        db.close()


def test_upsert_creates_new() -> None:
    db = SessionLocal()
    try:
        result = upsert(db, buyer_id=1, content="【称呼/身份】李女士", expected_version=0)
        assert result is True
        mem = get_by_buyer(db, buyer_id=1)
        assert mem is not None
        assert mem.content == "【称呼/身份】李女士"
        assert mem.version == 1
    finally:
        db.close()


def test_upsert_updates_same_version() -> None:
    db = SessionLocal()
    try:
        upsert(db, buyer_id=2, content="v1", expected_version=0)
        result = upsert(db, buyer_id=2, content="v2", expected_version=1)
        assert result is True
        mem = get_by_buyer(db, buyer_id=2)
        assert mem.content == "v2"
        assert mem.version == 2
    finally:
        db.close()


def test_upsert_rejects_stale_version() -> None:
    db = SessionLocal()
    try:
        upsert(db, buyer_id=3, content="v1", expected_version=0)
        result = upsert(db, buyer_id=3, content="v2", expected_version=0)
        assert result is False
        mem = get_by_buyer(db, buyer_id=3)
        assert mem.content == "v1"
        assert mem.version == 1
    finally:
        db.close()


def test_list_all_returns_all() -> None:
    db = SessionLocal()
    try:
        upsert(db, buyer_id=10, content="a", expected_version=0)
        upsert(db, buyer_id=11, content="b", expected_version=0)
        items = list_all(db)
        assert len(items) == 2
    finally:
        db.close()
