import streamlit as st
import pandas as pd
from decimal import Decimal

AI_SERVICE_TYPES = ("'AI_SERVICES'", "'CORTEX_FINE_TUNING'", "'SNOWPARK_CONTAINER_SERVICES'")

AI_FUNCTIONS = [
    "AI_COMPLETE", "AI_CLASSIFY", "AI_EXTRACT", "AI_FILTER", "AI_SENTIMENT",
    "AI_SUMMARIZE", "AI_TRANSLATE", "AI_EMBED", "AI_AGG", "AI_REDACT",
    "AI_PARSE_DOCUMENT", "COMPLETE", "EMBED_TEXT", "EXTRACT_ANSWER",
    "SENTIMENT", "SUMMARIZE", "TRANSLATE",
]


def _get_conn():
    return st.connection("snowflake")


def _build_ai_function_filter_simple():
    clauses = " OR ".join([f"QUERY_TEXT ILIKE '%{fn}%'" for fn in ["AI_COMPLETE", "AI_CLASSIFY", "AI_EXTRACT", "AI_FILTER", "AI_SENTIMENT", "AI_SUMMARIZE", "AI_TRANSLATE", "AI_EMBED", "AI_PARSE_DOCUMENT", "COMPLETE(", "EMBED_TEXT(", "EXTRACT_ANSWER(", "SENTIMENT(", "SUMMARIZE(", "TRANSLATE("]])
    return f"({clauses})"


@st.cache_data(ttl=600, show_spinner=False)
def _run_query(sql):
    conn = _get_conn()
    df = conn.query(sql)
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, Decimal)).any():
            df[col] = df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
    return df


def _safe_run(sql):
    try:
        return _run_query(sql)
    except Exception:
        return pd.DataFrame()


def safe_query(sql, error_msg="Query failed"):
    try:
        return _run_query(sql)
    except Exception as e:
        st.warning(f"{error_msg}: {e}")
        return pd.DataFrame()


def get_metering_history(start_date, end_date):
    sql = f"""
    SELECT
        SERVICE_TYPE,
        DATE_TRUNC('DAY', START_TIME) AS USAGE_DATE,
        SUM(CREDITS_USED) AS CREDITS_USED
    FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY
    WHERE START_TIME >= '{start_date}'
      AND START_TIME < '{end_date}'
      AND SERVICE_TYPE IN ({','.join(AI_SERVICE_TYPES)})
    GROUP BY SERVICE_TYPE, USAGE_DATE
    ORDER BY USAGE_DATE
    """
    return safe_query(sql, "Could not query METERING_HISTORY")


def get_daily_total_credits(start_date, end_date):
    sql = f"""
    SELECT
        DATE_TRUNC('DAY', START_TIME) AS USAGE_DATE,
        SUM(CREDITS_USED) AS CREDITS_USED
    FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY
    WHERE START_TIME >= '{start_date}'
      AND START_TIME < '{end_date}'
      AND SERVICE_TYPE IN ({','.join(AI_SERVICE_TYPES)})
    GROUP BY USAGE_DATE
    ORDER BY USAGE_DATE
    """
    return safe_query(sql, "Could not query daily credits")


@st.cache_data(ttl=600, show_spinner=False)
def get_metering_and_daily(start_date, end_date):
    sql = f"""
    SELECT
        SERVICE_TYPE,
        DATE_TRUNC('DAY', START_TIME) AS USAGE_DATE,
        SUM(CREDITS_USED) AS CREDITS_USED
    FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY
    WHERE START_TIME >= '{start_date}'
      AND START_TIME < '{end_date}'
      AND SERVICE_TYPE IN ({','.join(AI_SERVICE_TYPES)})
    GROUP BY SERVICE_TYPE, USAGE_DATE
    ORDER BY USAGE_DATE
    """
    metering_df = _safe_run(sql)
    if metering_df.empty:
        return metering_df, pd.DataFrame()
    daily_df = metering_df.groupby("USAGE_DATE", as_index=False)["CREDITS_USED"].sum()
    return metering_df, daily_df


