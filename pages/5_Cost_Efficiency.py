
import streamlit as st
import pandas as pd
import plotly.express as px
from src.dashboard_context import get_bundle
from src.ui import apply_theme, page_header, section_title, metric_card, fmt_bdt, TEXT, MUTED, ACCENT, CYAN, BORDER

apply_theme()
data, validation, r = get_bundle()
hubs=data["hubs"]; q6=r["q6"]
st.sidebar.markdown("## COST EFFICIENCY")
selected=st.sidebar.multiselect("Select hubs",hubs.hub_id.tolist(),default=hubs.hub_id.tolist(),
                                format_func=lambda x:f"{x} · {hubs.loc[hubs.hub_id.eq(x),'hub_name'].iloc[0]}",
                                key="cost_filter")
v=q6[q6.hub_id.isin(selected)].copy()
page_header("TASK 1 · Q6", "Cost efficiency", "Understand the cost to complete a delivery and how the cost mix changes by hub and week.")
w1=v[v.week.eq("Week 1")].set_index("hub_id")["cost_per_delivered_order"]
w2=v[v.week.eq("Week 2")].set_index("hub_id")["cost_per_delivered_order"]
common=w1.index.intersection(w2.index)
change=((w2.loc[common]/w1.loc[common])-1)*100 if len(common) else pd.Series(dtype=float)
a,b,c=st.columns(3)
with a: metric_card("Lowest Week 2 cost",fmt_bdt(v[v.week.eq("Week 2")].cost_per_delivered_order.min()),"Per delivered order")
with b: metric_card("Highest Week 2 cost",fmt_bdt(v[v.week.eq("Week 2")].cost_per_delivered_order.max()),"Per delivered order")
with c: metric_card("Highest cost hub","H03 Riverside","Hold/return burden remains high")
st.markdown("")
section_title("Cost per delivered order · Week 1 vs Week 2")
fig=px.bar(v,x="hub_name",y="cost_per_delivered_order",color="week",barmode="group",
           color_discrete_map={"Week 1":"#5D7597","Week 2":ACCENT},
           text=v.cost_per_delivered_order.map(lambda x:f"৳{x:.2f}"))
fig.update_traces(textposition="outside",cliponaxis=False)
fig.update_layout(height=360,margin=dict(l=8,r=8,t=15,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                  font_color=TEXT,legend_title_text="",xaxis=dict(showgrid=False,title=""),
                  yaxis=dict(gridcolor=BORDER,title="BDT / delivered order"))
st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
section_title("Operating cost composition", "Fixed pay, Variable daily allowance, Variable per-delivery allowance, hold fees and return fees.")
components=v.melt(id_vars=["hub_id","hub_name","week"],value_vars=["fixed_pay","variable_daily","variable_delivery_allowance","hold_cost","return_cost"],
                  var_name="cost_component",value_name="cost_bdt")
components["cost_component"]=components.cost_component.map({
    "fixed_pay":"Fixed salary","variable_daily":"Variable daily allowance",
    "variable_delivery_allowance":"Variable delivery allowance","hold_cost":"Hold charges","return_cost":"Return charges"
})
fig=px.bar(components,x="hub_name",y="cost_bdt",color="cost_component",facet_col="week",barmode="stack",
           color_discrete_sequence=["#5D7597","#58B8C9","#F6C85F","#E58B62","#F07D7D"])
fig.update_layout(height=380,margin=dict(l=8,r=8,t=35,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                  font_color=TEXT,legend_title_text="",xaxis=dict(showgrid=False,title=""),yaxis=dict(gridcolor=BORDER,title="BDT"))
st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
section_title("Detailed cost table")
table=v.copy()
for c in ["fixed_pay","variable_daily","variable_delivery_allowance","hold_cost","return_cost","total_operating_cost","cost_per_delivered_order"]:
    table[c]=table[c].map(lambda x:f"৳{x:,.2f}")
st.dataframe(table,use_container_width=True,hide_index=True)
st.caption("Q6 treats an agent-day as worked when at least one Assigned event exists that day. Costs are allocated to the week of the event; Delivered outcomes are the delivered-order denominator.")
