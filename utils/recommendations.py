import pandas as pd

MODEL_TIERS = {
    # High tier – most capable, highest cost per token
    "claude-4-sonnet": {"tier": "high", "cost_rank": 5, "use_case": "Most complex reasoning, code generation, analysis"},
    "claude-3-7-sonnet": {"tier": "high", "cost_rank": 5, "use_case": "Complex reasoning, code generation, analysis"},
    "claude-3-5-sonnet": {"tier": "high", "cost_rank": 5, "use_case": "Complex reasoning, code generation, analysis"},
    "claude-3.5-sonnet": {"tier": "high", "cost_rank": 5, "use_case": "Complex reasoning, code generation, analysis"},
    "deepseek-r1": {"tier": "high", "cost_rank": 5, "use_case": "Advanced reasoning, chain-of-thought tasks"},
    "openai-gpt-4.1": {"tier": "high", "cost_rank": 5, "use_case": "Complex reasoning, instruction following"},
    "llama3.1-405b": {"tier": "high", "cost_rank": 4, "use_case": "Complex open-source alternative"},
    "snowflake-llama-3.1-405b": {"tier": "high", "cost_rank": 4, "use_case": "Complex open-source, Snowflake-optimized"},
    "openai-gpt-oss-120b": {"tier": "high", "cost_rank": 4, "use_case": "Large-scale open-source reasoning"},
    # Medium tier – good quality/cost balance
    "mistral-large2": {"tier": "medium", "cost_rank": 3, "use_case": "General purpose, good quality/cost balance"},
    "llama3.1-70b": {"tier": "medium", "cost_rank": 3, "use_case": "General purpose open-source"},
    "llama3.3-70b": {"tier": "medium", "cost_rank": 3, "use_case": "General purpose open-source, updated"},
    "snowflake-llama-3.3-70b": {"tier": "medium", "cost_rank": 3, "use_case": "General purpose, Snowflake-optimized"},
    "llama4-maverick": {"tier": "medium", "cost_rank": 3, "use_case": "Next-gen open-source reasoning"},
    "llama4-scout": {"tier": "medium", "cost_rank": 3, "use_case": "Next-gen open-source, efficient"},
    "openai-gpt-oss-20b": {"tier": "medium", "cost_rank": 2, "use_case": "Mid-size open-source reasoning"},
    # Low tier – cost-effective for simple tasks
    "mixtral-8x7b": {"tier": "low", "cost_rank": 2, "use_case": "Cost-effective mixture of experts"},
    "llama3.1-8b": {"tier": "low", "cost_rank": 1, "use_case": "Simple tasks, classification, extraction"},
    "mistral-7b": {"tier": "low", "cost_rank": 1, "use_case": "Simple tasks, fast inference"},
    "snowflake-arctic": {"tier": "low", "cost_rank": 1, "use_case": "Enterprise SQL and coding tasks"},
}

DOWNGRADE_MAP = {
    "claude-4-sonnet": "claude-3-7-sonnet",
    "claude-3-7-sonnet": "llama3.3-70b",
    "claude-3-5-sonnet": "llama3.1-70b",
    "claude-3.5-sonnet": "llama3.1-70b",
    "deepseek-r1": "llama3.3-70b",
    "openai-gpt-4.1": "mistral-large2",
    "openai-gpt-oss-120b": "llama3.1-70b",
    "llama3.1-405b": "llama3.1-70b",
    "snowflake-llama-3.1-405b": "snowflake-llama-3.3-70b",
    "mistral-large2": "mixtral-8x7b",
    "llama3.1-70b": "llama3.1-8b",
    "llama3.3-70b": "llama3.1-8b",
    "llama4-maverick": "llama4-scout",
    "openai-gpt-oss-20b": "llama3.1-8b",
}


def generate_recommendations(metering_df, query_df, cortex_df, agent_df,
                             warehouse_df, repeated_df, credit_rate=4.0):
    recs = []

    recs.extend(_budget_recommendations(metering_df, credit_rate))
    recs.extend(_agent_recommendations(agent_df, credit_rate))
    recs.extend(_model_downgrade_recommendations(query_df, cortex_df, credit_rate))
    recs.extend(_caching_recommendations(repeated_df, credit_rate))
    recs.extend(_long_prompt_recommendations(query_df, credit_rate))
    recs.extend(_warehouse_recommendations(warehouse_df, credit_rate))
    recs.extend(_general_recommendations(query_df, metering_df))

    recs.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("severity", "low"), 3))
    return recs


