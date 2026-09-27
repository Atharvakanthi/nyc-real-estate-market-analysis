# Data Source

**Dataset:** NYC Citywide Rolling Calendar Sales (property sales, all boroughs)

**Publisher:** NYC Department of Finance, distributed via the NYC Open Data portal
(Socrata platform, operated by the City of New York)

**Dataset landing page:** https://data.cityofnewyork.us/City-Government/NYC-Citywide-Rolling-Calendar-Sales/usep-8jbt

**API endpoint used for download:** https://data.cityofnewyork.us/resource/w2pb-icbu.json

**Download method:** Public Socrata REST API, paginated `$limit`/`$offset` GET requests,
filtered to `sale_date >= 2018-01-01`, ordered by `sale_date`. No authentication,
registration, or API key was required.

**Download date:** 2026-09-27

**License:** NYC Open Data is published under the terms described at
https://opendata.cityofnewyork.us/overview/ — the data is made available by NYC
Open Data for public use, free of charge, without restriction, subject to the
portal's Terms of Use (https://www1.nyc.gov/home/terms-of-use.page). No
attribution beyond citing NYC Open Data / NYC Department of Finance is required.

## Why this dataset instead of Dubai Land Department data

The original target was Dubai Land Department transaction data published via
the Dubai Pulse open-data portal. From this build environment:

- `https://www.dubaipulse.gov.ae` did not resolve within a 15-second timeout
  (connection timed out).
- `https://dubaipulse.gov.ai` failed DNS resolution entirely.

Both were tested directly with `curl` before falling back to a substitute.
Since Dubai Pulse was unreachable from this sandbox, this project uses the
NYC Citywide Rolling Calendar Sales dataset instead, per the fallback options
specified for this task. The dataset is structurally very similar (individual
real-estate transactions with location, property type, building
characteristics, sale price and sale date), which lets the same analytical
approach — price per unit area by micro-market and property type, year-over-year
trend, transaction-volume leaders, and window-function rankings — carry over
directly. All SQL in this repo is written in portable, standard SQL (see the
README) so it can be re-pointed at Dubai Land Department data later if that
portal becomes reachable.

## Row count actually used

See `nyc_rolling_sales_raw.csv` in this folder. The download covers all
recorded sales from 2018-01-01 onward at the time of download (see README for
the exact row count logged during the run).
