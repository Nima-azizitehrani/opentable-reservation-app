# OpenTable-Style Reservation App

A full-stack restaurant reservation web application built with **Flask** and **MySQL**. Diners can browse
restaurants, book and cancel reservations, and managers get a dashboard of 18 analytical SQL reports.
The project started as graduate coursework and is kept here as a portfolio piece.

The interesting design choice: **the business rules live in the database, not just in the app.**
Triggers and stored procedures enforce them no matter which client connects — a reservation cannot
double-book a table, a party cannot exceed its table's capacity, a review can only be left for a
completed reservation, and cancelling a reservation automatically stamps its cancellation time.

## Features

- **Browse & search restaurants** — filter by name, city, or cuisine; each listing shows its average rating
- **Restaurant detail pages** — info, available tables, recent reviews
- **Book / cancel / update / delete reservations** — booking and cancellation go through stored procedures
  (`MakeReservation`, `CancelReservation`) so validation runs in the database
- **Customer portal** — create customers and manage their reservations
- **Manager dashboard with 18 SQL reports** — CTEs, window functions (`RANK`, `DENSE_RANK`, `LAG`/`LEAD`,
  `NTILE`, `PERCENT_RANK`, running totals), `ROLLUP` subtotals, relational division, and more
  (see `sql/06_complex_queries.sql`)

## Architecture

```
Browser ──► Flask (app.py) ──► db.py (mysql-connector) ──► MySQL
                                   ▲                          │
                                   └──── rules enforced ────┘
                        triggers + stored procedures + a rating function
```

| Layer | Files | Responsibility |
|---|---|---|
| Web | `app.py`, `templates/`, `static/` | Routes, form validation, rendering |
| Data access | `db.py` | One connection factory; credentials come from `.env`, never from code |
| Database | `sql/01`–`sql/06` | Schema (3NF), seed data, indexes/views, triggers, stored procedures, report queries |

All SQL from the app uses **parameterized queries** — no string-built SQL.

## Tech stack

- Python 3.11+ · Flask 3 · Jinja2 templates
- MySQL 8 · mysql-connector-python
- python-dotenv for configuration · gunicorn (production server entry point)

## Setup

**1. Create the database** — run the SQL files in order (MySQL Workbench, or the CLI):

```bash
mysql -u root -p < sql/01_schema.sql
mysql -u root -p opentable_app < sql/02_load_data.sql
mysql -u root -p opentable_app < sql/03_indexes_views.sql
mysql -u root -p opentable_app < sql/04_temp_tables.sql
mysql -u root -p opentable_app < sql/05_triggers_procs_functions.sql
# sql/06_complex_queries.sql is reference only — the app embeds these queries itself
```

**2. Configure the environment:**

```bash
cp .env.example .env   # then replace every placeholder with your local values
```

**3. Install and run:**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask --app app run --debug
```

Open http://127.0.0.1:5000

## What I learned

- **Database design is application design.** Normalizing to 3NF and pushing invariants (no double-booking,
  capacity checks, review gating) into triggers and stored procedures meant the app code could stay thin —
  and the rules hold even for a client that bypasses the app entirely.
- **Advanced SQL is a reporting engine.** Most of the manager dashboard is one well-written query per
  report: window functions and `ROLLUP` replaced what would have been pages of Python aggregation code.
- **Configuration is a security feature.** Moving credentials into `.env` (and shipping only a
  `.env.example`) made the project safe to share publicly without changing a line of logic.
