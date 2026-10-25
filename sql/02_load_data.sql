-- 02_load_data.sql
USE opentable_app;

INSERT INTO Customer (FirstName, LastName, Email, Phone) VALUES
('Hana','Zare','hana.zare1@example.com','+1-404-531-3471'),
('Alex','Smith','alex.smith2@example.com','+1-404-604-1791'),
('Sam','Johnson','sam.johnson3@example.com','+1-404-274-9779'),
('Taylor','Brown','taylor.brown4@example.com','+1-404-296-6991'),
('Jordan','Davis','jordan.davis5@example.com','+1-404-796-1950'),
('Casey','Miller','casey.miller6@example.com','+1-404-719-4517'),
('Riley','Wilson','riley.wilson7@example.com','+1-404-238-2408'),
('Ava','Moore','ava.moore8@example.com','+1-404-644-7851'),
('Mia','Taylor','mia.taylor9@example.com','+1-404-271-4943'),
('Noah','Anderson','noah.anderson10@example.com','+1-404-292-7955'),
('Liam','Thomas','liam.thomas11@example.com','+1-404-260-3028'),
('Emma','Jackson','emma.jackson12@example.com','+1-404-428-2013'),
('Olivia','White','olivia.white13@example.com','+1-404-790-7499'),
('Ethan','Harris','ethan.harris14@example.com','+1-404-250-4622'),
('Sophia','Martin','sophia.martin15@example.com','+1-404-247-3181');

INSERT INTO Restaurant (Name,Cuisine,PriceLevel,Phone,Street,City,State,Zip) VALUES
('Garden House','Sushi',1,'+1-404-385-2688','325 Beacon Blvd','Boston','MA','02108'),
('Stone Bar','Steakhouse',3,'+1-404-777-1976','570 Mission St','Atlanta','GA','30305'),
('Stone Kitchen','French',4,'+1-404-570-5911','486 Beacon Ave','San Francisco','CA','94103'),
('Urban Kitchen','Steakhouse',1,'+1-404-551-8353','317 Beacon Ave','Boston','MA','02108'),
('Garden Bar','Persian',1,'+1-404-355-9011','438 Michigan Ave','Boston','MA','02108'),
('Moon Table','Persian',3,'+1-404-708-8474','721 Market Blvd','San Francisco','CA','94103'),
('Blue Table','Mexican',4,'+1-404-517-8301','72 Mission Blvd','Atlanta','GA','30305'),
('Garden Grill','American',3,'+1-404-372-2918','973 K Ave','Atlanta','GA','30305'),
('Oak Table','Steakhouse',3,'+1-404-600-9134','766 Michigan Ave','Chicago','IL','60611'),
('Blue Kitchen','French',4,'+1-404-763-5561','294 Michigan Ave','Boston','MA','02108'),
('Moon Bistro','American',2,'+1-404-437-4822','94 Michigan St','Chicago','IL','60611'),
('Cedar House','Indian',2,'+1-404-629-9758','298 Peachtree St','San Francisco','CA','94103'),
('River Bar','Indian',3,'+1-404-870-1884','717 Beacon Blvd','Chicago','IL','60611'),
('Oak Grill','Mediterranean',4,'+1-404-693-7560','418 K St','Washington','DC','20001'),
('Cedar Kitchen','Persian',2,'+1-404-815-1861','176 Peachtree Ave','Washington','DC','20001');

INSERT INTO DiningTable (RestaurantID, TableNumber, Capacity) VALUES
(1,1,2),(1,2,2),
(2,1,6),(2,2,2),
(3,1,6),(3,2,2),
(4,1,4),(4,2,6),
(5,1,2),(5,2,2),
(6,1,2),(6,2,6),
(7,1,4),(7,2,2),
(8,1,8),(8,2,4),
(9,1,4),(9,2,6),
(10,1,4),(10,2,4),
(11,1,2),(11,2,2),
(12,1,4),(12,2,4),
(13,1,4),(13,2,4),
(14,1,4),(14,2,2),
(15,1,2),(15,2,2);

