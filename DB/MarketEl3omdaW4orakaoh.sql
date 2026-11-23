IF DB_ID(N'Market_El3omda_w_4orakaoh') IS NULL
BEGIN
	CREATE DATABASE Market_El3omda_w_4orakaoh;
END;
GO

USE Market_El3omda_w_4orakaoh;
GO

IF OBJECT_ID(N'categories', N'U') IS NULL -- N: Unicode not ASCII, U: User-Defined Table
BEGIN
	CREATE TABLE categories(
		id			INTEGER NOT NULL,
		name		NVARCHAR(100) NOT NULL,
		description TEXT NULL,
		created_at  DATETIME NOT NULL CONSTRAINT DF_categories_created_at DEFAULT SYSDATETIME(),

		CONSTRAINT PK_categories	  PRIMARY KEY (id),
		CONSTRAINT UQ_categories_name UNIQUE (name)
	);
END;
GO

IF OBJECT_ID(N'products', N'U') IS NULL
BEGIN
	CREATE TABLE products (
		id				INTEGER NOT NULL,
		name			NVARCHAR(200) NOT NULL, -- تقبل عربي و إنحليزي
		brand			VARCHAR(100) NULL,
		sku				VARCHAR(50) NULL, -- Stock Keeping Unit
		barcode			VARCHAR(50) NULL,
		price			FLOAT NOT NULL,
		purchase_price  FLOAT NOT NULL	  CONSTRAINT DF_products_purchase_price DEFAULT 0,
		size			VARCHAR(100) NULL,
		category_id		INTEGER NULL,
		description		TEXT NULL,
		image_path		VARCHAR(500) NULL,
		min_stock_level INTEGER NOT NULL  CONSTRAINT DF_products_min_stock	    DEFAULT 10,
		shelf_location  VARCHAR(100) NULL,
		is_active		BIT NOT NULL	  CONSTRAINT DF_products_is_active		DEFAULT 1, -- BOOL VALUE
		created_at		DATETIME NOT NULL CONSTRAINT DF_products_created_at		DEFAULT SYSDATETIME(),
		updated_at		DATETIME NOT NULL CONSTRAINT DF_products_updated_at		DEFAULT SYSDATETIME(),
		production_date DATE NOT NULL,
		expiration_date DATE NOT NULL,

		CONSTRAINT PK_products			 PRIMARY KEY (id),
		CONSTRAINT FK_products_category  FOREIGN KEY (category_id) REFERENCES categories (id),
		CONSTRAINT CK_products_price	 CHECK (price >= 0),
		CONSTRAINT CK_products_cost		 CHECK (purchase_price >= 0),
		CONSTRAINT CK_products_min_stock CHECK (min_stock_level >= 0),
		CONSTRAINT CK_products_date		 CHECK (Expiration_Date > Production_Date)
	);
END;
GO

IF OBJECT_ID(N'inventory', N'U') IS NULL
BEGIN
	CREATE TABLE inventory(
		id				  INTEGER NOT NULL,
		product_id		  INTEGER NOT NULL,
		quantity_in_stock INTEGER NOT NULL  CONSTRAINT DF_inventory_qty		   DEFAULT 0,
		quantity_on_shelf INTEGER NULL,
		last_counted_at	  DATETIME NULL,
		updated_at		  DATETIME NOT NULL CONSTRAINT DF_inventory_updated_at DEFAULT SYSDATETIME(),

		CONSTRAINT PK_inventory			PRIMARY KEY (id),
		CONSTRAINT FK_inventory_product FOREIGN KEY (product_id) REFERENCES products (id),
		CONSTRAINT CK_inventory_qty     CHECK (quantity_in_stock >= 0),   -- stock can never go negative
		CONSTRAINT CK_inventory_shelf   CHECK (quantity_on_shelf IS NULL OR quantity_on_shelf >= 0)
	);
END;
GO

