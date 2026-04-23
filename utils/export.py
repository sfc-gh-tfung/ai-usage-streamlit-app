import pandas as pd
from datetime import datetime


def build_html_report(current_credits, credit_rate, current_tokens, current_requests,
                      credits_delta, feature_df, days, start_date, end_date):
    """Build an HTML report summarizing the AI cost dashboard."""
    cost_str = f"${current_credits * credit_rate:,.2f}" if credit_rate else f"{current_credits:,.2f} credits"
    daily_avg = current_credits / max(days, 1)
    monthly_proj = daily_avg * 30
    monthly_cost = f"${monthly_proj * credit_rate:,.0f}" if credit_rate else f"{monthly_proj:,.1f} credits"

    # Feature breakdown rows
    feat_rows = ""
    if not feature_df.empty and "CREDITS" in feature_df.columns:
        summary = feature_df.groupby("FEATURE", as_index=False).agg(
            CREDITS=("CREDITS", "sum"),
            TOKENS=("TOKENS", "sum"),
            REQUEST_COUNT=("REQUEST_COUNT", "sum"),
        ).sort_values("CREDITS", ascending=False)
        for _, row in summary.iterrows():
            c = row["CREDITS"] if pd.notna(row["CREDITS"]) else 0
            t = row["TOKENS"] if pd.notna(row["TOKENS"]) else 0
            r = row["REQUEST_COUNT"] if pd.notna(row["REQUEST_COUNT"]) else 0
            feat_rows += f"""
            <tr>
                <td>{row['FEATURE']}</td>
                <td style="text-align:right">{c:,.4f}</td>
                <td style="text-align:right">{r:,.0f}</td>
                <td style="text-align:right">{t:,.0f}</td>
            </tr>"""

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>AI Cost Monitor Report</title>
<style>
    body {{ font-family: Arial, sans-serif;
           max-width: 800px; margin: 40px auto; padding: 0 20px; color: #5B5B5B; }}
    h1 {{ color: #000000; border-bottom: 2px solid #29B5E8; padding-bottom: 8px; font-weight: bold; }}
    h2 {{ color: #11567F; margin-top: 32px; font-weight: bold; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 20px 0; }}
    .kpi {{ background: #f8f9fa; border-radius: 8px; padding: 16px; text-align: center;
            border-top: 3px solid #29B5E8; }}
    .kpi-value {{ font-size: 1.5em; font-weight: bold; color: #000000; }}
    .kpi-label {{ font-size: 0.85em; color: #5B5B5B; margin-top: 4px; }}
    .kpi-delta {{ font-size: 0.8em; color: #5B5B5B; }}
    .summary {{ background: #e8f4f8; border-left: 4px solid #29B5E8; padding: 16px; margin: 20px 0;
                border-radius: 0 8px 8px 0; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
    th {{ background: #11567F; color: white; padding: 10px 12px; text-align: left; }}
    td {{ padding: 8px 12px; border-bottom: 1px solid #eee; }}
    tr:hover td {{ background: #f5f5f5; }}
    .footer {{ margin-top: 40px; padding-top: 16px; border-top: 1px solid #ddd;
               font-size: 0.8em; color: #5B5B5B; }}
    .run-rate {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 16px 0; }}
    .run-rate-item {{ background: #EAF6FC; border-radius: 8px; padding: 12px; text-align: center;
                      border-top: 2px solid #29B5E8; }}
</style>
</head>
<body>
<h1>Snowflake AI Cost Report</h1>
<p style="color:#5B5B5B">{start_date} to {end_date} ({days} days)</p>

<div class="kpi-grid">
    <div class="kpi">
        <div class="kpi-value">{current_credits:,.2f}</div>
        <div class="kpi-label">Total AI Credits</div>
        <div class="kpi-delta">{credits_delta} vs prior period</div>
    </div>
    <div class="kpi">
        <div class="kpi-value">{cost_str}</div>
        <div class="kpi-label">Estimated Cost</div>
    </div>
    <div class="kpi">
        <div class="kpi-value">{current_tokens:,.0f}</div>
        <div class="kpi-label">Tokens Consumed</div>
    </div>
    <div class="kpi">
        <div class="kpi-value">{current_requests:,.0f}</div>
        <div class="kpi-label">AI Requests</div>
    </div>
</div>

<div class="run-rate">
    <div class="run-rate-item">
        <strong>Monthly Run Rate</strong><br>
        {monthly_proj:,.1f} credits/mo<br>
        <span style="color:#666">{monthly_cost}</span>
    </div>
    <div class="run-rate-item">
        <strong>Cost per Request</strong><br>
        {"${:,.4f}".format(current_credits * credit_rate / current_requests) if current_requests > 0 and credit_rate else "N/A"}
    </div>
    <div class="run-rate-item">
        <strong>Cost per 1K Tokens</strong><br>
        {"${:,.4f}".format(current_credits * credit_rate / current_tokens * 1000) if current_tokens > 0 and credit_rate else "N/A"}
    </div>
</div>

<h2>Feature Breakdown</h2>
<table>
    <thead>
        <tr><th>Feature</th><th style="text-align:right">Credits</th><th style="text-align:right">Requests</th><th style="text-align:right">Tokens</th></tr>
    </thead>
    <tbody>
        {feat_rows if feat_rows else '<tr><td colspan="4">No feature data available</td></tr>'}
    </tbody>
</table>

<div class="footer">
    Generated {now} by Snowflake AI Cost Monitor
</div>
</body>
</html>"""
    return html
