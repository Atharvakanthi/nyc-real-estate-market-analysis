import duckdb
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import os

os.chdir(r"C:\python\dubai-real-estate-market-analysis")

con = duckdb.connect()
con.execute(open("sql/00_load_raw.sql", encoding="utf-8").read())
con.execute(open("sql/01_cleaning_and_dedup.sql", encoding="utf-8").read())

# ---- KPI summary ----
kpi = con.execute("""
    SELECT
        COUNT(*) AS total_transactions,
        ROUND(SUM(sale_price)) AS total_sales_value,
        ROUND(AVG(sale_price)) AS avg_sale_price,
        ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sale_price))) AS median_sale_price,
        ROUND(AVG(price_per_sqft),2) AS avg_price_per_sqft,
        MIN(sale_year) AS min_year,
        MAX(sale_year) AS max_year,
        COUNT(DISTINCT neighborhood) AS n_neighborhoods,
        COUNT(DISTINCT borough_name) AS n_boroughs
    FROM sales_clean
""").fetchdf().iloc[0]

# ---- YoY price trend per borough ----
trend = con.execute("""
    SELECT borough_name, sale_year,
           ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sale_price))) AS median_price,
           ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_per_sqft)),2) AS median_price_per_sqft,
           COUNT(*) AS txn_count
    FROM sales_clean
    GROUP BY borough_name, sale_year
    ORDER BY borough_name, sale_year
""").fetchdf()

# ---- Area / property type comparison (top neighborhoods by volume, avg psf by borough+type) ----
by_borough_type = con.execute("""
    SELECT borough_name, property_type,
           COUNT(*) AS txn_count,
           ROUND(AVG(price_per_sqft),2) AS avg_price_per_sqft
    FROM sales_clean
    GROUP BY borough_name, property_type
    HAVING COUNT(*) >= 20
    ORDER BY txn_count DESC
    LIMIT 25
""").fetchdf()

top_neighborhoods = con.execute("""
    SELECT borough_name, neighborhood,
           COUNT(*) AS txn_count,
           ROUND(AVG(price_per_sqft),2) AS avg_price_per_sqft,
           ROUND(AVG(sale_price)) AS avg_sale_price
    FROM sales_clean
    GROUP BY borough_name, neighborhood
    ORDER BY txn_count DESC
    LIMIT 15
""").fetchdf()

borough_summary = con.execute("""
    SELECT borough_name,
           COUNT(*) AS txn_count,
           ROUND(AVG(price_per_sqft),2) AS avg_price_per_sqft,
           ROUND(AVG(sale_price)) AS avg_sale_price
    FROM sales_clean
    GROUP BY borough_name
    ORDER BY txn_count DESC
""").fetchdf()

# ================= Build Plotly figures =================

BOROUGH_COLORS = {
    "Manhattan": "#4C78A8", "Brooklyn": "#F58518", "Queens": "#54A24B",
    "Bronx": "#E45756", "Staten Island": "#B279A2"
}

# --- Fig 1: YoY median price per sqft trend, one line per borough ---
fig_trend = go.Figure()
for b in trend["borough_name"].unique():
    d = trend[trend["borough_name"] == b]
    fig_trend.add_trace(go.Scatter(
        x=d["sale_year"], y=d["median_price_per_sqft"],
        mode="lines+markers", name=b,
        line=dict(color=BOROUGH_COLORS.get(b), width=3),
        marker=dict(size=7),
        hovertemplate="%{fullData.name}<br>Year: %{x}<br>Median $/sqft: $%{y:,.2f}<extra></extra>"
    ))
fig_trend.update_layout(
    title="Median Price per Square Foot Over Time, by Borough",
    xaxis_title="Sale Year", yaxis_title="Median price per sqft (USD)",
    template="plotly_white", legend_title="Borough", height=460,
)

# --- Fig 2: median sale price trend ---
fig_trend_price = go.Figure()
for b in trend["borough_name"].unique():
    d = trend[trend["borough_name"] == b]
    fig_trend_price.add_trace(go.Scatter(
        x=d["sale_year"], y=d["median_price"],
        mode="lines+markers", name=b,
        line=dict(color=BOROUGH_COLORS.get(b), width=3),
        marker=dict(size=7),
        hovertemplate="%{fullData.name}<br>Year: %{x}<br>Median price: $%{y:,.0f}<extra></extra>"
    ))
