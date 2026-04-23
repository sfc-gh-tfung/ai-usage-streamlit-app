import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Snowflake brand colors
SNOWFLAKE_BLUE = "#29B5E8"
MIDNIGHT = "#000000"
MID_BLUE = "#11567F"
MEDIUM_GRAY = "#5B5B5B"
STAR_BLUE = "#75CDD7"
VALENCIA_ORANGE = "#FF9F36"
PURPLE_MOON = "#7254A3"
FIRST_LIGHT = "#D45B90"

COLORS = [
    SNOWFLAKE_BLUE, MID_BLUE, STAR_BLUE, VALENCIA_ORANGE,
    PURPLE_MOON, FIRST_LIGHT, MEDIUM_GRAY, "#A3D5E6",
    "#1B8AB5", "#B8A9D4",
]

SERVICE_COLORS = {
    "AI_SERVICES": SNOWFLAKE_BLUE,
    "CORTEX_FINE_TUNING": MID_BLUE,
    "SNOWPARK_CONTAINER_SERVICES": STAR_BLUE,
}

FEATURE_COLORS = {
    "Cortex Functions": SNOWFLAKE_BLUE,
    "Cortex Search": MID_BLUE,
    "Cortex Analyst": STAR_BLUE,
    "Cortex Fine-Tuning": VALENCIA_ORANGE,
    "Cortex Agents": PURPLE_MOON,
    "Document AI": FIRST_LIGHT,
    "ML Functions": MEDIUM_GRAY,
    "SPCS": "#A3D5E6",
}

SEVERITY_COLORS = {
    "high": FIRST_LIGHT,
    "medium": VALENCIA_ORANGE,
    "low": SNOWFLAKE_BLUE,
}

LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="'Inter', -apple-system, BlinkMacSystemFont, sans-serif", color="#4a4a68", size=12),
    margin=dict(l=40, r=20, t=50, b=100),
    xaxis=dict(
        showgrid=True, gridcolor="rgba(0,0,0,0.05)",
        zeroline=False,
        tickfont=dict(size=11, color="#8b8ba3"),
    ),
    yaxis=dict(
        showgrid=True, gridcolor="rgba(0,0,0,0.05)",
        zeroline=False,
        tickfont=dict(size=11, color="#8b8ba3"),
    ),
    legend=dict(
        orientation="h", yanchor="top", y=-0.28, xanchor="center", x=0.5,
        font=dict(size=11, color="#6b6b85"),
        bgcolor="rgba(0,0,0,0)",
    ),
    hoverlabel=dict(
        bgcolor="rgba(255, 255, 255, 0.97)",
        bordercolor="rgba(114, 84, 163, 0.3)",
        font=dict(family="'Inter', sans-serif", size=12, color="#1a1a2e"),
    ),
)


def _apply_layout(fig, title=None, height=400):
    fig.update_layout(**LAYOUT_DEFAULTS, height=height)
    if title:
        fig.update_layout(title=dict(
            text=title, x=0, xanchor="left",
            font=dict(size=15, color="#2d2d44", family="'Inter', sans-serif"),
        ))
    return fig


def daily_credits_line(df, date_col="USAGE_DATE", value_col="CREDITS_USED", title="Daily AI credit consumption"):
    if df.empty:
        return _empty_chart(title)
    fig = px.line(df, x=date_col, y=value_col, markers=True)
    fig.update_traces(
        line=dict(color=PURPLE_MOON, width=2.5, shape="spline"),
        marker=dict(size=5, color=PURPLE_MOON, line=dict(width=1, color="#FFFFFF")),
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Credits: %{y:,.2f}<extra></extra>",
        fill="tozeroy", fillcolor="rgba(114, 84, 163, 0.06)",
    )
    return _apply_layout(fig, title)


def stacked_area_by_service(df, date_col="USAGE_DATE", value_col="CREDITS_USED",
                            group_col="SERVICE_TYPE", title="Daily consumption by AI service type"):
    if df.empty:
        return _empty_chart(title)
    fig = px.area(df, x=date_col, y=value_col, color=group_col,
                  color_discrete_map=SERVICE_COLORS)
    fig.update_traces(
        line=dict(width=1.5, shape="spline"),
        hovertemplate="<b>%{fullData.name}</b><br>%{x|%b %d}: %{y:,.2f} credits<extra></extra>",
    )
    return _apply_layout(fig, title)


