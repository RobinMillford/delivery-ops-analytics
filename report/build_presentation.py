from pathlib import Path
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.dml import MSO_THEME_COLOR

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
Q = ROOT / 'outputs' / 'query_results'

NAVY = '0B1220'
PANEL = '142137'
PANEL2 = '1A2A43'
BORDER = '2A3D59'
WHITE = 'F1F5FA'
MUTED = 'A9B8CB'
YELLOW = 'F6C85F'
CYAN = '58B8C9'
GREEN = '63C7A5'
RED = 'F07D7D'
ORANGE = 'E99A6B'

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]


def rgb(hexstr):
    return RGBColor.from_string(hexstr)


def rect(slide, x, y, w, h, fill=PANEL, line=BORDER, radius=True):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    sh = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = rgb(fill)
    sh.line.color.rgb = rgb(line); sh.line.width = Pt(0.8)
    if radius:
        try: sh.adjustments[0] = 0.08
        except Exception: pass
    return sh


def text(slide, x, y, w, h, txt, size=14, color=WHITE, bold=False,
         align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP, font='Aptos', margin=0.02):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear(); tf.word_wrap = True
    tf.margin_left = Inches(margin); tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin); tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run(); r.text = str(txt)
    r.font.name = font; r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = rgb(color)
    return box


def add_base(title, subtitle='', kicker='OPERATIONS REVIEW'):
    slide = prs.slides.add_slide(blank)
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = rgb(NAVY)
    # top accent / kicker
    rect(slide, 0.0, 0.0, 13.333, 0.09, YELLOW, YELLOW, radius=False)
    text(slide, 0.55, 0.28, 12.1, 0.25, kicker, 9, YELLOW, True)
    text(slide, 0.55, 0.62, 12.1, 0.48, title, 25, WHITE, True)
    if subtitle:
        text(slide, 0.57, 1.15, 12.0, 0.42, subtitle, 10.5, MUTED)
    # footer
    text(slide, 0.55, 7.18, 10.5, 0.15, 'DELIVERY - ON THE GO  |  DATA PERIOD: 13-26 OCT 2026  |  FORECAST: 27 OCT-23 NOV 2026', 7.2, MUTED)
    text(slide, 12.1, 7.16, 0.7, 0.18, f'{len(prs.slides):02d} / 08', 7.2, MUTED, align=PP_ALIGN.RIGHT)
    return slide


def metric(slide, x, y, w, label, value, note='', color=YELLOW):
    rect(slide, x, y, w, 1.12)
    text(slide, x+0.16, y+0.12, w-0.3, 0.20, label.upper(), 8, MUTED, True)
    text(slide, x+0.16, y+0.36, w-0.3, 0.40, value, 23, color, True)
    if note: text(slide, x+0.16, y+0.82, w-0.3, 0.20, note, 8, MUTED)


def label_value(slide, x, y, w, label, value, note='', accent=YELLOW):
    text(slide, x, y, w, 0.22, label.upper(), 8, MUTED, True)
    text(slide, x, y+0.25, w, 0.42, value, 19, accent, True)
    if note: text(slide, x, y+0.70, w, 0.35, note, 8.5, MUTED)


