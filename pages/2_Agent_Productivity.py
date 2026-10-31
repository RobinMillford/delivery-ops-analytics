
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.dashboard_context import get_bundle
from src.ui import apply_theme, page_header, section_title, metric_card, TEXT, MUTED, ACCENT, CYAN, BORDER

apply_theme()
data, validation, r = get_bundle()
events, agents, hubs = r["events"], data["agents"], data["hubs"]
st.sidebar.markdown("## AGENT ANALYTICS")
selected=st.sidebar.multiselect("Select hubs",hubs.hub_id.tolist(),default=hubs.hub_id.tolist(),
                                format_func=lambda x:f"{x} · {hubs.loc[hubs.hub_id.eq(x),'hub_name'].iloc[0]}",
                                key="agent_filter")
page_header("TASK 1 · Q1 + Q5", "Agent productivity", "Daily output, individual delivery performance and agents requiring a return-rate review.")
e=events[events.hub_id.isin(selected)]
counts=e.pivot_table(index="agent_id",columns="status",values="log_id",aggfunc="count",fill_value=0).reset_index()
for s in ["Assigned","Delivered","Hold","Returned"]:
    if s not in counts.columns: counts[s]=0
workdays=e[e.status.eq("Assigned")].groupby("agent_id").event_date.nunique().rename("workdays").reset_index()
stats=counts.merge(agents,on="agent_id",how="left").merge(workdays,on="agent_id",how="left").fillna({"workdays":0})
stats["deliveries_per_workday"]=stats["Delivered"]/stats["workdays"].replace(0,pd.NA)
stats["return_ratio"]=stats["Returned"]/stats["Assigned"].replace(0,pd.NA)
stats["delivery_ratio"]=stats["Delivered"]/stats["Assigned"].replace(0,pd.NA)
stats=stats[stats.hub_id.isin(selected)]
c1,c2,c3=st.columns(3)
with c1: metric_card("Agents represented",f"{stats.agent_id.nunique()}","Across selected hubs")
with c2: metric_card("High-return agents",str(int(r["q5"].hub_id.isin(selected).sum())),"Tenure >30 days and return ratio >15%")
with c3: metric_card("Best deliveries / workday",f"{stats.deliveries_per_workday.max():.1f}","Top individual rate")
st.markdown("")
section_title("Top 10 by deliveries per worked day", "Only days with at least one Assigned event count as worked days.")
top=stats.sort_values("deliveries_per_workday",ascending=False).head(10).sort_values("deliveries_per_workday")
fig=px.bar(top,x="deliveries_per_workday",y="agent_name",color="hub_id",orientation="h",
           color_discrete_sequence=["#F6C85F","#58B8C9","#63C7A5","#8D9DB8","#DA8FC3","#E58B62"],
           hover_data=["agent_id","hub_id","Assigned","Delivered","Returned"])
fig.update_layout(height=390,margin=dict(l=8,r=8,t=10,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                  font_color=TEXT,xaxis=dict(gridcolor=BORDER,title="Deliveries per worked day"),
                  yaxis=dict(showgrid=False,title=""))
st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
section_title("Return ratio vs assigned attempts", "The 15% threshold is the assessment's high-return flag.")
scatter=px.scatter(stats,x="Assigned",y="return_ratio",color="hub_id",size="Delivered",
                   hover_data=["agent_name","agent_id","salary_type","Returned"],opacity=.85)
scatter.add_hline(y=.15,line_dash="dash",line_color="#F07D7D",annotation_text="15% return threshold")
scatter.update_layout(height=330,margin=dict(l=8,r=8,t=10,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                      font_color=TEXT,xaxis=dict(gridcolor=BORDER,title="Assigned attempts"),
                      yaxis=dict(gridcolor=BORDER,title="Return ratio",tickformat=".0%"))
st.plotly_chart(scatter,use_container_width=True,config={"displayModeBar":False})
section_title("Agents meeting Q5 criteria")
high=r["q5"][r["q5"].hub_id.isin(selected)].copy()
if high.empty:
    st.success("No agents in the selected hubs meet both Q5 thresholds.")
else:
    high["return_ratio"]=high["return_ratio"].map(lambda x:f"{x:.2%}")
    st.dataframe(high.rename(columns={"Assigned":"Assigned attempts","Returned":"Returned attempts","return_ratio":"Return ratio"}),use_container_width=True,hide_index=True)
section_title("Daily agent-level output · first 20 rows")
q1=r["q1_daily"][r["q1_daily"].hub_id.isin(selected)].head(20).copy()
st.dataframe(q1,use_container_width=True,hide_index=True)
