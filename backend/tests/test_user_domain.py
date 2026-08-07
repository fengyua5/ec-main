import pytest
from fastapi import HTTPException
from app.models.user import Base, User
from app.db.session import engine, SessionLocal
from app.domain.users import list_users, get_user, set_user_active

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


def _add_user(email: str, role: str = "buyer", username: str | None = None, is_active: bool = True) -> User:
    db = SessionLocal()
    user = User(email=email, username=username, password_hash="hash", role=role, is_active=is_active)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


def test_list_users_pagination() -> None:
    for i in range(5):
        _add_user(f"user{i}@example.com")

    db = SessionLocal()
    users, total = list_users(db, page=1, page_size=2)
    db.close()

    assert total == 5
    assert len(users) == 2


def test_list_users_keyword_email() -> None:
    _add_user("alice@example.com")
    _add_user("bob@example.com")

    db = SessionLocal()
    users, total = list_users(db, keyword="alice")
    db.close()

    assert total == 1
    assert users[0].email == "alice@example.com"


def test_list_users_keyword_username() -> None:
    _add_user("c1@example.com", username="zhangsan")
    _add_user("c2@example.com", username="lisi")

    db = SessionLocal()
    users, total = list_users(db, keyword="zhang")
    db.close()

    assert total == 1
    assert users[0].username == "zhangsan"


def test_list_users_status_filter() -> None:
    _add_user("active@example.com", is_active=True)
    _add_user("inactive@example.com", is_active=False)

    db = SessionLocal()
    active, active_total = list_users(db, status_filter="active")
    inactive, inactive_total = list_users(db, status_filter="inactive")
    db.close()

    assert active_total == 1
    assert active[0].email == "active@example.com"
    assert inactive_total == 1
    assert inactive[0].email == "inactive@example.com"


def test_get_user_not_found() -> None:
    db = SessionLocal()
    with pytest.raises(HTTPException) as exc:
        get_user(db, 999)
    db.close()
    assert exc.value.status_code == 404


def test_set_user_active_toggle() -> None:
    target = _add_user("toggle@example.com")
    actor = _add_user("admin@example.com", role="admin")

    db = SessionLocal()
    user = set_user_active(db, target.id, False, actor=actor)
    assert user.is_active is False

    user = set_user_active(db, target.id, True, actor=actor)
    assert user.is_active is True
    db.close()


def test_set_user_active_prevents_disabling_self() -> None:
    actor = _add_user("selfadmin@example.com", role="admin")

    db = SessionLocal()
    with pytest.raises(HTTPException) as exc:
        set_user_active(db, actor.id, False, actor=actor)
    db.close()
    assert exc.value.status_code == 400
