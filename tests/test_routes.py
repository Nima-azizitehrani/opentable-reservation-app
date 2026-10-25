"""Route tests — the Flask app is exercised through its test client with the
database layer faked (see tests/conftest.py), so no MySQL server is needed."""


def test_home_redirects_to_restaurants(client):
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/restaurants" in resp.headers["Location"]


def test_restaurants_page_lists_restaurants(client):
    resp = client.get("/restaurants")
    assert resp.status_code == 200
    assert b"Luigi" in resp.data


def test_restaurant_detail_page(client):
    resp = client.get("/restaurant/1")
    assert resp.status_code == 200
    assert b"Luigi" in resp.data


def test_reports_dashboard_loads(client):
    resp = client.get("/reports")
    assert resp.status_code == 200


def test_customer_portal_loads(client):
    resp = client.get("/customer")
    assert resp.status_code == 200
    assert b"Test User" in resp.data or b"Test" in resp.data


def test_make_reservation_calls_stored_procedure(client, fake_db):
    resp = client.post(
        "/make_reservation",
        data={
            "customer_id": "1",
            "restaurant_id": "1",
            "table_id": "1",
            "reservation_datetime": "2026-11-01T19:00",
            "party_size": "2",
        },
    )
    assert resp.status_code == 302
    all_calls = [call for conn in fake_db for call in conn.proc_calls]
    assert any(c[1] == "MakeReservation" for c in all_calls), all_calls


def test_cancel_reservation_calls_stored_procedure(client, fake_db):
    resp = client.post("/cancel_reservation", data={"reservation_id": "10"})
    assert resp.status_code == 302
    all_calls = [call for conn in fake_db for call in conn.proc_calls]
    assert any(c[1] == "CancelReservation" for c in all_calls), all_calls


def test_make_reservation_rejects_bad_input_without_touching_db(client, fake_db):
    resp = client.post(
        "/make_reservation",
        data={
            "customer_id": "not-a-number",
            "restaurant_id": "1",
            "table_id": "1",
            "reservation_datetime": "2026-11-01T19:00",
            "party_size": "2",
        },
    )
    assert resp.status_code == 302  # redirects back with an error flash
    all_calls = [call for conn in fake_db for call in conn.proc_calls]
    assert all_calls == []


def test_run_unknown_report_redirects(client):
    resp = client.post("/run_report", data={"report_id": "does-not-exist", "city": ""})
    assert resp.status_code == 302
    assert "/reports" in resp.headers["Location"]