IF OBJECT_ID(N'stock_movements', N'U') IS NULL
BEGIN
	CREATE TABLE stock_movements(
		id				INTEGER NOT NULL,
		product_id		INTEGER NOT NULL,
		movement_type	VARCHAR(20) NOT NULL,
		quantity		INTEGER NOT NULL,
		reason			TEXT NULL,
		reference		VARCHAR(100) NULL,
		unit_cost		FLOAT NOT NULL    CONSTRAINT DF_stock_movements_unit_cost  DEFAULT 0,
		batch_number	VARCHAR(100) NULL,
		employee		VARCHAR(120) NULL,
		created_at		DATETIME NOT NULL CONSTRAINT DF_stock_movements_created_at DEFAULT SYSDATETIME(),
		expiration_date DATETIME NULL,

		CONSTRAINT PK_stock_movements			PRIMARY KEY (id),
		CONSTRAINT FK_stock_movements_product	FOREIGN KEY (product_id) REFERENCES products (id),
		CONSTRAINT CK_stock_movements_type		CHECK (movement_type IN ('RECEIVE', 'DELIVERY', 'SALE', 'WASTE', 'ADJUSTMENT', 'RETURN')),
		CONSTRAINT CK_stock_movements_qty		CHECK (quantity <> 0),
		CONSTRAINT CK_stock_movements_unit_cost CHECK (unit_cost >= 0)
	);
END;
GO

IF OBJECT_ID(N'sales', N'U') IS NULL
BEGIN
	CREATE TABLE sales (
	    id			 INTEGER NOT NULL,
	    sale_date	 DATETIME NOT NULL CONSTRAINT DF_sales_date DEFAULT SYSDATETIME(),
	    total_amount FLOAT NOT NULL,
	    source		 VARCHAR(20) NOT NULL,
	    notes		 TEXT NULL,
	    created_at	 DATETIME NOT NULL CONSTRAINT DF_sales_created_at DEFAULT SYSDATETIME(),

		CONSTRAINT PK_sales		   PRIMARY KEY (id),
		CONSTRAINT CK_sales_total  CHECK (total_amount >= 0),
		CONSTRAINT CK_sales_source CHECK (source IN ('MANUAL','POS'))
	);
END;
GO

IF OBJECT_ID(N'sale_items', N'U') IS NULL
BEGIN
	CREATE TABLE sale_items (
	    id		   INTEGER NOT NULL,
	    sale_id    INTEGER NOT NULL,
	    product_id INTEGER NOT NULL,
	    quantity   INTEGER NOT NULL,
	    unit_price FLOAT NOT NULL,
	    subtotal   FLOAT NOT NULL,

		CONSTRAINT PK_sale_items			PRIMARY KEY (id),
		CONSTRAINT FK_sale_items_sale_id	FOREIGN KEY (sale_id)    REFERENCES sales (id),
		CONSTRAINT FK_sale_items_product_id FOREIGN KEY (product_id) REFERENCES products (id),
		CONSTRAINT CK_sale_items_qty		CHECK (quantity > 0),
		CONSTRAINT CK_sale_items_price		CHECK (unit_price >= 0 AND subtotal >= 0),
		CONSTRAINT CK_sale_items_total		CHECK (subtotal = quantity * unit_price)
	);
END;
GO

IF OBJECT_ID(N'alerts', N'U') IS NULL
BEGIN
	CREATE TABLE alerts (
	    id		    INTEGER NOT NULL,
	    product_id  INTEGER NULL,
	    alert_type  VARCHAR(30) NOT NULL, -- LOW_STOCK, OUT_OF_STOCK, etc.
	    severity    VARCHAR(10) NOT NULL,
	    message     TEXT NOT NULL,
	    is_resolved BIT NOT NULL	  CONSTRAINT DF_alerts_is_resolved DEFAULT 0,
	    created_at  DATETIME NOT NULL CONSTRAINT DF_alerts_created_at  DEFAULT SYSDATETIME(),
	    resolved_at DATETIME NULL,

		CONSTRAINT PK_alerts			PRIMARY KEY (id),
		CONSTRAINT FK_alerts_product_id FOREIGN KEY (product_id) REFERENCES products (id),
		CONSTRAINT CK_alerts_severity   CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'))
	);
END;
GO

