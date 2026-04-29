import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.queries import (
    get_cortex_agent_usage,
    get_feature_credits_summary,
    get_credit_rate,
)
from utils.charts import feature_drilldown_line, feature_area_chart, COLORS
from utils.sidebar import render_sidebar
from utils.styles import inject_css, section_header

render_sidebar()
inject_css()

st.header("Feature breakdown")

start_date = st.session_state["start_date"]
end_date = st.session_state["end_date"]
credit_rate = st.session_state.get("credit_rate") or get_credit_rate()

st.caption("ACCOUNT_USAGE views have up to 45-minute latency.")

with st.spinner("Loading feature data..."):
    feature_df = get_feature_credits_summary(start_date, end_date)

if feature_df.empty:
    st.info("No AI feature usage data found for the selected time range.")
else:
    features_with_data = sorted(feature_df["FEATURE"].unique())
    selected_feature = st.selectbox("Select an AI feature", features_with_data)
    filtered = feature_df[feature_df["FEATURE"] == selected_feature].copy()

    # KPIs for selected feature
    total_credits = filtered["CREDITS"].sum() if "CREDITS" in filtered.columns and filtered["CREDITS"].notna().any() else 0
    total_tokens = filtered["TOKENS"].sum() if "TOKENS" in filtered.columns and filtered["TOKENS"].notna().any() else 0
    total_requests = filtered["REQUEST_COUNT"].sum() if "REQUEST_COUNT" in filtered.columns and filtered["REQUEST_COUNT"].notna().any() else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Credits", f"{total_credits:,.4f}")
    m2.metric("Estimated Cost", f"${total_credits * credit_rate:,.2f}" if credit_rate else "N/A")
    m3.metric("Total Tokens", f"{total_tokens:,.0f}")
    m4.metric("Total Requests", f"{total_requests:,.0f}")

    # Daily trend for selected feature
    section_header("📈", f"{selected_feature} — daily trend")
    daily = filtered.groupby("USAGE_DATE", as_index=False).agg(CREDITS=("CREDITS", "sum"))
    daily = daily[daily["CREDITS"].notna() & (daily["CREDITS"] > 0)]
    fig_line = feature_drilldown_line(daily, title=f"{selected_feature} — Daily credits")
    st.plotly_chart(fig_line, use_container_width=True)

    # Token trend if available
    if filtered["TOKENS"].notna().any() and filtered["TOKENS"].sum() > 0:
        daily_tokens = filtered.groupby("USAGE_DATE", as_index=False).agg(TOKENS=("TOKENS", "sum"))
        daily_tokens = daily_tokens[daily_tokens["TOKENS"].notna() & (daily_tokens["TOKENS"] > 0)]
        if not daily_tokens.empty:
            fig_tokens = feature_drilldown_line(daily_tokens, value_col="TOKENS",
                                                title=f"{selected_feature} — Daily tokens")
            st.plotly_chart(fig_tokens, use_container_width=True)

    # Agent-specific breakdown when Cortex Agents is selected
    if selected_feature == "Cortex Agents":
        section_header("🤖", "Agent breakdown")
        with st.spinner("Loading agent data..."):
            agent_df = get_cortex_agent_usage(start_date, end_date)

        if not agent_df.empty:
            group_cols = [c for c in ["AGENT_NAME", "USER_NAME"] if c in agent_df.columns]
            if not group_cols:
                group_cols = ["AGENT_NAME"]
            agg_dict = {}
            if "TOTAL_TOKENS" in agent_df.columns:
                agg_dict["TOTAL_TOKENS"] = ("TOTAL_TOKENS", "sum")
            if "TOKEN_CREDITS" in agent_df.columns:
                agg_dict["TOKEN_CREDITS"] = ("TOKEN_CREDITS", "sum")
            if "REQUEST_COUNT" in agent_df.columns:
                agg_dict["REQUEST_COUNT"] = ("REQUEST_COUNT", "sum")
            agent_summary = agent_df.groupby(group_cols).agg(**agg_dict).reset_index()
            if "TOKEN_CREDITS" in agent_summary.columns:
                agent_summary = agent_summary.sort_values("TOKEN_CREDITS", ascending=False)

            st.dataframe(agent_summary, hide_index=True)

            if "USAGE_DATE" in agent_df.columns and "TOKEN_CREDITS" in agent_df.columns:
                import plotly.express as px
                daily_agent = agent_df.groupby(["USAGE_DATE", "AGENT_NAME"]).agg(
                    TOKEN_CREDITS=("TOKEN_CREDITS", "sum"),
                ).reset_index()
                fig = px.line(daily_agent, x="USAGE_DATE", y="TOKEN_CREDITS", color="AGENT_NAME",
                              markers=True, title="Agent credits over time")
                fig.update_traces(
                    line=dict(width=2, shape="spline"),
                    marker=dict(size=4),
                    hovertemplate="<b>%{fullData.name}</b><br>%{x|%b %d}: %{y:,.2f} credits<extra></extra>",
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="'Inter', sans-serif", color="#4a4a68"), height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                                font=dict(size=11, color="#6b6b85"), bgcolor="rgba(0,0,0,0)"),
                    hoverlabel=dict(bgcolor="rgba(255, 255, 255, 0.97)", bordercolor="rgba(114, 84, 163, 0.3)",
                                    font=dict(family="'Inter', sans-serif", size=12, color="#1a1a2e")),
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No agent-level data available for this period.")

    # Raw data
    with st.expander("Raw data"):
        st.dataframe(filtered.sort_values("USAGE_DATE", ascending=False))