def _budget_recommendations(metering_df, credit_rate):
    recs = []
    if metering_df.empty:
        recs.append({
            "category": "Budget Controls",
            "severity": "high",
            "title": "Set up AI spending budget",
            "description": "No AI metering data found, but it's best practice to set up a budget proactively.",
            "savings": "Prevents unexpected overspend",
            "sql": """-- Create a budget for AI services (run in a schema you own)
CREATE SNOWFLAKE.CORE.BUDGET ai_services_budget();

-- Set the monthly spending limit (adjust based on expected usage)
CALL ai_services_budget!SET_SPENDING_LIMIT(1000);

-- Set up email notifications (requires a notification integration)
CALL ai_services_budget!SET_EMAIL_NOTIFICATIONS(
  'my_notification_integration',
  'admin@example.com'
);"""
        })
        return recs

    total_credits = metering_df["CREDITS_USED"].sum() if "CREDITS_USED" in metering_df.columns else 0
    if "USAGE_DATE" in metering_df.columns:
        n_days = max(metering_df["USAGE_DATE"].nunique(), 1)
    else:
        n_days = 30
    daily_avg = total_credits / n_days
    monthly_estimate = daily_avg * 30
    suggested_budget = round(monthly_estimate * 1.2, 0)

    recs.append({
        "category": "Budget Controls",
        "severity": "high",
        "title": "Create an AI services budget",
        "description": (f"Based on trailing usage ({daily_avg:.1f} credits/day), estimated monthly spend "
                        f"is ~{monthly_estimate:.0f} credits (${monthly_estimate * credit_rate:,.0f}). "
                        f"Recommended budget: {suggested_budget:.0f} credits with 20% buffer."),
        "savings": f"Prevents overspend beyond ${suggested_budget * credit_rate:,.0f}/month",
        "sql": f"""-- Create a budget for AI services (run in a schema you own)
CREATE SNOWFLAKE.CORE.BUDGET ai_services_budget();

-- Set the monthly spending limit
CALL ai_services_budget!SET_SPENDING_LIMIT({suggested_budget:.0f});

-- Set up email notifications (requires a notification integration)
CALL ai_services_budget!SET_EMAIL_NOTIFICATIONS(
  'my_notification_integration',
  'admin@example.com'
);"""
    })

    recs.append({
        "category": "Budget Controls",
        "severity": "medium",
        "title": "Create a resource monitor as backup",
        "description": "Resource monitors provide an additional safety net by suspending warehouses when credit limits are reached.",
        "savings": "Hard stop on runaway costs",
        "sql": f"""CREATE RESOURCE MONITOR ai_resource_monitor
  WITH CREDIT_QUOTA = {suggested_budget:.0f}
  FREQUENCY = MONTHLY
  START_TIMESTAMP = IMMEDIATELY
  TRIGGERS
    ON 50 PERCENT DO NOTIFY
    ON 75 PERCENT DO NOTIFY
    ON 90 PERCENT DO NOTIFY
    ON 100 PERCENT DO SUSPEND;"""
    })

    return recs


def _agent_recommendations(agent_df, credit_rate):
    recs = []
    if agent_df.empty:
        return recs

    total_tokens = 0
    if "TOTAL_TOKENS" in agent_df.columns:
        total_tokens = agent_df["TOTAL_TOKENS"].sum()

    if total_tokens > 100000:
        agent_names = agent_df["AGENT_NAME"].unique() if "AGENT_NAME" in agent_df.columns else []
        for agent_name in agent_names[:5]:
            agent_data = agent_df[agent_df["AGENT_NAME"] == agent_name]
            avg_tokens = agent_data["TOTAL_TOKENS"].mean() if "TOTAL_TOKENS" in agent_data.columns else 0
            total_agent_credits = agent_data["TOKEN_CREDITS"].sum() if "TOKEN_CREDITS" in agent_data.columns else 0

            recs.append({
                "category": "Agent Controls",
                "severity": "high" if total_agent_credits > 10 else "medium",
                "title": f"Set token limits on agent: {agent_name}",
                "description": (f"Agent '{agent_name}' averages {avg_tokens:.0f} tokens per request. "
                                f"Total credits: {total_agent_credits:.4f}. "
                                f"Setting a token budget in the agent specification can prevent runaway costs."),
                "savings": f"Up to {total_agent_credits * 0.2:.1f} credits ({total_agent_credits * 0.2 * credit_rate:.0f}$)",
                "sql": f"""-- Set token budget on agent via specification
ALTER AGENT {agent_name} MODIFY LIVE VERSION SET SPECIFICATION =
$$
orchestration:
  budget:
    seconds: 30
    tokens: 4096
$$;"""
            })

    return recs


