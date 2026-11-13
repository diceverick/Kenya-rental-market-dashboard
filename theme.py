"""Visual identity: palette, global CSS, HTML components, Plotly styling."""
from __future__ import annotations

import html

import streamlit as st

BG, SURFACE, PANEL, BORDER = "#080A0C", "#101316", "#161A1E", "#272D32"
TEXT, MUTED, DIM = "#F2F4F5", "#929BA3", "#5D666E"
ACCENT, BLUE, TEAL, AMBER, RED, GREY = "#2DD4A0", "#5B8DEF", "#2BB3B1", "#E0A33A", "#E5604D", "#7C8791"
SEQ = [[0.0, "#12201C"], [0.5, "#17604B"], [1.0, "#25A07C"]]
CAT = [ACCENT, BLUE, AMBER, TEAL, RED, GREY]
FONT = "Inter, 'Helvetica Neue', Helvetica, Arial, sans-serif"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
html, body, .stApp, [class*="css"] { font-family: Inter, 'Helvetica Neue', Helvetica, Arial, sans-serif; }
.stApp { background: #080A0C; color: #F2F4F5; }
[data-testid="stHeader"] { background: rgba(8,10,12,.88); backdrop-filter: blur(8px); border-bottom: 1px solid #272D32; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding: 2.4rem 3rem 4rem !important; max-width: 1600px; }
[data-testid="stSidebar"] { background: #0C0F11; border-right: 1px solid #272D32; }
[data-testid="stSidebar"] .block-container, [data-testid="stSidebarUserContent"] { padding-top: 1.2rem !important; }
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="base-input"] {
  background: #101316 !important; border: 1px solid #272D32 !important; border-radius: 2px !important; }
div[data-baseweb="select"] > div:hover { border-color: #4A545C !important; }
span[data-baseweb="tag"] { background: #1B2127 !important; border: 1px solid #272D32 !important; border-radius: 2px !important; }
span[data-baseweb="tag"] span { color: #F2F4F5 !important; }
.stButton > button, .stDownloadButton > button {
  background: transparent; border: 1px solid #272D32; border-radius: 2px; color: #F2F4F5;
  font-size: 11.5px; letter-spacing: .1em; text-transform: uppercase; padding: .45rem 1rem; }
.stButton > button:hover, .stDownloadButton > button:hover { border-color: #2DD4A0; color: #2DD4A0; background: transparent; }
[data-testid="stWidgetLabel"] p { font-size: 11.5px; color: #929BA3; letter-spacing: .02em; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color: #272D32 !important; border-radius: 2px !important; background: #0C0F11; }
[data-testid="stExpander"] { border: 1px solid #272D32 !important; border-radius: 2px !important; background: #0C0F11; }
[data-testid="stDataFrame"] { border: 1px solid #272D32; }
[data-testid="stCaptionContainer"] { color: #929BA3; }
hr { border-color: #272D32 !important; }

.hero { display: flex; justify-content: space-between; align-items: flex-end; gap: 32px;
  border-bottom: 1px solid #272D32; padding-bottom: 24px; margin-bottom: 28px; }
.eyebrow { font-size: 10.5px; letter-spacing: .2em; color: #2DD4A0; text-transform: uppercase; margin-bottom: 12px; }
.hero-t { font-size: 30px; font-weight: 300; letter-spacing: .14em; line-height: 1.3; text-transform: uppercase; }
.hero-t b { font-weight: 600; }
.hero-s { font-size: 22px; font-weight: 400; letter-spacing: .02em; line-height: 1.3; }
.hero p { color: #929BA3; font-size: 13px; max-width: 660px; margin: 12px 0 0; line-height: 1.65; }
.meta { font-size: 11px; color: #929BA3; text-align: right; line-height: 2; white-space: nowrap; font-variant-numeric: tabular-nums; }
.meta span { color: #F2F4F5; margin-left: 6px; }

.kpi { background: #101316; border: 1px solid #272D32; padding: 18px 20px; box-sizing: border-box; }
.kpi.lg { min-height: 132px; border-top: 2px solid #2DD4A0; }
.kpi.sm { min-height: 96px; padding: 14px 20px; }
.kpi-l, .ins-l { font-size: 10.5px; letter-spacing: .14em; text-transform: uppercase; color: #929BA3; }
.kpi-v { font-size: 34px; font-weight: 400; letter-spacing: -.02em; margin-top: 10px; line-height: 1.1; font-variant-numeric: tabular-nums; }
.kpi.sm .kpi-v { font-size: 22px; margin-top: 8px; }
.kpi-v .cur { font-size: 12px; color: #929BA3; letter-spacing: .1em; margin-right: 8px; font-weight: 400; }
.kpi-v .unit { font-size: 12px; color: #929BA3; margin-left: 6px; font-weight: 400; letter-spacing: .04em; }
.kpi-s { font-size: 11.5px; color: #929BA3; margin-top: 8px; line-height: 1.4; }

.sec { display: flex; align-items: center; gap: 14px; margin: 40px 0 16px; font-size: 11px;
  letter-spacing: .18em; text-transform: uppercase; color: #929BA3; }
.sec:after { content: ""; flex: 1; height: 1px; background: #272D32; }
.ct { font-size: 13px; font-weight: 500; margin: 2px 0 2px; }
.cs { font-size: 11.5px; color: #929BA3; margin-bottom: 4px; }

.ins { background: #101316; border: 1px solid #272D32; padding: 18px 20px; min-height: 158px; box-sizing: border-box; }
.ins-h { font-size: 21px; font-weight: 500; margin: 10px 0 8px; letter-spacing: -.01em; }
.ins-d { font-size: 12.5px; color: #929BA3; line-height: 1.65; }
.ins-d b { color: #F2F4F5; font-weight: 500; }

.empty { border: 1px dashed #272D32; padding: 56px 24px; text-align: center; color: #F2F4F5; font-size: 15px; margin-top: 12px; }
.empty span { color: #929BA3; font-size: 12.5px; display: block; margin-top: 8px; }
.note { border-left: 2px solid #E0A33A; background: #101316; padding: 12px 16px; font-size: 12.5px; color: #929BA3; line-height: 1.6; margin: 4px 0 8px; }
.note b { color: #F2F4F5; font-weight: 500; }

.side-t { font-size: 10.5px; letter-spacing: .2em; text-transform: uppercase; color: #2DD4A0; margin-bottom: 14px; }
.side-l { font-size: 10.5px; letter-spacing: .14em; text-transform: uppercase; color: #929BA3; margin: 20px 0 6px; }
.cnt { border: 1px solid #272D32; background: #101316; padding: 12px 14px; margin-bottom: 12px; }
.cnt b { font-size: 26px; font-weight: 400; font-variant-numeric: tabular-nums; letter-spacing: -.02em; }
.cnt span { display: block; font-size: 11px; color: #929BA3; margin-top: 2px; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def e(x) -> str:
    return html.escape(str(x))


def hero(source: str, updated: str, n: int, total: int) -> None:
    st.markdown(
        '<div class="hero"><div><div class="eyebrow">Property market analytics</div>'
        '<div class="hero-t">Kenya Real Estate<br><b>Market Intelligence</b></div>'
        '<p>Asking rents across Kenya. Every figure is calculated '
        'from the source dataset and responds to the filter panel.</p></div>'
        f'<div class="meta">Source<span>{e(source)}</span><br>Refreshed<span>{e(updated)}</span><br>'
        f'In view<span>{n:,} of {total:,} listings</span></div></div>', unsafe_allow_html=True)


def page_head(title: str, desc: str, n: int, total: int) -> None:
    st.markdown(
        f'<div class="hero"><div><div class="eyebrow">Kenya real estate · market intelligence</div>'
        f'<div class="hero-s">{e(title)}</div><p>{e(desc)}</p></div>'
        f'<div class="meta">In view<span>{n:,} of {total:,} listings</span></div></div>', unsafe_allow_html=True)


def section(label: str) -> None:
    st.markdown(f'<div class="sec">{e(label)}</div>', unsafe_allow_html=True)


def chart_title(title: str, sub: str = "") -> None:
    st.markdown(f'<div class="ct">{e(title)}</div><div class="cs">{e(sub)}</div>', unsafe_allow_html=True)


def kpi(label: str, value: str, sub: str = "", size: str = "lg") -> str:
    return (f'<div class="kpi {size}"><div class="kpi-l">{e(label)}</div>'
            f'<div class="kpi-v">{value}</div><div class="kpi-s">{sub}</div></div>')


def money(v) -> str:
    return f'<span class="cur">KSh</span>{v:,.0f}'


def insight(label: str, head: str, detail: str) -> str:
    return (f'<div class="ins"><div class="ins-l">{e(label)}</div>'
            f'<div class="ins-h">{head}</div><div class="ins-d">{detail}</div></div>')


def empty_state() -> None:
    st.markdown('<div class="empty">No listings match the current filters.'
                '<span>Widen the rent range, clear a neighbourhood or region, or press Reset filters.</span></div>',
                unsafe_allow_html=True)


def style(fig, height: int = 360, grid: str | None = "y", legend: bool = False):
    """Apply the shared chart language to a Plotly figure."""
    fig.update_layout(
        height=height, margin=dict(l=4, r=14, t=34 if legend else 8, b=4),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, size=12, color=MUTED), colorway=CAT, showlegend=legend,
        legend=dict(orientation="h", x=0, y=1.12, bgcolor="rgba(0,0,0,0)", font=dict(size=11, color=MUTED)),
        hoverlabel=dict(bgcolor=PANEL, bordercolor=BORDER, font=dict(family=FONT, size=12, color=TEXT)),
        bargap=0.3)
    ax = dict(linecolor=BORDER, tickcolor=BORDER, zeroline=False, automargin=True,
              title_font=dict(size=11, color=DIM), tickfont=dict(size=11, color=MUTED))
    fig.update_xaxes(showgrid=grid == "x", gridcolor="#1B2024", **ax)
    fig.update_yaxes(showgrid=grid == "y", gridcolor="#1B2024", **ax)
    return fig