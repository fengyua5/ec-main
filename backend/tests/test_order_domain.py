import pytest
from fastapi import HTTPException
from app.domain.orders import (
    ORDER_STATUSES,
    get_next_statuses,
    validate_transition,
)


def test_order_statuses_contains_six_states() -> None:
    assert ORDER_STATUSES == [
        "pending_payment",
        "pending_delivery",
        "in_delivery",
        "delivered",
        "cancelled",
        "refunded",
    ]


def test_next_statuses_pending_payment() -> None:
    assert get_next_statuses("pending_payment") == ["pending_delivery", "cancelled"]


def test_next_statuses_pending_delivery() -> None:
    assert get_next_statuses("pending_delivery") == ["in_delivery", "cancelled", "refunded"]


def test_next_statuses_in_delivery() -> None:
    assert get_next_statuses("in_delivery") == []


def test_terminal_states_have_no_next() -> None:
    for state in ["delivered", "cancelled", "refunded"]:
        assert get_next_statuses(state) == []


def test_validate_transition_allows_legal() -> None:
    validate_transition("pending_payment", "pending_delivery")
    validate_transition("pending_delivery", "in_delivery")


def test_validate_transition_rejects_in_delivery_move() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_transition("in_delivery", "delivered")
    assert exc.value.status_code == 400


def test_validate_transition_rejects_illegal() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_transition("pending_payment", "in_delivery")
    assert exc.value.status_code == 400


def test_validate_transition_rejects_terminal_move() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_transition("delivered", "pending_delivery")
    assert exc.value.status_code == 400


def test_validate_transition_rejects_unknown_target() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_transition("pending_payment", "not_a_status")
    assert exc.value.status_code == 400