def table(slide, x, y, w, h, headers, rows, widths=None, font_size=8.2, row_h=None):
    nrows, ncols = len(rows)+1, len(headers)
    shp = slide.shapes.add_table(nrows, ncols, Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = shp.table
    if widths:
        for i, width in enumerate(widths): tbl.columns[i].width = Inches(width)
    for ri in range(nrows):
        for ci in range(ncols):
            cell = tbl.cell(ri, ci)
            cell.margin_left = Inches(0.08); cell.margin_right = Inches(0.06)
            cell.margin_top = Inches(0.03); cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(PANEL2 if ri == 0 else (PANEL if ri % 2 else '192A42'))
            cell.text = str(headers[ci] if ri == 0 else rows[ri-1][ci])
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.LEFT
                for run in p.runs:
                    run.font.name = 'Aptos'; run.font.size = Pt(font_size if ri else font_size)
                    run.font.bold = ri == 0; run.font.color.rgb = rgb(YELLOW if ri == 0 else WHITE)
    return tbl


def simple_bars(slide, x, y, w, h, items, max_value=None, color=YELLOW,
                suffix='', target=None, target_label=''):
    # Native editable bars, labels and baseline.
    max_value = max_value or max(v for _, v in items)
    label_w = 1.35
    bar_x = x + label_w
    bar_w = w - label_w - 0.8
    row_h = h / max(1, len(items))
    for i, (name, val) in enumerate(items):
        yy = y + i*row_h
        text(slide, x, yy+0.04, label_w-0.08, row_h-0.02, name, 8.2, MUTED, True, valign=MSO_ANCHOR.MIDDLE)
        rect(slide, bar_x, yy+row_h*0.25, bar_w, row_h*0.42, '20314C', '20314C', radius=False)
        this_w = max(0.02, bar_w * val / max_value)
        rect(slide, bar_x, yy+row_h*0.25, this_w, row_h*0.42, color, color, radius=False)
        text(slide, bar_x+bar_w+0.05, yy+0.02, 0.72, row_h-0.02, f'{val:.1f}{suffix}', 8.2, WHITE, True, valign=MSO_ANCHOR.MIDDLE)
    if target is not None:
        tx = bar_x + bar_w * target/max_value
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(tx), Inches(y), Inches(0.015), Inches(h))
        line.fill.solid(); line.fill.fore_color.rgb = rgb(RED); line.line.color.rgb = rgb(RED)
        if target_label: text(slide, min(tx+0.06, x+w-1.15), y-0.18, 1.1, 0.15, target_label, 7.4, RED, True)

# Slide 1
s = add_base('Do not approve eight hires.', 'A targeted response fixes the real constraints and uses spare capacity before expanding payroll.', 'HEAD OF OPERATIONS | DECISION BRIEF')
rect(s, 0.55, 1.82, 7.55, 3.72, PANEL, BORDER)
text(s, 0.82, 2.08, 6.9, 0.25, 'RECOMMENDED OPERATING PLAN', 9, YELLOW, True)
label_value(s, 0.82, 2.52, 2.05, 'Transfer', '2 agents', 'H02 Lakeview -> H01 Greenfield', CYAN)
label_value(s, 3.05, 2.52, 2.05, 'Hire', '2 Fixed', 'H04 Hillcrest', GREEN)
label_value(s, 5.27, 2.52, 2.25, 'Intervene', 'H03', 'Fund the hold-reduction programme', YELLOW)
rect(s, 0.82, 4.10, 6.90, 1.05, PANEL2, PANEL2)
text(s, 1.05, 4.29, 2.1, 0.18, 'FIRST-MONTH SPEND', 8, MUTED, True)
text(s, 1.05, 4.56, 2.2, 0.36, 'BDT 62,800', 23, WHITE, True)
text(s, 4.0, 4.29, 2.3, 0.18, 'BUDGET RESERVE', 8, MUTED, True)
text(s, 4.0, 4.56, 2.1, 0.36, 'BDT 7,200', 23, GREEN, True)
rect(s, 8.35, 1.82, 4.43, 3.72, PANEL, BORDER)
text(s, 8.64, 2.10, 3.8, 0.3, 'WHY THIS IS BETTER', 9, YELLOW, True)
for i,(head,body) in enumerate([
    ('Use idle capacity','H02 is at 56.17% Week 2 utilisation and can release two Fixed agents within Cluster A.'),
    ('Hire only at the hard gap','H04 is the most constrained hub at 95.87% utilisation; two hires close its forecast gap.'),
    ('Fix the process at H03','64.42% of Riverside Week 2 holds are agent-side. Hiring alone would not remove Late Dispatch.')
]):
    yy=2.56+i*0.88
    text(s,8.64,yy,3.72,0.22,head,10,WHITE,True)
    text(s,8.64,yy+0.25,3.75,0.50,body,8.2,MUTED)
text(s,0.60,5.88,12.1,0.6,'Decision: approve the targeted plan, not the eight-agent request. Accept a managed two-week Riverside exception to the 85% planning target while keeping projected workload below the 40-attempt standard.',11,WHITE,True)

