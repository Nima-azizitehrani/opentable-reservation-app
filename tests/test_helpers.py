"""Pure-function tests for the validation/formatting helpers in app.py.
No database involved at all."""
import pytest

from app import dollars, parse_datetime_local, to_int, validate_phone


def test_to_int_accepts_plain_numbers():
    assert to_int("Party size", "4") == 4


def test_to_int_rejects_non_numbers():
    with pytest.raises(ValueError):
        to_int("Party size", "four")


def test_to_int_enforces_range():
    with pytest.raises(ValueError):
        to_int("Party size", "0", min_v=1, max_v=100)
    with pytest.raises(ValueError):
        to_int("Party size", "101", min_v=1, max_v=100)


def test_parse_datetime_local_from_html_input():
    assert parse_datetime_local("2026-11-01T19:30") == "2026-11-01 19:30:00"


def test_parse_datetime_local_requires_a_value():
    with pytest.raises(ValueError):
        parse_datetime_local("")


def test_validate_phone_accepts_10_to_15_digits():
    assert validate_phone("3125551234") == "3125551234"


def test_validate_phone_rejects_letters_and_short_numbers():
    with pytest.raises(ValueError):
        validate_phone("312-555-1234")
    with pytest.raises(ValueError):
        validate_phone("12345")


def test_dollars_price_levels():
    assert dollars(1) == "$"
    assert dollars(3) == "$$$"
    assert dollars(None) == "$"  # clamps to at least one
    assert dollars(9) == "$$$$"  # clamps to at most four
