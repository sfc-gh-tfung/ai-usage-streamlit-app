import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.queries import get_daily_total_credits, get_credit_rate
from utils.charts import forecast_chart, gauge_chart, anomaly_highlight_chart
from utils.sidebar import render_sidebar
from utils.styles import inject_css, section_header

render_sidebar()
inject_css()

st.header("Alerts & forecast")

start_date = st.session_state.get("start_date", (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
end_date = st.session_state.get("end_date", datetime.now().strftime("%Y-%m-%d"))
credit_rate = st.session_state.get("credit_rate") or get_credit_rate()

st.caption("Forecasts use simple linear regression on historical data. Actual usage may vary.")

with st.spinner("Loading forecast data..."):
    daily_df = get_daily_total_credits(start_date, end_date)

tab_forecast, tab_budget, tab_anomalies, tab_alerts = st.tabs(["Forecast", "Budget gauge", "Anomalies", "Alert SQL"])

with tab_forecast:
    if daily_df.empty:
        st.info("No historical credit data available to generate a forecast.")
    else:
        daily_df = daily_df.sort_values("USAGE_DATE").copy()
        daily_df["USAGE_DATE"] = pd.to_datetime(daily_df["USAGE_DATE"])
        daily_df["DAY_NUM"] = (daily_df["USAGE_DATE"] - daily_df["USAGE_DATE"].min()).dt.days

        if len(daily_df) >= 2:
            x = daily_df["DAY_NUM"].values
            y = daily_df["CREDITS_USED"].values

            coeffs = np.polyfit(x, y, 1)
            slope, intercept = coeffs[0], coeffs[1]
            residuals = y - (slope * x + intercept)
            std_residual = np.std(residuals) if len(residuals) > 0 else 0

            last_date = daily_df["USAGE_DATE"].max()
            last_day_num = daily_df["DAY_NUM"].max()

            forecast_dates = pd.date_range(last_date + timedelta(days=1), periods=30, freq="D")
            forecast_day_nums = np.arange(last_day_num + 1, last_day_num + 31)
            forecast_values = slope * forecast_day_nums + intercept
            forecast_upper = forecast_values + 1.96 * std_residual
            forecast_lower = np.maximum(forecast_values - 1.96 * std_residual, 0)

            forecast_df = pd.DataFrame({
                "USAGE_DATE": forecast_dates,
                "FORECAST": forecast_values,
                "UPPER": forecast_upper,
                "LOWER": forecast_lower,
            })

            projected_30d = forecast_values.sum()
            c1, c2, c3 = st.columns(3)
            c1.metric("Projected 30-day spend", f"{projected_30d:,.1f} credits")
            c2.metric("Projected 30-day cost", f"${projected_30d * credit_rate:,.0f}" if credit_rate else "N/A")
            daily_trend = slope
            c3.metric("Daily trend", f"{daily_trend:+.3f} credits/day")

            fig = forecast_chart(daily_df, forecast_df)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Not enough data points to generate a forecast. Need at least 2 days of data.")

with tab_budget:
    st.caption("Set your monthly credit budget below to track spending.")

    monthly_target = st.number_input(
        "Monthly budget target (credits)",
        min_value=0.0,
        value=100.0,
        step=10.0,
        format="%.0f",
    )

    if not daily_df.empty:
        now = datetime.now()
        month_start = now.replace(day=1).strftime("%Y-%m-%d")
        daily_df_ts = daily_df.copy()
        daily_df_ts["USAGE_DATE"] = pd.to_datetime(daily_df_ts["USAGE_DATE"])
        month_df = daily_df_ts[daily_df_ts["USAGE_DATE"] >= month_start]
        current_month_spend = month_df["CREDITS_USED"].sum() if not month_df.empty else 0
    else:
        current_month_spend = 0

    fig = gauge_chart(current_month_spend, monthly_target)
    st.plotly_chart(fig, use_container_width=True)

    pct = (current_month_spend / monthly_target * 100) if monthly_target > 0 else 0
    days_in_month = 30
    day_of_month = datetime.now().day
    projected_month = (current_month_spend / day_of_month * days_in_month) if day_of_month > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Current month spend", f"{current_month_spend:,.2f} credits")
    c2.metric("Budget used", f"{pct:.1f}%")
    c3.metric("Projected month-end", f"{projected_month:,.1f} credits")

    if pct > 90:
        st.error(f"Budget usage at {pct:.1f}%! Consider immediate action to reduce AI spending.")
    elif pct > 75:
        st.warning(f"Budget usage at {pct:.1f}%. Monitor closely.")
    elif pct > 50:
        st.info(f"Budget usage at {pct:.1f}%. On track.")

with tab_anomalies:
    if daily_df.empty:
        st.info("No daily data available for anomaly detection.")
    else:
        anomaly_df = daily_df.sort_values("USAGE_DATE").copy()
        anomaly_df["USAGE_DATE"] = pd.to_datetime(anomaly_df["USAGE_DATE"])
        anomaly_df["ROLLING_AVG_7D"] = anomaly_df["CREDITS_USED"].rolling(7, min_periods=1).mean()
        anomaly_df["IS_ANOMALY"] = anomaly_df["CREDITS_USED"] > (anomaly_df["ROLLING_AVG_7D"] * 2)

        fig = anomaly_highlight_chart(anomaly_df)
        st.plotly_chart(fig, use_container_width=True)

        anomalies = anomaly_df[anomaly_df["IS_ANOMALY"]]
        if not anomalies.empty:
            section_header("⚠️", f"Anomaly days ({len(anomalies)} detected)")
            st.dataframe(anomalies[["USAGE_DATE", "CREDITS_USED", "ROLLING_AVG_7D"]], hide_index=True)
        else:
            st.success("No anomaly days detected in the selected period.")

with tab_alerts:
    section_header("🔔", "Deploy Snowflake alerts for AI spend monitoring")
    st.caption("Copy and run these SQL snippets to set up automated spend alerts.")

    with st.expander("Alert: Daily AI spend exceeds threshold"):
        st.code("""-- Create a notification integration first (if not exists)
CREATE NOTIFICATION INTEGRATION IF NOT EXISTS ai_spend_email
  TYPE = EMAIL
  ENABLED = TRUE
  ALLOWED_RECIPIENTS = ('your-email@company.com');

-- Alert when daily AI spend exceeds 10 credits
CREATE OR REPLACE ALERT ai_daily_spend_alert
  WAREHOUSE = 'COMPUTE_WH'
  SCHEDULE = 'USING CRON 0 8 * * * UTC'
IF (EXISTS (
    SELECT 1
    FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY
    WHERE START_TIME >= DATEADD('DAY', -1, CURRENT_TIMESTAMP())
      AND SERVICE_TYPE IN ('AI_SERVICES', 'CORTEX_FINE_TUNING', 'SNOWPARK_CONTAINER_SERVICES')
    HAVING SUM(CREDITS_USED) > 10
))
THEN
  CALL SYSTEM$SEND_EMAIL(
    'ai_spend_email',
    'your-email@company.com',
    'AI Spend Alert: Daily threshold exceeded',
    'Daily AI credit consumption exceeded the 10-credit threshold. Please review.'
  );

ALTER ALERT ai_daily_spend_alert RESUME;""", language="sql")

    with st.expander("Alert: Weekly spend anomaly detection"):
        st.code("""-- Alert when weekly spend is 2x the previous week
CREATE OR REPLACE ALERT ai_weekly_anomaly_alert
  WAREHOUSE = 'COMPUTE_WH'
  SCHEDULE = 'USING CRON 0 8 * * 1 UTC'
IF (EXISTS (
    WITH weekly AS (
        SELECT
            DATE_TRUNC('WEEK', START_TIME) AS WEEK_START,
            SUM(CREDITS_USED) AS WEEKLY_CREDITS
        FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY
        WHERE START_TIME >= DATEADD('WEEK', -2, CURRENT_TIMESTAMP())
          AND SERVICE_TYPE IN ('AI_SERVICES', 'CORTEX_FINE_TUNING', 'SNOWPARK_CONTAINER_SERVICES')
        GROUP BY WEEK_START
        ORDER BY WEEK_START DESC
        LIMIT 2
    )
    SELECT 1
    FROM weekly
    QUALIFY WEEKLY_CREDITS > 2 * LAG(WEEKLY_CREDITS) OVER (ORDER BY WEEK_START)
))
THEN
  CALL SYSTEM$SEND_EMAIL(
    'ai_spend_email',
    'your-email@company.com',
    'AI Spend Anomaly: Weekly spend doubled',
    'This week AI credit consumption is more than 2x last week. Investigate immediately.'
  );

ALTER ALERT ai_weekly_anomaly_alert RESUME;""", language="sql")

    with st.expander("Alert: Monthly budget threshold (75%)"):
        st.code(f"""-- Alert when monthly AI spend reaches 75% of budget
CREATE OR REPLACE ALERT ai_monthly_budget_alert
  WAREHOUSE = 'COMPUTE_WH'
  SCHEDULE = 'USING CRON 0 */6 * * * UTC'
IF (EXISTS (
    SELECT 1
    FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY
    WHERE START_TIME >= DATE_TRUNC('MONTH', CURRENT_TIMESTAMP())
      AND SERVICE_TYPE IN ('AI_SERVICES', 'CORTEX_FINE_TUNING', 'SNOWPARK_CONTAINER_SERVICES')
    HAVING SUM(CREDITS_USED) > {monthly_target * 0.75:.0f}
))
THEN
  CALL SYSTEM$SEND_EMAIL(
    'ai_spend_email',
    'your-email@company.com',
    'AI Budget Alert: 75% threshold reached',
    'Monthly AI credit consumption has reached 75% of the {monthly_target:.0f}-credit budget.'
  );

ALTER ALERT ai_monthly_budget_alert RESUME;""", language="sql")

    with st.expander("Resource monitor for hard spend cap"):
        st.code(f"""-- Create a resource monitor as a hard stop
CREATE OR REPLACE RESOURCE MONITOR ai_spend_monitor
  WITH CREDIT_QUOTA = {monthly_target:.0f}
  FREQUENCY = MONTHLY
  START_TIMESTAMP = IMMEDIATELY
  TRIGGERS
    ON 50 PERCENT DO NOTIFY
    ON 75 PERCENT DO NOTIFY
    ON 90 PERCENT DO NOTIFY
    ON 100 PERCENT DO SUSPEND;

-- Assign to specific warehouses used for AI workloads
ALTER WAREHOUSE COMPUTE_WH SET RESOURCE_MONITOR = ai_spend_monitor;""", language="sql")