# Slide 2
s = add_base('Demand rose faster than staffing capacity.', 'Across the two-week observation window, both orders and delivery attempts accelerated in Week 2.', '01 | DEMAND SIGNAL')
metric(s,0.55,1.78,2.9,'Order growth','+16.3%','10,534 -> 12,255 orders',YELLOW)
metric(s,3.62,1.78,2.9,'Attempt growth','+19.0%','11,689 -> 13,906 attempts',CYAN)
metric(s,6.69,1.78,2.9,'Orders observed','22,789','13-26 October 2026',WHITE)
metric(s,9.76,1.78,3.02,'Attempt pressure','25,595','1.12 attempts per order overall',GREEN)
rect(s,0.55,3.18,7.35,3.38,PANEL,BORDER)
text(s,0.82,3.43,6.8,0.25,'WEEKLY VOLUME COMPARISON',9,YELLOW,True)
# grouped bars
chart_x, chart_y, base_y = 1.05, 4.15, 6.05
vals = [('Orders',10534,12255,YELLOW),('Assigned attempts',11689,13906,CYAN)]
for idx,(name,v1,v2,col) in enumerate(vals):
    gx = 1.7 + idx*3.0
    scale = 1.55/14000
    h1,h2=v1*scale,v2*scale
    rect(s,gx,base_y-h1,0.72,h1,'5D7597','5D7597',radius=False)
    rect(s,gx+0.84,base_y-h2,0.72,h2,col,col,radius=False)
    text(s,gx-0.1,base_y+0.10,0.9,0.2,'Week 1',8,MUTED,align=PP_ALIGN.CENTER)
    text(s,gx+0.78,base_y+0.10,0.9,0.2,'Week 2',8,MUTED,align=PP_ALIGN.CENTER)
    text(s,gx-0.2,base_y-h1-0.26,1.1,0.2,f'{v1:,}',8.2,WHITE,True,align=PP_ALIGN.CENTER)
    text(s,gx+0.65,base_y-h2-0.26,1.1,0.2,f'{v2:,}',8.2,WHITE,True,align=PP_ALIGN.CENTER)
    text(s,gx-0.2,6.40,2.0,0.2,name,8.5,col,True,align=PP_ALIGN.CENTER)
rect(s,8.15,3.18,4.63,3.38,PANEL,BORDER)
text(s,8.45,3.43,3.95,0.25,'WHAT THE CHANGE MEANS',9,YELLOW,True)
text(s,8.45,3.92,3.85,0.38,'Attempts grew 2.6 percentage points faster than orders.',15,WHITE,True)
text(s,8.45,4.54,3.85,0.55,'More volume is being generated by repeat work, not just more new parcels. Staffing should therefore use attempts per order, not order count alone.',9,MUTED)
text(s,8.45,5.42,3.85,0.72,'Planning implication: forecast each hub’s order volume using its observed 14-day attempts-per-order ratio, then apply the 85% workload target.',9,GREEN,True)

# Slide 3
s = add_base('Capacity is uneven across the six hubs.', 'Week 2 utilisation is calculated as assigned attempts / (active agents x 40 attempts/day x 7 days).', '02 | CAPACITY')
q2=pd.read_csv(Q/'q2_hub_utilisation.csv')
util_items=[(f"{r.hub_id} {r.hub_name}",float(r.week2_utilisation*100)) for r in q2.itertuples()]
rect(s,0.55,1.85,8.0,4.90,PANEL,BORDER)
text(s,0.85,2.13,7.3,0.25,'WEEK 2 UTILISATION BY HUB',9,YELLOW,True)
simple_bars(s,0.92,2.72,7.2,3.45,util_items,max_value=110,color=YELLOW,suffix='%',target=85,target_label='85% target')
rect(s,8.85,1.85,3.93,4.90,PANEL,BORDER)
text(s,9.15,2.13,3.3,0.25,'ACTION FLAGS',9,YELLOW,True)
for i,(h,val,act,col) in enumerate([
 ('H04 Hillcrest','95.87%','Hire 2 Fixed agents',RED),
 ('H03 Riverside','90.80%','Reduce agent-side holds',ORANGE),
 ('H01 Greenfield','88.64%','Receive 2 H02 transfers',RED),
 ('H06 Westwood','80.36%','Monitor only',CYAN),
 ('H05 Brookside','71.49%','Retain surplus; review returns',GREEN),
 ('H02 Lakeview','56.17%','Eligible same-cluster donor',GREEN),
]):
    yy=2.65+i*0.62
    text(s,9.15,yy,1.75,0.18,h,8.3,WHITE,True)
    text(s,11.05,yy,1.35,0.18,val,8.3,col,True,align=PP_ALIGN.RIGHT)
    text(s,9.15,yy+0.21,3.15,0.24,act,7.7,MUTED)

