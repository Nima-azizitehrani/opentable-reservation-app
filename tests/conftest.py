"""Shared fixtures: a fake MySQL layer so the Flask routes can be tested
without a live MySQL server.

app.py imports `get_conn` from db.py and calls it for every query. The tests
patch `app.get_conn` with a factory that returns FakeConnection objects whose
cursors replay canned rows based on the SQL they are given, and record any
stored-procedure calls.
"""
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Canned rows
# ---------------------------------------------------------------------------
RESTAURANT_ROW = (1, "Luigi's Trattoria", "Chicago", "Italian", 2, 4.5)
RESTAURANT_DETAIL = (1, "Luigi's Trattoria", "Italian", 2, "3125551234", "Chicago", "IL")

CUSTOMER_DICT = {
    "CustomerID": 1,
    "FirstName": "Test",
    "LastName": "User",
    "Phone": "3125551234",
    "Email": "test@example.com",
}
RESTAURANT_DICT = {"RestaurantID": 1, "Name": "Luigi's Trattoria", "City": "Chicago"}
TABLE_DICT = {"TableID": 1, "RestaurantID": 1, "TableNumber": 5, "Capacity": 4}
RESERVATION_DICT = {
    "ReservationID": 10,
    "CustomerID": 1,
    "RestaurantID": 1,
    "TableID": 1,
    "ReservationDateTime": "2026-11-01 19:00:00",
    "PartySize": 2,
    "Status": "BOOKED",
    "CustomerName": "Test User",
    "RestaurantName": "Luigi's Trattoria",
    "TableNumber": 5,
}


def _rows_for(sql, dictionary):
    """Return canned rows for a query, chosen by what the SQL selects."""
    s = " ".join(sql.split()).lower()
    if "distinct city" in s:
        return [("Austin",), ("Chicago",)]
    if "distinct cuisine" in s:
        return [("Italian",), ("Mexican",)]
    if dictionary:
        if "from customer" in s:
            return [CUSTOMER_DICT]
        if "from reservation" in s:
            return [RESERVATION_DICT]
        if "from diningtable" in s:
            return [TABLE_DICT]
        if "from restaurant" in s:
            return [RESTAURANT_DICT]
        return []
    # tuple cursors
    if "getavgrating" in s and "from" not in s:
        return [(4.5,)]
    if "from review" in s:
        return []
    if "from diningtable" in s:
        return [(1, 4)]
    if "where restaurantid" in s and "from restaurant" in s:
        return [RESTAURANT_DETAIL]
    if "from restaurant" in s:
        return [RESTAURANT_ROW]
    return []


class FakeCursor:
    def __init__(self, dictionary=False):
        self.dictionary = dictionary
        self.description = None
        self._rows = []
        self.calls = []

    def execute(self, sql, params=()):
        self.calls.append(("execute", sql, params))
        self._rows = _rows_for(sql, self.dictionary)
        if self._rows and isinstance(self._rows[0], dict):
            self.description = [(k,) for k in self._rows[0].keys()]
        elif self._rows:
            self.description = [("col",)] * len(self._rows[0])

    def callproc(self, name, args=()):
        self.calls.append(("callproc", name, tuple(args)))

    def fetchall(self):
        return list(self._rows)

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def close(self):
        pass


class FakeConnection:
    """Stands in for a mysql.connector connection. Remembers its cursors so
    tests can assert which stored procedures were called."""

    def __init__(self):
        self.cursors = []
        self.committed = False
        self.closed = False

    def cursor(self, dictionary=False):
        cur = FakeCursor(dictionary=dictionary)
        self.cursors.append(cur)
        return cur

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True

    @property
    def proc_calls(self):
        return [c for cur in self.cursors for c in cur.calls if c[0] == "callproc"]


@pytest.fixture()
def fake_db():
    """Patch app.get_conn so every call returns a fresh FakeConnection.
    Yields the list of connections created, in order."""
    connections = []

    def factory():
        conn = FakeConnection()
        connections.append(conn)
        return conn

    with patch("app.get_conn", side_effect=factory):
        yield connections


@pytest.fixture()
def client(fake_db):
    import app as app_module

    app_module.app.config.update(TESTING=True)
    with app_module.app.test_client() as c:
        yield c
