
from __future__ import annotations

import streamlit as st
import pandas as pd

BG = "#0B1220"
PANEL = "#121D2F"
PANEL_2 = "#17243A"
TEXT = "#E8EEF7"
MUTED = "#9BAAC0"
ACCENT = "#F6C85F"
CYAN = "#58B8C9"
GREEN = "#63C7A5"
RED = "#F07D7D"
BORDER = "#26364E"

def apply_theme():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
        html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif; }}
        .stApp {{ background: radial-gradient(circle at 80% -15%, #1A2C46 0%, {BG} 45%); color: {TEXT}; }}
        [data-testid="stSidebar"] {{ background: #0D1728; border-right: 1px solid {BORDER}; }}
        [data-testid="stSidebar"] * {{ color: {TEXT}; }}
        [data-testid="stHeader"] {{ background: rgba(11,18,32,.85); }}
        h1,h2,h3 {{ font-family: 'Manrope',sans-serif !important; letter-spacing:-.03em; color:{TEXT}; }}
        h1 {{ font-size:2.15rem !important; font-weight:800 !important; }}
        h2 {{ font-size:1.28rem !important; font-weight:700 !important; }}
        h3 {{ font-size:1.02rem !important; font-weight:700 !important; }}
        p, label, span {{ color:{TEXT}; }}
        .block-container {{ padding-top: 2rem; padding-bottom: 3rem; max-width: 1500px; }}
        .eyebrow {{ text-transform:uppercase; letter-spacing:.16em; font-size:.67rem; color:{ACCENT}; font-weight:700; margin-bottom:.45rem; }}
        .page-subtitle {{ color:{MUTED}; font-size:.96rem; margin-top:-.65rem; margin-bottom:1.4rem; }}
        .metric-card {{ background:linear-gradient(145deg,{PANEL_2},{PANEL}); border:1px solid {BORDER}; border-radius:17px; padding:17px 18px; min-height:118px; }}
        .metric-label {{ color:{MUTED}; text-transform:uppercase; letter-spacing:.1em; font-size:.68rem; font-weight:700; }}
        .metric-value {{ color:{TEXT}; font-family:'Manrope',sans-serif; font-size:1.85rem; font-weight:800; margin-top:7px; line-height:1.15; }}
        .metric-note {{ color:{MUTED}; font-size:.75rem; margin-top:7px; }}
        .section-panel {{ background:{PANEL}; border:1px solid {BORDER}; border-radius:16px; padding:16px 18px; }}
        .insight {{ border-left:3px solid {ACCENT}; padding:8px 0 8px 12px; margin:8px 0; }}
        .insight-title {{ font-size:.82rem; font-weight:700; color:{TEXT}; }}
        .insight-body {{ font-size:.76rem; color:{MUTED}; margin-top:3px; line-height:1.45; }}
        .pill {{ display:inline-block; padding:4px 9px; border-radius:30px; font-size:.68rem; font-weight:700; background:#26364E; color:{TEXT}; }}
        .pill-red {{ background:#492C3A; color:#FFC2C2; }}
        .pill-green {{ background:#183E3B; color:#A5E8D4; }}
        .footnote {{ font-size:.72rem; color:{MUTED}; }}
        [data-testid="stDataFrame"] {{ border:1px solid {BORDER}; border-radius:12px; overflow:hidden; }}
        .stButton>button {{ background:{ACCENT}; color:#182231; border:0; border-radius:9px; font-weight:700; }}
        .stDownloadButton>button {{ background:#223651; color:{TEXT}; border:1px solid {BORDER}; border-radius:9px; }}
        hr {{ border-color:{BORDER}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def page_header(kicker: str, title: str, subtitle: str):
    st.markdown(f'<div class="eyebrow">{kicker}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)

def metric_card(label: str, value: str, note: str = ""):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )

def section_title(title: str, note: str | None = None):
    st.markdown(f"### {title}")
    if note:
        st.caption(note)

def hub_filter(hubs_df: pd.DataFrame, key: str = "hub_filter"):
    options = hubs_df["hub_id"].tolist()
    return st.sidebar.multiselect(
        "Hubs",
        options,
        default=options,
        format_func=lambda hub_id: f"{hub_id} · {hubs_df.loc[hubs_df.hub_id.eq(hub_id), 'hub_name'].iloc[0]}",
        key=key,
    )

def fmt_bdt(value: float) -> str:
    return f"৳{value:,.0f}"
