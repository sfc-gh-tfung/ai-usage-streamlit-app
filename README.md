# AI on Snowflake — Cost & Usage Monitor

A Streamlit-in-Snowflake dashboard for monitoring Cortex AI feature usage, costs, and optimization opportunities. Runs on **container runtime** for shared caching and fast load times.

![Runtime](https://img.shields.io/badge/runtime-container-blue) ![Python](https://img.shields.io/badge/python-3.11-green) ![Streamlit](https://img.shields.io/badge/streamlit-1.50+-red)

## What it does

- **Overview** — KPI metrics, period-over-period deltas, daily trends, feature breakdown, exportable HTML reports
- **Feature Breakdown** — Drill into each AI feature (Cortex Functions, Agents, Analyst, Search, etc.) with daily credit/token charts
- **User Analysis** — Per-user query overhead, trend comparison, and anomaly detection
- **Cost Optimization** — Data-driven recommendations for budgets, model downgrades, caching, and warehouse sizing
- **Alerts & Forecast** — 30-day linear forecast, budget gauge, anomaly detection, and ready-to-copy alert SQL templates

## Prerequisites

- Snowflake account (Enterprise edition or higher recommended)
- ACCOUNTADMIN role (or a role with `IMPORTED PRIVILEGES` on the `SNOWFLAKE` database)
- A compute pool for container runtime (or use an existing one like `SYSTEM_COMPUTE_POOL_CPU`)
- An external access integration for PyPI packages (e.g., `PYPI_ACCESS_INTEGRATION`)
- A warehouse for SQL queries
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) v3.14.0+ (`snow`)

## Data sources

All data comes from built-in Snowflake views — no external data or additional tables required:

| View | Purpose |
|------|---------|
| `SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY` | AI credit consumption (billing truth) |
| `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_USAGE_HISTORY` | LLM function usage |
| `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_ANALYST_USAGE_HISTORY` | Cortex Analyst usage |
| `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_SEARCH_DAILY_USAGE_HISTORY` | Cortex Search usage |
| `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY` | Cortex Agent usage |
| `SNOWFLAKE.ACCOUNT_USAGE.SNOWFLAKE_INTELLIGENCE_USAGE_HISTORY` | Snowflake Intelligence |
| `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY` | Cortex Code CLI |
| `SNOWFLAKE.ACCOUNT_USAGE.DOCUMENT_AI_USAGE_HISTORY` | Document AI |
| `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FINE_TUNING_USAGE_HISTORY` | Fine-tuning jobs |
| `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY` | REST API calls |
| `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` | AI query details, user analysis |
| `SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY` | Warehouse compute |
| `SNOWFLAKE.ORGANIZATION_USAGE.RATE_SHEET_DAILY` | $/credit rate (auto-fetched) |

## Deployment (5 minutes)

### Step 1: Configure Snowflake CLI

If you don't have a Snowflake CLI connection, create one:

```bash
snow connection add
```

### Step 2: Run the setup SQL

Open a Snowflake worksheet with the ACCOUNTADMIN role, and run `setup.sql`. This creates:
- Database and schema for the app
- A compute pool for container runtime (or you can use an existing one)
- Grants `IMPORTED PRIVILEGES` on the `SNOWFLAKE` database

```bash
snow sql -f setup.sql --connection <your_connection>
```

### Step 3: Update `snowflake.yml`

Edit `snowflake.yml` to match your environment:

```yaml
definition_version: 2
entities:
  ai_cost_monitor:
    type: streamlit
    identifier:
      name: AI_COST_MONITOR
      database: AI_MONITOR_DB          # your database
      schema: STREAMLIT_APP            # your schema
    query_warehouse: COMPUTE_WH        # your warehouse
    runtime_name: SYSTEM$ST_CONTAINER_RUNTIME_PY3_11
    compute_pool: STREAMLIT_COMPUTE_POOL  # your compute pool
    external_access_integrations:
      - PYPI_ACCESS_INTEGRATION        # your PyPI integration
    main_file: Overview.py
    artifacts:
      - Overview.py
      - pyproject.toml
      - pages/2_Feature_Breakdown.py
      - pages/3_User_Analysis.py
      - pages/4_Optimization.py
      - pages/5_Alerts & Forecast.py
      - utils/__init__.py
      - utils/charts.py
      - utils/export.py
      - utils/queries.py
      - utils/recommendations.py
      - utils/sidebar.py
      - utils/styles.py
```

### Step 4: Deploy

```bash
snow streamlit deploy --replace --connection <your_connection>
```

Or use the included deploy script:

```bash
chmod +x deploy.sh
./deploy.sh <your_connection>
```

### Step 5: Open the app

Navigate to **Projects > Streamlit** in Snowsight and open **AI Cost Monitor**.

## File structure

```
Overview.py                    # Main dashboard page
pyproject.toml                 # Python dependencies (container runtime)
snowflake.yml                  # Deployment manifest
environment.yml                # Legacy warehouse runtime deps (not used)
pages/
  2_Feature_Breakdown.py       # Per-feature drilldown
  3_User_Analysis.py           # User-level consumption
  4_Optimization.py            # Cost optimization recommendations
  5_Alerts & Forecast.py       # Forecasting, budget, anomaly detection, alert SQL
utils/
  __init__.py
  charts.py                    # Plotly chart functions
  export.py                    # HTML report generator
  queries.py                   # All Snowflake SQL queries (cached)
  recommendations.py           # Optimization recommendation engine
  sidebar.py                   # Shared sidebar with time range picker + refresh button
  styles.py                    # CSS theme
setup.sql                      # One-time database/schema/compute pool setup
deploy.sh                      # Automated deployment script
```

## Customization

- **Warehouse**: Edit `query_warehouse` in `snowflake.yml`
- **Compute pool**: Edit `compute_pool` in `snowflake.yml`
- **Database/Schema**: Edit `identifier.database` and `identifier.schema` in `snowflake.yml`
- **Budget defaults**: The Alerts & Forecast page lets users set budget targets interactively
- **Credit rate**: Automatically fetched from `RATE_SHEET_DAILY`; displays "N/A" if unavailable
- **Cache TTL**: Query results cached for 10 minutes; use the sidebar **Refresh data** button to clear cache

## Notes

- ACCOUNT_USAGE views have up to **45-minute latency**. Data may not reflect the most recent activity.
- The credit rate is auto-fetched from `ORGANIZATION_USAGE.RATE_SHEET_DAILY`. This requires the ORGADMIN role or appropriate privileges. If unavailable, cost estimates show "N/A".
- Container runtime shares a single app instance across all viewers — caching benefits everyone.
- No data leaves your Snowflake account. All queries run inside Snowflake.
