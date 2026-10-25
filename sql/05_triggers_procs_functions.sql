-- 05_triggers_procs_functions.sql
USE opentable_app;

-- TRIGGER: Auto-populate CanceledAt when a reservation is cancelled
-- Business rule: If Status changes to 'CANCELED', set CanceledAt to current timestamp.
DROP TRIGGER IF EXISTS trg_set_canceled_at;

DELIMITER //
CREATE TRIGGER trg_set_canceled_at
BEFORE UPDATE ON Reservation
FOR EACH ROW
BEGIN
  IF NEW.Status = 'CANCELED' AND OLD.Status <> 'CANCELED' THEN
    SET NEW.CanceledAt = NOW();
  END IF;
END//
DELIMITER ;

-- TRIGGER: Prevent double-booking for active (BOOKED) reservations
DROP TRIGGER IF EXISTS trg_no_double_booking_ins;

DELIMITER //
CREATE TRIGGER trg_no_double_booking_ins
BEFORE INSERT ON Reservation
FOR EACH ROW
BEGIN
  IF NEW.Status = 'BOOKED' AND EXISTS (
    SELECT 1
    FROM Reservation r
    WHERE r.TableID = NEW.TableID
      AND r.ReservationDateTime = NEW.ReservationDateTime
      AND r.Status = 'BOOKED'
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Double-booking not allowed';
  END IF;
END//

-- Ensure party size does not exceed table capacity (INSERT)
DROP TRIGGER IF EXISTS trg_party_size_capacity_ins;//
CREATE TRIGGER trg_party_size_capacity_ins
BEFORE INSERT ON Reservation
FOR EACH ROW
BEGIN
  DECLARE cap INT;
  SELECT Capacity INTO cap FROM DiningTable WHERE TableID = NEW.TableID;
  IF cap IS NULL THEN
    SIGNAL SQLSTATE "45000" SET MESSAGE_TEXT = "Invalid TableID";
  END IF;
  IF NEW.PartySize > cap THEN
    SIGNAL SQLSTATE "45000" SET MESSAGE_TEXT = "Party size exceeds table capacity";
  END IF;
END//

-- Ensure party size does not exceed table capacity (UPDATE)
DROP TRIGGER IF EXISTS trg_party_size_capacity_upd;//
CREATE TRIGGER trg_party_size_capacity_upd
BEFORE UPDATE ON Reservation
FOR EACH ROW
BEGIN
  DECLARE cap INT;
  SELECT Capacity INTO cap FROM DiningTable WHERE TableID = NEW.TableID;
  IF cap IS NULL THEN
    SIGNAL SQLSTATE "45000" SET MESSAGE_TEXT = "Invalid TableID";
  END IF;
  IF NEW.PartySize > cap THEN
    SIGNAL SQLSTATE "45000" SET MESSAGE_TEXT = "Party size exceeds table capacity";
  END IF;
END//

-- Prevent double booking on UPDATE as well
DROP TRIGGER IF EXISTS trg_no_double_booking_upd;//
CREATE TRIGGER trg_no_double_booking_upd
BEFORE UPDATE ON Reservation
FOR EACH ROW
BEGIN
  IF EXISTS (
    SELECT 1
    FROM Reservation r
    WHERE r.TableID = NEW.TableID
      AND r.ReservationDateTime = NEW.ReservationDateTime
      AND r.Status = "BOOKED"
      AND r.ReservationID <> OLD.ReservationID
  ) THEN
    SIGNAL SQLSTATE "45000" SET MESSAGE_TEXT = "No double booking: the table is already reserved for that time";
  END IF;
END//

DELIMITER ;

-- TRIGGER: Allow reviews only for COMPLETED reservations
DROP TRIGGER IF EXISTS trg_review_only_completed;

DELIMITER //
CREATE TRIGGER trg_review_only_completed
BEFORE INSERT ON Review
FOR EACH ROW
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM Reservation r
    WHERE r.ReservationID = NEW.ReservationID
      AND r.Status = 'COMPLETED'
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Reviews require a COMPLETED reservation';
  END IF;
END//
DELIMITER ;


-- =========================================================
-- STORED PROCEDURE: CancelReservation
-- Purpose: Cancel a reservation by ID (trigger will set CanceledAt automatically).
DROP PROCEDURE IF EXISTS CancelReservation;

DELIMITER //
CREATE PROCEDURE CancelReservation(IN p_resID INT)
BEGIN
  UPDATE Reservation
  SET Status = 'CANCELED'
  WHERE ReservationID = p_resID;
END//
DELIMITER ;

-- =========================================================
-- STORED PROCEDURE: MakeReservation
-- Purpose: Create a BOOKED reservation with simple validation:
--   1) The table must belong to the given restaurant
--   2) Party size must not exceed table capacity
DROP PROCEDURE IF EXISTS MakeReservation;

DELIMITER //
CREATE PROCEDURE MakeReservation(
  IN p_customerID   INT,
  IN p_restaurantID INT,
  IN p_tableID      INT,
  IN p_time         DATETIME,
  IN p_party        INT
)
BEGIN
  -- Validate table belongs to restaurant
  IF NOT EXISTS (
    SELECT 1
    FROM DiningTable
    WHERE TableID = p_tableID
      AND RestaurantID = p_restaurantID
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Table does not belong to this restaurant';
  END IF;

  -- Validate capacity
  IF p_party > (
    SELECT Capacity
    FROM DiningTable
    WHERE TableID = p_tableID
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Party size exceeds table capacity';
  END IF;

  INSERT INTO Reservation(CustomerID, RestaurantID, TableID, ReservationDateTime, PartySize, Status)
  VALUES (p_customerID, p_restaurantID, p_tableID, p_time, p_party, 'BOOKED');
END//
DELIMITER ;

-- =========================================================
-- FUNCTION: GetAvgRating
-- Purpose: Return the average rating for all reviews associated with a restaurant.
-- If no reviews exist, return 0.00.
DROP FUNCTION IF EXISTS GetAvgRating;

DELIMITER //
CREATE FUNCTION GetAvgRating(p_restID INT)
RETURNS DECIMAL(4,2)
READS SQL DATA
DETERMINISTIC
BEGIN
  DECLARE x DECIMAL(4,2);

  SELECT AVG(rv.Rating) INTO x
  FROM Reservation r
  JOIN Review rv ON rv.ReservationID = r.ReservationID
  WHERE r.RestaurantID = p_restID;

  RETURN IFNULL(x, 0.00);
END//
DELIMITER ;

-- =========================================================
-- VERIFICATION

SHOW TRIGGERS;
SHOW PROCEDURE STATUS WHERE Db = 'opentable_app';
SHOW FUNCTION STATUS WHERE Db = 'opentable_app';

-- =========================================================
-- SMALL TESTS

-- Test 1: Trigger proof (CanceledAt changes when Status becomes CANCELED)
-- Pick an existing ReservationID from your data (example: 21)
SELECT ReservationID, Status, CanceledAt FROM Reservation WHERE ReservationID = 21;
CALL CancelReservation(21);
SELECT ReservationID, Status, CanceledAt FROM Reservation WHERE ReservationID = 21;

-- Test 2: Function proof (returns avg rating or 0.00)
SELECT GetAvgRating(6) AS AvgRatingForRestaurant1;
