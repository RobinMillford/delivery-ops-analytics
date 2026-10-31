
import streamlit as st
import pandas as pd
import plotly.express as px
from src.dashboard_context import get_bundle
from src.ui import apply_theme, page_header, section_title, metric_card, TEXT, MUTED, ACCENT, CYAN, BORDER

apply_theme()
data, validation, r = get_bundle()
hubs=data["hubs"]
st.sidebar.markdown("## HOLDS & RETURNS")
selected=st.sidebar.multiselect("Select hubs",hubs.hub_id.tolist(),default=hubs.hub_id.tolist(),
                                format_func=lambda x:f"{x} · {hubs.loc[hubs.hub_id.eq(x),'hub_name'].iloc[0]}",
                                key="holds_filter")
q3=r["q3"][r["q3"].hub_id.isin(selected)]
q4=r["q4"][r["q4"].hub_id.isin(selected)]
reasons=r["q3_reasons"][r["q3_reasons"].hub_id.isin(selected)]
events=r["events"][r["events"].hub_id.isin(selected)]
page_header("TASK 1 · Q3 + Q4", "Holds & returns", "Separate customer-side friction from agent-side execution failures, then trace the final outcome of held orders.")
week2_holds=int(q3.total_holds.sum())
agent_holds=int(q3.agent_side_holds.sum())
held_orders=int(q4.held_order_count.sum())
delivered_after_hold=int(q4.Delivered.sum())
a,b,c,d=st.columns(4)
with a: metric_card("Week 2 hold events",f"{week2_holds:,}","All selected hubs")
with b: metric_card("Agent-side holds",f"{agent_holds:,}",f"{agent_holds/week2_holds:.1%} of Week 2 holds")
with c: metric_card("Orders held at least once",f"{held_orders:,}","Unique orders across 14 days")
with d: metric_card("Finally delivered",f"{delivered_after_hold:,}",f"{delivered_after_hold/held_orders:.1%} of held orders")
st.markdown("")
section_title("Week 2 hold composition by hub", "Agent-side reasons are Late Dispatch, Not Attempted and Agent Time Shortage.")
hold_comp=q3.copy()
hold_comp["customer_side_holds"]=hold_comp["total_holds"]-hold_comp["agent_side_holds"]
hold_long=hold_comp.melt(id_vars=["hub_name"],value_vars=["agent_side_holds","customer_side_holds"],var_name="side",value_name="holds")
hold_long["side"]=hold_long.side.map({"agent_side_holds":"Agent-side","customer_side_holds":"Customer-side"})
fig=px.bar(hold_long,x="hub_name",y="holds",color="side",barmode="stack",
           color_discrete_map={"Agent-side":"#F6C85F","Customer-side":"#587393"})
fig.update_layout(height=330,margin=dict(l=8,r=8,t=10,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                  font_color=TEXT,legend_title_text="",xaxis=dict(showgrid=False,title=""),yaxis=dict(gridcolor=BORDER,title="Hold events"))
st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
section_title("Top reasons by hub")
reason_chart=reasons[reasons.reason_rank.le(2)].copy()
fig=px.bar(reason_chart,x="hub_id",y="hold_count",color="hold_reason",barmode="group",
           color_discrete_sequence=["#F6C85F","#58B8C9"])
fig.update_layout(height=300,margin=dict(l=8,r=8,t=10,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                  font_color=TEXT,legend_title_text="",xaxis=dict(showgrid=False,title="Hub"),
                  yaxis=dict(gridcolor=BORDER,title="Hold events"))
st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
section_title("Final outcomes for orders held at least once", "Unique orders, grouped by their final order status.")
q4_long=q4.melt(id_vars=["hub_name"],value_vars=["Delivered","Returned","Hold"],var_name="final_outcome",value_name="orders")
fig=px.bar(q4_long,x="hub_name",y="orders",color="final_outcome",barmode="stack",
           color_discrete_map={"Delivered":"#63C7A5","Returned":"#F07D7D","Hold":"#F6C85F"})
fig.update_layout(height=340,margin=dict(l=8,r=8,t=10,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                  font_color=TEXT,legend_title_text="",xaxis=dict(showgrid=False,title=""),yaxis=dict(gridcolor=BORDER,title="Held orders"))
st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
table=q4[["hub_id","hub_name","held_order_count","Delivered","delivered_share","Returned","returned_share","Hold","hold_share"]].copy()
for c in ["delivered_share","returned_share","hold_share"]: table[c]=table[c].map(lambda x:f"{x:.1%}")
st.dataframe(table,use_container_width=True,hide_index=True)