def get_ai_query_history(start_date, end_date, limit=1000):
    fn_filter = _build_ai_function_filter_simple()
    sql = f"""
    SELECT
        QUERY_ID,
        LEFT(QUERY_TEXT, 300) AS QUERY_TEXT,
        USER_NAME,
        WAREHOUSE_NAME,
        DATABASE_NAME,
        SCHEMA_NAME,
        EXECUTION_STATUS,
        START_TIME,
        END_TIME,
        TOTAL_ELAPSED_TIME,
        CREDITS_USED_CLOUD_SERVICES,
        ROWS_PRODUCED,
        BYTES_SCANNED
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
    WHERE START_TIME >= '{start_date}'
      AND START_TIME < '{end_date}'
      AND {fn_filter}
      AND EXECUTION_STATUS = 'SUCCESS'
    ORDER BY START_TIME DESC
    LIMIT {limit}
    """
    return safe_query(sql, "Could not query QUERY_HISTORY")


def get_warehouse_metering(start_date, end_date):
    sql = f"""
    SELECT
        WAREHOUSE_NAME,
        DATE_TRUNC('DAY', START_TIME) AS USAGE_DATE,
        SUM(CREDITS_USED) AS CREDITS_USED
    FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
    WHERE START_TIME >= '{start_date}'
      AND START_TIME < '{end_date}'
    GROUP BY WAREHOUSE_NAME, USAGE_DATE
    ORDER BY USAGE_DATE
    """
    return safe_query(sql, "Could not query WAREHOUSE_METERING_HISTORY")


def get_cortex_usage_history(start_date, end_date):
    sql = f"""
    SELECT
        FUNCTION_NAME,
        MODEL_NAME,
        DATE_TRUNC('DAY', START_TIME) AS USAGE_DATE,
        SUM(TOKENS) AS TOTAL_TOKENS,
        SUM(TOKEN_CREDITS) AS TOKEN_CREDITS,
        COUNT(*) AS REQUEST_COUNT
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_USAGE_HISTORY
    WHERE START_TIME >= '{start_date}'
      AND START_TIME < '{end_date}'
    GROUP BY FUNCTION_NAME, MODEL_NAME, USAGE_DATE
    ORDER BY USAGE_DATE
    """
    return safe_query(sql, "CORTEX_FUNCTIONS_USAGE_HISTORY not available")


def get_cortex_agent_usage(start_date, end_date):
    sql = f"""
    SELECT
        AGENT_NAME,
        USER_NAME,
        DATE_TRUNC('DAY', START_TIME) AS USAGE_DATE,
        SUM(TOKENS) AS TOTAL_TOKENS,
        SUM(TOKEN_CREDITS) AS TOKEN_CREDITS,
        COUNT(*) AS REQUEST_COUNT
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY
    WHERE START_TIME >= '{start_date}'
      AND START_TIME < '{end_date}'
    GROUP BY AGENT_NAME, USER_NAME, USAGE_DATE
    ORDER BY USAGE_DATE
    """
    return safe_query(sql, "CORTEX_AGENT_USAGE_HISTORY not available")


def get_user_ai_consumption(start_date, end_date):
    fn_filter = _build_ai_function_filter_simple()
    sql = f"""
    SELECT
        USER_NAME,
        DATE_TRUNC('DAY', START_TIME) AS USAGE_DATE,
        COUNT(*) AS QUERY_COUNT,
        SUM(CREDITS_USED_CLOUD_SERVICES) AS CLOUD_SERVICES_CREDITS,
        MAX(START_TIME) AS LAST_ACTIVE
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
    WHERE START_TIME >= '{start_date}'
      AND START_TIME < '{end_date}'
      AND {fn_filter}
      AND EXECUTION_STATUS = 'SUCCESS'
    GROUP BY USER_NAME, USAGE_DATE
    ORDER BY USAGE_DATE
    """
    return safe_query(sql, "Could not query user AI consumption")


