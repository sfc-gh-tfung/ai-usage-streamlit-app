"""
Shared CSS styles for the Snowflake AI Cost Monitor dashboard.
Canva-inspired clean light theme with soft shadows, rounded cards,
and lots of whitespace.
"""
import streamlit as st

# ── Snowflake brand palette ──────────────────────────────────────────
SNOWFLAKE_BLUE = "#29B5E8"
MIDNIGHT = "#000000"
MID_BLUE = "#11567F"
MEDIUM_GRAY = "#5B5B5B"
STAR_BLUE = "#75CDD7"
VALENCIA_ORANGE = "#FF9F36"
PURPLE_MOON = "#7254A3"
FIRST_LIGHT = "#D45B90"


def inject_css():
    """Inject the Canva-inspired clean light CSS theme. Call once at the top of every page."""
    st.markdown(
        """
        <style>
        /* ── Global resets ─────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .stApp {
            background: #FFFFFF;
        }

        /* ── Typography ───────────────────────────────────── */
        h1 {
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
            color: #1a1a2e !important;
        }
        h2 {
            font-weight: 600 !important;
            letter-spacing: -0.01em !important;
            color: #2d2d44 !important;
        }
        h3 {
            font-weight: 600 !important;
            color: #3d3d56 !important;
        }
        p, li, span, div {
            color: #4a4a68 !important;
        }
        .stCaption, .stCaption p {
            color: #8b8ba3 !important;
        }

        /* ── KPI metric cards ─────────────────────────────── */
        [data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #e8e8ef;
            border-radius: 16px;
            padding: 20px 24px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
            transition: all 0.2s ease;
        }
        [data-testid="stMetric"]:hover {
            border-color: #d0d0e0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06), 0 2px 4px rgba(0, 0, 0, 0.03);
            transform: translateY(-1px);
        }
        [data-testid="stMetric"] label {
            color: #8b8ba3 !important;
            font-size: 0.78rem !important;
            font-weight: 500 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #1a1a2e !important;
            font-size: 1.8rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
        }
        [data-testid="stMetric"] [data-testid="stMetricDelta"] {
            font-size: 0.82rem !important;
            font-weight: 500 !important;
        }

        /* ── Section containers ────────────────────────────── */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
            background: #FFFFFF;
            border: 1px solid #e8e8ef;
            border-radius: 16px;
            padding: 4px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        }

        /* ── Tabs ──────────────────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
            background: #f5f5fa;
            border-radius: 12px;
            padding: 4px;
            border: 1px solid #e8e8ef;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            padding: 8px 20px;
            color: #8b8ba3 !important;
            font-weight: 500;
            font-size: 0.85rem;
            transition: all 0.2s ease;
            border: none !important;
            background: transparent;
        }
        .stTabs [aria-selected="true"] {
            background: #FFFFFF !important;
            color: #7254A3 !important;
            border: none !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
        }
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: #7254A3 !important;
            height: 2px;
            border-radius: 2px;
        }
        .stTabs [data-baseweb="tab-border"] {
            display: none;
        }

        /* ── Dataframes ────────────────────────────────────── */
        [data-testid="stDataFrame"] {
            border: 1px solid #e8e8ef;
            border-radius: 12px;
            overflow: hidden;
        }

        /* ── Sidebar ───────────────────────────────────────── */
        [data-testid="stSidebar"] {
            background: #f8f8fc;
            border-right: 1px solid #e8e8ef;
        }
        [data-testid="stSidebar"] [data-testid="stMarkdown"] p {
            color: #6b6b85 !important;
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #2d2d44 !important;
        }

        /* ── Buttons ───────────────────────────────────────── */
        .stDownloadButton > button,
        .stButton > button {
            background: linear-gradient(135deg, #7254A3 0%, #8B6FC0 100%);
            border: none;
            border-radius: 12px;
            color: #FFFFFF !important;
            font-weight: 500;
            padding: 10px 24px;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(114, 84, 163, 0.2);
        }
        .stDownloadButton > button:hover,
        .stButton > button:hover {
            background: linear-gradient(135deg, #6344A3 0%, #7B5FB0 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(114, 84, 163, 0.3);
        }
        .stDownloadButton > button span,
        .stButton > button span,
        .stDownloadButton > button p,
        .stButton > button p {
            color: #FFFFFF !important;
        }

        /* ── Select boxes & inputs ─────────────────────────── */
        [data-testid="stSelectbox"] > div > div,
        .stDateInput > div > div > input,
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {
            background: #FFFFFF !important;
            border: 1px solid #e0e0eb !important;
            border-radius: 10px !important;
            color: #2d2d44 !important;
        }
        [data-testid="stSelectbox"] > div > div:focus-within,
        .stTextInput > div > div > input:focus {
            border-color: #7254A3 !important;
            box-shadow: 0 0 0 2px rgba(114, 84, 163, 0.15) !important;
        }

        /* ── Expanders ─────────────────────────────────────── */
        [data-testid="stExpander"] {
            background: #FFFFFF;
            border: 1px solid #e8e8ef;
            border-radius: 12px;
        }
        [data-testid="stExpander"] summary span {
            color: #3d3d56 !important;
            font-weight: 500;
        }

        /* ── Alerts and callouts ───────────────────────────── */
        .stAlert {
            border-radius: 12px;
            border: none;
        }

        /* ── Plotly charts ─────────────────────────────────── */
        [data-testid="stPlotlyChart"] {
            background: #FFFFFF;
            border: 1px solid #e8e8ef;
            border-radius: 16px;
            padding: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        }

        /* ── Scrollbar ─────────────────────────────────────── */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #f5f5fa;
        }
        ::-webkit-scrollbar-thumb {
            background: #d0d0e0;
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #b0b0c8;
        }

        /* ── Custom card classes (for HTML injection) ──────── */
        .saas-card {
            background: #FFFFFF;
            border: 1px solid #e8e8ef;
            border-radius: 16px;
            padding: 20px 24px;
            margin-bottom: 12px;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        }
        .saas-card:hover {
            border-color: #d0d0e0;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
            transform: translateY(-1px);
        }
        .saas-card h4 {
            color: #1a1a2e !important;
            font-weight: 600 !important;
            margin: 0 0 8px 0;
            font-size: 1rem;
        }
        .saas-card p {
            color: #6b6b85 !important;
            margin: 0;
            font-size: 0.88rem;
            line-height: 1.5;
        }

        /* ── Highlight / callout box ──────────────────────── */
        .highlight-box {
            background: linear-gradient(135deg, #f0ebff 0%, #e8f4fd 100%);
            border: 1px solid #d8d0f0;
            border-left: 3px solid #7254A3;
            border-radius: 12px;
            padding: 16px 20px;
            margin: 8px 0 16px 0;
        }
        .highlight-box p {
            color: #3d3d56 !important;
            font-size: 0.9rem;
            margin: 0;
            line-height: 1.6;
        }
        .highlight-box strong {
            color: #7254A3 !important;
        }

        /* ── Recommendation cards (severity borders) ──────── */
        .rec-card {
            background: #FFFFFF;
            border: 1px solid #e8e8ef;
            border-radius: 16px;
            padding: 20px 24px;
            margin-bottom: 12px;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        }
        .rec-card:hover {
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.07);
            transform: translateY(-1px);
        }
        .rec-card.high {
            border-left: 3px solid #D45B90;
        }
        .rec-card.medium {
            border-left: 3px solid #FF9F36;
        }
        .rec-card.low {
            border-left: 3px solid #29B5E8;
        }
        .rec-card .rec-title {
            color: #1a1a2e !important;
            font-weight: 600 !important;
            font-size: 1rem;
            margin: 0 0 6px 0;
        }
        .rec-card .rec-meta {
            font-size: 0.78rem;
            margin: 0 0 10px 0;
        }
        .rec-card .rec-meta .severity-high { color: #D45B90 !important; }
        .rec-card .rec-meta .severity-medium { color: #FF9F36 !important; }
        .rec-card .rec-meta .severity-low { color: #29B5E8 !important; }
        .rec-card .rec-meta .savings { color: #11567F !important; }
        .rec-card .rec-desc {
            color: #6b6b85 !important;
            font-size: 0.85rem;
            line-height: 1.5;
            margin: 0;
        }

        /* ── Section headers ──────────────────────────────── */
        .section-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 28px 0 12px 0;
            padding-bottom: 8px;
            border-bottom: 1px solid #e8e8ef;
        }
        .section-header .icon {
            font-size: 1.2rem;
        }
        .section-header h3 {
            color: #2d2d44 !important;
            font-weight: 600 !important;
            font-size: 1.1rem !important;
            margin: 0 !important;
        }

        /* ── Stat pill (inline badge) ─────────────────────── */
        .stat-pill {
            display: inline-block;
            background: #f0ebff;
            border: 1px solid #d8d0f0;
            border-radius: 20px;
            padding: 4px 14px;
            font-size: 0.82rem;
            font-weight: 500;
            color: #7254A3 !important;
            margin-right: 8px;
        }

        /* ── Hero banner (Canva-style gradient header) ────── */
        .hero-banner {
            background: linear-gradient(135deg, #7254A3 0%, #29B5E8 50%, #75CDD7 100%);
            border-radius: 20px;
            padding: 32px 36px;
            margin-bottom: 24px;
            color: #FFFFFF !important;
            position: relative;
            overflow: hidden;
        }
        .hero-banner::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 60%;
            height: 200%;
            background: radial-gradient(ellipse, rgba(255,255,255,0.1) 0%, transparent 70%);
            pointer-events: none;
        }
        .hero-banner h1 {
            color: #FFFFFF !important;
            font-size: 1.8rem !important;
            margin: 0 0 4px 0 !important;
        }
        .hero-banner p {
            color: rgba(255, 255, 255, 0.85) !important;
            font-size: 0.95rem;
            margin: 0;
        }

        /* ── Info chip (latency notice) ───────────────────── */
        .info-chip {
            display: inline-block;
            background: #f5f5fa;
            border: 1px solid #e0e0eb;
            border-radius: 8px;
            padding: 6px 14px;
            margin-bottom: 16px;
        }
        .info-chip span {
            color: #8b8ba3 !important;
            font-size: 0.8rem;
        }

        /* ── Footer / powered-by ──────────────────────────── */
        .powered-by {
            text-align: center;
            padding: 16px 0 8px 0;
            border-top: 1px solid #e8e8ef;
            margin-top: 24px;
        }
        .powered-by span {
            color: #8b8ba3 !important;
            font-size: 0.75rem;
            letter-spacing: 0.03em;
        }
        .powered-by .sf-logo {
            color: #29B5E8 !important;
            font-weight: 600;
        }

        /* ── Hide Streamlit default elements ───────────────── */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_header(icon: str, title: str):
    """Render a styled section header with icon."""
    st.markdown(
        f'<div class="section-header">'
        f'<span class="icon">{icon}</span>'
        f'<h3>{title}</h3>'
        f'</div>',
        unsafe_allow_html=True,
    )


def highlight_box(text: str):
    """Render a styled callout / highlight box."""
    st.markdown(
        f'<div class="highlight-box"><p>{text}</p></div>',
        unsafe_allow_html=True,
    )


def hero_banner(title: str, subtitle: str):
    """Render a Canva-style gradient hero banner."""
    st.markdown(
        f'<div class="hero-banner">'
        f'<h1>{title}</h1>'
        f'<p>{subtitle}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )


def recommendation_card(title: str, severity: str, savings: str, description: str, icon: str = ""):
    """Render a styled recommendation card with severity-colored left border."""
    sev_class = severity.lower() if severity.lower() in ("high", "medium", "low") else "low"
    sev_label = severity.upper()
    st.markdown(
        f'<div class="rec-card {sev_class}">'
        f'<div class="rec-title">{icon} {title}</div>'
        f'<div class="rec-meta">'
        f'<span class="severity-{sev_class}">\u25cf {sev_label}</span>'
        f' &nbsp;\u00b7&nbsp; '
        f'<span class="savings">Potential savings: {savings}</span>'
        f'</div>'
        f'<div class="rec-desc">{description}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def powered_by_footer():
    """Render a 'Powered by Snowflake' footer in the sidebar."""
    st.markdown(
        '<div class="powered-by">'
        '<span>Powered by <span class="sf-logo">&#10052; Snowflake</span></span>'
        '</div>',
        unsafe_allow_html=True,
    )
