-- 02_price_per_sqft_by_area_and_type.sql
-- Price per square foot by micro-market (neighborhood) and property type.
-- Dialect: PostgreSQL / ANSI SQL.

SELECT
    borough_name,
    neighborhood,
    property_type,
    COUNT(*)                                            AS transaction_count,
    ROUND(AVG(price_per_sqft)::NUMERIC, 2)               AS avg_price_per_sqft,
    ROUND(
        (PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_per_sqft))::NUMERIC, 2
    )                                                    AS median_price_per_sqft,
    ROUND(MIN(price_per_sqft)::NUMERIC, 2)               AS min_price_per_sqft,
    ROUND(MAX(price_per_sqft)::NUMERIC, 2)               AS max_price_per_sqft
FROM sales_clean
GROUP BY borough_name, neighborhood, property_type
HAVING COUNT(*) >= 5
ORDER BY avg_price_per_sqft DESC;