def get_user_summary(start_date, end_date):
    fn_filter = _build_ai_function_filter_simple()
    sql = f"""
    SELECT
        USER_NAME,
        COUNT(*) AS TOTAL_QUERIES,
        SUM(CREDITS_USED_CLOUD_SERVICES) AS CLOUD_SERVICES_CREDITS,
        AVG(CREDITS_USED_CLOUD_SERVICES) AS AVG_CLOUD_SERVICES_PER_QUERY,
        MAX(START_TIME) AS LAST_ACTIVE
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
    WHERE START_TIME >= '{start_date}'
      AND START_TIME < '{end_date}'
      AND {fn_filter}
      AND EXECUTION_STATUS = 'SUCCESS'
    GROUP BY USER_NAME
    ORDER BY CLOUD_SERVICES_CREDITS DESC
    LIMIT 20
    """
    return safe_query(sql, "Could not query user summary")


def get_connection_info():
    sql = "SELECT CURRENT_ROLE() AS ROLE, CURRENT_WAREHOUSE() AS WAREHOUSE, CURRENT_ACCOUNT() AS ACCOUNT, CURRENT_USER() AS USERNAME"
    return safe_query(sql, "Could not fetch connection info")


@st.cache_data(ttl=86400, show_spinner=False)
def get_credit_rate():
    sql = """
    SELECT EFFECTIVE_RATE
    FROM SNOWFLAKE.ORGANIZATION_USAGE.RATE_SHEET_DAILY
    WHERE ACCOUNT_LOCATOR = CURRENT_ACCOUNT()
      AND USAGE_TYPE = 'overage-compute'
    ORDER BY DATE DESC
    LIMIT 1
    """
    try:
        df = _run_query(sql)
        if not df.empty and "EFFECTIVE_RATE" in df.columns:
            return float(df.iloc[0]["EFFECTIVE_RATE"])
    except Exception:
        pass
    return None


def get_repeated_queries(start_date, end_date, min_count=3):
    fn_filter = _build_ai_function_filter_simple()
    sql = f"""
    SELECT
        MD5(QUERY_TEXT) AS QUERY_HASH,
        ANY_VALUE(LEFT(QUERY_TEXT, 200)) AS SAMPLE_QUERY,
        COUNT(*) AS EXECUTION_COUNT,
        SUM(CREDITS_USED_CLOUD_SERVICES) AS TOTAL_CREDITS,
        ANY_VALUE(USER_NAME) AS USER_NAME
    FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
    WHERE START_TIME >= '{start_date}'
      AND START_TIME < '{end_date}'
      AND {fn_filter}
      AND EXECUTION_STATUS = 'SUCCESS'
    GROUP BY MD5(QUERY_TEXT)
    HAVING COUNT(*) >= {min_count}
    ORDER BY TOTAL_CREDITS DESC
    LIMIT 50
    """
    return safe_query(sql, "Could not query repeated AI calls")


