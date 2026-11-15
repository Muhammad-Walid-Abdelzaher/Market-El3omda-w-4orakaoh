IF DB_ID(N'Market_El3omda_w_4orakaoh') IS NULL
BEGIN
	CREATE DATABASE Market_El3omda_w_4orakaoh;
END;
GO

USE Market_El3omda_w_4orakaoh;
GO

IF OBJECT_ID(N'Products', N'U') IS NULL
BEGIN
	CREATE TABLE Products (
		Product_ID VARCHAR(20) NOT NULL,
		Name NVARCHAR(100) NOT NULL, -- تقبل عربي و إنحليزي
		Company VARCHAR(60) NOT NULL,
		Category VARCHAR(50) NOT NULL,
		Production_Date DATE NOT NULL,
		Expiration_Date DATE NOT NULL,
		Price DECIMAL(6,2), -- أغلي حاجة ممكن تُشتري قيمتها: 9999.99
		Sold INT NOT NULL CONSTRAINT DF_Product_Sold DEFAULT 0,

		CONSTRAINT PK_Product PRIMARY KEY (Product_ID) WITH (IGNORE_DUP_KEY = ON),
		CONSTRAINT CK_Product_Sold CHECK (Sold IN (0,1)),
		CONSTRAINT CK_Product_Price CHECK (Price >= 0),
		CONSTRAINT CK_Product_Date CHECK (Expiration_Date > Production_Date)
	);
END;
GO

-- We've Created [Index] so quantity/COUNT queries execute fast in the backend
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Product_Name_Sold' AND object_id = OBJECT_ID(N'Products'))
BEGIN
	CREATE INDEX IX_Product_Name_Sold ON Products (Name,Sold);
END;
GO

SET DATEFORMAT dmy;
-- Sample Data
INSERT INTO Products (Product_ID,
					  Name,
					  Company,
					  Category,
					  Production_Date,
					  Expiration_Date,
					  Price)
			VALUES   ('6221000000011', N'Big Chips - Cheese', 'Big Chips', 'Snacks', '19-11-2026', '19-11-2027', 10.00),
					 ('6221000000012', N'Big Chips - Cheese', 'Big Chips', 'Snacks', '19-11-2026', '19-11-2027', 10.00),
					 ('6221000000013', N'V-Cola - توت', 'Benefit Company for Healthy Food and Beverage', 'Soft Drinks', '19-11-2026', '19-6-2027', 15.00),
					 ('6221000000014', N'V-Cola - كولا', 'Benefit Company for Healthy Food and Beverage', 'Soft Drinks', '19-11-2026', '19-7-2027', 14.50),
					 ('0062210000000', N'Molto Twist', 'Edita', 'Snacks', '19-11-2026', '19-8-2027', 25.00),
					 ('0062210000001', N'Twinkies - Double Cream', 'Edita', 'Snacks', '19-11-2026', '19-9-2027', 25.00);
GO

-- Test Commands Used:

select * from Products
-- delete from products where product_id = 6221000000013000
-- select * from Products
-- update products set Expiration_Date = '19-6-2027' where Product_ID = '6221000000013'
-- update products set Expiration_Date = '19-7-2027' where Product_ID = '6221000000014'
-- update products set Expiration_Date = '19-8-2027' where Product_ID = '0062210000000'
-- update products set Expiration_Date = '19-9-2027' where Product_ID = '0062210000001'


-- Quantity of one product (what's left in stock)
SELECT COUNT(*) AS Qty FROM Products WHERE Name = N'V-Cola - كولا' AND Sold = 0;

-- Quantity of every product
SELECT Name, COUNT(*) AS Qty FROM Products WHERE Sold = 0 GROUP BY Name;

-- Sell a product after successful payment (the "auto decrement")
-- If Qty = 0, the item was already sold or the code doesn't exist.
UPDATE Products SET Sold = 1 WHERE product_id = '6221000000011' AND Sold = 0;

-- Days left before expiry (for the alerts logic)
SELECT product_id, Name, DATEDIFF(DAY, Production_Date, Expiration_Date) AS Days_Left FROM Products WHERE Sold = 0 ORDER BY Days_Left;
