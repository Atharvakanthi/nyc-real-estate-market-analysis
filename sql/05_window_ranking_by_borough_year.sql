-- 05_window_ranking_by_borough_year.sql
-- Ranks neighborhoods within each borough and year by median price-per-sqft,
-- using RANK() and ROW_NUMBER() window functions. Surfaces the top 3
-- neighborhoods per borough per year (e.g. for "hottest micro-market" reporting).
-- Dialect: PostgreSQL / ANSI SQL.

WITH neighborhood_year AS (
    SELECT
        borough_name,
        neighborhood,
        sale_year,
        COUNT(*)                                                                     AS transaction_count,
        ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_per_sqft))::NUMERIC, 2) AS median_price_per_sqft
    FROM sales_clean
    GROUP BY borough_name, neighborhood, sale_year
    HAVING COUNT(*) >= 5
),
ranked AS (
    SELECT
        *,
        RANK() OVER (
            PARTITION BY borough_name, sale_year
            ORDER BY median_price_per_sqft DESC
        )                                                                            AS price_rank,
        ROW_NUMBER() OVER (
            PARTITION BY borough_name, sale_year
            ORDER BY transaction_count DESC
        )                                                                            AS volume_rank
    FROM neighborhood_year
)
SELECT
    borough_name,
    sale_year,
    neighborhood,
    transaction_count,
    median_price_per_sqft,
    price_rank,
    volume_rank
FROM ranked
WHERE price_rank <= 3
ORDER BY borough_name, sale_year, price_rank;
