"""Structural tests for the SQL layer: the files exist, load in a known
order, and define the objects the application depends on (tables, the two
stored procedures, the rating function, and the business-rule triggers)."""
import re
from pathlib import Path

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"

EXPECTED_FILES = [
    "01_schema.sql",
    "02_load_data.sql",
    "03_indexes_views.sql",
    "04_temp_tables.sql",
    "05_triggers_procs_functions.sql",
    "06_complex_queries.sql",
]

EXPECTED_TABLES = ["Customer", "Restaurant", "DiningTable", "Reservation", "Review", "Favorite"]


def _read(name):
    return (SQL_DIR / name).read_text(encoding="utf-8", errors="ignore")


def _all_sql():
    return "\n".join(_read(name) for name in EXPECTED_FILES)


def test_sql_files_exist():
    for name in EXPECTED_FILES:
        assert (SQL_DIR / name).is_file(), f"missing {name}"


def test_schema_creates_all_tables():
    sql = _all_sql()
    for table in EXPECTED_TABLES:
        assert re.search(rf"CREATE\s+TABLE\s+{table}\b", sql, re.IGNORECASE), table


def test_stored_procedures_exist():
    sql = _all_sql()
    for proc in ("MakeReservation", "CancelReservation"):
        assert re.search(rf"CREATE\s+PROCEDURE\s+{proc}\b", sql, re.IGNORECASE), proc


def test_rating_function_exists():
    assert re.search(r"CREATE\s+FUNCTION\s+GetAvgRating\b", _all_sql(), re.IGNORECASE)


def test_double_booking_trigger_exists():
    """The core business rule: a table cannot be booked twice at the same time."""
    sql = _all_sql()
    triggers = re.findall(r"CREATE\s+TRIGGER\s+(\w+)", sql, re.IGNORECASE)
    assert any("double_booking" in t.lower() for t in triggers), triggers


def test_cancellation_timestamp_trigger_exists():
    sql = _all_sql()
    assert re.search(r"CREATE\s+TRIGGER\s+trg_set_canceled_at\b", sql, re.IGNORECASE)


def test_schema_is_normalized_with_foreign_keys():
    schema = _read("01_schema.sql")
    assert schema.upper().count("FOREIGN KEY") >= 4 or schema.upper().count("REFERENCES") >= 4


def test_complex_queries_file_has_18_reports():
    text = _read("06_complex_queries.sql")
    # Each report query is introduced by a numbered comment header (Q1..Q18) or a SELECT.
    assert text.upper().count("SELECT") >= 18