def _model_downgrade_recommendations(query_df, cortex_df, credit_rate):
    recs = []
    if query_df.empty and cortex_df.empty:
        return recs

    model_usage = {}
    if not cortex_df.empty and "MODEL_NAME" in cortex_df.columns:
        for _, row in cortex_df.iterrows():
            model = str(row.get("MODEL_NAME", "")).lower()
            credits = row.get("TOKEN_CREDITS", 0) or 0
            count = row.get("REQUEST_COUNT", 0) or 0
            if model in model_usage:
                model_usage[model]["credits"] += credits
                model_usage[model]["count"] += count
            else:
                model_usage[model] = {"credits": credits, "count": count}

    for model, usage in model_usage.items():
        if model in DOWNGRADE_MAP:
            alt = DOWNGRADE_MAP[model]
            current_tier = MODEL_TIERS.get(model, {})
            alt_tier = MODEL_TIERS.get(alt, {})
            current_rank = current_tier.get("cost_rank", 3)
            alt_rank = alt_tier.get("cost_rank", 1)
            savings_pct = max(0, (current_rank - alt_rank) / current_rank * 100) if current_rank > 0 else 0
            estimated_savings = usage["credits"] * (savings_pct / 100)

            if estimated_savings > 0.1:
                recs.append({
                    "category": "Model Selection",
                    "severity": "high" if estimated_savings > 5 else "medium",
                    "title": f"Consider downgrading from {model} to {alt}",
                    "description": (f"You used {model} for {usage['count']} requests ({usage['credits']:.2f} credits). "
                                   f"Switching to {alt} could save ~{savings_pct:.0f}% "
                                   f"(~{estimated_savings:.1f} credits / ${estimated_savings * credit_rate:.0f})."),
                    "savings": f"~{estimated_savings:.1f} credits (${estimated_savings * credit_rate:.0f})",
                    "sql": f"-- Replace '{model}' with '{alt}' in your AI function calls\n-- Example:\n-- Before: SELECT AI_COMPLETE('{model}', prompt) ...\n-- After:  SELECT AI_COMPLETE('{alt}', prompt) ..."
                })

    return recs


def _caching_recommendations(repeated_df, credit_rate):
    recs = []
    if repeated_df.empty:
        return recs

    total_wasted = repeated_df["TOTAL_CREDITS"].sum() if "TOTAL_CREDITS" in repeated_df.columns else 0
    total_dupes = len(repeated_df)

    if total_dupes > 0:
        recs.append({
            "category": "Query Optimization",
            "severity": "high" if total_wasted > 5 else "medium",
            "title": f"Cache {total_dupes} repeated AI function calls",
            "description": (f"Found {total_dupes} unique AI queries executed 3+ times each, "
                            f"costing {total_wasted:.2f} total credits. "
                            f"Implement result caching to avoid redundant LLM calls."),
            "savings": f"Up to {total_wasted * 0.6:.1f} credits (${total_wasted * 0.6 * credit_rate:.0f})",
            "sql": """-- Option 1: Create a result cache table
CREATE TABLE IF NOT EXISTS ai_result_cache (
    query_hash VARCHAR,
    function_name VARCHAR,
    input_text VARCHAR,
    result_text VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Option 2: Use query tags for tracking
ALTER SESSION SET QUERY_TAG = 'ai_cached_result';

-- Option 3: Deduplicate inputs before calling AI functions
WITH deduped AS (
    SELECT DISTINCT input_column
    FROM my_table
)
SELECT input_column, AI_COMPLETE('model', input_column) AS result
FROM deduped;"""
        })

    return recs


def _long_prompt_recommendations(query_df, credit_rate):
    recs = []
    if query_df.empty or "QUERY_TEXT" not in query_df.columns:
        return recs

    long_queries = query_df[query_df["QUERY_TEXT"].str.len() > 16000]
    if len(long_queries) > 0:
        estimated_credits = long_queries["CREDITS_USED_CLOUD_SERVICES"].sum() if "CREDITS_USED_CLOUD_SERVICES" in long_queries.columns else 0
        recs.append({
            "category": "Query Optimization",
            "severity": "medium",
            "title": f"Optimize {len(long_queries)} queries with long prompts",
            "description": (f"Found {len(long_queries)} AI queries with estimated 4000+ tokens "
                            f"(>16K characters). Consider truncating, summarizing inputs, "
                            f"or using chunking strategies."),
            "savings": f"Potentially {estimated_credits * 0.3:.1f} credits (${estimated_credits * 0.3 * credit_rate:.0f})",
            "sql": """-- Truncate long inputs before sending to AI
SELECT AI_COMPLETE('model',
    LEFT(long_text_column, 8000)  -- Limit to ~2000 tokens
) AS result
FROM my_table;

-- Or summarize first, then process
WITH summarized AS (
    SELECT id, SNOWFLAKE.CORTEX.SUMMARIZE(long_text_column) AS summary
    FROM my_table
)
SELECT id, AI_COMPLETE('model', summary) AS result
FROM summarized;"""
        })

    return recs


