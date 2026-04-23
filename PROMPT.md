Build a Streamlit-in-Snowflake (SiS) multi-page application called "AI on Snowflake" that provides visibility into Snowflake Cortex AI feature usage, costs, and optimization opportunities. The app uses a clean, Canva-inspired light theme with Snowflake brand accent colors. Deploy it to a Snowflake account using **container runtime**.

## Requirements

### Platform & Dependencies
- Streamlit-in-Snowflake using **container runtime** (not warehouse runtime)
- Dependencies specified in `pyproject.toml` (not `environment.yml`):
  - snowflake-connector-python>=3.3.0
  - streamlit[snowflake]>=1.50.0
  - plotly>=5.18.0
  - pandas>=2.0.0
  - numpy>=1.24.0
- Use `st.connection("snowflake")` for the Snowflake connection (not Snowpark `get_active_session()`)
- All queries go through a cached `_run_query()` function with `@st.cache_data(ttl=600)` that also converts `Decimal` columns to `float` (since `st.connection().query()` returns `Decimal` for numeric Snowflake columns)
- Error handling via `safe_query()` wrapper (with `st.warning()`) and `_safe_run()` (silent, for use inside other cached functions)
- Light-themed Plotly charts (transparent backgrounds, dark text, Inter font)
- Sidebar refresh button that clears all caches via `st.cache_data.clear()` + `st.rerun()`
- Date range selection persists across tabs using `st.session_state` and widget `key` parameters

### Deployment Configuration
- `snowflake.yml` with `definition_version: 2` for container runtime
- `runtime_name: SYSTEM$ST_CONTAINER_RUNTIME_PY3_11`
- Requires a compute pool (e.g., `SYSTEM_COMPUTE_POOL_CPU`) and external access integration for PyPI (e.g., `PYPI_ACCESS_INTEGRATION`)
- Deploy via Snowflake CLI v3.14.0+: `snow streamlit deploy --replace --connection <connection>`
- All source files listed in `artifacts` section of `snowflake.yml`

### Visual Theme — Canva-Inspired Light Design
The app follows a clean, modern light theme inspired by Canva's UI, with Snowflake brand accent colors:

- **Background:** Clean white (`#FFFFFF`) main background
- **Cards:** White with subtle borders (`#e8e8ef`), soft shadows, 16px rounded corners
- **Hero banner:** Purple-to-blue gradient (`#7254A3` → `#29B5E8` → `#75CDD7`) on Overview page
- **Primary accent:** Purple Moon (`#7254A3`) — used for buttons, chart lines, stat pills, tab highlights
- **Secondary accent:** Snowflake Blue (`#29B5E8`) — used for brand elements and severity-low indicators
- **Sidebar:** Light gray (`#f8f8fc`) with subtle border
- **Lots of whitespace and breathing room**
- **Soft pastel tones** for highlight boxes and callout areas

**Color Palette (Snowflake brand):**
- SNOWFLAKE BLUE: `#29B5E8` — Brand accent, severity-low, powered-by footer
- MIDNIGHT: `#000000` — Reserved (not used in light theme)
- MID-BLUE: `#11567F` — Secondary chart color, savings text in rec cards
- MEDIUM GRAY: `#5B5B5B` — Chart secondary color
- STAR BLUE: `#75CDD7` — Chart secondary color, hero banner gradient end
- VALENCIA ORANGE: `#FF9F36` — Forecast lines, medium severity
- PURPLE MOON: `#7254A3` — Primary accent (buttons, chart lines, tabs, stat pills, highlight borders)
- FIRST LIGHT: `#D45B90` — High severity, anomaly markers, gauge threshold

**Light Theme Text Colors:**
- Primary text: `#1a1a2e` (headings, metric values, card titles)
- Secondary text: `#2d2d44` (h2 headings, section headers)
- Tertiary text: `#3d3d56` (h3 headings)
- Body text: `#4a4a68` (paragraphs, chart fonts)
- Muted text: `#6b6b85` (sidebar text, card descriptions, legend)
- Caption text: `#8b8ba3` (labels, captions, subtle text)
- Border color: `#e8e8ef` (cards, dividers, containers)
- Light background: `#f5f5fa` (tab backgrounds, scrollbar tracks)
- Sidebar background: `#f8f8fc`

**Typography:**
- Font family: Inter, -apple-system, BlinkMacSystemFont, sans-serif (imported from Google Fonts, set via CSS injection and Plotly layout)
- h1 titles: 700 weight, `#1a1a2e`
- h2 subheadings: 600 weight, `#2d2d44`
- h3 subheadings: 600 weight, `#3d3d56`
- Body/captions: `#4a4a68` / `#8b8ba3`