@st.cache_data(ttl=600, show_spinner=False)
def get_feature_credits_summary(start_date, end_date):
    features = []

    sql = f"""
    SELECT 'Cortex Functions' AS FEATURE,
           DATE_TRUNC('DAY', START_TIME) AS USAGE_DATE,
           SUM(TOKEN_CREDITS) AS CREDITS,
           SUM(TOKENS) AS TOKENS,
           COUNT(*) AS REQUEST_COUNT
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_USAGE_HISTORY
    WHERE START_TIME >= '{start_date}' AND START_TIME < '{end_date}'
    GROUP BY USAGE_DATE ORDER BY USAGE_DATE
    """
    features.append(_safe_run(sql))

    sql = f"""
    SELECT 'Cortex Analyst' AS FEATURE,
           DATE_TRUNC('DAY', START_TIME) AS USAGE_DATE,
           SUM(CREDITS) AS CREDITS,
           NULL AS TOKENS,
           SUM(REQUEST_COUNT) AS REQUEST_COUNT
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_ANALYST_USAGE_HISTORY
    WHERE START_TIME >= '{start_date}' AND START_TIME < '{end_date}'
    GROUP BY USAGE_DATE ORDER BY USAGE_DATE
    """
    features.append(_safe_run(sql))

    sql = f"""
    SELECT 'Cortex Search' AS FEATURE,
           USAGE_DATE,
           SUM(CREDITS) AS CREDITS,
           SUM(TOKENS) AS TOKENS,
           NULL AS REQUEST_COUNT
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_SEARCH_DAILY_USAGE_HISTORY
    WHERE USAGE_DATE >= '{start_date}' AND USAGE_DATE < '{end_date}'
    GROUP BY USAGE_DATE ORDER BY USAGE_DATE
    """
    features.append(_safe_run(sql))

    sql = f"""
    SELECT 'Cortex Agents' AS FEATURE,
           DATE_TRUNC('DAY', START_TIME) AS USAGE_DATE,
           SUM(TOKEN_CREDITS) AS CREDITS,
           SUM(TOKENS) AS TOKENS,
           COUNT(*) AS REQUEST_COUNT
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY
    WHERE START_TIME >= '{start_date}' AND START_TIME < '{end_date}'
    GROUP BY USAGE_DATE ORDER BY USAGE_DATE
    """
    features.append(_safe_run(sql))

    sql = f"""
    SELECT 'Snowflake Intelligence' AS FEATURE,
           DATE_TRUNC('DAY', START_TIME) AS USAGE_DATE,
           SUM(TOKEN_CREDITS) AS CREDITS,
           SUM(TOKENS) AS TOKENS,
           COUNT(*) AS REQUEST_COUNT
    FROM SNOWFLAKE.ACCOUNT_USAGE.SNOWFLAKE_INTELLIGENCE_USAGE_HISTORY
    WHERE START_TIME >= '{start_date}' AND START_TIME < '{end_date}'
    GROUP BY USAGE_DATE ORDER BY USAGE_DATE
    """
    features.append(_safe_run(sql))

    sql = f"""
    SELECT 'Cortex Code' AS FEATURE,
           DATE_TRUNC('DAY', USAGE_TIME) AS USAGE_DATE,
           SUM(TOKEN_CREDITS) AS CREDITS,
           SUM(TOKENS) AS TOKENS,
           COUNT(*) AS REQUEST_COUNT
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY
    WHERE USAGE_TIME >= '{start_date}' AND USAGE_TIME < '{end_date}'
    GROUP BY USAGE_DATE ORDER BY USAGE_DATE
    """
    features.append(_safe_run(sql))

    sql = f"""
    SELECT 'Document AI' AS FEATURE,
           DATE_TRUNC('DAY', START_TIME) AS USAGE_DATE,
           SUM(CREDITS_USED) AS CREDITS,
           NULL AS TOKENS,
           COUNT(*) AS REQUEST_COUNT
    FROM SNOWFLAKE.ACCOUNT_USAGE.DOCUMENT_AI_USAGE_HISTORY
    WHERE START_TIME >= '{start_date}' AND START_TIME < '{end_date}'
    GROUP BY USAGE_DATE ORDER BY USAGE_DATE
    """
    features.append(_safe_run(sql))

    sql = f"""
    SELECT 'Cortex Fine-Tuning' AS FEATURE,
           DATE_TRUNC('DAY', START_TIME) AS USAGE_DATE,
           SUM(TOKEN_CREDITS) AS CREDITS,
           SUM(TOKENS) AS TOKENS,
           COUNT(*) AS REQUEST_COUNT
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FINE_TUNING_USAGE_HISTORY
    WHERE START_TIME >= '{start_date}' AND START_TIME < '{end_date}'
    GROUP BY USAGE_DATE ORDER BY USAGE_DATE
    """
    features.append(_safe_run(sql))

    sql = f"""
    SELECT 'Cortex REST API' AS FEATURE,
           DATE_TRUNC('DAY', START_TIME) AS USAGE_DATE,
           NULL AS CREDITS,
           SUM(TOKENS) AS TOKENS,
           COUNT(*) AS REQUEST_COUNT
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY
    WHERE START_TIME >= '{start_date}' AND START_TIME < '{end_date}'
    GROUP BY USAGE_DATE ORDER BY USAGE_DATE
    """
    features.append(_safe_run(sql))

    non_empty = [df for df in features if not df.empty]
    if not non_empty:
        return pd.DataFrame()
    return pd.concat(non_empty, ignore_index=True)