# Slide 4
s = add_base('Riverside is a process problem; Brookside is a returns problem.', 'The interventions should be different. A blanket headcount response would miss both signals.', '03 | QUALITY & PRODUCTIVITY')
metric(s,0.55,1.82,2.9,'Week 2 holds · H03','874','563 agent-side',RED)
metric(s,3.62,1.82,2.9,'Agent-side share · H03','64.42%','Late Dispatch: 312 holds',ORANGE)
metric(s,6.69,1.82,2.9,'Held orders delivered','81.49%','2,118 of 2,599 held orders',GREEN)
metric(s,9.76,1.82,3.02,'Held orders returned','9.43%','245 of 2,599 held orders',CYAN)
rect(s,0.55,3.25,6.0,3.37,PANEL,BORDER)
text(s,0.83,3.52,5.4,0.24,'TOP HOLD PATTERNS · WEEK 2',9,YELLOW,True)
q3=pd.read_csv(Q/'q3_week2_hold_reasons.csv')
r3=q3[q3.hub_id.eq('H03')].iloc[0]
text(s,0.85,4.03,5.3,0.28,'Riverside (H03)',13,WHITE,True)
text(s,0.85,4.45,5.25,0.3,f"{r3['top_1_hold_reason']}  {int(r3['top_1_hold_count'])} holds",10,RED,True)
text(s,0.85,4.88,5.15,0.55,'Action: review dispatch cut-off, route assignment, scan discipline and agent readiness before increasing permanent headcount.',9,MUTED)
text(s,0.85,5.75,5.25,0.45,'Brookside (H05): three agents exceed the >15% return-ratio flag after >30 days tenure.',9,GREEN,True)
rect(s,6.82,3.25,5.96,3.37,PANEL,BORDER)
text(s,7.12,3.52,5.3,0.24,'HIGH-RETURN AGENTS · Q5',9,YELLOW,True)
q5=pd.read_csv(Q/'q5_high_return_agents.csv')
for i,r in enumerate(q5.itertuples()):
    yy=4.02+i*0.68
    text(s,7.12,yy,2.1,0.2,f'{r.agent_id} · {r.agent_name}',9,WHITE,True)
    text(s,9.50,yy,1.05,0.2,r.hub_id,8.5,MUTED,True)
    text(s,10.65,yy,1.72,0.2,f'{r.return_ratio:.2%} returns',9,RED,True,align=PP_ALIGN.RIGHT)
    text(s,7.12,yy+0.26,4.9,0.2,f'{r.Returned} returned / {r.Assigned} assigned',7.8,MUTED)

# Slide 5
s = add_base('The four-week forecast shows a five-agent gross shortfall.', 'Q7 uses each hub’s 14-day attempts-per-order ratio and 34 planned attempts per agent per day.', '04 | FORECAST & STAFFING')
q7=pd.read_csv(Q/'q7_forecast_staffing.csv')
peak=q7.groupby(['hub_id','hub_name'],as_index=False).agg(peak_required=('required_agents','max'),active_agents=('active_agents','first'),peak_week=('required_agents','idxmax'))
peak=peak.sort_values('hub_id')
peak['gap']=peak.peak_required-peak.active_agents
rect(s,0.55,1.82,7.65,4.92,PANEL,BORDER)
text(s,0.85,2.10,7.0,0.24,'PEAK STAFFING NEED BY HUB · BEFORE INTERVENTIONS',9,YELLOW,True)
rows=[]
for r in peak.itertuples():
    gap=f'+{r.gap}' if r.gap>0 else str(r.gap)
    rows.append([r.hub_id+' '+r.hub_name,str(r.active_agents),str(r.peak_required),gap])
