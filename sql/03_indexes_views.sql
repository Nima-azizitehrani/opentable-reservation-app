-- 03_indexes_views.sql
-- Indexes + Views (and show them)

USE opentable_app;

-- ---------- Indexes ----------
-- Speed lookups of reservations by restaurant and datetime
CREATE INDEX idx_res_rest_dt ON Reservation (RestaurantID, ReservationDateTime);

-- Help search restaurants by city and cuisine
CREATE INDEX idx_rest_city_cui ON Restaurant (City, Cuisine);

-- Help filter reviews by rating
CREATE INDEX idx_review_rating ON Review (Rating);

-- show indexes
SHOW INDEX FROM Reservation;
SHOW INDEX FROM Restaurant;
SHOW INDEX FROM Review;

-- ---------- Views ----------
-- Upcoming reservations per restaurant (helps host/manager)
CREATE OR REPLACE VIEW v_upcoming_reservations AS
SELECT
  r.ReservationID,
  r.ReservationDateTime,
  r.PartySize,
  r.Status,
  CONCAT(c.FirstName,' ',c.LastName) AS CustomerName,
  rt.Name AS RestaurantName,
  dt.TableNumber
FROM Reservation r
JOIN Customer c    ON c.CustomerID = r.CustomerID
JOIN Restaurant rt ON rt.RestaurantID = r.RestaurantID
JOIN DiningTable dt ON dt.TableID = r.TableID
WHERE r.Status = 'BOOKED'
ORDER BY r.ReservationDateTime;

-- view outputs
SELECT * FROM v_upcoming_reservations LIMIT 10;
