import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.sidebar import render_sidebar
from utils.styles import inject_css, section_header, highlight_box, hero_banner
from utils.queries import (
    get_metering_and_daily,
    get_feature_credits_summary,
    get_credit_rate,
)
from utils.charts import daily_credits_line, feature_area_chart, donut_chart
from utils.export import build_html_report

st.set_page_config(page_title="AI on Snowflake", layout="wide")
inject_css()
render_sidebar()

hero_banner("❄️ AI on Snowflake", "Snowflake AI Cost and Usage Monitoring")

start_date = st.session_state.get("start_date", (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
end_date = st.session_state.get("end_date", datetime.now().strftime("%Y-%m-%d"))
days = st.session_state.get("days", 7)
credit_rate = st.session_state.get("credit_rate") or get_credit_rate()

prev_end = start_date
prev_start = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=days)).strftime("%Y-%m-%d")

st.markdown(
    '<div class="info-chip">'
    '<span>ℹ ACCOUNT_USAGE views have up to 45-minute latency</span>'
    '</div>',
    unsafe_allow_html=True,
)

with st.spinner("Loading dashboard data..."):
    metering_df, daily_df = get_metering_and_daily(start_date, end_date)
    prev_metering_df, _ = get_metering_and_daily(prev_start, prev_end)
    feature_df = get_feature_credits_summary(start_date, end_date)
    prev_feature_df = get_feature_credits_summary(prev_start, prev_end)

current_credits = metering_df["CREDITS_USED"].sum() if not metering_df.empty and "CREDITS_USED" in metering_df.columns else 0
prev_credits = prev_metering_df["CREDITS_USED"].sum() if not prev_metering_df.empty and "CREDITS_USED" in prev_metering_df.columns else 0

current_tokens = feature_df["TOKENS"].sum() if not feature_df.empty and "TOKENS" in feature_df.columns else 0
prev_tokens = prev_feature_df["TOKENS"].sum() if not prev_feature_df.empty and "TOKENS" in prev_feature_df.columns else 0

current_requests = feature_df["REQUEST_COUNT"].sum() if not feature_df.empty and "REQUEST_COUNT" in feature_df.columns else 0
prev_requests = prev_feature_df["REQUEST_COUNT"].sum() if not prev_feature_df.empty and "REQUEST_COUNT" in prev_feature_df.columns else 0

credits_delta = f"{((current_credits - prev_credits) / prev_credits * 100):+.1f}%" if prev_credits > 0 else "N/A"
tokens_delta = f"{((current_tokens - prev_tokens) / prev_tokens * 100):+.1f}%" if prev_tokens > 0 else "N/A"
requests_delta = f"{((current_requests - prev_requests) / prev_requests * 100):+.1f}%" if prev_requests > 0 else "N/A"

# ── Highlights ──────────────────────────────────────────────────────
highlights = []
if current_credits > 0 and credit_rate:
    highlights.append(f"<strong>${current_credits * credit_rate:,.2f}</strong> spent ({current_credits:,.2f} credits)")
elif current_credits > 0:
    highlights.append(f"<strong>{current_credits:,.2f} credits</strong> consumed")
if prev_credits > 0 and current_credits > 0:
    pct_change = (current_credits - prev_credits) / prev_credits * 100
    direction = "up" if pct_change > 0 else "down"
    highlights.append(f"{direction} {abs(pct_change):.1f}% vs prior period")
if not feature_df.empty and "CREDITS" in feature_df.columns:
    feat_summary = feature_df.groupby("FEATURE", as_index=False)["CREDITS"].sum().sort_values("CREDITS", ascending=False)
    if not feat_summary.empty and feat_summary["CREDITS"].sum() > 0:
        top_feat = feat_summary.iloc[0]
        top_pct = top_feat["CREDITS"] / feat_summary["CREDITS"].sum() * 100
        highlights.append(f"top feature is <strong>{top_feat['FEATURE']}</strong> ({top_pct:.0f}% of credits)")
if current_requests > 0:
    highlights.append(f"{current_requests:,.0f} requests consuming {current_tokens:,.0f} tokens")
if highlights:
    highlight_box(" · ".join(highlights))

# ── KPI Cards ───────────────────────────────────────────────────────
section_header("📊", "Key metrics")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total AI Credits", f"{current_credits:,.2f}", delta=credits_delta, delta_color="inverse")
k2.metric("Estimated Cost", f"${current_credits * credit_rate:,.2f}" if credit_rate else "N/A", delta=credits_delta if credit_rate else None, delta_color="inverse")
if credit_rate:
    k2.markdown(
        f"<p style='margin-top:-12px;font-size:0.72rem;color:#8b8ba3 !important;'>Based on ${credit_rate:.2f}/credit</p>",
        unsafe_allow_html=True,
    )
k3.metric("Tokens Consumed", f"{current_tokens:,.0f}", delta=tokens_delta, delta_color="inverse")
k4.metric("AI Requests", f"{current_requests:,}", delta=requests_delta, delta_color="inverse")