IF OBJECT_ID(N'restocking_tasks', N'U') IS NULL
BEGIN
	CREATE TABLE restocking_tasks (
	    id				INTEGER NOT NULL,
	    product_id		INTEGER NOT NULL,
	    quantity_needed INTEGER NOT NULL,
	    priority		VARCHAR(10) NOT NULL CONSTRAINT DF_restocking_priority   DEFAULT 'MEDIUM',
	    status			VARCHAR(20) NOT NULL CONSTRAINT DF_restocking_status     DEFAULT 'PENDING',
	    source			VARCHAR(30) NOT NULL CONSTRAINT DF_restocking_source     DEFAULT 'MANUAL',
	    assigned_to		VARCHAR(100) NULL,
	    created_at		DATETIME NOT NULL	 CONSTRAINT DF_restocking_created_at DEFAULT SYSDATETIME(),
	    completed_at	DATETIME NULL,

		CONSTRAINT PK_restocking_tasks			  PRIMARY KEY (id),
		CONSTRAINT FK_restocking_tasks_product_id FOREIGN KEY (product_id) REFERENCES products (id),
		CONSTRAINT CK_restocking_tasks_qty		  CHECK (quantity_needed > 0),
		CONSTRAINT CK_restocking_tasks_priority   CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')),
		CONSTRAINT CK_restocking_tasks_status	  CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'))
	);
END;
GO

IF OBJECT_ID(N'shelf_observations', N'U') IS NULL
BEGIN
	CREATE TABLE shelf_observations (
	    id			   INTEGER NOT NULL,
	    image_path	   NVARCHAR(500) NOT NULL,
	    shelf_location NVARCHAR(100) NULL,
	    status		   VARCHAR(20) NOT NULL CONSTRAINT DF_shelf_obs_status		DEFAULT 'PENDING',
	    notes		   TEXT NULL,
	    captured_at	   DATETIME NOT NULL    CONSTRAINT DF_shelf_obs_captured_at DEFAULT SYSDATETIME(),
	    processed_at   DATETIME NULL,

		CONSTRAINT PK_shelf_observations		PRIMARY KEY (id),
		CONSTRAINT CK_shelf_observations_status CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'))
	);
END;
GO

IF OBJECT_ID(N'detections', N'U') IS NULL
BEGIN
	CREATE TABLE detections (
	    id				  INTEGER NOT NULL,
	    observation_id	  INTEGER NOT NULL,
	    product_id		  INTEGER NULL,
	    label			  VARCHAR(200) NOT NULL,
	    confidence		  FLOAT NOT NULL,
	    bbox_x			  FLOAT NOT NULL,
	    bbox_y			  FLOAT NOT NULL,
	    bbox_width		  FLOAT NOT NULL,
	    bbox_height		  FLOAT NOT NULL,
	    status			  VARCHAR(20) NOT NULL,
	    verified_quantity INTEGER NULL,
	    employee_notes	  TEXT NULL,
	    reviewed_at		  DATETIME NULL,
		
		CONSTRAINT PK_detections				PRIMARY KEY (id),
		CONSTRAINT FK_detections_observation_id FOREIGN KEY (observation_id) REFERENCES shelf_observations (id),
		CONSTRAINT FK_detections_product_id		FOREIGN KEY (product_id)	 REFERENCES products (id),
		CONSTRAINT CK_detections_confidence		CHECK (confidence BETWEEN 0 AND 1),
		CONSTRAINT CK_detections_bbox			CHECK (bbox_x >= 0 AND bbox_y >= 0 AND bbox_width >= 0 AND bbox_height >= 0),
		CONSTRAINT CK_detections_status			CHECK (status IN ('PENDING', 'CONFIRMED', 'CORRECTED', 'REJECTED')),
		CONSTRAINT CK_detections_verified		CHECK (verified_quantity IS NULL OR verified_quantity >= 0)
	);
END;
GO

IF OBJECT_ID(N'ai_conversations', N'U') IS NULL
BEGIN
	CREATE TABLE ai_conversations (
	    id		   INTEGER NOT NULL,
	    session_id VARCHAR(50) NOT NULL,
	    role	   VARCHAR(20) NOT NULL,
	    content    TEXT NOT NULL,
	    tool_calls TEXT NULL,
	    created_at DATETIME NOT NULL CONSTRAINT DF_ai_conversations_created_at DEFAULT SYSDATETIME(),

		CONSTRAINT PK_ai_conversations		PRIMARY KEY (id),
		CONSTRAINT CK_ai_conversations_role CHECK (role IN ('user','assistant','system'))
	);
