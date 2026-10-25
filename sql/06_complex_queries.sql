-- Complex SQL Queries (Q1-Q18): the 18 manager-dashboard reports

-- Q1: Top restaurants by reservations (CTE + aggregate)
WITH res_counts AS (
  SELECT RestaurantID, COUNT(*) AS total_res
  FROM Reservation
  GROUP BY RestaurantID
)
SELECT r.RestaurantID, r.Name, rc.total_res
FROM res_counts rc
JOIN Restaurant r ON r.RestaurantID = rc.RestaurantID
ORDER BY rc.total_res DESC, r.Name;

-- Q2: Restaurants with no reservations (NOT EXISTS / anti-join)
SELECT r.RestaurantID, r.Name
FROM Restaurant r
WHERE NOT EXISTS (
  SELECT 1
  FROM Reservation res
  WHERE res.RestaurantID = r.RestaurantID
)
ORDER BY r.RestaurantID, r.Name;

-- Q3: Customers with at least one review (EXISTS)
SELECT c.CustomerID, c.FirstName, c.LastName
FROM Customer c
WHERE EXISTS (
  SELECT 1
  FROM Reservation res
  JOIN Review rv ON rv.ReservationID = res.ReservationID
  WHERE res.CustomerID = c.CustomerID
)
ORDER BY c.CustomerID;

-- Q4: Avg rating per restaurant + review count (LEFT JOIN + aggregates)
SELECT r.RestaurantID, r.Name,
       COUNT(rv.ReviewID) AS review_cnt,
       ROUND(AVG(rv.Rating), 2) AS avg_rating
FROM Restaurant r
LEFT JOIN Reservation res ON res.RestaurantID = r.RestaurantID
LEFT JOIN Review rv ON rv.ReservationID = res.ReservationID
GROUP BY r.RestaurantID, r.Name
ORDER BY avg_rating DESC, review_cnt DESC, r.Name;

-- Q5: Customers who favorited ALL restaurants in a city (double NOT EXISTS / relational division)
SELECT c.CustomerID, c.FirstName, c.LastName
FROM Customer c
WHERE NOT EXISTS (
  SELECT 1
  FROM Restaurant r
  WHERE r.City = 'Atlanta'
    AND NOT EXISTS (
      SELECT 1
      FROM Favorite f
      WHERE f.CustomerID = c.CustomerID
        AND f.RestaurantID = r.RestaurantID
    )
)
ORDER BY c.CustomerID;

-- Q6: Repeat customers with 2+ reservations (GROUP BY + HAVING)
SELECT c.CustomerID, c.FirstName, c.LastName, COUNT(*) AS total_res
FROM Customer c
JOIN Reservation res ON res.CustomerID = c.CustomerID
GROUP BY c.CustomerID, c.FirstName, c.LastName
HAVING COUNT(*) >= 2
ORDER BY total_res DESC, c.LastName, c.FirstName;

-- Q7: Reservations by restaurant + grand total (ROLLUP + GROUPING)
SELECT
  COALESCE(r.Name, 'GRAND TOTAL') AS restaurant_name,
  COUNT(*) AS total_res,
  GROUPING(r.Name) AS is_grand_total
FROM Reservation res
JOIN Restaurant r ON r.RestaurantID = res.RestaurantID
GROUP BY r.Name WITH ROLLUP
ORDER BY (GROUPING(r.Name)=1) ASC, total_res DESC, restaurant_name;

-- Q8: Restaurants ranked by average rating (RANK window function)
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

-- Q9: UNION - combines customers who reserved + customers who reviewed
SELECT CustomerID, 'reservation' AS source
FROM Reservation
UNION
SELECT res.CustomerID, 'review' AS source
FROM Review rv
JOIN Reservation res ON res.ReservationID = rv.ReservationID
ORDER BY CustomerID, source;

-- Q10: Restaurant rating leaderboard (PERCENT_RANK + CUME_DIST inside CTE)
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

-- Q11: Restaurant quartiles by reservation volume (NTILE)
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

-- Q12: Day-over-day reservation change (LAG + NULLIF)
-- NULLIF prevents division by zero when calculating percent change
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

-- Q13: Top 3 restaurants per city (CTE + DENSE_RANK)
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

-- Q14: Largest gaps between reservations per customer (LAG + TIMESTAMPDIFF)
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

-- Q15: Reservation sequence per customer (ROW_NUMBER)
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

-- Q16: Next reservation on the same table (LEAD)
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

-- Q17: Running total + running avg of daily guests per restaurant (CTE + window frames)
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

-- Q18: Total guests by (City, Cuisine) with subtotals (ROLLUP)
SELECT
    COALESCE(rt.City, 'ALL CITIES') AS City,
    COALESCE(rt.Cuisine, 'ALL CUISINES') AS Cuisine,
    SUM(res.PartySize) AS TotalGuests
FROM Restaurant AS rt
JOIN Reservation AS res ON res.RestaurantID = rt.RestaurantID
GROUP BY rt.City, rt.Cuisine
WITH ROLLUP;