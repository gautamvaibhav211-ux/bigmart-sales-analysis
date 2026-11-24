-- Business questions for the Big Mart Sales Analysis | MySQL 8.0+
-- All figures are recorded sales for 2013 in this dataset (item-outlet records).
USE bigmart_sales;

-- 1) Outlet-format performance
SELECT outlet_type,
       COUNT(*)                          AS records,
       ROUND(SUM(item_outlet_sales), 2)  AS total_sales,
       ROUND(AVG(item_outlet_sales), 2)  AS avg_sales
FROM sales
GROUP BY outlet_type
ORDER BY total_sales DESC;

-- 2) Individual outlet ranking
SELECT outlet_identifier, outlet_type, outlet_location_type,
       ROUND(SUM(item_outlet_sales), 2)                 AS total_sales,
       RANK() OVER (ORDER BY SUM(item_outlet_sales) DESC) AS sales_rank
FROM sales
GROUP BY outlet_identifier, outlet_type, outlet_location_type
ORDER BY sales_rank;

-- 3) Average sales by city tier
SELECT outlet_location_type,
       COUNT(DISTINCT outlet_identifier) AS outlets,
       ROUND(AVG(item_outlet_sales), 2)  AS avg_sales,
       ROUND(SUM(item_outlet_sales), 2)  AS total_sales
FROM sales
GROUP BY outlet_location_type
ORDER BY avg_sales DESC;

-- 4) Item-category sales share
SELECT item_category,
       ROUND(SUM(item_outlet_sales), 2) AS total_sales,
       ROUND(100 * SUM(item_outlet_sales) / SUM(SUM(item_outlet_sales)) OVER (), 2) AS pct_total
FROM sales
GROUP BY item_category
ORDER BY total_sales DESC;

-- 5) Top item types
SELECT item_type,
       ROUND(SUM(item_outlet_sales), 2) AS total_sales,
       COUNT(*)                         AS records
FROM sales
GROUP BY item_type
ORDER BY total_sales DESC
LIMIT 10;

-- 6) Price-tier performance
SELECT mrp_tier,
       COUNT(*)                         AS records,
       ROUND(AVG(item_mrp), 2)          AS avg_mrp,
       ROUND(AVG(item_outlet_sales), 2) AS avg_sales
FROM sales
GROUP BY mrp_tier
ORDER BY avg_mrp;

-- 7) Outlet size comparison
-- Caution: outlet_size is missing for 3 whole outlets in the raw data (2,410 records),
-- so those sizes are filled-in assumptions. outlet_size_imputed separates them out.
SELECT outlet_size, outlet_size_imputed,
       COUNT(DISTINCT outlet_identifier) AS outlets,
       ROUND(AVG(item_outlet_sales), 2)  AS avg_sales,
       ROUND(SUM(item_outlet_sales), 2)  AS total_sales
FROM sales
GROUP BY outlet_size, outlet_size_imputed
ORDER BY outlet_size, outlet_size_imputed;

-- 8) Fat-content comparison: food and drink items only, because non-consumables are labelled Non-Edible
SELECT item_fat_content,
       COUNT(*)                         AS records,
       ROUND(SUM(item_outlet_sales), 2) AS total_sales,
       ROUND(AVG(item_outlet_sales), 2) AS avg_sales
FROM sales
WHERE item_fat_content <> 'Non-Edible'
GROUP BY item_fat_content
ORDER BY total_sales DESC;

-- 9) Establishment-year comparison
SELECT outlet_establishment_year, outlet_age,
       COUNT(DISTINCT outlet_identifier) AS outlets,
       ROUND(AVG(item_outlet_sales), 2)  AS avg_sales
FROM sales
GROUP BY outlet_establishment_year, outlet_age
ORDER BY outlet_establishment_year;

-- 10) Grocery stores vs supermarkets
SELECT CASE WHEN outlet_type = 'Grocery Store' THEN 'Grocery Store' ELSE 'Supermarket' END AS format_group,
       COUNT(*)                         AS records,
       ROUND(SUM(item_outlet_sales), 2) AS total_sales,
       ROUND(AVG(item_outlet_sales), 2) AS avg_sales
FROM sales
GROUP BY format_group;

-- 11) Top products across outlets
SELECT item_identifier, item_type,
       ROUND(SUM(item_outlet_sales), 2)  AS total_sales,
       COUNT(DISTINCT outlet_identifier) AS outlets_sold_in
FROM sales
GROUP BY item_identifier, item_type
ORDER BY total_sales DESC
LIMIT 10;

-- 12) Shelf-visibility buckets
SELECT CASE WHEN item_visibility < 0.05 THEN 'Low (<5%)'
            WHEN item_visibility < 0.10 THEN 'Medium (5-10%)'
            WHEN item_visibility < 0.15 THEN 'High (10-15%)'
            ELSE 'Very High (15%+)' END AS visibility_bucket,
       COUNT(*)                         AS records,
       ROUND(AVG(item_outlet_sales), 2) AS avg_sales
FROM sales
GROUP BY visibility_bucket
ORDER BY MIN(item_visibility);

-- 13) Outlet concentration: share of dataset sales from each outlet
SELECT outlet_identifier,
       ROUND(SUM(item_outlet_sales), 2) AS total_sales,
       ROUND(100 * SUM(item_outlet_sales) / SUM(SUM(item_outlet_sales)) OVER (), 2) AS pct_total
FROM sales
GROUP BY outlet_identifier
ORDER BY total_sales DESC;

-- 14) Product presence across outlets (descriptive only, not customer retention)
SELECT item_identifier,
       COUNT(DISTINCT outlet_identifier) AS outlet_count,
       ROUND(SUM(item_outlet_sales), 2)  AS total_sales
FROM sales
GROUP BY item_identifier
ORDER BY outlet_count DESC, total_sales DESC
LIMIT 20;

-- 15) Top 3 item types within each item category (CTEs + window function)
WITH item_type_sales AS (
    SELECT item_category, item_type, SUM(item_outlet_sales) AS total_sales
    FROM sales
    GROUP BY item_category, item_type
),
ranked_item_types AS (
    SELECT item_category, item_type,
           ROUND(total_sales, 2) AS total_sales,
           ROW_NUMBER() OVER (PARTITION BY item_category ORDER BY total_sales DESC) AS category_rank
    FROM item_type_sales
)
SELECT item_category, item_type, total_sales, category_rank
FROM ranked_item_types
WHERE category_rank <= 3
ORDER BY item_category, category_rank;

-- 16) Data-quality check: record counts and missing values (expect 8523 rows, 0 missing)
SELECT COUNT(*)                                      AS total_records,
       COUNT(DISTINCT item_identifier)               AS unique_products,
       COUNT(DISTINCT outlet_identifier)             AS outlets,
       SUM(item_weight IS NULL)                      AS missing_weight,
       SUM(outlet_size IS NULL)                      AS missing_outlet_size,
       SUM(item_visibility = 0)                      AS zero_visibility,
       SUM(outlet_size_imputed = 'Yes')              AS outlet_size_filled_in
FROM sales;
