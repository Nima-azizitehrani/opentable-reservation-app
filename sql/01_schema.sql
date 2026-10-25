-- 01_schema.sql
-- OpenTable schema (Customer, Restaurant, DiningTable, Reservation, Review, Favorite)

DROP DATABASE IF EXISTS opentable_app;
CREATE DATABASE opentable_app;
USE opentable_app;

-- ---------- Customer ----------
CREATE TABLE Customer (
  CustomerID INT AUTO_INCREMENT PRIMARY KEY,
  FirstName  VARCHAR(50) NOT NULL,
  LastName   VARCHAR(50) NOT NULL,
  Email      VARCHAR(255) NOT NULL UNIQUE,
  Phone      VARCHAR(25),
  CreatedAt  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------- Restaurant ----------
CREATE TABLE Restaurant (
  RestaurantID INT AUTO_INCREMENT PRIMARY KEY,
  Name       VARCHAR(120) NOT NULL,
  Cuisine    VARCHAR(50)  NOT NULL,
  PriceLevel TINYINT NOT NULL,
  Phone      VARCHAR(25),
  Street     VARCHAR(120),
  City       VARCHAR(60) NOT NULL,
  State      CHAR(2) NOT NULL,
  Zip        VARCHAR(10),
  CreatedAt  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK (PriceLevel BETWEEN 1 AND 4)
);

-- ---------- DiningTable ----------
CREATE TABLE DiningTable (
  TableID INT AUTO_INCREMENT PRIMARY KEY,
  RestaurantID INT NOT NULL,
  TableNumber  INT NOT NULL,
  Capacity     INT NOT NULL,
  UNIQUE (RestaurantID, TableNumber),
  FOREIGN KEY (RestaurantID) REFERENCES Restaurant(RestaurantID),
  CHECK (Capacity > 0)
);

-- ---------- Reservation ----------
CREATE TABLE Reservation (
  ReservationID INT AUTO_INCREMENT PRIMARY KEY,
  CustomerID INT NOT NULL,
  RestaurantID INT NOT NULL,
  TableID INT NOT NULL,
  ReservationDateTime DATETIME NOT NULL,
  PartySize INT NOT NULL,
  Status VARCHAR(10) NOT NULL DEFAULT 'BOOKED',
  CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CanceledAt DATETIME NULL,

  FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID),
  FOREIGN KEY (RestaurantID) REFERENCES Restaurant(RestaurantID),
  FOREIGN KEY (TableID) REFERENCES DiningTable(TableID),

  CHECK (PartySize > 0),
  CHECK (Status IN ('BOOKED','COMPLETED','CANCELED'))
);

-- ---------- Review ----------
CREATE TABLE Review (
  ReviewID INT AUTO_INCREMENT PRIMARY KEY,
  ReservationID INT NOT NULL UNIQUE,
  Rating INT NOT NULL,
  Comment VARCHAR(255),
  CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (ReservationID) REFERENCES Reservation(ReservationID),
  CHECK (Rating BETWEEN 1 AND 5)
);

-- ---------- Favorite ----------
CREATE TABLE Favorite (
  CustomerID INT NOT NULL,
  RestaurantID INT NOT NULL,
  CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (CustomerID, RestaurantID),
  FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID),
  FOREIGN KEY (RestaurantID) REFERENCES Restaurant(RestaurantID)
);

SHOW TABLES;
