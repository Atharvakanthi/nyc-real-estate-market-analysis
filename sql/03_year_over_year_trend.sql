-- 03_year_over_year_trend.sql
-- Year-over-year change in median price and median price-per-sqft, by borough.
-- Dialect: PostgreSQL / ANSI SQL (uses the LAG() window function).

WITH yearly AS (
    SELECT
        borough_name,
        sale_year,
        COUNT(*)                                                            AS transaction_count,
        ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sale_price))::NUMERIC, 2)        AS median_price,
        ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_per_sqft))::NUMERIC, 2)    AS median_price_per_sqft
    FROM sales_clean
    GROUP BY borough_name, sale_year
)
SELECT
    borough_name,
    sale_year,
    transaction_count,
    median_price,
    median_price_per_sqft,
    LAG(median_price) OVER (PARTITION BY borough_name ORDER BY sale_year)              AS prev_year_median_price,
    ROUND(
        100.0 * (median_price - LAG(median_price) OVER (PARTITION BY borough_name ORDER BY sale_year))
        / NULLIF(LAG(median_price) OVER (PARTITION BY borough_name ORDER BY sale_year), 0)
    , 2)                                                                                AS yoy_price_pct_change,
    ROUND(
        100.0 * (median_price_per_sqft - LAG(median_price_per_sqft) OVER (PARTITION BY borough_name ORDER BY sale_year))
        / NULLIF(LAG(median_price_per_sqft) OVER (PARTITION BY borough_name ORDER BY sale_year), 0)
    , 2)                                                                                AS yoy_price_per_sqft_pct_change
FROM yearly
ORDER BY borough_name, sale_year;
