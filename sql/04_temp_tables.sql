-- 04_temp_tables.sql
USE opentable_app;

DROP TEMPORARY TABLE IF EXISTS daily_summary;

CREATE TEMPORARY TABLE daily_summary AS
SELECT
  DATE(ReservationDateTime) AS Day,
  COUNT(*) AS NumReservations,
  SUM(PartySize) AS TotalGuests
FROM Reservation
GROUP BY DATE(ReservationDateTime);

SELECT * FROM daily_summary ORDER BY Day;

DROP TEMPORARY TABLE IF EXISTS daily_summary;