fig_trend_price.update_layout(
    title="Median Sale Price Over Time, by Borough",
    xaxis_title="Sale Year", yaxis_title="Median sale price (USD)",
    template="plotly_white", legend_title="Borough", height=460,
)

# --- Fig 3: Borough comparison bar (avg $/sqft) ---
fig_borough_psf = go.Figure(go.Bar(
    x=borough_summary["borough_name"], y=borough_summary["avg_price_per_sqft"],
    marker_color=[BOROUGH_COLORS.get(b) for b in borough_summary["borough_name"]],
    text=borough_summary["avg_price_per_sqft"].map(lambda v: f"${v:,.0f}"),
    textposition="outside",
    hovertemplate="%{x}<br>Avg $/sqft: $%{y:,.2f}<extra></extra>"
))
fig_borough_psf.update_layout(
    title="Average Price per Square Foot by Borough",
    xaxis_title="Borough", yaxis_title="Avg price per sqft (USD)",
    template="plotly_white", height=420,
)

# --- Fig 4: property type comparison (top 25 borough x property type combos by volume) ---
by_borough_type["label"] = by_borough_type["borough_name"] + " — " + by_borough_type["property_type"]
by_borough_type_sorted = by_borough_type.sort_values("avg_price_per_sqft", ascending=True)
fig_type = go.Figure(go.Bar(
    x=by_borough_type_sorted["avg_price_per_sqft"],
    y=by_borough_type_sorted["label"],
    orientation="h",
    marker_color=[BOROUGH_COLORS.get(b) for b in by_borough_type_sorted["borough_name"]],
    hovertemplate="%{y}<br>Avg $/sqft: $%{x:,.2f}<br>Transactions: %{customdata}<extra></extra>",
    customdata=by_borough_type_sorted["txn_count"],
))
fig_type.update_layout(
    title="Avg Price per Sqft by Borough & Property Type (top 25 by transaction volume)",
    xaxis_title="Avg price per sqft (USD)", yaxis_title="",
    template="plotly_white", height=700, margin=dict(l=260),
)

# --- Fig 5: Top neighborhoods by transaction volume ---
top_neighborhoods_sorted = top_neighborhoods.sort_values("txn_count", ascending=True)
fig_top_nb = go.Figure(go.Bar(
    x=top_neighborhoods_sorted["txn_count"],
    y=top_neighborhoods_sorted["neighborhood"] + " (" + top_neighborhoods_sorted["borough_name"] + ")",
    orientation="h",
    marker_color=[BOROUGH_COLORS.get(b) for b in top_neighborhoods_sorted["borough_name"]],
    hovertemplate="%{y}<br>Transactions: %{x}<br>Avg price: $%{customdata:,.0f}<extra></extra>",
    customdata=top_neighborhoods_sorted["avg_sale_price"],
))
fig_top_nb.update_layout(
    title="Top 15 Micro-Markets (Neighborhoods) by Transaction Volume",
    xaxis_title="Transaction count", yaxis_title="",
    template="plotly_white", height=560, margin=dict(l=260),
)

# ================= Assemble HTML =================

def fig_html(fig, div_id):
    return pio.to_html(fig, include_plotlyjs=False, full_html=False, div_id=div_id)

trend_html = fig_html(fig_trend, "fig_trend")
trend_price_html = fig_html(fig_trend_price, "fig_trend_price")
borough_psf_html = fig_html(fig_borough_psf, "fig_borough_psf")
type_html = fig_html(fig_type, "fig_type")
top_nb_html = fig_html(fig_top_nb, "fig_top_nb")

plotly_js = pio.to_html(go.Figure(), include_plotlyjs="cdn", full_html=False).split('<div')[0]  # grabs script tag block
# simpler: just embed cdn script tag directly
plotly_cdn = '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'

