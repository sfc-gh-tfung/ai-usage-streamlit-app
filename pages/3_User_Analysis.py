import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.queries import get_user_summary, get_user_ai_consumption, get_credit_rate
from utils.charts import user_bar_chart, multi_user_trend
from utils.sidebar import render_sidebar
from utils.styles import inject_css, section_header

render_sidebar()
inject_css()

st.header("User analysis")

start_date = st.session_state.get("start_date", (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
end_date = st.session_state.get("end_date", datetime.now().strftime("%Y-%m-%d"))
credit_rate = st.session_state.get("credit_rate") or get_credit_rate()

st.caption("ACCOUNT_USAGE views have up to 45-minute latency.")
st.caption("Credits on this page reflect SQL query execution overhead (cloud services), "
           "not AI token inference costs. AI token costs are shown on the Overview and Feature Breakdown pages.")

with st.spinner("Loading user data..."):
    user_summary_df = get_user_summary(start_date, end_date)
    user_daily_df = get_user_ai_consumption(start_date, end_date)

tab_overview, tab_trends, tab_anomalies = st.tabs(["Overview", "User trends", "Anomaly detection"])

with tab_overview:
    if user_summary_df.empty:
        st.info("No AI usage data found for any users in the selected time range.")
    else:
        col1, col2 = st.columns([1, 1])

        with col1:
            fig = user_bar_chart(user_summary_df, x_col="CLOUD_SERVICES_CREDITS",
                                title="Top 20 users by query execution overhead")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            section_header("\U0001f4cb", "User summary")
            display_cols = [c for c in ["USER_NAME", "CLOUD_SERVICES_CREDITS", "TOTAL_QUERIES", "AVG_CLOUD_SERVICES_PER_QUERY", "LAST_ACTIVE"] if c in user_summary_df.columns]
            st.dataframe(user_summary_df[display_cols], hide_index=True)

with tab_trends:
    if not user_daily_df.empty and "USER_NAME" in user_daily_df.columns:
        all_users = sorted(user_daily_df["USER_NAME"].unique())
        selected_users = st.multiselect(
            "Select users to compare (max 5)",
            all_users,
            default=all_users[:min(3, len(all_users))],
            max_selections=5,
        )

        if selected_users:
            filtered = user_daily_df[user_daily_df["USER_NAME"].isin(selected_users)]
            fig = multi_user_trend(filtered, value_col="CLOUD_SERVICES_CREDITS",
                                   title="Per-user query overhead over time")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Select at least one user to see trends.")
    else:
        st.info("No daily user consumption data available.")

with tab_anomalies:
    if not user_daily_df.empty and "CLOUD_SERVICES_CREDITS" in user_daily_df.columns and "USER_NAME" in user_daily_df.columns:
        section_header("\u26a0\ufe0f", "Users with unusual activity spikes")
        st.caption("Flagged when daily usage exceeds 2 standard deviations above their rolling 7-day average.")

        anomaly_records = []
        for user in user_daily_df["USER_NAME"].unique():
            user_data = user_daily_df[user_daily_df["USER_NAME"] == user].sort_values("USAGE_DATE").copy()
            if len(user_data) < 3:
                continue
            user_data["ROLLING_AVG"] = user_data["CLOUD_SERVICES_CREDITS"].rolling(7, min_periods=1).mean()
            user_data["ROLLING_STD"] = user_data["CLOUD_SERVICES_CREDITS"].rolling(7, min_periods=1).std().fillna(0)
            user_data["THRESHOLD"] = user_data["ROLLING_AVG"] + 2 * user_data["ROLLING_STD"]
            spikes = user_data[user_data["CLOUD_SERVICES_CREDITS"] > user_data["THRESHOLD"]]
            for _, spike in spikes.iterrows():
                anomaly_records.append({
                    "USER_NAME": user,
                    "DATE": spike["USAGE_DATE"],
                    "CLOUD_SERVICES_CREDITS": spike["CLOUD_SERVICES_CREDITS"],
                    "ROLLING_AVG": spike["ROLLING_AVG"],
                    "THRESHOLD": spike["THRESHOLD"],
                    "DEVIATION": (spike["CLOUD_SERVICES_CREDITS"] - spike["ROLLING_AVG"]) / spike["ROLLING_STD"] if spike["ROLLING_STD"] > 0 else 0,
                })

        if anomaly_records:
            anomaly_df = pd.DataFrame(anomaly_records).sort_values("CLOUD_SERVICES_CREDITS", ascending=False)
            st.dataframe(anomaly_df, hide_index=True)
        else:
            st.success("No unusual activity spikes detected for any users in this period.")
    else:
        st.info("Insufficient data for anomaly detection.")