INSERT INTO Reservation (CustomerID, RestaurantID, TableID, ReservationDateTime, PartySize, Status, CanceledAt) VALUES
(12,6,12,'2026-02-16 20:15:00',5,'COMPLETED',NULL),
(4,9,18,'2026-02-05 20:00:00',5,'COMPLETED',NULL),
(11,14,27,'2026-02-09 20:30:00',2,'COMPLETED',NULL),
(13,4,8,'2026-02-21 18:15:00',2,'CANCELED','2026-02-21 16:15:00'),
(12,13,25,'2026-02-07 20:45:00',3,'COMPLETED',NULL),
(1,13,26,'2026-02-16 19:15:00',6,'COMPLETED',NULL),
(8,13,26,'2026-02-12 18:15:00',2,'COMPLETED',NULL),
(8,4,8,'2026-02-07 19:00:00',4,'COMPLETED',NULL),
(13,11,21,'2026-02-04 19:15:00',4,'COMPLETED',NULL),
(7,13,26,'2026-02-03 20:45:00',4,'CANCELED','2026-02-03 18:45:00'),
(12,2,3,'2026-02-06 18:00:00',2,'CANCELED','2026-02-06 16:00:00'),
(13,11,21,'2026-02-20 20:45:00',6,'COMPLETED',NULL),
(3,9,17,'2026-02-01 18:00:00',5,'COMPLETED',NULL),
(7,14,27,'2026-02-07 18:30:00',2,'COMPLETED',NULL),
(9,4,8,'2026-02-09 20:45:00',2,'BOOKED',NULL),
(15,12,24,'2026-02-15 20:45:00',5,'BOOKED',NULL),
(9,3,5,'2026-02-15 18:00:00',2,'BOOKED',NULL),
(3,8,15,'2026-02-18 18:30:00',6,'CANCELED','2026-02-18 16:30:00'),
(13,13,25,'2026-02-18 18:15:00',2,'COMPLETED',NULL),
(1,13,25,'2026-02-17 19:00:00',2,'CANCELED','2026-02-17 17:00:00'),
(6,10,19,'2026-02-09 19:45:00',5,'BOOKED',NULL),
(12,9,18,'2026-02-18 18:45:00',2,'CANCELED','2026-02-18 16:45:00'),
(2,7,14,'2026-02-11 18:15:00',4,'BOOKED',NULL),
(4,11,22,'2026-02-04 18:30:00',2,'COMPLETED',NULL),
(15,3,6,'2026-02-08 20:00:00',4,'CANCELED','2026-02-08 18:00:00'),
(3,11,21,'2026-02-06 20:45:00',5,'CANCELED','2026-02-06 18:45:00'),
(6,7,13,'2026-02-12 19:00:00',6,'COMPLETED',NULL),
(1,6,12,'2026-02-15 20:00:00',4,'COMPLETED',NULL),
(9,10,20,'2026-02-17 18:00:00',2,'BOOKED',NULL),
(2,5,10,'2026-02-02 18:30:00',2,'CANCELED','2026-02-02 16:30:00');

INSERT INTO Review (ReservationID, Rating, Comment) VALUES
(1,4,'Great service and atmosphere.'),
(2,5,'Solid experience, good value.'),
(3,4,'Food was excellent; will return.'),
(5,5,'Food was excellent; will return.'),
(6,5,'Quick seating and tasty dishes.'),
(7,3,'Solid experience, good value.'),
(8,5,'Loved the flavors and friendly staff.'),
(9,3,'Loved the flavors and friendly staff.'),
(12,5,'Solid experience, good value.'),
(13,3,'Solid experience, good value.'),
(14,3,'Solid experience, good value.'),
(19,3,'Food was excellent; will return.'),
(24,4,'Great service and atmosphere.'),
(28,5,'Great service and atmosphere.'),
(29,4,'Great service and atmosphere.');

INSERT INTO Favorite (CustomerID, RestaurantID) VALUES
(3,1),(4,9),(4,15),(5,10),(9,11),
(1,3),(1,12),(4,2),(5,9),(9,7),
(13,4),(1,5),(6,13),(3,5),(5,11),
(5,8),(9,9),(1,1),(9,12),(15,15);

-- Counts (evidence)
SELECT COUNT(*) AS Customers   FROM Customer;
SELECT COUNT(*) AS Restaurants FROM Restaurant;
SELECT COUNT(*) AS Tables      FROM DiningTable;
SELECT COUNT(*) AS Reservations FROM Reservation;
SELECT COUNT(*) AS Reviews     FROM Review;
SELECT COUNT(*) AS Favorites   FROM Favorite;

