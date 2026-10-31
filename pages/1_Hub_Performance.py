
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.dashboard_context import get_bundle
from src.ui import apply_theme, page_header, section_title, metric_card, fmt_bdt, TEXT, MUTED, ACCENT, CYAN, BORDER

apply_theme()
data, validation, r = get_bundle()
hubs, q2, q7 = data["hubs"], r["q2"], r["q7"]
st.sidebar.markdown("## HUB ANALYSIS")
selected = st.sidebar.multiselect("Select hubs", hubs.hub_id.tolist(), default=hubs.hub_id.tolist(),
                                  format_func=lambda x:f"{x} · {hubs.loc[hubs.hub_id.eq(x),'hub_name'].iloc[0]}",
                                  key="hub_perf_filter")
view=q2[q2.hub_id.isin(selected)].copy()
page_header("TASK 3 · DASHBOARD", "Hub performance", "Compare demand, workload utilisation and forecast staffing needs across the six hubs.")
a,b,c=st.columns(3)
with a: metric_card("Above 85% in Week 2",str(int(view.week2_above_target.sum())), "Planning target breaches")
with b: metric_card("Fastest attempt growth", f"{view.loc[view.attempt_change_pct.idxmax(),'hub_id']} · {view.attempt_change_pct.max():.1f}%", "Week 2 vs Week 1")
with c: metric_card("Highest utilisation", f"{view.loc[view.week2_utilisation.idxmax(),'hub_id']} · {view.week2_utilisation.max():.1%}", "Week 2")
st.markdown("")
section_title("Weekly utilisation", "Utilisation = Assigned attempts / (available agents × 40 × 7).")
long=view.melt(id_vars=["hub_id","hub_name"],value_vars=["week1_utilisation","week2_utilisation"],var_name="week",value_name="utilisation")
long["week"]=long.week.map({"week1_utilisation":"Week 1","week2_utilisation":"Week 2"})
fig=px.bar(long,x="hub_name",y="utilisation",color="week",barmode="group",
           color_discrete_map={"Week 1":"#5D7597","Week 2":ACCENT},text=long.utilisation.map(lambda v:f"{v:.1%}"))
fig.add_hline(y=.85,line_dash="dash",line_color="#F07D7D",annotation_text="85% target")
fig.update_traces(textposition="outside",cliponaxis=False)
fig.update_layout(height=360,margin=dict(l=8,r=8,t=25,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                  font_color=TEXT,legend_title_text="",xaxis=dict(showgrid=False,title=""),
                  yaxis=dict(gridcolor=BORDER,tickformat=".0%",title="Utilisation",range=[0,1.12]))
st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
section_title("Week-on-week pressure", "Growth in assigned attempts is not uniform. H01 and H03 accelerate fastest.")
g=px.bar(view,x="hub_name",y="attempt_change_pct",color="attempt_change_pct",
         color_continuous_scale=["#5D7597",ACCENT],text=view.attempt_change_pct.map(lambda v:f"{v:+.1f}%"))
g.update_traces(textposition="outside",cliponaxis=False)
g.update_layout(height=260,margin=dict(l=8,r=8,t=10,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                font_color=TEXT,coloraxis_showscale=False,xaxis=dict(showgrid=False,title=""),
                yaxis=dict(gridcolor=BORDER,title="Attempt change (%)"))
st.plotly_chart(g,use_container_width=True,config={"displayModeBar":False})
section_title("Capacity table", "The same headcount rules are used in the SQL assessment.")
tab=view[["hub_id","hub_name","Week 1","Week 2","week1_agents","week2_agents","week1_utilisation","week2_utilisation","week2_above_target"]].copy()
tab["week1_utilisation"]=tab["week1_utilisation"].map(lambda x:f"{x:.1%}")
tab["week2_utilisation"]=tab["week2_utilisation"].map(lambda x:f"{x:.1%}")
tab=tab.rename(columns={"Week 1":"W1 attempts","Week 2":"W2 attempts","week1_agents":"W1 agents","week2_agents":"W2 agents","week1_utilisation":"W1 utilisation","week2_utilisation":"W2 utilisation","week2_above_target":"Above target"})
st.dataframe(tab,use_container_width=True,hide_index=True)
st.caption("Week 1 includes all 64 rostered agents; Week 2 includes the 62 Active agents because two inactive agents left after Week 1.")
