import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.queries import (
    get_metering_history, get_ai_query_history, get_cortex_usage_history,
    get_cortex_agent_usage, get_warehouse_metering, get_repeated_queries,
    get_credit_rate,
)
from utils.recommendations import generate_recommendations, get_model_reference_table
from utils.sidebar import render_sidebar
from utils.styles import inject_css, section_header, highlight_box, recommendation_card

render_sidebar()
inject_css()

st.header("Cost optimization")

start_date = st.session_state["start_date"]
end_date = st.session_state["end_date"]
credit_rate = st.session_state.get("credit_rate") or get_credit_rate()

st.caption("Recommendations generated from your actual usage data.")

with st.spinner("Analyzing usage patterns..."):
    metering_df = get_metering_history(start_date, end_date)
    cortex_df = get_cortex_usage_history(start_date, end_date)
    agent_df = get_cortex_agent_usage(start_date, end_date)
    warehouse_df = get_warehouse_metering(start_date, end_date)
    repeated_df = get_repeated_queries(start_date, end_date, min_count=3)
    query_df = get_ai_query_history(start_date, end_date, limit=500)

    recs = generate_recommendations(
        metering_df, query_df, cortex_df, agent_df,
        warehouse_df, repeated_df, credit_rate or 0,
    )

if not recs:
    st.info("No specific recommendations at this time. Your AI usage looks efficient!")
else:
    total_savings = 0
    for rec in recs:
        savings_str = rec.get("savings", "")
        if "credits" in savings_str.lower():
            try:
                import re
                nums = re.findall(r"[\d.]+", savings_str.split("credits")[0])
                if nums:
                    total_savings += float(nums[-1])
            except Exception:
                pass

    high_count = sum(1 for r in recs if r.get("severity") == "high")
    med_count = sum(1 for r in recs if r.get("severity") == "medium")

    k1, k2, k3 = st.columns(3)
    k1.metric("Action Items", len(recs))
    k2.metric("High Priority", high_count)
    k3.metric("Potential Savings", f"${total_savings * credit_rate:,.0f}" if credit_rate else f"{total_savings:.1f} credits")

    if total_savings > 0 and credit_rate:
        highlight_box(
            f"We identified <strong>{len(recs)} optimization opportunities</strong> that could save "
            f"up to <strong>${total_savings * credit_rate:,.0f}/month</strong> ({total_savings:.1f} credits). "
            f"<strong>{high_count} high-priority</strong> items should be addressed first."
        )

    categories = sorted(set(r.get("category", "Other") for r in recs))
    for category in categories:
        section_header("\U0001f4cb", category)
        cat_recs = [r for r in recs if r.get("category") == category]

        for rec in cat_recs:
            severity = rec.get("severity", "low")
            icon = {"high": "\U0001f534", "medium": "\U0001f7e1", "low": "\U0001f7e2"}.get(severity, "\U0001f7e2")
            recommendation_card(
                title=rec["title"],
                severity=severity,
                savings=rec.get("savings", "N/A"),
                description=rec.get("description", ""),
                icon=icon,
            )

with st.expander("Technical details"):
    tech_tab_recs, tech_tab_models, tech_tab_data = st.tabs(["SQL templates", "Model reference", "Raw data"])

    with tech_tab_recs:
        if recs:
            for rec in recs:
                if rec.get("sql"):
                    st.markdown(f"**{rec['title']}**")
                    st.code(rec["sql"], language="sql")
        else:
            st.info("No SQL templates available.")

    with tech_tab_models:
        st.caption("Available models with cost tiers and recommended use cases.")
        model_ref = get_model_reference_table()
        if not model_ref.empty:
            for tier in ["High", "Medium", "Low"]:
                tier_df = model_ref[model_ref["Cost Tier"] == tier]
                if not tier_df.empty:
                    icon = {"High": "\U0001f534", "Medium": "\U0001f7e1", "Low": "\U0001f7e2"}[tier]
                    st.markdown(f"{icon} **{tier} cost tier**")
                    st.dataframe(tier_df[["Model", "Recommended Use Case"]], hide_index=True)

        if not cortex_df.empty and "MODEL_NAME" in cortex_df.columns:
            st.markdown("**Your model usage mapped to tiers**")
            from utils.recommendations import MODEL_TIERS
            usage_by_model = cortex_df.groupby("MODEL_NAME").agg(
                TOKEN_CREDITS=("TOKEN_CREDITS", "sum"),
                TOTAL_TOKENS=("TOTAL_TOKENS", "sum"),
                REQUEST_COUNT=("REQUEST_COUNT", "sum"),
            ).reset_index()
            usage_by_model["COST_TIER"] = usage_by_model["MODEL_NAME"].apply(
                lambda x: MODEL_TIERS.get(str(x).lower(), {}).get("tier", "unknown").capitalize()
            )
            st.dataframe(usage_by_model.sort_values("TOKEN_CREDITS", ascending=False), hide_index=True)

    with tech_tab_data:
        with st.expander("Repeated queries (caching candidates)"):
            if not repeated_df.empty:
                st.dataframe(repeated_df, hide_index=True)
            else:
                st.info("No repeated AI queries found (threshold: 3+ identical calls).")

        with st.expander("Warehouse metering (all workloads)"):
            st.caption("Credits below reflect total warehouse compute, not just AI inference.")
            if not warehouse_df.empty:
                wh_summary = warehouse_df.groupby("WAREHOUSE_NAME").agg(
                    TOTAL_CREDITS=("CREDITS_USED", "sum"),
                ).reset_index().sort_values("TOTAL_CREDITS", ascending=False)
                st.dataframe(wh_summary, hide_index=True)
            else:
                st.info("No warehouse metering data available.")

        with st.expander("Agent usage details"):
            if not agent_df.empty:
                st.dataframe(agent_df, hide_index=True)
            else:
                st.info("No Cortex Agent usage data available.")