kpi_cards = f"""
<div class="kpi-grid">
  <div class="kpi-card">
    <div class="kpi-label">Total Transactions</div>
    <div class="kpi-value">{int(kpi['total_transactions']):,}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Total Sales Value</div>
    <div class="kpi-value">${kpi['total_sales_value']/1e9:,.2f}B</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Median Sale Price</div>
    <div class="kpi-value">${kpi['median_sale_price']:,.0f}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Avg Price / Sqft</div>
    <div class="kpi-value">${kpi['avg_price_per_sqft']:,.2f}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Years Covered</div>
    <div class="kpi-value">{int(kpi['min_year'])}&ndash;{int(kpi['max_year'])}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Neighborhoods Analyzed</div>
    <div class="kpi-value">{int(kpi['n_neighborhoods'])}</div>
  </div>
</div>
"""

borough_table_rows = "".join(
    f"<tr><td>{r.borough_name}</td><td>{int(r.txn_count):,}</td>"
    f"<td>${r.avg_sale_price:,.0f}</td><td>${r.avg_price_per_sqft:,.2f}</td></tr>"
    for r in borough_summary.itertuples()
)

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NYC Residential Real Estate Market Dashboard</title>
{plotly_cdn}
<style>
  :root {{
    --bg: #f7f8fa; --card-bg: #ffffff; --text: #1c1e21; --muted: #6b7280;
    --accent: #4C78A8; --border: #e5e7eb;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg); color: var(--text);
  }}
  header {{
    background: linear-gradient(135deg, #1c2b4a, #365d8e);
    color: white; padding: 32px 24px;
  }}
  header h1 {{ margin: 0 0 6px 0; font-size: 26px; }}
  header p {{ margin: 0; opacity: 0.9; font-size: 14px; max-width: 900px; }}
  main {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
  section {{ margin-bottom: 36px; }}
  h2 {{ font-size: 19px; border-bottom: 2px solid var(--border); padding-bottom: 8px; }}
  .kpi-grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 14px; margin-top: 16px;
  }}
  .kpi-card {{
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px; text-align: center;
  }}
  .kpi-label {{ font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }}
  .kpi-value {{ font-size: 22px; font-weight: 700; margin-top: 6px; color: var(--accent); }}
  .chart-card {{
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px;
    padding: 8px; margin-bottom: 20px;
  }}
  table {{ width: 100%; border-collapse: collapse; background: var(--card-bg); border-radius: 10px; overflow: hidden; }}
  th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); font-size: 14px; }}
  th {{ background: #eef1f6; }}
  footer {{ text-align: center; padding: 24px; color: var(--muted); font-size: 12px; }}
</style>
</head>
<body>
<header>
  <h1>NYC Residential &amp; Commercial Real Estate Market Dashboard</h1>
  <p>Independent market research built from the public NYC Citywide Rolling Calendar Sales
     dataset ({int(kpi['min_year'])}&ndash;{int(kpi['max_year'])}). Explores price trends, price per
     square foot, and transaction-volume leaders across all five boroughs to support
     buyer, analyst, and investor decision-making.</p>
</header>
<main>

  <section id="overview">
    <h2>1. Market Overview</h2>
    {kpi_cards}
    <div style="margin-top:20px;" class="chart-card">{borough_psf_html}</div>
    <table>
      <thead><tr><th>Borough</th><th>Transactions</th><th>Avg Sale Price</th><th>Avg Price / Sqft</th></tr></thead>
      <tbody>{borough_table_rows}</tbody>
    </table>
  </section>

  <section id="trend">
    <h2>2. Price Trend Over Time</h2>
    <div class="chart-card">{trend_price_html}</div>
    <div class="chart-card">{trend_html}</div>
  </section>

  <section id="comparison">
    <h2>3. Area &amp; Property-Type Comparison</h2>
    <div class="chart-card">{top_nb_html}</div>
    <div class="chart-card">{type_html}</div>
  </section>

</main>
<footer>
  Data: NYC Citywide Rolling Calendar Sales, NYC Open Data (public dataset). This
  dashboard is a self-contained HTML/Plotly build used in place of Power BI /
  Tableau, which could not be installed in the build environment.
</footer>
</body>
</html>
"""

out_path = r"C:\python\dubai-real-estate-market-analysis\dashboard\market_dashboard.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

print("Wrote", out_path, "size bytes:", os.path.getsize(out_path))
print(kpi)
