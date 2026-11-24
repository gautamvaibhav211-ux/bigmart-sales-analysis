-- Big Mart Sales Analysis | MySQL 8.0+
-- Table layout matches data/cleaned/bigmart_sales_cleaned.csv (same column order).

CREATE DATABASE IF NOT EXISTS bigmart_sales;
USE bigmart_sales;

DROP TABLE IF EXISTS sales;
CREATE TABLE sales (
    item_identifier           VARCHAR(15)   NOT NULL,
    item_weight               DECIMAL(7,3),
    item_fat_content          VARCHAR(15),
    item_visibility           DECIMAL(10,7),
    item_type                 VARCHAR(40),
    item_mrp                  DECIMAL(10,4),
    outlet_identifier         VARCHAR(10)   NOT NULL,
    outlet_establishment_year INT,
    outlet_size               VARCHAR(10),
    outlet_location_type      VARCHAR(10),
    outlet_type               VARCHAR(25),
    item_outlet_sales         DECIMAL(12,4),
    outlet_age                INT,
    item_category             VARCHAR(20),
    price_per_unit_weight     DECIMAL(10,2),
    mrp_tier                  VARCHAR(10),
    outlet_size_imputed       VARCHAR(3),   -- 'Yes' = size was missing in the raw data and was filled in
    PRIMARY KEY (item_identifier, outlet_identifier)
);

-- Load the cleaned CSV: use the Table Data Import Wizard in MySQL Workbench,
-- or enable LOCAL INFILE and run:
-- LOAD DATA LOCAL INFILE 'data/cleaned/bigmart_sales_cleaned.csv'
--     INTO TABLE sales
--     FIELDS TERMINATED BY ',' ENCLOSED BY '"'
--     LINES TERMINATED BY '\n'
--     IGNORE 1 ROWS;

CREATE INDEX idx_sales_outlet_type ON sales (outlet_type);
CREATE INDEX idx_sales_item_type   ON sales (item_type);
CREATE INDEX idx_sales_tier        ON sales (outlet_location_type);

-- Quick check after loading: expect 8523 rows.
-- SELECT COUNT(*) FROM sales;
