-- 01_cleaning_and_dedup.sql
-- Cleans and de-duplicates the raw sales extract into an analysis-ready table.
-- Dialect: PostgreSQL (portable ANSI SQL; no PostgreSQL-only syntax is used
-- beyond CAST/NULLIF, which are standard).
--
-- Cleaning rules applied:
--   1. Cast text columns to proper numeric/date types.
--   2. Drop rows with no sale price or an implausible sale price (<= $1,000).
--      NYC deed-transfer records include many $0 / $1 "sales" between family
--      members, foreclosures, or corporate ownership transfers that are not
--      arm's-length market transactions.
--   3. Drop rows with no usable gross square footage, since price-per-square-
--      foot analysis is meaningless without it.
--   4. De-duplicate on (borough, block, lot, apartment_number, sale_date,
--      sale_price) using ROW_NUMBER() -- the source data occasionally repeats
--      a transaction across export batches.
--   5. Map numeric borough codes to readable names.

DROP TABLE IF EXISTS sales_clean;

CREATE TABLE sales_clean AS
WITH typed AS (
    SELECT
        CAST(borough AS INTEGER)                       AS borough_code,
        CASE CAST(borough AS INTEGER)
            WHEN 1 THEN 'Manhattan'
            WHEN 2 THEN 'Bronx'
            WHEN 3 THEN 'Brooklyn'
            WHEN 4 THEN 'Queens'
            WHEN 5 THEN 'Staten Island'
            ELSE 'Unknown'
        END                                             AS borough_name,
        TRIM(neighborhood)                              AS neighborhood,
        TRIM(building_class_category)                   AS property_type,
        CAST(NULLIF(TRIM(REPLACE(block, ',', '')), '')  AS BIGINT)         AS block,
        CAST(NULLIF(TRIM(REPLACE(lot, ',', '')), '')    AS BIGINT)         AS lot,
        NULLIF(TRIM(apartment_number), '')               AS apartment_number,
        TRIM(address)                                    AS address,
        NULLIF(TRIM(zip_code), '')                       AS zip_code,
        CAST(NULLIF(TRIM(REPLACE(residential_units, ',', '')), '') AS INTEGER) AS residential_units,
        CAST(NULLIF(TRIM(REPLACE(commercial_units, ',', '')), '') AS INTEGER)  AS commercial_units,
        CAST(NULLIF(TRIM(REPLACE(total_units, ',', '')), '') AS INTEGER)        AS total_units,
        CAST(NULLIF(TRIM(REPLACE(land_square_feet, ',', '')), '') AS DOUBLE PRECISION)  AS land_square_feet,
        CAST(NULLIF(TRIM(REPLACE(gross_square_feet, ',', '')), '') AS DOUBLE PRECISION) AS gross_square_feet,
        CAST(NULLIF(TRIM(REPLACE(year_built, ',', '')), '') AS INTEGER)         AS year_built,
        CAST(NULLIF(TRIM(REPLACE(sale_price, ',', '')), '') AS DOUBLE PRECISION) AS sale_price,
        CAST(sale_date AS DATE)                          AS sale_date,
        CAST(NULLIF(TRIM(latitude), '') AS DOUBLE PRECISION)  AS latitude,
        CAST(NULLIF(TRIM(longitude), '') AS DOUBLE PRECISION) AS longitude
    FROM sales_raw
),
filtered AS (
    SELECT
        *,
        EXTRACT(YEAR FROM sale_date)::INTEGER  AS sale_year,
        sale_price / NULLIF(gross_square_feet, 0) AS price_per_sqft
    FROM typed
    WHERE sale_price IS NOT NULL
      AND sale_price > 1000
      AND gross_square_feet IS NOT NULL
      AND gross_square_feet > 0
      AND sale_date IS NOT NULL
),
deduped AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY borough_code, block, lot, apartment_number, sale_date, sale_price
            ORDER BY sale_date
        ) AS rn
    FROM filtered
)
SELECT
    borough_code, borough_name, neighborhood, property_type,
    block, lot, apartment_number, address, zip_code,
    residential_units, commercial_units, total_units,
    land_square_feet, gross_square_feet, year_built,
    sale_price, sale_date, sale_year, price_per_sqft,
    latitude, longitude
FROM deduped
WHERE rn = 1;

-- Sanity check row counts (run manually):
-- SELECT (SELECT COUNT(*) FROM sales_raw) AS raw_rows,
--        (SELECT COUNT(*) FROM sales_clean) AS clean_rows;