END;
GO

-- We've Created [Indices] so queries execute fast in the backend
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_products_barcode' AND object_id = OBJECT_ID(N'products'))
BEGIN
	CREATE UNIQUE INDEX UX_products_barcode
		ON products (barcode) WHERE barcode IS NOT NULL;
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_products_sku' AND object_id = OBJECT_ID(N'products'))
BEGIN
	CREATE UNIQUE INDEX UX_products_sku
		ON products (sku) WHERE sku IS NOT NULL;
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_products_name' AND object_id = OBJECT_ID(N'products'))
BEGIN
	CREATE INDEX IX_products_name
		ON products (name) INCLUDE (barcode, price, is_active);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_products_category_id' AND object_id = OBJECT_ID(N'products'))
BEGIN
	CREATE INDEX IX_products_category_id
		ON products (category_id);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_inventory_product_id' AND object_id = OBJECT_ID(N'inventory'))
BEGIN
	CREATE UNIQUE INDEX UX_inventory_product_id
		ON inventory (product_id) INCLUDE (quantity_in_stock, quantity_on_shelf);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_stock_movements_product_id' AND object_id = OBJECT_ID(N'stock_movements'))
BEGIN
	CREATE INDEX IX_stock_movements_product_id
	    ON stock_movements (product_id);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_stock_movements_movement_type' AND object_id = OBJECT_ID(N'stock_movements'))
BEGIN
	CREATE INDEX IX_stock_movements_movement_type
		ON stock_movements (movement_type);
END;
GO

-- Expiry alerts: only rows that actually have an expiration date are indexed
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_stock_movements_expiration' AND object_id = OBJECT_ID(N'stock_movements'))
BEGIN
	CREATE INDEX IX_stock_movements_expiration 
		ON stock_movements (expiration_date) INCLUDE (product_id, batch_number, quantity) WHERE expiration_date IS NOT NULL;
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_sale_items_sale_id' AND object_id = OBJECT_ID(N'sale_items'))
BEGIN
	CREATE INDEX IX_sale_items_sale_id ON
		sale_items (sale_id);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_sale_items_product_id' AND object_id = OBJECT_ID(N'sale_items'))
BEGIN
	CREATE INDEX IX_sale_items_product_id
		ON sale_items (product_id);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_alerts_product_id' AND object_id = OBJECT_ID(N'alerts'))
BEGIN
	CREATE INDEX IX_alerts_product_id
		ON alerts (product_id);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_alerts_is_resolved' AND object_id = OBJECT_ID(N'alerts'))
BEGIN
	CREATE INDEX IX_alerts_is_resolved
		ON alerts (is_resolved);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_restocking_tasks_product_id' AND object_id = OBJECT_ID(N'restocking_tasks'))
BEGIN
	CREATE INDEX IX_restocking_tasks_product_id
		ON restocking_tasks (product_id);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_detections_observation_id' AND object_id = OBJECT_ID(N'detections'))
BEGIN
	CREATE INDEX IX_detections_observation_id
		ON detections (observation_id);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_detections_product_id' AND object_id = OBJECT_ID(N'detections'))
BEGIN
	CREATE INDEX IX_detections_product_id
		ON detections (product_id);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_ai_conversations_session_id' AND object_id = OBJECT_ID(N'ai_conversations'))
BEGIN
	CREATE INDEX IX_ai_conversations_session_id
		ON ai_conversations (session_id);
END;
GO

												-- TESTING ONLY (NOT THE ACTUAL DATA) --
USE Market_El3omda_w_4orakaoh;
GO

SET NOCOUNT ON;
GO

-- 1. Clean slate (children first)
DELETE FROM alerts;
DELETE FROM sale_items;
DELETE FROM sales;
DELETE FROM stock_movements;
DELETE FROM inventory;
DELETE FROM products;
DELETE FROM categories;
GO

-- 2. Sample data
INSERT INTO categories (id, name) VALUES
    (1, N'Snacks'),
    (2, N'Soft Drinks'),
    (3, N'Dairy');

INSERT INTO products
    (id, name, brand, sku, barcode, price, purchase_price, category_id,
     min_stock_level, shelf_location, production_date, expiration_date)