def top_queries_bar(df, x_col="CREDITS_USED", y_col="QUERY_ID", title="Top 10 most expensive AI queries"):
    if df.empty:
        return _empty_chart(title)
    display_df = df.head(10).copy()
    display_df["LABEL"] = display_df[y_col].astype(str).str[:12] + "..."
    fig = px.bar(display_df, x=x_col, y="LABEL", orientation="h",
                 color_discrete_sequence=[PURPLE_MOON])
    fig.update_traces(
        marker=dict(line=dict(width=0), cornerradius=6),
        hovertemplate="<b>%{y}</b><br>Credits: %{x:,.2f}<extra></extra>",
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return _apply_layout(fig, title)


def donut_chart(df, values_col, names_col, title="Cost by feature category"):
    if df.empty:
        return _empty_chart(title)
    fig = px.pie(df, values=values_col, names=names_col, hole=0.55,
                 color=names_col, color_discrete_map=FEATURE_COLORS)
    fig.update_traces(
        textposition="inside", textinfo="percent+label",
        textfont=dict(size=11),
        hovertemplate="<b>%{label}</b><br>Credits: %{value:,.2f}<br>Share: %{percent}<extra></extra>",
        marker=dict(line=dict(color="#FFFFFF", width=2)),
    )
    total = df[values_col].sum()
    fig.add_annotation(
        text=f"<b>{total:,.1f}</b><br><span style='font-size:11px;color:#8b8ba3'>total credits</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=18, color="#1a1a2e", family="'Inter', sans-serif"),
    )
    return _apply_layout(fig, title, height=400)


def user_bar_chart(df, x_col="TOTAL_CREDITS", y_col="USER_NAME",
                   title="Top 20 users by AI credit consumption"):
    if df.empty:
        return _empty_chart(title)
    fig = px.bar(df.head(20), x=x_col, y=y_col, orientation="h",
                 color_discrete_sequence=[PURPLE_MOON])
    fig.update_traces(
        marker=dict(line=dict(width=0), cornerradius=6),
        hovertemplate="<b>%{y}</b><br>Credits: %{x:,.2f}<extra></extra>",
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return _apply_layout(fig, title, height=max(400, len(df.head(20)) * 30))


def multi_user_trend(df, date_col="USAGE_DATE", value_col="CREDITS_USED",
                     group_col="USER_NAME", title="Per-user consumption over time"):
    if df.empty:
        return _empty_chart(title)
    fig = px.line(df, x=date_col, y=value_col, color=group_col,
                  markers=True, color_discrete_sequence=COLORS)
    fig.update_traces(
        line=dict(width=2, shape="spline"),
        marker=dict(size=4),
        hovertemplate="<b>%{fullData.name}</b><br>%{x|%b %d}: %{y:,.2f} credits<extra></extra>",
    )
    return _apply_layout(fig, title)


def forecast_chart(historical_df, forecast_df, date_col="USAGE_DATE", value_col="CREDITS_USED",
                   title="30-day AI spend forecast"):
    fig = go.Figure()

    if not historical_df.empty:
        fig.add_trace(go.Scatter(
            x=historical_df[date_col], y=historical_df[value_col],
            mode="lines+markers", name="Historical",
            line=dict(color=PURPLE_MOON, width=2.5, shape="spline"),
            marker=dict(size=4, color=PURPLE_MOON),
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Actual: %{y:,.2f} credits<extra></extra>",
        ))

    if not forecast_df.empty:
        fig.add_trace(go.Scatter(
            x=forecast_df[date_col], y=forecast_df["FORECAST"],
            mode="lines", name="Forecast",
            line=dict(color=VALENCIA_ORANGE, width=2.5, dash="dash", shape="spline"),
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Forecast: %{y:,.2f} credits<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=pd.concat([forecast_df[date_col], forecast_df[date_col][::-1]]),
            y=pd.concat([forecast_df["UPPER"], forecast_df["LOWER"][::-1]]),
            fill="toself", fillcolor="rgba(255,159,54,0.08)",
            line=dict(color="rgba(255,159,54,0)"), name="Confidence band",
            hoverinfo="skip",
        ))

    fig.update_yaxes(title_text="Credits")
    return _apply_layout(fig, title, height=450)


def gauge_chart(current_value, target_value, title="Monthly budget consumption"):
    pct = (current_value / target_value * 100) if target_value > 0 else 0
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=current_value,
        title=dict(text=title, font=dict(size=16, color="#2d2d44")),
        delta=dict(reference=target_value, relative=False, valueformat=".1f"),
        number=dict(suffix=" credits", valueformat=".1f", font=dict(color="#1a1a2e")),
        gauge=dict(
            axis=dict(range=[0, max(target_value * 1.2, current_value * 1.1)]),
            bar=dict(color=PURPLE_MOON),
            bgcolor="rgba(0,0,0,0.03)",
            steps=[
                dict(range=[0, target_value * 0.5], color="rgba(114,84,163,0.08)"),
                dict(range=[target_value * 0.5, target_value * 0.75], color="rgba(255,159,54,0.12)"),
                dict(range=[target_value * 0.75, target_value], color="rgba(212,91,144,0.15)"),
            ],
            threshold=dict(line=dict(color=FIRST_LIGHT, width=3), thickness=0.8, value=target_value),
        ),
    ))
    return _apply_layout(fig, height=350)