table(s,0.85,2.62,7.0,2.78,['Hub','Active now','Peak required','Gross gap'],rows,widths=[3.1,1.2,1.35,1.35],font_size=9)
text(s,0.88,5.72,6.85,0.62,'Gross positive gap: 5 agents (H01 +2, H03 +1, H04 +2). H02 and H05 have surplus capacity; only H02 can support H01 because transfers must stay inside a cluster.',9,MUTED)
rect(s,8.48,1.82,4.30,4.92,PANEL,BORDER)
text(s,8.78,2.10,3.7,0.24,'DEPLOYMENT LOGIC',9,YELLOW,True)
for i,(h,v,n,c) in enumerate([
 ('H01','+2','Same-cluster transfer from H02',CYAN),
 ('H02','-3 to -4','Donor; 9 agents remain after moves',GREEN),
 ('H03','+1','Programme reduces attempts; temporary target exception',ORANGE),
 ('H04','+2','Hire 2 Fixed agents',RED),
 ('H05','-1 to -2','Surplus; no cross-cluster move',GREEN),
 ('H06','0','No change',CYAN),
]):
    yy=2.68+i*0.58
    text(s,8.78,yy,0.75,0.2,h,9,WHITE,True)
    text(s,9.55,yy,1.05,0.2,v,9,c,True)
    text(s,10.58,yy,1.95,0.40,n,7.5,MUTED)

# Slide 6
s = add_base('Approve a targeted plan hub by hub.', 'Two Fixed hires address the lasting gap at Hillcrest; transfers solve Greenfield; Riverside gets a process intervention.', '05 | RECOMMENDATION')
rect(s,0.55,1.82,12.23,4.90,PANEL,BORDER)
text(s,0.85,2.10,11.6,0.24,'HUB ACTIONS AND INCREMENTAL FIRST-MONTH COST',9,YELLOW,True)
rows=[
 ['H01 Greenfield','Receive 2 Fixed transfers from H02','BDT 4,000'],
 ['H02 Lakeview','Transfer A1018 and A1015; 9 agents remain','No new spend'],
 ['H03 Riverside','Launch hold-reduction programme; no immediate hire','BDT 15,000'],
 ['H04 Hillcrest','Hire 2 Fixed agents; 11 agents total','BDT 43,800'],
 ['H05 Brookside','No hire; review 3 high-return agents','No new spend'],
 ['H06 Westwood','No staffing change','No new spend'],
]
table(s,0.85,2.58,11.62,3.22,['Hub','Action','First-month cost'],rows,widths=[2.2,6.5,2.92],font_size=9)
text(s,0.86,6.04,11.5,0.32,'Transfer candidates: A1018 (92.78% deliveries, 3.09% returns) and A1015 (90.86% deliveries, 2.65% returns). Both are Fixed agents in Cluster A.',8.5,MUTED)

# Slide 7
s = add_base('The BDT 70,000 budget is sufficient.', 'The recommended response costs BDT 62,800 in the first month and retains a BDT 7,200 reserve.', '06 | BUDGET & EXPECTED RETURN')
metric(s,0.55,1.82,2.9,'Budget available','70,000','BDT',WHITE)
metric(s,3.62,1.82,2.9,'First-month spend','62,800','89.7% of budget',YELLOW)
metric(s,6.69,1.82,2.9,'Reserve','7,200','10.3% held back',GREEN)
metric(s,9.76,1.82,3.02,'Programme net benefit','10,682','Avoided hold fees less programme cost',CYAN)
rect(s,0.55,3.25,6.2,3.32,PANEL,BORDER)
text(s,0.84,3.52,5.5,0.24,'BUDGET ALLOCATION',9,YELLOW,True)
alloc=[('H04 Fixed salaries',33800,YELLOW),('Hiring fees',10000,CYAN),('H02 -> H01 transfer fees',4000,GREEN),('H03 programme',15000,ORANGE)]
maxv=35000
for i,(name,val,col) in enumerate(alloc):
    yy=4.0+i*0.55
    text(s,0.85,yy,2.25,0.22,name,8.2,MUTED)
    rect(s,3.15,yy+0.02,2.35,0.18,'20314C','20314C',radius=False)
    rect(s,3.15,yy+0.02,2.35*val/maxv,0.18,col,col,radius=False)
    text(s,5.62,yy-0.02,0.8,0.24,f'{val:,}',8.5,WHITE,True,align=PP_ALIGN.RIGHT)