VALUES
    (1, N'Big Chips - Cheese',   N'Big Chips', 'BC-CHS',  '6221000000011', 10.00,  7.00, 1, 10, N'A1', '20261119', '20271119'),
    (2, N'V-Cola - توت',         N'Benefit Company for Healthy Food and Beverage', 'VC-BRY', '6221000000013', 15.00, 11.00, 2, 10, N'B1', '20261119', '20270619'),
    (3, N'V-Cola - كولا',        N'Benefit Company for Healthy Food and Beverage', 'VC-COL', '6221000000014', 14.50, 10.50, 2, 10, N'B1', '20261119', '20270719'),
    (4, N'Molto Twist',          N'Edita',     'MT-001',  '0062210000000', 25.00, 19.00, 1, 10, N'A2', '20261119', '20270819'),
    (5, N'Twinkies - Double Cream', N'Edita',  'TW-DBL',  '0062210000001', 25.00, 19.00, 1, 10, N'A2', '20261119', '20270919'),
    (6, N'Fresh Milk 1L',        N'Local Dairy', 'MLK-1L', '6221000000099', 40.00, 32.00, 3,  5, N'C1', '20261115', '20261201');

-- Starting stock: #3 is LOW (8 <= 10), #4 is OUT (0), #6 expires soon
INSERT INTO inventory (id, product_id, quantity_in_stock, quantity_on_shelf) VALUES
    (1, 1, 50, 30),
    (2, 2, 30, 20),
    (3, 3,  8,  8),
    (4, 4,  0,  0),
    (5, 5, 20, 15),
    (6, 6, 12, 12);

-- Matching RECEIVE movements, with batch + expiry
INSERT INTO stock_movements
    (id, product_id, movement_type, quantity, reason, reference, unit_cost, batch_number, employee, expiration_date)
VALUES
    (1, 1, 'RECEIVE', 50, N'Initial stock', 'PO-1001', 7.00,  'B-CHS-01', N'Ahmed', '20271119'),
    (2, 2, 'RECEIVE', 30, N'Initial stock', 'PO-1001', 11.00, 'B-BRY-01', N'Ahmed', '20270619'),
    (3, 3, 'RECEIVE', 8,  N'Initial stock', 'PO-1002', 10.50, 'B-COL-01', N'Ahmed', '20270719'),
    (4, 5, 'RECEIVE', 20, N'Initial stock', 'PO-1002', 19.00, 'B-TW-01',  N'Ahmed', '20270919'),
    (5, 6, 'RECEIVE', 12, N'Initial stock', 'PO-1003', 32.00, 'B-MLK-01', N'Ahmed', '20261201');
GO

-- 3. A sale: items + stock decrement in ONE transaction
--	2 x Big Chips (10.00) + 1 x V-Cola كولا (14.50) = 34.50
SET XACT_ABORT ON;
BEGIN TRY
    BEGIN TRAN;

    INSERT INTO sales (id, sale_date, total_amount, source, created_at)
    VALUES (1, SYSDATETIME(), 34.50, 'POS', SYSDATETIME());

    INSERT INTO sale_items (id, sale_id, product_id, quantity, unit_price, subtotal) VALUES
        (1, 1, 1, 2, 10.00, 20.00),
        (2, 1, 3, 1, 14.50, 14.50);

    -- Guarded decrement: touches 0 rows if there isn't enough stock
    UPDATE inventory
       SET quantity_in_stock = quantity_in_stock - 2, updated_at = SYSDATETIME()
     WHERE product_id = 1 AND quantity_in_stock >= 2;
    IF @@ROWCOUNT = 0 THROW 50001, 'Not enough stock for product 1', 1;

    UPDATE inventory
       SET quantity_in_stock = quantity_in_stock - 1, updated_at = SYSDATETIME()
     WHERE product_id = 3 AND quantity_in_stock >= 1;
    IF @@ROWCOUNT = 0 THROW 50001, 'Not enough stock for product 3', 1;

    INSERT INTO stock_movements (id, product_id, movement_type, quantity, reference, employee) VALUES
        (6, 1, 'SALE', -2, 'SALE-1', N'Cashier 1'),
        (7, 3, 'SALE', -1, 'SALE-1', N'Cashier 1');

    COMMIT;
    PRINT 'PASS: sale committed';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    PRINT 'FAIL: sale rolled back - ' + ERROR_MESSAGE();