# ── Run Rate & Unit Economics ───────────────────────────────────────
if current_credits > 0 and days > 0:
    daily_avg = current_credits / days
    monthly_projection = daily_avg * 30
    r1, r2, r3 = st.columns(3)
    monthly_cost = f"${monthly_projection * credit_rate:,.0f}" if credit_rate else f"{monthly_projection:,.1f} cr"
    r1.metric("Monthly Run Rate", monthly_cost)
    if current_requests > 0 and credit_rate:
        r2.metric("Cost per Request", f"${current_credits * credit_rate / current_requests:,.4f}")
    else:
        r2.metric("Cost per Request", "N/A")
    if current_tokens > 0 and credit_rate:
        r3.metric("Cost per 1K Tokens", f"${current_credits * credit_rate / current_tokens * 1000:,.4f}")
    else:
        r3.metric("Cost per 1K Tokens", "N/A")

# ── Charts ──────────────────────────────────────────────────────────
if daily_df.empty and metering_df.empty:
    st.info("No AI usage data found for the selected time range. "
            "This could mean no AI features have been used, or you may need "
            "IMPORTED PRIVILEGES on the SNOWFLAKE database.")
else:
    section_header("📈", "Usage trends")
    col1, col2 = st.columns(2)
    with col1:
        fig_line = daily_credits_line(daily_df)
        st.plotly_chart(fig_line, use_container_width=True)
    with col2:
        fig_area = feature_area_chart(feature_df)
        st.plotly_chart(fig_area, use_container_width=True)

    # ── Feature breakdown ───────────────────────────────────────────
    if not feature_df.empty:
        section_header("🧩", "AI feature breakdown")
        summary = feature_df.groupby("FEATURE", as_index=False).agg(
            CREDITS=("CREDITS", "sum"),
            TOKENS=("TOKENS", "sum"),
            REQUEST_COUNT=("REQUEST_COUNT", "sum"),
        ).sort_values("CREDITS", ascending=False)

        col_donut, col_summary = st.columns([1, 1])
        with col_donut:
            fig_donut = donut_chart(summary, "CREDITS", "FEATURE", title="Credits by AI feature")
            st.plotly_chart(fig_donut, use_container_width=True)

        with col_summary:
            for _, row in summary.iterrows():
                credits_val = row["CREDITS"] if pd.notna(row["CREDITS"]) else 0
                tokens_val = row["TOKENS"] if pd.notna(row["TOKENS"]) else 0
                requests_val = row["REQUEST_COUNT"] if pd.notna(row["REQUEST_COUNT"]) else 0
                pct = (credits_val / summary["CREDITS"].sum() * 100) if summary["CREDITS"].sum() > 0 else 0
                st.markdown(
                    f'<div class="saas-card">'
                    f'<h4>{row["FEATURE"]}</h4>'
                    f'<p>'
                    f'<span class="stat-pill">{credits_val:,.4f} credits</span>'
                    f'<span class="stat-pill">{requests_val:,.0f} requests</span>'
                    f'<span class="stat-pill">{tokens_val:,.0f} tokens</span>'
                    f'<span style="color:#8b8ba3 !important;font-size:0.78rem;margin-left:4px;">{pct:.1f}% of total</span>'
                    f'</p></div>',
                    unsafe_allow_html=True,
                )

# ── Export Section ──────────────────────────────────────────────────
section_header("📤", "Export report")

exp_col1, exp_col2 = st.columns(2)

with exp_col1:
    html_report = build_html_report(
        current_credits, credit_rate, current_tokens, current_requests,
        credits_delta, feature_df, days, start_date, end_date,
    )
    st.download_button(
        label="Download HTML Report",
        data=html_report,
        file_name=f"ai_cost_report_{start_date}_to_{end_date}.html",
        mime="text/html",
    )

with exp_col2:
    st.markdown("**Email report**")
    st.caption("Run the SQL below in a Snowflake worksheet to email this report.")
    email_addr = st.text_input("Recipient email")
    if email_addr:
        email_sql = f"""-- Requires a notification integration
-- CREATE NOTIFICATION INTEGRATION IF NOT EXISTS ai_report_email
--   TYPE = EMAIL ENABLED = TRUE
--   ALLOWED_RECIPIENTS = ('{email_addr}');

CALL SYSTEM$SEND_EMAIL(
  'ai_report_email',
  '{email_addr}',
  'AI Cost Report: {start_date} to {end_date}',
  'AI spend: {current_credits:,.2f} credits ({"${:.2f}".format(current_credits * credit_rate) if credit_rate else "N/A"}). '
  || 'Requests: {current_requests:,.0f}. Tokens: {current_tokens:,.0f}. '
  || 'See the AI Cost Monitor dashboard for full details.'
);"""
        st.code(email_sql, language="sql")
