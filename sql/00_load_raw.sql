-- 00_load_raw.sql
-- Loads the raw NYC Citywide Rolling Calendar Sales CSV into a staging table.
--
-- NOTE ON DIALECT: this single file is DuckDB-specific (read_csv_auto) because
-- it is the ingestion step used to reproduce this project locally. Every
-- other .sql file in this folder (01-05) is written in portable ANSI/PostgreSQL
-- SQL and does not depend on DuckDB. If you are loading into PostgreSQL
-- instead, replace this file's body with a `COPY sales_raw FROM
-- 'nyc_rolling_sales_sample.csv' WITH (FORMAT csv, HEADER true)` after
-- creating a matching table with TEXT columns.

DROP TABLE IF EXISTS sales_raw;

CREATE TABLE sales_raw AS
SELECT *
FROM read_csv_auto(
    'data/nyc_rolling_sales_sample.csv',
    ALL_VARCHAR = TRUE,
    HEADER = TRUE
);
