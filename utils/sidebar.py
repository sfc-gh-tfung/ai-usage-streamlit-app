import streamlit as st
from datetime import timedelta, date
from utils.styles import powered_by_footer

TIME_RANGES = {
    "Last 7 days": 7,
    "Last 14 days": 14,
    "Last 30 days": 30,
    "Last 90 days": 90,
}

OPTIONS = list(TIME_RANGES.keys()) + ["Custom date range"]


def _store_range():
    st.session_state["saved_range"] = st.session_state["_w_range"]


def _store_start():
    st.session_state["saved_start"] = st.session_state["_w_start"]


def _store_end():
    st.session_state["saved_end"] = st.session_state["_w_end"]


def render_sidebar():
    if "saved_range" not in st.session_state:
        st.session_state["saved_range"] = "Last 7 days"
    if "saved_start" not in st.session_state:
        st.session_state["saved_start"] = date.today() - timedelta(days=30)
    if "saved_end" not in st.session_state:
        st.session_state["saved_end"] = date.today()

    st.session_state["_w_range"] = st.session_state["saved_range"]

    with st.sidebar:
        st.markdown(
            '<div style="text-align:center;padding:20px 0 12px 0;">'
            '<div style="font-size:2.4em;margin-bottom:4px;">&#10052;</div>'
            '<div style="font-size:1.1rem;font-weight:600;color:#1a1a2e !important;letter-spacing:-0.01em;">'
            'AI on Snowflake</div>'
            '<div style="font-size:0.72rem;color:#8b8ba3 !important;margin-top:2px;">Cost & Usage Monitor</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div style="border-bottom:1px solid #e8e8ef;margin:8px 0 16px 0;"></div>',
            unsafe_allow_html=True,
        )

        if st.button("Refresh data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown(
            '<div style="border-bottom:1px solid #e8e8ef;margin:8px 0 16px 0;"></div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<p style="font-size:0.78rem;font-weight:500;color:#8b8ba3 !important;'
            'text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Time range</p>',
            unsafe_allow_html=True,
        )
        range_option = st.selectbox(
            "Preset",
            OPTIONS,
            label_visibility="collapsed",
            key="_w_range",
            on_change=_store_range,
        )
        if range_option == "Custom date range":
            st.session_state["_w_start"] = st.session_state["saved_start"]
            st.session_state["_w_end"] = st.session_state["saved_end"]
            col1, col2 = st.columns(2)
            with col1:
                start = st.date_input("Start", key="_w_start", on_change=_store_start)
            with col2:
                end = st.date_input("End", key="_w_end", on_change=_store_end)
        else:
            days = TIME_RANGES[range_option]
            end = date.today()
            start = end - timedelta(days=days)

        st.session_state["start_date"] = start.strftime("%Y-%m-%d")
        st.session_state["end_date"] = (end + timedelta(days=1)).strftime("%Y-%m-%d")
        st.session_state["days"] = (end - start).days

        from utils.queries import get_credit_rate
        fetched_rate = get_credit_rate()
        if fetched_rate is not None:
            st.session_state["credit_rate"] = fetched_rate
        else:
            st.session_state["credit_rate"] = None

        st.markdown(
            '<div style="border-bottom:1px solid #e8e8ef;margin:16px 0 12px 0;"></div>',
            unsafe_allow_html=True,
        )

        with st.expander("About"):
            st.caption(
                "**AI on Snowflake** provides visibility into AI/ML feature "
                "consumption, cost trends, and optimization recommendations.\n\n"
                "Data comes from SNOWFLAKE.ACCOUNT_USAGE views which have up to "
                "45-minute latency. Results may not reflect the most recent activity."
            )

        powered_by_footer()
