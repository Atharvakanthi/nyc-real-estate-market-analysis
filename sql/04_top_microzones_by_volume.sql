-- 04_top_microzones_by_volume.sql
-- Top 20 neighborhoods ("micro-markets") by transaction volume, with
-- summary pricing stats for each.
-- Dialect: PostgreSQL / ANSI SQL.

SELECT
    borough_name,
    neighborhood,
    COUNT(*)                                                AS transaction_count,
    ROUND(SUM(sale_price)::NUMERIC, 0)                      AS total_sales_value,
    ROUND(AVG(sale_price)::NUMERIC, 0)                      AS avg_sale_price,
    ROUND(AVG(price_per_sqft)::NUMERIC, 2)                  AS avg_price_per_sqft
FROM sales_clean
GROUP BY borough_name, neighborhood
ORDER BY transaction_count DESC
LIMIT 20;
