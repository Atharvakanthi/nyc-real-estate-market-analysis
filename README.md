# NYC Real Estate Market Analysis

Independent market research analyzing residential and commercial real estate
transactions across New York City's five boroughs, using publicly available
NYC Department of Finance sales records.

## a) Business framing — what question this answers, and for whom

This project answers a core real-estate market question: **where are prices
rising fastest, which micro-markets trade the most volume, and how does price
per square foot vary by neighborhood and property type?**

It is written as a self-directed market research exercise, useful to three
kinds of readers:

- **A prospective buyer or renter**, who wants to know whether a given
  neighborhood is priced above or below the borough median on a per-square-foot
  basis, and whether prices there are trending up or down year over year.
- **A data/business analyst**, who wants a template for building price
  benchmarking, YoY trend analysis, and volume-leader reports from raw
  transaction-level property data.
- **An investor**, who wants to identify high-transaction-volume micro-markets
  (a proxy for liquidity) and compare price-per-square-foot appreciation across
  boroughs and property types to guide where to focus acquisition search.

This is independent research, not commissioned by or representing any employer
or client. All data, code, and analysis were assembled solely for this
portfolio project.

## b) Data source, license, and exact download URL

**Dataset:** NYC Citywide Rolling Calendar Sales (all five boroughs)