**Shared CSS Module (`utils/styles.py`):**
All pages call `inject_css()` from this shared module. It provides a centralized CSS theme so every page gets consistent styling without duplicating CSS blocks. The module also exports helper functions:
- `inject_css()` — Full CSS theme injection (call once at top of every page)
- `section_header(icon, title)` — Styled section header with icon and bottom border
- `highlight_box(text)` — Pastel gradient callout box with purple left border
- `hero_banner(title, subtitle)` — Gradient hero banner (used on Overview)
- `recommendation_card(title, severity, savings, description, icon)` — Severity-colored card
- `powered_by_footer()` — "Powered by Snowflake" footer for sidebar

CSS classes defined: `.saas-card`, `.highlight-box`, `.hero-banner`, `.info-chip`, `.rec-card`, `.rec-card.high/.medium/.low`, `.section-header`, `.stat-pill`, `.powered-by`

### Data Sources
All data comes from `SNOWFLAKE.ACCOUNT_USAGE` views. The app should query these:

**AI credit metering (billing truth):**
- `METERING_HISTORY` filtered to `SERVICE_TYPE IN ('AI_SERVICES', 'CORTEX_FINE_TUNING', 'SNOWPARK_CONTAINER_SERVICES')`

**Per-feature usage (9 views, queried individually and concatenated into a unified DataFrame):**
- `CORTEX_FUNCTIONS_USAGE_HISTORY` — LLM functions (COMPLETE, EMBED_TEXT, etc.)
- `CORTEX_ANALYST_USAGE_HISTORY` — Cortex Analyst
- `CORTEX_SEARCH_DAILY_USAGE_HISTORY` — Cortex Search
- `CORTEX_AGENT_USAGE_HISTORY` — Cortex Agents
- `SNOWFLAKE_INTELLIGENCE_USAGE_HISTORY` — Snowflake Intelligence
- `CORTEX_CODE_CLI_USAGE_HISTORY` — Cortex Code (note: uses `USAGE_TIME` not `START_TIME`)
- `DOCUMENT_AI_USAGE_HISTORY` — Document AI
- `CORTEX_FINE_TUNING_USAGE_HISTORY` — Cortex Fine-Tuning
- `CORTEX_REST_API_USAGE_HISTORY` — Cortex REST API (tokens only, no credits)

Each view returns: FEATURE (literal string), USAGE_DATE, CREDITS, TOKENS, REQUEST_COUNT. Concat all non-empty results.