def _warehouse_recommendations(warehouse_df, credit_rate):
    recs = []
    if warehouse_df.empty:
        return recs

    total_wh_credits = warehouse_df["CREDITS_USED"].sum() if "CREDITS_USED" in warehouse_df.columns else 0
    if total_wh_credits > 1:
        recs.append({
            "category": "General",
            "severity": "medium",
            "title": "Optimize warehouse sizing for AI query workloads",
            "description": (f"Detected {total_wh_credits:.1f} warehouse credits used by queries that call "
                            f"Cortex AI Functions. Note: AI inference itself is serverless and billed "
                            f"per token, but the SQL queries that invoke AI functions still consume "
                            f"warehouse credits. Consider right-sizing these warehouses."),
            "savings": f"Up to {total_wh_credits * 0.3:.1f} credits (${total_wh_credits * 0.3 * credit_rate:.0f})",
            "sql": """-- Cortex AI Functions are serverless (billed per token),
-- but the SQL queries calling them use warehouse compute.
-- Right-size the warehouse for AI workloads:

-- Use a smaller warehouse for simple AI calls
ALTER WAREHOUSE my_ai_warehouse SET WAREHOUSE_SIZE = 'XSMALL';

-- Enable auto-suspend to avoid idle costs
ALTER WAREHOUSE my_ai_warehouse SET AUTO_SUSPEND = 60;

-- Check which warehouses run AI queries
SELECT WAREHOUSE_NAME, COUNT(*) AS ai_query_count
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE QUERY_TEXT ILIKE '%AI_COMPLETE%'
   OR QUERY_TEXT ILIKE '%AI_CLASSIFY%'
   OR QUERY_TEXT ILIKE '%AI_EXTRACT%'
GROUP BY WAREHOUSE_NAME
ORDER BY ai_query_count DESC;"""
        })

    return recs


def _general_recommendations(query_df, metering_df):
    recs = []

    if not query_df.empty and "START_TIME" in query_df.columns:
        try:
            query_df = query_df.copy()
            query_df["HOUR"] = pd.to_datetime(query_df["START_TIME"]).dt.hour
            hourly = query_df.groupby("HOUR").size()
            if len(hourly) > 0:
                peak_hour = hourly.idxmax()
                off_peak = hourly.idxmin()
                peak_count = hourly.max()
                off_peak_count = hourly.min()
                if peak_count > off_peak_count * 3:
                    recs.append({
                        "category": "General",
                        "severity": "low",
                        "title": "Schedule AI workloads during off-peak hours",
                        "description": (f"Peak AI usage at hour {peak_hour}:00 ({peak_count} queries) "
                                        f"vs off-peak at hour {off_peak}:00 ({off_peak_count} queries). "
                                        f"Scheduling batch workloads off-peak may reduce contention."),
                        "savings": "Improved performance and potential cost reduction",
                        "sql": f"""-- Create a task to run AI workloads during off-peak hours
CREATE TASK ai_batch_processing
  WAREHOUSE = 'COMPUTE_WH'
  SCHEDULE = 'USING CRON 0 {off_peak} * * * UTC'
AS
  CALL run_ai_batch_job();"""
                    })
        except Exception:
            pass

    recs.append({
        "category": "General",
        "severity": "low",
        "title": "Tag AI workloads for better tracking",
        "description": "Use query tags to categorize AI workloads for easier cost attribution and monitoring.",
        "savings": "Better cost visibility and attribution",
        "sql": """-- Set query tags before AI workloads
ALTER SESSION SET QUERY_TAG = 'ai_workload:sentiment_analysis';

-- Or use object-level tags
ALTER WAREHOUSE my_warehouse SET TAG ai_workload_type = 'cortex_inference';

-- Query tagged workloads
SELECT QUERY_TAG, COUNT(*), SUM(CREDITS_USED_CLOUD_SERVICES)
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE QUERY_TAG LIKE 'ai_workload%'
GROUP BY QUERY_TAG;"""
    })

    return recs


def get_model_reference_table():
    rows = []
    for model, info in MODEL_TIERS.items():
        rows.append({
            "Model": model,
            "Cost Tier": info["tier"].capitalize(),
            "Recommended Use Case": info["use_case"],
        })
    return pd.DataFrame(rows).sort_values("Cost Tier")