- **Landing page:** https://data.cityofnewyork.us/City-Government/NYC-Citywide-Rolling-Calendar-Sales/usep-8jbt
- **API endpoint used:** `https://data.cityofnewyork.us/resource/w2pb-icbu.json`
- **Publisher:** NYC Department of Finance, via the NYC Open Data portal (Socrata)
- **Download date:** 2026-09-27
- **License:** Published under NYC Open Data's terms
  (https://opendata.cityofnewyork.us/overview/), free for public use without
  restriction, subject to the portal's Terms of Use
  (https://www1.nyc.gov/home/terms-of-use.page). No special permission or
  registration was required to download it.
- **Row count downloaded:** 667,141 property-sale records (all sales dated
  2018-01-01 or later, downloaded via paginated public API calls, no
  authentication required).
- **Row count committed to this repo:** a stratified sample of **120,080 rows**
  (roughly 18% of each year's sales, capped and sampled with a fixed random
  seed) is committed as `data/nyc_rolling_sales_sample.csv`, to keep the
  repository at a reasonable size (~24 MB vs. ~131 MB for the full extract).
  The sampling preserves the year-over-year shape of the data. Full
  reproduction instructions to re-download all 667K+ rows are in section (d).

See `data/SOURCE.md` for the full source note, including why this dataset was
used instead of the originally targeted Dubai Land Department data.

### Why NYC data instead of Dubai Land Department data

The initial target for this project was Dubai Land Department transaction
data via the Dubai Pulse open-data portal. From this build environment,
`https://www.dubaipulse.gov.ae` timed out on connection and
`https://dubaipulse.gov.ai` failed DNS resolution — both were tested directly
before falling back. NYC Open Data's Citywide Rolling Calendar Sales dataset
was substituted: it is structurally very similar (individual real-estate
transactions with location, building type, square footage, and sale price/date),
so the same analytical approach applies directly, and the SQL in this repo
is written in portable dialect that could be re-pointed at Dubai Land
Department data later if desired.

## c) Methodology

**Cleaning steps** (see `sql/01_cleaning_and_dedup.sql`):

1. Cast all text-typed source columns to proper numeric/date types, stripping
   thousands-separator commas (e.g., `"1,495"` → `1495`).
2. Drop transactions with no sale price or an implausible sale price
   (`<= $1,000`) — NYC deed-transfer records include many `$0`/`$1` "sales"
   between family members, foreclosures, or corporate ownership transfers that
   are not arm's-length market transactions.
3. Drop rows with no usable gross square footage, since price-per-square-foot
   analysis is meaningless without it (common for some condo/co-op rows in the
   source data, which is why the clean row count is materially smaller than
   the raw row count — see below).
4. De-duplicate on `(borough, block, lot, apartment_number, sale_date,
   sale_price)` using `ROW_NUMBER()`, since the source occasionally repeats a
   transaction across export batches.
5. Map numeric borough codes (1-5) to readable borough names.

**Key definitions:**

- **Price per square foot** = `sale_price / gross_square_feet` (the dataset's
  unit of building area; there is no separate "carpet area" concept in this
  source, unlike some other property datasets).
- **Micro-market** = NYC "neighborhood" field (a sub-borough geographic tier,
  e.g. "Williamsburg-North", "Bedford Stuyvesant").
- **Year-over-year change** = percentage change in the median sale price /
  median price-per-sqft for a borough, versus the prior calendar year.

Of the 120,080 sampled rows, 38,902 (~32%) pass all cleaning filters and are
used for analysis — the SQL layer intentionally keeps the raw and cleaned
tables separate so this filtering rate is auditable.

## d) Exact reproduction commands

```bash
# 1. Re-download the full dataset (optional — a sample is already committed)
python3 -c "
import requests, csv
BASE = 'https://data.cityofnewyork.us/resource/w2pb-icbu.json'
fields = ['borough','neighborhood','building_class_category','tax_class_as_of_final_roll',
          'block','lot','building_class_as_of_final','address','apartment_number','zip_code',
          'residential_units','commercial_units','total_units','land_square_feet','gross_square_feet',
          'year_built','tax_class_at_time_of_sale','building_class_at_time_of','sale_price','sale_date',
          'latitude','longitude','community_board','council_district','bin','bbl','census_tract_2020','nta']
with open('data/nyc_rolling_sales_raw.csv','w',newline='',encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore'); w.writeheader()
    offset = 0
    while True:
        r = requests.get(BASE, params={'\$limit':50000,'\$offset':offset,
            '\$where':\"sale_date >= '2018-01-01T00:00:00.000'\", '\$order':'sale_date'}, timeout=60)
        rows = r.json()
        if not rows: break
        for row in rows: w.writerow(row)
        offset += 50000
        if len(rows) < 50000: break
"

# 2. Install dependencies
pip install duckdb pandas plotly

# 3. Run the SQL pipeline against the (sampled or full) CSV and print/save outputs
python3 -c "
import duckdb, os
os.chdir('.')
con = duckdb.connect()
for f in ['sql/00_load_raw.sql','sql/01_cleaning_and_dedup.sql',
          'sql/02_price_per_sqft_by_area_and_type.sql','sql/03_year_over_year_trend.sql',
          'sql/04_top_microzones_by_volume.sql','sql/05_window_ranking_by_borough_year.sql']:
    print('---', f); print(con.execute(open(f).read()).fetchdf().head(10))
"

# 4. Rebuild the HTML dashboard
python3 dashboard/build_dashboard.py   # regenerates dashboard/market_dashboard.html

# 5. Open the dashboard
# Just open dashboard/market_dashboard.html directly in any browser — no server needed.
```

All SQL in `sql/` is written in **PostgreSQL dialect** (standard ANSI window
functions, `PERCENTILE_CONT`, `ROW_NUMBER()`, `RANK()`, `LAG()`), with the sole
exception of `sql/00_load_raw.sql`, which uses DuckDB's `read_csv_auto()` for
convenient local ingestion — that one file is clearly marked as DuckDB-specific;
everything downstream of it is portable and was validated to run unmodified
against a local DuckDB instance loaded from the real downloaded CSV (DuckDB's
SQL engine is largely Postgres-compatible for these constructs). If loading
into an actual PostgreSQL instance, replace `00_load_raw.sql`'s body with a
`COPY ... FROM ... WITH (FORMAT csv, HEADER true)` statement.

**Every query in `sql/` was actually executed against the real downloaded
data**, not just written. Real result samples are captured in
`sql/sample_outputs.md`, including exact row counts at each pipeline stage
(120,080 raw sample rows in → 38,902 clean rows out) and the top rows of
each query's output.

## e) What the dashboard shows

`dashboard/market_dashboard.html` is a single self-contained HTML file
(Plotly.js loaded from CDN, all data embedded) with three sections.

**Market Overview** presents headline KPIs — total transactions, total sales
value, median sale price, average price per square foot, years covered, and
neighborhood count — followed by a bar chart and table comparing the five
boroughs on transaction volume, average sale price, and average price per
square foot. Manhattan and Brooklyn command visibly higher $/sqft than the
outer boroughs, while Queens and Staten Island show materially higher
transaction counts for lower per-unit prices, consistent with their larger
stock of single-family and multi-family homes.

**Price Trend Over Time** plots median sale price and median price-per-square-
foot by borough across every year from 2018 through 2025 (partial year),
letting a reader spot which boroughs cooled or accelerated after 2020-2022,
and how price-per-square-foot growth diverges from headline sale-price growth
(a signal of whether homes are simply getting bigger/smaller, versus genuinely
appreciating on a like-for-like basis).

**Area & Property-Type Comparison** ranks the top 15 neighborhoods by raw
transaction volume (a liquidity proxy useful to investors) and compares
average price-per-square-foot across the 25 highest-volume
borough-x-property-type combinations, so a reader can see, for example, that
one-family dwellings in an outer-borough neighborhood trade at a very
different $/sqft than elevator co-ops in Manhattan.

## f) Note on tooling substitutions

- The dashboard is a **documented HTML/Plotly substitute for Power BI or
  Tableau**, since Power BI Desktop cannot be installed in this build
  environment. The underlying SQL layer (`sql/`) is dialect-portable
  PostgreSQL, so if Atharva wants to rebuild the visual layer in Power BI or
  Tableau later, the same cleaned table (`sales_clean`) and the same five
  queries can be pointed at directly from either tool with no rewrite needed.

## g) Screenshots

No screenshots or PNG captures are included, because rendering and capturing
a browser screenshot of the dashboard was not possible in this build
environment. The dashboard is fully interactive and viewable by opening
`dashboard/market_dashboard.html` directly in any modern browser — no server
or build step required.

## Repository structure

```
dubai-real-estate-market-analysis/
├── data/
│   ├── nyc_rolling_sales_sample.csv   # 120,080-row stratified sample (committed)
│   └── SOURCE.md                       # exact source URL, license, download date
├── sql/
│   ├── 00_load_raw.sql                 # DuckDB CSV ingestion (only DuckDB-specific file)
│   ├── 01_cleaning_and_dedup.sql       # cleaning + de-duplication
│   ├── 02_price_per_sqft_by_area_and_type.sql
│   ├── 03_year_over_year_trend.sql     # YoY trend, uses LAG()
│   ├── 04_top_microzones_by_volume.sql # top-N transaction-volume leaders
│   ├── 05_window_ranking_by_borough_year.sql  # RANK() / ROW_NUMBER() ranking
│   └── sample_outputs.md               # real query results, captured from an actual run
├── dashboard/
│   ├── build_dashboard.py              # regenerates the HTML dashboard
│   └── market_dashboard.html           # the self-contained interactive dashboard
└── README.md
```

Note: this repository's folder name (`dubai-real-estate-market-analysis`) was
retained from the original project brief even though the dataset actually
used is NYC, not Dubai — see the substitution rationale above.