END CATCH;
GO

-- 4. Constraint tests: every one of these SHOULD be rejected
SET XACT_ABORT OFF;

-- 4.1 Overselling must be blocked (stock can never go negative)
BEGIN TRY
    UPDATE inventory SET quantity_in_stock = quantity_in_stock - 999 WHERE product_id = 1;
    PRINT 'FAIL 4.1: negative stock was allowed';
END TRY
BEGIN CATCH PRINT 'PASS 4.1: negative stock rejected'; END CATCH;

-- 4.2 Duplicate barcode
BEGIN TRY
    INSERT INTO products (id, name, barcode, price, production_date, expiration_date)
    VALUES (90, N'Dup Barcode', '6221000000011', 5, '20261101', '20271101');
    PRINT 'FAIL 4.2: duplicate barcode was allowed';
END TRY
BEGIN CATCH PRINT 'PASS 4.2: duplicate barcode rejected'; END CATCH;

-- 4.4 Expiry before production
BEGIN TRY
    INSERT INTO products (id, name, barcode, price, production_date, expiration_date)
    VALUES (91, N'Bad Dates', '111', 5, '20271101', '20261101');
    PRINT 'FAIL 4.3: bad dates were allowed';
END TRY
BEGIN CATCH PRINT 'PASS 4.3: expiry <= production rejected'; END CATCH;

-- 4.4 Negative price
BEGIN TRY
    INSERT INTO products (id, name, barcode, price, production_date, expiration_date)
    VALUES (92, N'Neg Price', '222', -1, '20261101', '20271101');
    PRINT 'FAIL 4.4: negative price was allowed';
END TRY
BEGIN CATCH PRINT 'PASS 4.4: negative price rejected'; END CATCH;

-- 4.5 Invalid movement type
BEGIN TRY
    INSERT INTO stock_movements (id, product_id, movement_type, quantity)
    VALUES (99, 1, 'STOLEN', -1);
    PRINT 'FAIL 4.5: invalid movement type was allowed';
END TRY
BEGIN CATCH PRINT 'PASS 4.5: invalid movement type rejected'; END CATCH;

-- 4.6 Zero-quantity sale item
BEGIN TRY
    INSERT INTO sale_items (id, sale_id, product_id, quantity, unit_price, subtotal)
    VALUES (99, 1, 1, 0, 10, 0);
    PRINT 'FAIL 4.6: zero quantity was allowed';
END TRY
BEGIN CATCH PRINT 'PASS 4.6: zero quantity rejected'; END CATCH;

-- 4.7 Unknown product in a foreign key
BEGIN TRY
    INSERT INTO inventory (id, product_id, quantity_in_stock) VALUES (99, 12345, 1);
    PRINT 'FAIL 4.7: orphan inventory row was allowed';
END TRY
BEGIN CATCH PRINT 'PASS 4.7: foreign key rejected orphan row'; END CATCH;

-- 4.8 Two inventory rows for the same product (unique index)
BEGIN TRY
    INSERT INTO inventory (id, product_id, quantity_in_stock) VALUES (98, 1, 5);
    PRINT 'FAIL 4.8: duplicate inventory row was allowed';
END TRY
BEGIN CATCH PRINT 'PASS 4.8: duplicate inventory row rejected'; END CATCH;

-- 4.9 Arabic text round-trips correctly
IF EXISTS (SELECT 1 FROM products WHERE id = 3 AND name = N'V-Cola - كولا')
    PRINT 'PASS 4.9: Arabic name stored and matched';
ELSE
    PRINT 'FAIL 4.9: Arabic name was corrupted';
GO

-- 5. Functional queries

-- 5.1 Current stock for every product
SELECT p.id, p.name, i.quantity_in_stock, i.quantity_on_shelf, p.min_stock_level
FROM products p
JOIN inventory i ON i.product_id = p.id
ORDER BY p.id;

-- 5.2 Stock of one product by barcode (what the scanner would ask)
SELECT p.name, i.quantity_in_stock
FROM products p
JOIN inventory i ON i.product_id = p.id
WHERE p.barcode = '6221000000014';