rect(s,7.03,3.25,5.75,3.32,PANEL,BORDER)
text(s,7.33,3.52,5.1,0.24,'RIVERSIDE HOLD PROGRAMME · MODELLED',9,YELLOW,True)
text(s,7.33,4.02,2.1,0.48,'856',25,WHITE,True)
text(s,9.28,4.09,2.9,0.28,'agent-side holds avoided over 4 weeks',8.8,MUTED)
text(s,7.33,4.80,2.2,0.48,'25,682',24,GREEN,True)
text(s,9.28,4.86,2.9,0.3,'BDT gross avoided hold charges',8.8,MUTED)
text(s,7.33,5.55,5.0,0.65,'Assumption: a linear ramp to 50% reduction over 14 days from 27 Oct. Estimated net direct benefit after the BDT 15,000 programme fee: BDT 10,682.',8.0,MUTED)

# Slide 8
s = add_base('Control the first 14 days; then reassess.', 'The plan is conditional. Use daily operating signals—not a fixed hiring promise—to release the reserve.', '07 | RISKS, CONTROLS & DECISION')
rect(s,0.55,1.82,8.05,4.92,PANEL,BORDER)
text(s,0.85,2.10,7.35,0.24,'EARLY-WARNING TRIGGERS',9,YELLOW,True)
risks=[
 ('Riverside agent-side holds','Track holds/order vs 25.71% Week 2 proxy. If no visible improvement by Day 14, revise intervention.'),
 ('Riverside workload','Forecast 35.2 and 34.4 attempts/agent/day in Weeks 1-2. Escalate above 40 or if backlog rises.'),
 ('H04 ramp','New hires plan at 24 attempts/day for first 7 days, then 34. Escalate if materially below ramp.'),
 ('H02 donor buffer','After two transfers, 9 remain versus peak need of 8. No third transfer.'),
 ('Demand / attempt intensity','Investigate if actual orders exceed forecast by 10% or attempts/order rises 5% above model.')
]
for i,(a,b) in enumerate(risks):
    yy=2.55+i*0.77
    text(s,0.86,yy,2.15,0.25,a,9,WHITE,True)
    text(s,3.02,yy,5.15,0.52,b,8.1,MUTED)
rect(s,8.88,1.82,3.90,4.92,PANEL,BORDER)
text(s,9.18,2.10,3.25,0.24,'DECISION REQUEST',9,YELLOW,True)
text(s,9.18,2.58,3.12,0.48,'Approve the BDT 62,800 plan.',18,WHITE,True)
text(s,9.18,3.25,3.1,0.72,'1. Authorise two H02 -> H01 transfers.\n2. Approve two Fixed hires at H04.\n3. Release BDT 15,000 for H03 programme.',9,MUTED)
text(s,9.18,4.52,3.05,0.75,'Retain BDT 7,200 reserve. Review results at Day 7 and Day 14; trigger new capacity only if the workload or backlog threshold is breached.',9,GREEN,True)
text(s,9.18,5.70,3.0,0.65,'Dashboard source is prepared in Streamlit. Public hosting and the final shareable URL still need to be completed by the candidate.',7.5,MUTED)

# metadata and save
prs.core_properties.title = 'Delivery - On The Go | Operations Decision Brief'
prs.core_properties.subject = 'Data Analyst Technical Assessment | 4-week staffing and budget recommendation'
prs.core_properties.author = 'Candidate'
prs.core_properties.keywords = 'operations analytics, staffing, delivery, dashboard, budget'
outfile = OUT / 'presentation.pptx'
prs.save(outfile)
print(outfile)
