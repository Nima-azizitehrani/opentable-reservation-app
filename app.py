# app.py
# Flask application for a restaurant reservation system (OpenTable-style).
# Handles routing, connects to MySQL, and renders templates.

import os
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, url_for
from db import get_conn

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret")

##############################################
# HELPER FUNCTIONS
# Basic validation + DB utilities
###############################################

def _clean(s):
    # Remove extra spaces from form inputs
    return (s or "").strip()


def to_int(name, value, min_v=1, max_v=10_000_000):
    # Convert input to integer and validate range
    v = _clean(value)
    try:
        n = int(v)
    except Exception as e:
        raise ValueError(f"{name} must be a number") from e
    if n < min_v or n > max_v:
        raise ValueError(f"{name} must be between {min_v} and {max_v}")
    return n


def parse_datetime_local(value):
    # Convert HTML datetime-local format to MySQL format
    v = _clean(value)
    if not v:
        raise ValueError("Reservation date/time is required")

    if "T" in v:
        fmt = "%Y-%m-%dT%H:%M" if len(v) == 16 else "%Y-%m-%dT%H:%M:%S"
        dt = datetime.strptime(v, fmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    try:
        dt = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        dt = datetime.strptime(v, "%Y-%m-%d %H:%M")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def validate_phone(phone):
    # Validates that phone number is digits only and between 10-15 characters.
    # This is application-level validation before the data even reaches MySQL.
    p = _clean(phone)
    if not p.isdigit():
        raise ValueError("Phone must contain digits only")
    if not (10 <= len(p) <= 15):
        raise ValueError("Phone must be 10 to 15 digits")
    return p


def fetch_all(sql, params=()):
    # Run SELECT query and return rows
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


def fetch_all_dict(sql, params=()):
    # Runs a SELECT query and returns rows as dictionaries
    # (so templates can access columns by name).
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


def exec_stmt(sql, params=()):
    # Executes INSERT, UPDATE, or DELETE and commits the change.
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def call_proc(proc_name, args):
    # Calls a stored procedure (MakeReservation or CancelReservation).
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.callproc(proc_name, args)
        conn.commit()
    finally:
        conn.close()


def dollars(level):
    # Converts price level (1–4) into dollar signs for display.
    try:
        n = int(level or 0)
    except Exception:
        n = 0
    return "$" * max(1, min(n, 4))


def restaurant_image(restaurant_id):
    # Returns image path for restaurant (currently shared image).
    return "img/restaurant.jpg"


def get_cities():
    # Returns list of distinct cities for filter dropdown.
    rows = fetch_all("SELECT DISTINCT City FROM Restaurant ORDER BY City")
    return [r[0] for r in rows]


def get_cuisines():
    # Returns list of distinct cuisines for filter dropdown.
    rows = fetch_all("SELECT DISTINCT Cuisine FROM Restaurant ORDER BY Cuisine")
    return [r[0] for r in rows]


# Allow templates to use dollars() and restaurant_image().
app.jinja_env.globals.update(dollars=dollars, restaurant_image=restaurant_image)


###############################################
# RESTAURANT ROUTES
# Handles browsing restaurants and making reservations
###############################################

@app.get("/")
def home():
    # Redirect to restaurants page
    return redirect(url_for("restaurants"))


@app.get("/restaurants")
def restaurants():
    # Get search filters from URL
    q = _clean(request.args.get("q"))
    city = _clean(request.args.get("city"))
    cuisine = _clean(request.args.get("cuisine"))

    # Build WHERE conditions based on filters
    where = []
    params = []

    if q:
        where.append("r.Name LIKE %s")
        params.append(f"%{q}%")
    if city:
        where.append("r.City = %s")
        params.append(city)
    if cuisine:
        where.append("r.Cuisine = %s")
        params.append(cuisine)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    ## Get restaurants + average rating
    rows = fetch_all(
        f"""
        SELECT r.RestaurantID, r.Name, r.City, r.Cuisine, r.PriceLevel,
               ROUND(GetAvgRating(r.RestaurantID), 2) AS AvgRating
        FROM Restaurant r
        {where_sql}
        ORDER BY r.City, r.Name
        """,
        tuple(params),
    )

    # Send data to template
    return render_template(
        "restaurants.html",
        title="Restaurants",
        q=q,
        city=city,
        cuisine=cuisine,
        cities=get_cities(),
        cuisines=get_cuisines(),
        rows=rows,
        body_class="has-photo bg_restaurant",
    )


@app.get("/restaurant/<int:restaurant_id>")
def restaurant_detail(restaurant_id):
    # Show details for one restaurant
    rid = restaurant_id

    # Get restaurant info
    r = fetch_all(
        """
        SELECT RestaurantID, Name, Cuisine, PriceLevel, Phone, City, State
        FROM Restaurant
        WHERE RestaurantID = %s
        """,
        (rid,),
    )
    if not r:
        # If not found, show error
        flash("Restaurant not found", "error")
        return redirect(url_for("restaurants"))

    r = r[0]  # fetch_all returns a list, we want just the first (and only) row

    # Get average rating
    avg = fetch_all("SELECT ROUND(GetAvgRating(%s), 2)", (rid,))
    avg_rating = avg[0][0] if avg else None

    # Get tables for booking form
    tables = fetch_all(
        "SELECT TableID, Capacity FROM DiningTable WHERE RestaurantID = %s ORDER BY TableID",
        (rid,),
    )

    # Get 10 most recent reviews
    reviews = fetch_all(
        """
        SELECT rv.ReviewID, rv.Rating, rv.Comment, rv.CreatedAt
        FROM Review rv
        JOIN Reservation res ON res.ReservationID = rv.ReservationID
        WHERE res.RestaurantID = %s
        ORDER BY rv.CreatedAt DESC
        LIMIT 10
        """,
        (rid,),
    )
    # Render detail page
    return render_template(
        "restaurant_detail.html",
        title=r[1],
        r=r,
        avg_rating=avg_rating,
        tables=tables,
        reviews=reviews,
        body_class="has-photo bg_restaurant",
    )


@app.post("/reserve")
def reserve():
    # Create reservation from restaurant page
    try:
        customer_id = to_int("Customer ID", request.form.get("customer_id", ""))
        restaurant_id = to_int("Restaurant ID", request.form.get("restaurant_id", ""))
        table_id = to_int("Table ID", request.form.get("table_id", ""))
        dt = parse_datetime_local(request.form.get("reservation_datetime", ""))
        party_size = to_int("Party size", request.form.get("party_size", ""), 1, 100)

        # Call stored procedure
        # Show success or error message
        call_proc("MakeReservation", (customer_id, restaurant_id, table_id, dt, party_size))
        flash("Reservation created.", "success")
    except Exception as e:
        msg = str(e)
        if "1452" in msg and "CustomerID" in msg:
            msg = "Customer ID does not exist. Please check the ID and try again."
        flash(msg, "error")

    # Redirect back to restaurant page
    return redirect(url_for("restaurant_detail", restaurant_id=int(request.form.get("restaurant_id") or 1)))


###############################################
# CUSTOMER & RESERVATION ROUTES
# Lets users create customers and manage reservations
###############################################

@app.get("/customer")
def customer_portal():
    # Loads the Customers and Reservations page.
    customers = fetch_all_dict(
        "SELECT CustomerID, FirstName, LastName, Phone, Email FROM Customer ORDER BY CustomerID"
    )
    restaurants_rows = fetch_all_dict(
        "SELECT RestaurantID, Name, City FROM Restaurant ORDER BY City, Name"
    )
    tables = fetch_all_dict(
        "SELECT TableID, RestaurantID, TableNumber, Capacity FROM DiningTable ORDER BY RestaurantID, TableNumber"
    )
    # Join across 4 tables to get human-readable names for the reservations table
    reservations = fetch_all_dict(
        """
        SELECT res.ReservationID, res.CustomerID, res.RestaurantID, res.TableID,
               res.ReservationDateTime, res.PartySize, res.Status,
               CONCAT(c.FirstName,' ',c.LastName) AS CustomerName,
               r.Name AS RestaurantName,
               t.TableNumber
        FROM Reservation res
        JOIN Customer c ON c.CustomerID = res.CustomerID
        JOIN Restaurant r ON r.RestaurantID = res.RestaurantID
        JOIN DiningTable t ON t.TableID = res.TableID
        ORDER BY res.ReservationDateTime DESC
        LIMIT 80
        """
    )

    return render_template(
        "customer.html",
        title="Customers & Reservations",
        customers=customers,
        restaurants=restaurants_rows,
        tables=tables,
        reservations=reservations,
        body_class="has-photo bg_background",
    )


@app.post("/create_customer")
def create_customer():
    # Create new customer
    # Validates all inputs before inserting into the database.
    # Any validation error is shown as a red flash message.
    try:
        first = _clean(request.form.get("first_name"))
        last = _clean(request.form.get("last_name"))
        if not first or not last:
            raise ValueError("First name and last name are required")

        # validate_phone checks that the number is digits only and 10-15 characters
        phone = validate_phone(request.form.get("phone", ""))
        email = _clean(request.form.get("email"))
        if email and "@" not in email:
            raise ValueError("Email looks invalid")

        exec_stmt(
            "INSERT INTO Customer (FirstName, LastName, Phone, Email) VALUES (%s,%s,%s,%s)",
            (first, last, phone, email),
        )
        flash("Customer created successfully.", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("customer_portal"))


@app.post("/make_reservation")
def make_reservation():
    # Create reservation from customer page
    # Same logic as /reserve but submitted from the customer page instead of the restaurant detail page.
    try:
        cid = to_int("Customer ID", request.form.get("customer_id", ""))
        rid = to_int("Restaurant ID", request.form.get("restaurant_id", ""))
        tid = to_int("Table ID", request.form.get("table_id", ""))
        dt = parse_datetime_local(request.form.get("reservation_datetime", ""))
        party = to_int("Party size", request.form.get("party_size", ""), 1, 100)

        # Calls the MakeReservation stored procedure.
        # The trg_no_double_booking and trg_party_size_capacity triggers
        call_proc("MakeReservation", (cid, rid, tid, dt, party))
        flash("Reservation created.", "success")
    except Exception as e:
        msg = str(e)
        if "1452" in msg and "CustomerID" in msg:
            msg = "Customer ID does not exist. Please check the ID and try again."
        flash(msg, "error")

    return redirect(url_for("customer_portal"))


@app.post("/cancel_reservation")
def cancel_reservation():
    # Cancel reservation using stored procedure
    # The trg_set_canceled_at trigger then automatically fills in
    # the CanceledAt timestamp - we don't do that manually here.
    try:
        res_id = to_int("Reservation ID", request.form.get("reservation_id", ""))
        call_proc("CancelReservation", (res_id,))
        flash("Reservation canceled.", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("customer_portal"))


@app.post("/update_reservation")
def update_reservation():
    # Update reservation date/time and party size
    try:
        res_id = to_int("Reservation ID", request.form.get("reservation_id", ""))
        dt = parse_datetime_local(request.form.get("new_reservation_datetime", ""))
        party = to_int("Party size", request.form.get("new_party_size", ""), 1, 100)

        exec_stmt(
            "UPDATE Reservation SET ReservationDateTime=%s, PartySize=%s WHERE ReservationID=%s",
            (dt, party, res_id),
        )
        flash("Reservation updated.", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("customer_portal"))


@app.post("/delete_reservation")
def delete_reservation():
    # Permanently delete reservation
    # This will fail with a foreign key error if a Review exists for this reservation
    try:
        res_id = to_int("Reservation ID", request.form.get("reservation_id", ""))
        exec_stmt("DELETE FROM Reservation WHERE ReservationID=%s", (res_id,))
        flash("Reservation deleted.", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("customer_portal"))


###############################################
# MANAGER REPORTS
# 19 SQL reports using advanced queries (CTEs, window functions, ROLLUP, etc.)
###############################################

# Each report has id, group, title, optional city filter, and SQL query.
REPORTS = [
    # ── RESTAURANTS GROUP ──

    # Q1: CTE (WITH clause) - counts reservations per restaurant
    {"id": "1", "group": "Restaurants", "title": "Top restaurants by reservation count", "needs_city": False,
     "sql": """
        WITH res_counts AS (
          SELECT RestaurantID, COUNT(*) AS total_res
          FROM Reservation
          GROUP BY RestaurantID
        )
        SELECT r.RestaurantID, r.Name, rc.total_res
        FROM res_counts rc
        JOIN Restaurant r ON r.RestaurantID = rc.RestaurantID
        ORDER BY rc.total_res DESC, r.Name;
     """},

    # Q2: Restaurants with no reservations (NOT EXISTS / anti-join)
    {"id": "2", "group": "Restaurants", "title": "Restaurants with no reservations", "needs_city": False,
     "sql": """
        SELECT r.RestaurantID, r.Name
        FROM Restaurant r
        WHERE NOT EXISTS (
          SELECT 1
          FROM Reservation res
          WHERE res.RestaurantID = r.RestaurantID
        )
        ORDER BY r.RestaurantID, r.Name;
     """},

    # Q3: Customers with at least one review (EXISTS)
    {"id": "3", "group": "Customers", "title": "Customers who have at least one review", "needs_city": False,
     "sql": """
        SELECT c.CustomerID, c.FirstName, c.LastName
        FROM Customer c
        WHERE EXISTS (
          SELECT 1
          FROM Reservation res
          JOIN Review rv ON rv.ReservationID = res.ReservationID
          WHERE res.CustomerID = c.CustomerID
        )
        ORDER BY c.CustomerID;
     """},

    # Q4: Avg rating per restaurant + review count (LEFT JOIN + aggregates)
    {"id": "4", "group": "Restaurants", "title": "Average rating per restaurant (with review count)", "needs_city": False,
     "sql": """
        SELECT r.RestaurantID, r.Name,
               COUNT(rv.ReviewID) AS review_cnt,
               ROUND(AVG(rv.Rating), 2) AS avg_rating
        FROM Restaurant r
        LEFT JOIN Reservation res ON res.RestaurantID = r.RestaurantID
        LEFT JOIN Review rv ON rv.ReservationID = res.ReservationID
        GROUP BY r.RestaurantID, r.Name
        ORDER BY avg_rating DESC, review_cnt DESC, r.Name;
     """},

    # Q5: Customers who favorited ALL restaurants in a city (double NOT EXISTS)
    {"id": "5", "group": "Customers", "title": "Customers who favorited ALL restaurants in a selected city", "needs_city": True,
     "sql": """
        SELECT c.CustomerID, c.FirstName, c.LastName
        FROM Customer c
        WHERE NOT EXISTS (
          SELECT 1
          FROM Restaurant r
          WHERE r.City = %(city)s
            AND NOT EXISTS (
              SELECT 1
              FROM Favorite f
              WHERE f.CustomerID = c.CustomerID
                AND f.RestaurantID = r.RestaurantID
            )
        )
        ORDER BY c.CustomerID;
     """},

    # Q6: GROUP BY + HAVING - finds customers with 2 or more reservations
    {"id": "6", "group": "Customers", "title": "Repeat customers (2+ reservations)", "needs_city": False,
     "sql": """
        SELECT c.CustomerID, c.FirstName, c.LastName, COUNT(*) AS total_res
        FROM Customer c
        JOIN Reservation res ON res.CustomerID = c.CustomerID
        GROUP BY c.CustomerID, c.FirstName, c.LastName
        HAVING COUNT(*) >= 2
        ORDER BY total_res DESC, c.LastName, c.FirstName;
     """},

    # Q7: Reservations by restaurant + grand total (ROLLUP + GROUPING)
    {"id": "7", "group": "Restaurants", "title": "Reservation totals by restaurant (including grand total)", "needs_city": False,
     "sql": """
        SELECT
          COALESCE(r.Name, 'GRAND TOTAL') AS restaurant_name,
          COUNT(*) AS total_res,
          GROUPING(r.Name) AS is_grand_total
        FROM Reservation res
        JOIN Restaurant r ON r.RestaurantID = res.RestaurantID
        GROUP BY r.Name WITH ROLLUP
        ORDER BY (GROUPING(r.Name)=1) ASC, total_res DESC, restaurant_name;
     """},

    # Q8: RANK() - ranks restaurants by average review rating (highest first)
    {"id": "8", "group": "Restaurants", "title": "Restaurants ranked by average rating", "needs_city": False,
     "sql": """
        SELECT
          r.RestaurantID,
          r.Name AS RestaurantName,
          ROUND(AVG(rv.Rating), 2) AS AvgRating,
          RANK() OVER (ORDER BY AVG(rv.Rating) DESC) AS RatingRank
        FROM Restaurant r
        JOIN Reservation res ON res.RestaurantID = r.RestaurantID
        JOIN Review rv ON rv.ReservationID = res.ReservationID
        GROUP BY r.RestaurantID, r.Name
        ORDER BY AvgRating DESC;
     """},

    # Q9: UNION - combines two lists (customers who reserved + customers who reviewed)
    {"id": "9", "group": "Customers", "title": "Customer engagement sources (reservation vs review)", "needs_city": False,
     "sql": """
        SELECT CustomerID, 'reservation' AS source
        FROM Reservation
        UNION
        SELECT res.CustomerID, 'review' AS source
        FROM Review rv
        JOIN Reservation res ON res.ReservationID = rv.ReservationID
        ORDER BY CustomerID, source;
     """},

    # Q10: PERCENT_RANK + CUME_DIST window functions inside a CTE. Shows where each restaurant sits in the rating distribution.
    {"id": "10", "group": "Restaurants", "title": "Restaurant rating leaderboard (percentile + cumulative distribution)", "needs_city": False,
     "sql": """
        WITH rating_stats AS (
          SELECT r.RestaurantID,
                 r.Name,
                 COUNT(rv.ReviewID) AS review_cnt,
                 ROUND(AVG(rv.Rating), 2) AS avg_rating
          FROM Restaurant r
          LEFT JOIN Reservation res ON res.RestaurantID = r.RestaurantID
          LEFT JOIN Review rv ON rv.ReservationID = res.ReservationID
          GROUP BY r.RestaurantID, r.Name
        )
        SELECT RestaurantID,
               Name,
               review_cnt,
               avg_rating,
               ROUND(PERCENT_RANK() OVER (ORDER BY avg_rating), 3) AS percent_rank_by_rating,
               ROUND(CUME_DIST()    OVER (ORDER BY avg_rating), 3) AS cume_dist_by_rating
        FROM rating_stats
        ORDER BY avg_rating DESC, review_cnt DESC, Name;
     """},

    # Q11: NTILE(4) - divides restaurants into 4 quartiles by reservation volume
    {"id": "11", "group": "Trends", "title": "Restaurant quartiles by reservation volume", "needs_city": False,
     "sql": """
        WITH res_ct AS (
          SELECT r.RestaurantID, r.Name, COUNT(res.ReservationID) AS total_res
          FROM Restaurant r
          LEFT JOIN Reservation res ON res.RestaurantID = r.RestaurantID
          GROUP BY r.RestaurantID, r.Name
        )
        SELECT RestaurantID,
               Name,
               total_res,
               NTILE(4) OVER (ORDER BY total_res DESC) AS reservation_quartile
        FROM res_ct
        ORDER BY total_res DESC, Name;
     """},


    # Q12: LAG window function - compares each day's count to the previous day.
    # NULLIF prevents division by zero when calculating percent change.
    {"id": "12", "group": "Trends", "title": "Day-over-day reservation change", "needs_city": False,
     "sql": """
        WITH daily AS (
          SELECT DATE(ReservationDateTime) AS d, COUNT(*) AS daily_cnt
          FROM Reservation
          GROUP BY DATE(ReservationDateTime)
        )
        SELECT d,
               daily_cnt,
               LAG(daily_cnt) OVER (ORDER BY d) AS prev_day_cnt,
               (daily_cnt - LAG(daily_cnt) OVER (ORDER BY d)) AS delta,
               ROUND(
                 (daily_cnt - LAG(daily_cnt) OVER (ORDER BY d))
                 / NULLIF(LAG(daily_cnt) OVER (ORDER BY d), 0)
               , 3) AS pct_change
        FROM daily
        ORDER BY d;
     """},

    # Q13: Top 3 restaurants per city (CTE + DENSE_RANK)
    {"id": "13", "group": "Restaurants", "title": "Top 3 restaurants per city by reservations", "needs_city": False,
     "sql": """
        WITH counts AS (
          SELECT r.City, r.RestaurantID, r.Name, COUNT(*) AS total_res
          FROM Reservation res
          JOIN Restaurant r ON r.RestaurantID = res.RestaurantID
          GROUP BY r.City, r.RestaurantID, r.Name
        ),
        ranked AS (
          SELECT *,
                 DENSE_RANK() OVER (PARTITION BY City ORDER BY total_res DESC) AS city_rank
          FROM counts
        )
        SELECT City, RestaurantID, Name, total_res, city_rank
        FROM ranked
        WHERE city_rank <= 3
        ORDER BY City, city_rank, total_res DESC, Name;
     """},

    # Q14: Finds the longest gaps between reservations per customer. (LAG + TIMESTAMPDIFF)
    {"id": "14", "group": "Customers", "title": "Largest gaps between reservations (per customer)", "needs_city": False,
     "sql": """
        WITH ordered AS (
          SELECT res.CustomerID,
                 res.ReservationDateTime,
                 LAG(res.ReservationDateTime) OVER (
                   PARTITION BY res.CustomerID
                   ORDER BY res.ReservationDateTime
                 ) AS prev_dt
          FROM Reservation res
        )
        SELECT CustomerID,
               ReservationDateTime,
               prev_dt,
               TIMESTAMPDIFF(DAY, prev_dt, ReservationDateTime) AS gap_days
        FROM ordered
        WHERE prev_dt IS NOT NULL
        ORDER BY gap_days DESC, CustomerID
        LIMIT 50;
     """},

    # Q15: Reservation sequence per customer (ROW_NUMBER)
    {"id": "15", "group": "Customers", "title": "Reservation sequence number per customer", "needs_city": False,
     "sql": """
        SELECT
            c.CustomerID,
            CONCAT(c.FirstName, ' ', c.LastName) AS CustomerName,
            res.ReservationID,
            res.ReservationDateTime,
            ROW_NUMBER() OVER (
                PARTITION BY c.CustomerID
                ORDER BY res.ReservationDateTime
            ) AS ReservationSeqForCustomer
        FROM Customer AS c
        JOIN Reservation AS res ON res.CustomerID = c.CustomerID
        ORDER BY c.CustomerID, ReservationSeqForCustomer;
     """},

    # Q16: Next reservation on the same table (LEAD)
    {"id": "16", "group": "Restaurants", "title": "Next reservation time on the same table", "needs_city": False,
     "sql": """
        SELECT
            res.TableID,
            res.ReservationID,
            res.ReservationDateTime,
            LEAD(res.ReservationDateTime, 1) OVER (
                PARTITION BY res.TableID
                ORDER BY res.ReservationDateTime
            ) AS NextReservationOnTable
        FROM Reservation AS res
        ORDER BY res.TableID, res.ReservationDateTime;
     """},

    # Q17: Running total & running avg of daily guests per restaurant (CTE + window)
    {"id": "17", "group": "Trends", "title": "Running total and running average of daily guests per restaurant", "needs_city": False,
     "sql": """
        WITH DailyRestaurantGuests AS (
            SELECT
                r.RestaurantID,
                r.Name AS RestaurantName,
                DATE(res.ReservationDateTime) AS Day,
                SUM(res.PartySize) AS TotalGuests
            FROM Restaurant AS r
            JOIN Reservation AS res ON res.RestaurantID = r.RestaurantID
            GROUP BY r.RestaurantID, r.Name, DATE(res.ReservationDateTime)
        )
        SELECT
            RestaurantID,
            RestaurantName,
            Day,
            TotalGuests,
            SUM(TotalGuests) OVER (
                PARTITION BY RestaurantID
                ORDER BY Day
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS RunningTotalGuests,
            ROUND(
                AVG(TotalGuests) OVER (
                    PARTITION BY RestaurantID
                    ORDER BY Day
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ),
                2
            ) AS RunningAvgGuests
        FROM DailyRestaurantGuests
        ORDER BY RestaurantID, Day;
     """},

    # Q18: Total guests by (City, Cuisine) with subtotals (ROLLUP)
    {"id": "18", "group": "Trends", "title": "Total guests by City and Cuisine (with subtotals)", "needs_city": False,
     "sql": """
        SELECT
            COALESCE(rt.City, 'ALL CITIES') AS City,
            COALESCE(rt.Cuisine, 'ALL CUISINES') AS Cuisine,
            SUM(res.PartySize) AS TotalGuests
        FROM Restaurant AS rt
        JOIN Reservation AS res ON res.RestaurantID = rt.RestaurantID
        GROUP BY rt.City, rt.Cuisine
        WITH ROLLUP;
     """},
]


@app.get("/reports")
def reports():
    # Loads the Manager Dashboard page.
    # Organizes the 19 reports into groups (Restaurants, Customers, Trends)
    # for display in the grouped button layout.
    cities = [c for c in get_cities() if c.lower() != "chicago"]
    default_city = ""  # default to "All" so no city is pre-selected

    # Build a dictionary of {group_name: [list of reports in that group]}
    # This is what the template loops over to render the grouped sections.
    groups = {}
    for r in REPORTS:
        groups.setdefault(r["group"], []).append(r)

    return render_template(
        "reports.html",
        title="Reports",
        groups=groups,
        cities=cities,
        default_city=default_city,
        body_class="has-photo bg_background",
    )


@app.post("/run_report")
def run_report():
    # Executes whichever report button was clicked on the dashboard.
    report_id = _clean(request.form.get("report_id"))
    city = _clean(request.form.get("city"))

    # Find the matching report from our REPORTS list by ID
    report = next((r for r in REPORTS if r["id"] == report_id), None)
    if not report:
        flash("Unknown report", "error")
        return redirect(url_for("reports"))

    conn = get_conn()
    try:
        cur = conn.cursor()

        if report.get("needs_city"):
            if not city:
                raise ValueError("Please select a city for this report")
            cur.execute(report["sql"], {"city": city})
        else:
            cur.execute(report["sql"])

        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []

        # results.html dynamically renders any table of data using cols and rows
        return render_template(
            "results.html",
            title=f"Report {report_id}",
            subtitle=report.get("title"),
            cols=cols,
            rows=rows,
            body_class="has-photo bg_background",
        )
    except Exception as e:
        # If the SQL fails for any reason, show the error and go back to reports
        flash(str(e), "error")
        return redirect(url_for("reports"))
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(debug=True)