-- 5.3 Low / out-of-stock products
SELECT p.id, p.name, i.quantity_in_stock, p.min_stock_level,
       CASE WHEN i.quantity_in_stock = 0 THEN 'OUT_OF_STOCK' ELSE 'LOW_STOCK' END AS alert_type
FROM products p
JOIN inventory i ON i.product_id = p.id
WHERE p.is_active = 1 AND i.quantity_in_stock <= p.min_stock_level;

-- 5.4 Days left before expiry (from TODAY, not from production date)
SELECT p.id, p.name, p.expiration_date,
       DATEDIFF(DAY, CAST(GETDATE() AS DATE), p.expiration_date) AS days_left
FROM products p
JOIN inventory i ON i.product_id = p.id
WHERE i.quantity_in_stock > 0
ORDER BY days_left;

-- 5.5 Batches expiring within 30 days (uses IX_stock_movements_expiration)
SELECT sm.product_id, p.name, sm.batch_number, sm.quantity AS received_qty, sm.expiration_date,
       DATEDIFF(DAY, CAST(GETDATE() AS DATE), sm.expiration_date) AS days_left
FROM stock_movements sm
JOIN products p ON p.id = sm.product_id
WHERE sm.expiration_date IS NOT NULL
  AND sm.expiration_date <= DATEADD(DAY, 30, CAST(GETDATE() AS DATE))
ORDER BY sm.expiration_date;

-- 5.6 Sale receipt
SELECT s.id AS sale_id, s.sale_date, p.name, si.quantity, si.unit_price, si.subtotal, s.total_amount
FROM sales s
JOIN sale_items si ON si.sale_id = s.id
JOIN products p    ON p.id = si.product_id
WHERE s.id = 1;

-- 5.7 Integrity check: sale total must equal the sum of its items (expect 0 rows)
SELECT s.id, s.total_amount, SUM(si.subtotal) AS items_total
FROM sales s
JOIN sale_items si ON si.sale_id = s.id
GROUP BY s.id, s.total_amount
HAVING ABS(s.total_amount - SUM(si.subtotal)) > 0.001;

-- 5.8 Integrity check: inventory must equal the sum of stock movements
--     (expect 0 rows; products 2 and 4 have no matching movements in this sample,
--      so they WILL appear - that itself is a useful reminder to log every change)
SELECT i.product_id, i.quantity_in_stock AS inventory_qty,
       ISNULL(SUM(sm.quantity), 0)       AS movements_qty
FROM inventory i
LEFT JOIN stock_movements sm ON sm.product_id = i.product_id
GROUP BY i.product_id, i.quantity_in_stock
HAVING i.quantity_in_stock <> ISNULL(SUM(sm.quantity), 0);

-- 5.9 Best sellers
SELECT p.name, SUM(si.quantity) AS units_sold, SUM(si.subtotal) AS revenue
FROM sale_items si
JOIN products p ON p.id = si.product_id
GROUP BY p.name
ORDER BY units_sold DESC;
GO

-- 6. Generate alerts from the data (no duplicates)
INSERT INTO alerts (id, product_id, alert_type, severity, message)
SELECT 1000 + ROW_NUMBER() OVER (ORDER BY p.id),
       p.id,
       CASE WHEN i.quantity_in_stock = 0 THEN 'OUT_OF_STOCK' ELSE 'LOW_STOCK' END,
       CASE WHEN i.quantity_in_stock = 0 THEN 'CRITICAL' ELSE 'MEDIUM' END,
       CONCAT(N'Stock for ', p.name, N' is ', i.quantity_in_stock, N' (min ', p.min_stock_level, N')')
FROM products p
JOIN inventory i ON i.product_id = p.id
WHERE i.quantity_in_stock <= p.min_stock_level
  AND NOT EXISTS (SELECT 1 FROM alerts a
                  WHERE a.product_id = p.id AND a.is_resolved = 0
                    AND a.alert_type IN ('LOW_STOCK', 'OUT_OF_STOCK'));

SELECT a.id, p.name, a.alert_type, a.severity, a.message, a.is_resolved
FROM alerts a
LEFT JOIN products p ON p.id = a.product_id
ORDER BY a.id;
GO
