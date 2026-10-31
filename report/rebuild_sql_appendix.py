from pathlib import Path
import textwrap
import fitz
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
REPORT = Path(__file__).resolve().parent
FINAL = REPORT / 'final_assessment.pdf'
SQL_FILE = ROOT / 'sql' / 'assessment_queries.sql'
TEMP_SQL = REPORT / '_sql_appendix_raw.pdf'
TEMP_OUT = REPORT / '_assessment_rebuilt.pdf'

PAGE_W, PAGE_H = landscape(A4)
font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
pdfmetrics.registerFont(TTFont('DejaVuMono', font_path))
pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))

raw_lines = SQL_FILE.read_text(encoding='utf-8').splitlines()
# Wrap only when needed, preserving SQL operators and comments as literal selectable characters.
wrapped = []
for line in raw_lines:
    if len(line) <= 150:
        wrapped.append(line)
    elif not line.strip():
        wrapped.append('')
    else:
        chunks = textwrap.wrap(line, width=150, subsequent_indent='    ',
                               break_long_words=False, break_on_hyphens=False,
                               replace_whitespace=False, drop_whitespace=False)
        wrapped.extend(chunks or [''])

c = canvas.Canvas(str(TEMP_SQL), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
c.setTitle('Appendix A - Editable PostgreSQL SQL')
c.setAuthor('Candidate')
left, right = 38, PAGE_W-34
body_top = PAGE_H - 48
body_bottom = 34
line_h = 8.35
max_lines = int((body_top-body_bottom)//line_h)

page_num = 23
line_idx = 0
while line_idx < len(wrapped):
    # Consistent report header.
    c.setFillColorRGB(0.043, 0.075, 0.125)
    c.rect(0, PAGE_H-36, PAGE_W, 36, fill=1, stroke=0)
    c.setFillColorRGB(1,1,1)
    c.setFont('DejaVuSans', 8)
    c.drawString(left, PAGE_H-23, 'DELIVERY - ON THE GO  |  DATA ANALYST TECHNICAL ASSESSMENT')
    c.setFillColorRGB(0.10,0.18,0.30)
    c.roundRect(left, PAGE_H-54, right-left, 13, 3, fill=1, stroke=0)
    c.setFillColorRGB(0.97,0.78,0.37)
    c.setFont('DejaVuSans-Bold', 7)
    c.drawString(left+7, PAGE_H-50, 'APPENDIX A  |  EDITABLE POSTGRESQL SQL  |  QUERIES Q1-Q7')

    y = body_top
    for _ in range(max_lines):
        if line_idx >= len(wrapped): break
        line = wrapped[line_idx]
        # Use a slightly stronger color for major section marker comments.
        if line.strip().startswith('-- Q') and len(line.strip()) < 90:
            c.setFillColorRGB(0.06,0.20,0.34)
        elif line.strip().startswith('--'):
            c.setFillColorRGB(0.31,0.38,0.48)
        else:
            c.setFillColorRGB(0.08,0.10,0.14)
        c.setFont('DejaVuMono', 6.65)
        c.drawString(left, y, line)
        y -= line_h
        line_idx += 1
    # Footer.
    c.setFillColorRGB(0.37,0.43,0.53)
    c.setFont('DejaVuSans', 6.5)
    c.drawString(left, 17, 'Assessment analysis package  |  SQL source: sql/assessment_queries.sql')
    c.drawRightString(right, 17, f'Page {page_num}')
    c.showPage()
    page_num += 1
c.save()

# Keep the validated report front matter, all results, strategy and dashboard pages (1-22),
# then replace the escaped SQL appendix with raw selectable SQL generated above.
base = fitz.open(FINAL)
rebuilt = fitz.open()
rebuilt.insert_pdf(base, from_page=0, to_page=21)
# Strict-target alternative: include the budgeted alternative that hires one Variable agent at H03
# rather than funding the Riverside process programme.
strategy_page = rebuilt[12]  # page 13 in the report
strategy_page.draw_rect(fitz.Rect(42, 421, 798, 542), color=(0.82, 0.86, 0.91),
                        fill=(0.96, 0.975, 0.99), width=0.8, overlay=True)
strategy_page.insert_text((54, 442), 'STRICT 85% ALTERNATIVE', fontname='hebo', fontsize=9.2,
                          color=(0.08, 0.17, 0.29), overlay=True)
alt_text = (
    'Replace the H03 hold-reduction programme with one Variable hire at Riverside. '
    'Keeping two Fixed hires at H04 and two H02-to-H01 transfers, the estimated first-month '
    'cost is BDT 68,036 (including BDT 15,236 Variable pay and a BDT 5,000 hiring fee), '
    'leaving BDT 1,964. This option meets the 85% planning target earlier, but does not fix '
    'the agent-side dispatch problem and gives up the modelled BDT 25,682 of avoided hold charges.'
)
strategy_page.insert_textbox(fitz.Rect(54, 452, 785, 527), alt_text, fontname='helv', fontsize=8.1,
                             lineheight=1.25, color=(0.15, 0.20, 0.27), overlay=True)
# Remove original footer text cleanly, then add a single corrected footer to pages 1-22.
for i in range(len(rebuilt)):
    p = rebuilt[i]
    p.add_redact_annot(fitz.Rect(30, 566, 814, 584), fill=(1, 1, 1), cross_out=False)
    p.apply_redactions(images=0, graphics=0)
    p.insert_text((37, 576), 'Assessment analysis package  |  Data period: 13-26 Oct 2026  |  Forecast: 27 Oct-23 Nov 2026',
                  fontname='helv', fontsize=6.5, color=(0.37, 0.43, 0.53), overlay=True)
    p.insert_text((776, 576), f'Page {i+1}', fontname='helv', fontsize=7,
                  color=(0.37, 0.43, 0.53), overlay=True)
appendix = fitz.open(TEMP_SQL)
rebuilt.insert_pdf(appendix)
meta = base.metadata
meta['title'] = 'Delivery - On The Go | Data Analyst Technical Assessment'
meta['subject'] = 'SQL assessment, strategic analysis, dashboard previews and editable PostgreSQL SQL'
rebuilt.set_metadata(meta)
rebuilt.save(TEMP_OUT, garbage=4, deflate=True)
base.close(); appendix.close(); rebuilt.close()
TEMP_OUT.replace(FINAL)
TEMP_SQL.unlink(missing_ok=True)
print(f'Rebuilt {FINAL} with raw SQL appendix')
