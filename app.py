
from pathlib import Path
import sys
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.dashboard_context import get_bundle
from src.ui import apply_theme, page_header, metric_card, section_title, fmt_bdt, BG, PANEL, TEXT, MUTED, ACCENT, CYAN, GREEN, RED, BORDER

st.set_page_config(
    page_title="Delivery On The Go | Operations Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

data, validation, r = get_bundle()
hubs = data["hubs"].copy()
events = r["events"]
q1 = r["q1_daily"]
q1_hub = r["q1_hub"]
q2 = r["q2"]
q3 = r["q3"]
q4 = r["q4"]
q5 = r["q5"]
q6 = r["q6"]
q7 = r["q7"]

st.sidebar.markdown("## 📦 DELIVERY / OTG")
st.sidebar.caption("OPERATIONS INTELLIGENCE  ·  OCT–NOV 2026")
st.sidebar.markdown("---")
st.sidebar.markdown("**Workspace**")
st.sidebar.markdown("`14-day actuals`  →  `4-week forecast`")
st.sidebar.markdown("---")
st.sidebar.markdown("**Decision focus**")
st.sidebar.markdown("Capacity · Productivity · Cost")
st.sidebar.markdown("---")
st.sidebar.caption("Internal assessment model | Data through 26 Oct 2026")

page_header(
    "OPERATIONS CONTROL TOWER",
    "Executive overview",
    "A decision-focused view of hub capacity, delivery outcomes and the next four weeks of demand.",
)

# Global filter applies to the executive overview.
selected_hubs = st.sidebar.multiselect(
    "Filter hubs",
    hubs["hub_id"].tolist(),
    default=hubs["hub_id"].tolist(),
    format_func=lambda hub_id: f"{hub_id} · {hubs.loc[hubs.hub_id.eq(hub_id), 'hub_name'].iloc[0]}",
    key="executive_hubs",
)
filtered_q2 = q2[q2["hub_id"].isin(selected_hubs)]
filtered_events = events[events["hub_id"].isin(selected_hubs)]
week1_orders = int(data["orders"][data["orders"]["created_at"].dt.date <= pd.Timestamp("2026-10-19").date()]["order_id"].nunique())
week2_orders = int(data["orders"][data["orders"]["created_at"].dt.date >= pd.Timestamp("2026-10-20").date()]["order_id"].nunique())
order_growth = (week2_orders / week1_orders - 1) * 100
active_agents = int(data["agents"]["active_status"].eq("Active").sum())
delivered = int(events["status"].eq("Delivered").sum())
held_orders = int(q4["held_order_count"].sum())

c1,c2,c3,c4 = st.columns(4)
with c1: metric_card("Orders · 14 days", f"{len(data['orders']):,}", f"Week 2 order volume grew {order_growth:.1f}%")
with c2: metric_card("Successful deliveries", f"{delivered:,}", f"{delivered/len(data['orders']):.1%} of original orders")
with c3: metric_card("Active agents", f"{active_agents}", "Two inactive agents left after Week 1")
with c4: metric_card("Hubs above 85% target", f"{int(q2['week2_above_target'].sum())}/6", "H01 · H03 · H04 in Week 2")

st.markdown("")
left,right = st.columns([1.45,1])
with left:
    section_title("Daily demand and workload", "Assigned attempts by event date; all six hubs are included or filtered above.")
    trend = (filtered_events[filtered_events["status"].eq("Assigned")]
             .groupby("event_date").size().rename("Assigned attempts").reset_index())
    order_trend = (data["orders"][data["orders"]["hub_id"].isin(selected_hubs)]
                   .groupby(data["orders"]["created_at"].dt.date).size().rename("New orders").reset_index()
                   .rename(columns={"created_at":"event_date"}))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend["event_date"], y=trend["Assigned attempts"], mode="lines+markers",
                             name="Assigned attempts", line=dict(color=ACCENT,width=3), fill="tozeroy",
                             fillcolor="rgba(246,200,95,.10)"))
    fig.add_trace(go.Scatter(x=order_trend.iloc[:,0], y=order_trend["New orders"], mode="lines+markers",
                             name="New orders", line=dict(color=CYAN,width=2,dash="dot")))
    fig.update_layout(height=315, margin=dict(l=8,r=8,t=12,b=8), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font_color=TEXT, legend=dict(orientation="h",y=1.12),
                      xaxis=dict(showgrid=False),yaxis=dict(gridcolor=BORDER,title="Count"))
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
with right:
    section_title("Where to act first", "Three different issues need three different responses.")
    st.markdown(
        '<div class="section-panel">'
        '<div class="insight"><div class="insight-title">H04 · Hillcrest</div><div class="insight-body">95.87% Week 2 utilisation. Forecast requires 11 agents versus 9 active today.</div></div>'
        '<div class="insight"><div class="insight-title">H03 · Riverside</div><div class="insight-body">563 agent-side holds in Week 2. Late Dispatch is the leading reason.</div></div>'
        '<div class="insight"><div class="insight-title">H01 · Greenfield</div><div class="insight-body">88.64% Week 2 utilisation. H02 is an eligible same-cluster transfer source.</div></div>'
        '</div>', unsafe_allow_html=True
    )

st.markdown("")
section_title("Hub utilisation · Week 1 vs Week 2", "The planning target is 85% of the 40-attempt standard.")
util = filtered_q2.melt(id_vars=["hub_id","hub_name"],value_vars=["week1_utilisation","week2_utilisation"],
                         var_name="period",value_name="utilisation")
util["period"]=util["period"].map({"week1_utilisation":"Week 1","week2_utilisation":"Week 2"})
fig = px.bar(util,x="hub_name",y="utilisation",color="period",barmode="group",
             color_discrete_map={"Week 1":"#5D7597","Week 2":ACCENT},text=util["utilisation"].map(lambda x:f"{x:.0%}"))
fig.add_hline(y=.85,line_dash="dash",line_color=RED,annotation_text="85% target",annotation_position="top left")
fig.update_traces(textposition="outside",cliponaxis=False)
fig.update_layout(height=350,margin=dict(l=8,r=8,t=20,b=8),paper_bgcolor="rgba(0,0,0,0)",
                  plot_bgcolor="rgba(0,0,0,0)",font_color=TEXT,legend_title_text="",
                  xaxis=dict(showgrid=False,title=""),yaxis=dict(gridcolor=BORDER,title="Utilisation",tickformat=".0%",range=[0,1.12]))
st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

st.markdown("---")
section_title("Recommended operating response", "A targeted plan is more cost-efficient than approving eight new agents.")
plan_cols=st.columns(3)
with plan_cols[0]:
    metric_card("New hires", "2 Fixed", "H04 · Hillcrest")
with plan_cols[1]:
    metric_card("Agent transfers", "2", "H02 → H01 · same cluster")
with plan_cols[2]:
    metric_card("First-month spend", fmt_bdt(62800), f"{fmt_bdt(7200)} remaining from BDT 70,000")
st.caption("Modelled hold programme at H03: approximately 856 avoided agent-side holds and BDT 25,682 in avoided hold charges over four forecast weeks. Assumes linear ramp to full effect over 14 days.")