def anomaly_highlight_chart(df, date_col="USAGE_DATE", value_col="CREDITS_USED",
                            anomaly_col="IS_ANOMALY", title="Spending anomalies"):
    if df.empty:
        return _empty_chart(title)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[date_col], y=df[value_col],
        mode="lines+markers", name="Daily spend",
        line=dict(color=PURPLE_MOON, width=2.5, shape="spline"),
        marker=dict(size=4, color=PURPLE_MOON),
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Spend: %{y:,.2f} credits<extra></extra>",
        fill="tozeroy", fillcolor="rgba(114, 84, 163, 0.04)",
    ))
    if anomaly_col in df.columns:
        anomalies = df[df[anomaly_col]]
        if not anomalies.empty:
            fig.add_trace(go.Scatter(
                x=anomalies[date_col], y=anomalies[value_col],
                mode="markers", name="Anomaly",
                marker=dict(color=FIRST_LIGHT, size=12, symbol="x",
                            line=dict(width=2, color=FIRST_LIGHT)),
                hovertemplate="<b>ANOMALY</b><br>%{x|%b %d}: %{y:,.2f} credits<extra></extra>",
            ))
    return _apply_layout(fig, title)


def feature_area_chart(df, date_col="USAGE_DATE", value_col="CREDITS",
                       group_col="FEATURE", title="AI Credit Usage by Feature"):
    if df.empty:
        return _empty_chart(title)
    fig = px.area(df, x=date_col, y=value_col, color=group_col,
                  color_discrete_sequence=COLORS)
    fig.update_traces(
        line=dict(width=1.5, shape="spline"),
        hovertemplate="<b>%{fullData.name}</b><br>%{x|%b %d}: %{y:,.2f} credits<extra></extra>",
    )
    return _apply_layout(fig, title)


def feature_drilldown_line(df, date_col="USAGE_DATE", value_col="CREDITS",
                           title="Daily Credits"):
    if df.empty:
        return _empty_chart(title)
    fig = px.line(df, x=date_col, y=value_col, markers=True)
    fig.update_traces(
        line=dict(color=PURPLE_MOON, width=2.5, shape="spline"),
        marker=dict(size=5, color=PURPLE_MOON, line=dict(width=1, color="#FFFFFF")),
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Credits: %{y:,.2f}<extra></extra>",
        fill="tozeroy", fillcolor="rgba(114, 84, 163, 0.06)",
    )
    return _apply_layout(fig, title)


def _empty_chart(title="No data available"):
    fig = go.Figure()
    fig.add_annotation(
        text="No data available for the selected time range",
        xref="paper", yref="paper", x=0.5, y=0.5,
        font=dict(size=14, color="#8b8ba3", family="'Inter', sans-serif"),
        showarrow=False,
    )
    return _apply_layout(fig, title)