**Query-level data:**
- `QUERY_HISTORY` filtered by AI function names in QUERY_TEXT (AI_COMPLETE, AI_CLASSIFY, AI_EXTRACT, AI_FILTER, AI_SENTIMENT, AI_SUMMARIZE, AI_TRANSLATE, AI_EMBED, AI_PARSE_DOCUMENT, COMPLETE(, EMBED_TEXT(, etc.)
- Note: `CREDITS_USED_CLOUD_SERVICES` in QUERY_HISTORY is SQL execution overhead, NOT AI token credits. Label it clearly as "cloud services" or "query execution overhead" everywhere it appears.

**Other:**
- `WAREHOUSE_METERING_HISTORY` — warehouse compute (all workloads, not AI-specific)
- `ORGANIZATION_USAGE.RATE_SHEET_DAILY` — auto-fetch $/credit rate (cache for 24h)

### Query Architecture
Three-layer pattern for data access:

1. `_run_query(sql)` — Core cached layer with `@st.cache_data(ttl=600)`. Runs SQL via `st.connection("snowflake").query()` and converts any `Decimal` columns to `float`.
2. `_safe_run(sql)` — Silent error handling wrapper around `_run_query()`. Returns empty DataFrame on failure. Used inside other `@st.cache_data` functions to avoid `st.warning()` in cached context.
3. `safe_query(sql, error_msg)` — Error handling wrapper with `st.warning()`. Used by page-level code that is not itself cached.

Functions that aggregate multiple queries (like `get_metering_and_daily`, `get_feature_credits_summary`) use `@st.cache_data(ttl=600)` at the function level and call `_safe_run()` internally.

### File Structure
```
Overview.py                    # Main page — hero banner, KPIs, charts, export
pyproject.toml                 # Python dependencies (container runtime)
snowflake.yml                  # Deployment manifest (definition_version: 2)
pages/
  2_Feature_Breakdown.py       # Per-feature drilldown
  3_User_Analysis.py           # User-level consumption
  4_Optimization.py            # Cost optimization recommendations
  5_Alerts & Forecast.py       # Forecasting, budget gauge, anomaly detection, alert SQL
utils/
  __init__.py                  # Empty
  queries.py                   # All Snowflake queries (cached via _run_query)
  charts.py                    # All Plotly chart functions with light-theme colors
  styles.py                    # Shared CSS module — inject_css(), section_header(), etc.
  sidebar.py                   # Shared sidebar with time range picker + refresh button
  recommendations.py           # Recommendation engine with model tiers
  export.py                    # HTML report generator with Snowflake brand styling
setup.sql                      # One-time database/schema/compute pool setup
deploy.sh                      # Automated deployment script
environment.yml                # Legacy warehouse runtime deps (kept for reference)
```

### Page Descriptions

**Overview (Overview.py):**
- Page title (browser tab): "AI on Snowflake"
- Gradient hero banner via `hero_banner("❄️ AI on Snowflake", "Snowflake AI Cost and Usage Monitoring")`
- CSS injected via `inject_css()` from `utils/styles.py`
- Info chip for latency notice (uses `.info-chip` CSS class)
- Natural-language highlights line in a `.highlight-box`: "$X spent (Y credits), down Z% vs prior period, top feature is Cortex Analyst (94% of credits), 51 requests consuming 10,487 tokens."
- 4 KPI metrics with period-over-period deltas (delta_color="inverse" since cost going up is bad): Total AI Credits, Estimated Cost (with $/credit subtitle), Tokens Consumed, AI Requests
- 3 run-rate metrics: Monthly Run Rate, Cost per Request, Cost per 1K Tokens
- Two charts side by side: daily credits line chart, feature area chart
- Feature breakdown with donut chart + per-feature `.saas-card` metric cards with `.stat-pill` badges
- Export section: HTML report download button (purple gradient) + email SQL template

**Feature Breakdown (2_Feature_Breakdown.py):**
- CSS injected via `inject_css()`
- Selectbox to pick an AI feature
- 4 KPI metrics for selected feature
- Daily credit trend line chart
- Daily token trend (if tokens available)
- Agent-specific breakdown when "Cortex Agents" selected (sub-table + agent line chart with light-theme inline layout)
- Raw data expander

**User Analysis (3_User_Analysis.py):**
- CSS injected via `inject_css()`
- Three tabs: Overview, User trends, Anomaly detection
- Loads both `user_summary_df` and `user_daily_df` before the tabs in a single spinner (avoids undefined variable bugs)
- Overview: horizontal bar chart + summary table
- User trends: multi-select users (max 5) + multi-line trend chart
- Anomaly detection: rolling 7-day average, flag when daily usage > mean + 2*std
- IMPORTANT: The column from QUERY_HISTORY is `CLOUD_SERVICES_CREDITS` (aliased from `CREDITS_USED_CLOUD_SERVICES`). Add a caption explaining these are SQL execution overhead, not AI inference costs.

**Optimization (4_Optimization.py):**
- CSS injected via `inject_css()`
- Executive-friendly: clean `.rec-card` recommendation cards (severity icon, title, savings) as the default view
- Summary KPIs: Action Items count, High Priority count, Potential Savings
- Natural-language summary sentence about opportunities in a `.highlight-box`
- All technical details (SQL templates, model reference table, raw data) hidden in a single "Technical details" expander at the bottom
- Loads all data once at the top and reuses DataFrames (avoids duplicate queries)
- Recommendation engine (`recommendations.py`) generates recs from: budget analysis, agent token limits, model downgrade suggestions (with DOWNGRADE_MAP), caching opportunities for repeated queries, long prompt optimization, warehouse right-sizing, off-peak scheduling, query tagging

**Alerts & Forecast (5_Alerts & Forecast.py):**
- CSS injected via `inject_css()`
- Four tabs: Forecast, Budget gauge, Anomalies, Alert SQL
- Forecast: linear regression (numpy polyfit) on daily credits, 30-day projection with 95% confidence band (Valencia Orange dashed line, orange fill), y-axis labeled "Credits"
- Budget gauge: user-configurable monthly target, gauge chart (Purple Moon bar, branded step colors), current/projected month-end metrics, colored warnings at 50/75/90%
- Anomalies: rolling 7-day average, flag days where spend > 2x rolling avg (First Light X markers)
- Alert SQL: ready-to-copy SQL templates for daily threshold, weekly anomaly, monthly budget, and resource monitor alerts

### Shared Sidebar (sidebar.py)
- Centered snowflake icon (❄ HTML entity `&#10052;`) at the top
- App title: "AI on Snowflake" in dark text (`#1a1a2e`)
- Subtitle: "Cost & Usage Monitor" in muted text (`#8b8ba3`)
- Dividers: subtle gray (`#e8e8ef`)
- **Refresh data** button that calls `st.cache_data.clear()` + `st.rerun()`
- Time range selector: presets (7/14/30/90 days) + custom date range
- Date range persists across tabs via `key` parameters on widgets (`_range_option`, `_custom_start`, `_custom_end`) tied to `st.session_state`
- Auto-fetches credit rate from `RATE_SHEET_DAILY` on load
- Stores start_date, end_date, days, credit_rate in st.session_state
- About expander explaining data latency
- `powered_by_footer()` at the bottom

### Charts (charts.py)
- Consistent light theme: transparent backgrounds, dark text (`#4a4a68`), Inter font, subtle gray grid lines (`rgba(0,0,0,0.05)`)
- Snowflake brand color palette:
  ```python
  COLORS = [SNOWFLAKE_BLUE, MID_BLUE, STAR_BLUE, VALENCIA_ORANGE,
            PURPLE_MOON, FIRST_LIGHT, MEDIUM_GRAY, "#A3D5E6", "#1B8AB5", "#B8A9D4"]
  ```
- Named color constants: `SNOWFLAKE_BLUE`, `MIDNIGHT`, `MID_BLUE`, `MEDIUM_GRAY`, `STAR_BLUE`, `VALENCIA_ORANGE`, `PURPLE_MOON`, `FIRST_LIGHT`
- SERVICE_COLORS: AI_SERVICES → Snowflake Blue, CORTEX_FINE_TUNING → Mid-Blue, SNOWPARK_CONTAINER_SERVICES → Star Blue
- FEATURE_COLORS: 8 features mapped to brand colors
- SEVERITY_COLORS: high → First Light, medium → Valencia Orange, low → Snowflake Blue
- LAYOUT_DEFAULTS:
  - `font=dict(family="'Inter', -apple-system, BlinkMacSystemFont, sans-serif", color="#4a4a68", size=12)`
  - `margin=dict(l=40, r=20, t=50, b=100)` — extra bottom margin for legend
  - Legend: horizontal, centered below chart (`y=-0.28, xanchor="center", x=0.5`)
  - Hover labels: white background (`rgba(255, 255, 255, 0.97)`), purple border, dark text
  - Grid: `rgba(0,0,0,0.05)`, tick font `#8b8ba3`
- Primary line/bar color: Purple Moon (`#7254A3`) for single-series charts
- Donut chart: white segment borders, dark center annotation text (`#1a1a2e`)
- Bar charts: 6px corner radius
- All charts use a shared `_apply_layout()` helper
- Empty state: centered "No data available" annotation in `#8b8ba3`
- Chart types: line, stacked area, horizontal bar, donut/pie, forecast with confidence band, gauge, anomaly highlight (scatter with X markers)

### Recommendations Engine (recommendations.py)
- MODEL_TIERS dict mapping ~20 Cortex models to high/medium/low tiers with cost_rank and use_case
- DOWNGRADE_MAP suggesting cheaper alternatives
- 7 recommendation generators: budget, agents, model downgrades, caching, long prompts, warehouse sizing, general (scheduling + tagging)
- Each rec has: category, severity (high/medium/low), title, description, savings estimate, SQL template
- Sort by severity (high first)

### HTML Export (export.py)
- Self-contained HTML report with Snowflake brand inline CSS
- Font: Arial, sans-serif
- h1: Midnight (`#000000`) with Snowflake Blue (`#29B5E8`) bottom border
- h2: Mid-Blue (`#11567F`) bold
- KPI cards: `border-top: 3px solid #29B5E8`, values in Midnight, labels in Medium Gray
- Table headers: Mid-Blue (`#11567F`) background, white text
- Run-rate items: light blue background (`#EAF6FC`) with Snowflake Blue top border
- Footer: Medium Gray text
- KPI grid, run rate section, feature breakdown table
- Generated timestamp in footer

### Important Notes
- All ACCOUNT_USAGE views have up to 45-minute latency — display this as a caption/info-chip on every page
- METERING_HISTORY is the billing truth for AI credits; feature-level views provide granular breakdowns but may not sum to the exact same total
- The credit rate should be auto-fetched from RATE_SHEET_DAILY with 24-hour cache, with a None fallback (show "N/A" when unavailable)
- Use `hide_index=True` on all st.dataframe() calls
- Use period-over-period comparison (current period vs same-length prior period) for all delta calculations
- Every page must call `inject_css()` from `utils/styles.py` — the CSS only applies to the currently rendered page in SiS
- Use Snowflake brand colors for accents; the light theme text palette (`#1a1a2e` through `#8b8ba3`) provides readable contrast on white backgrounds
- `st.connection("snowflake").query()` returns `Decimal` types for numeric columns — always convert to `float` in the query layer
- Container runtime shares a single app instance across all viewers — caching benefits everyone
