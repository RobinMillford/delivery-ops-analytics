
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.dashboard_context import get_bundle
from src.ui import apply_theme, page_header, section_title, metric_card, fmt_bdt, TEXT, MUTED, ACCENT, CYAN, GREEN, RED, BORDER

apply_theme()
data, validation, r = get_bundle()
hubs=data["hubs"]; q7=r["q7"]; prog=r["programme_weekly"]; stg=r["strategic"]
st.sidebar.markdown("## FORECAST & STAFFING")
selected=st.sidebar.multiselect("Select hubs",hubs.hub_id.tolist(),default=hubs.hub_id.tolist(),
                                format_func=lambda x:f"{x} · {hubs.loc[hubs.hub_id.eq(x),'hub_name'].iloc[0]}",
                                key="forecast_filter")
v=q7[q7.hub_id.isin(selected)].copy()
page_header("TASK 1 · Q7  |  TASK 2 · Q8 + Q9", "Forecast & staffing", "Translate expected orders into attempt demand, staffing gaps and a costed response.")
peak=v.groupby(["hub_id","hub_name"]).staffing_gap.max()
gross_shortfall=int(peak.clip(lower=0).sum())
c1,c2,c3,c4=st.columns(4)
with c1: metric_card("Forecast horizon","4 weeks","27 Oct – 23 Nov 2026")
with c2: metric_card("Peak gross shortfall",str(gross_shortfall),"Across hubs before transfers")
with c3: metric_card("Recommended new hires","2","Both Fixed · H04")
with c4: metric_card("Budget used",fmt_bdt(stg["total_budget_spend"]),f"{fmt_bdt(stg['budget_remaining'])} reserve")
st.markdown("")
section_title("Required agents by hub and forecast week", "Required = CEIL(expected orders × historical attempts/order ÷ (7 × 40 × 85%)).")
req=v[["hub_id","hub_name","week_label","required_agents","active_agents"]].copy()
fig=go.Figure()
for hub_id in selected:
    d=req[req.hub_id.eq(hub_id)]
    if len(d):
        fig.add_trace(go.Scatter(x=d.week_label,y=d.required_agents,mode="lines+markers",name=f"{hub_id} required"))
fig.update_layout(height=350,margin=dict(l=8,r=8,t=10,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                  font_color=TEXT,xaxis=dict(showgrid=False,title="Forecast week"),
                  yaxis=dict(gridcolor=BORDER,title="Required agents",dtick=1))
st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
gap=v.copy()
gap["gap_label"]=gap.staffing_gap.map(lambda x:"Shortfall" if x>0 else ("Surplus" if x<0 else "Balanced"))
fig=px.bar(gap,x="week_label",y="staffing_gap",color="hub_id",barmode="group",
           hover_data=["hub_name","required_agents","active_agents"])
fig.add_hline(y=0,line_color=TEXT,line_width=1)
fig.update_layout(height=300,margin=dict(l=8,r=8,t=10,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                  font_color=TEXT,xaxis=dict(showgrid=False,title="Week"),yaxis=dict(gridcolor=BORDER,title="Staffing gap (+ = shortage)"))
st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
section_title("Riverside hold-programme scenario", "The programme reduces agent-side holds by 50% at full effect over 14 days. Linear ramp is an explicit assumption.")
p=prog.copy()
p["week_label"]=p["week_start"].dt.strftime("%d %b")
fig=go.Figure()
fig.add_trace(go.Bar(x=p.week_label,y=p.avoided_holds,name="Avoided holds",marker_color=ACCENT))
fig.add_trace(go.Scatter(x=p.week_label,y=p.utilisation_vs_standard*100,name="Utilisation vs standard",
                         mode="lines+markers",yaxis="y2",line=dict(color=CYAN,width=3)))
fig.update_layout(height=330,margin=dict(l=8,r=8,t=10,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                  font_color=TEXT,legend=dict(orientation="h",y=1.14),xaxis=dict(showgrid=False,title="Forecast week"),
                  yaxis=dict(gridcolor=BORDER,title="Avoided hold events"),yaxis2=dict(title="Utilisation (%)",overlaying="y",side="right",range=[0,100],showgrid=False))
st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
prog_table=p[["week_label","expected_orders","hold_reduction_fraction","avoided_holds","adjusted_attempts","utilisation_vs_standard","required_agents_at_target","hold_cost_saving_bdt"]].copy()
prog_table["hold_reduction_fraction"]=prog_table["hold_reduction_fraction"].map(lambda x:f"{x:.1%}")
prog_table["avoided_holds"]=prog_table["avoided_holds"].map(lambda x:f"{x:,.0f}")
prog_table["adjusted_attempts"]=prog_table["adjusted_attempts"].map(lambda x:f"{x:,.0f}")
prog_table["utilisation_vs_standard"]=prog_table["utilisation_vs_standard"].map(lambda x:f"{x:.1%}")
prog_table["hold_cost_saving_bdt"]=prog_table["hold_cost_saving_bdt"].map(fmt_bdt)
st.dataframe(prog_table,use_container_width=True,hide_index=True)
st.markdown("")
section_title("Recommended staffing action")
action=pd.DataFrame([
    {"Hub":"H01 Greenfield","Action":"Receive 2 transfers from H02","Post-action agents":12,"Peak required":12},
    {"Hub":"H02 Lakeview","Action":"Transfer 2 Fixed agents to H01","Post-action agents":9,"Peak required":8},
    {"Hub":"H03 Riverside","Action":"Launch hold-reduction programme; no hire","Post-action agents":12,"Peak required after full effect":12},
    {"Hub":"H04 Hillcrest","Action":"Hire 2 Fixed agents","Post-action agents":11,"Peak required":11},
    {"Hub":"H05 Brookside","Action":"No hire; retain surplus","Post-action agents":11,"Peak required":10},
    {"Hub":"H06 Westwood","Action":"No change","Post-action agents":9,"Peak required":9},
])
st.dataframe(action,use_container_width=True,hide_index=True)
st.caption("Riverside runs at 87.9% and 86.1% of standard capacity in the first two forecast weeks while the programme ramps; both remain below the 100% standard workload. After full effect, forecast utilisation falls below the 85% planning target.")
