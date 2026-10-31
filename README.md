# Delivery - On The Go | Data Analyst Technical Assessment

A complete, data-backed assessment project built from the eight supplied CSV tables. The dashboard source is a multi-page Streamlit application; analysis and calculations are kept in reusable Python modules.

## Run the dashboard

```bash
cd delivery_ops_assessment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app expects the eight source CSV files in `data/`. They are included in this package.

## Dashboard pages

1. **Executive overview** - order and attempt trends, KPI cards, hub utilisation and priority actions.
2. **Hub performance** - Week 1 / Week 2 utilisation, attempt growth and headcount.
3. **Agent productivity** - agent-day output, top individual delivery rates and Q5 high-return flags.
4. **Holds & returns** - agent/customer-side hold mix, top hold reasons and final outcomes of held orders.
5. **Forecast & staffing** - four-week agent requirements, staffing gaps and the Riverside programme scenario.
6. **Cost efficiency** - cost per delivered order and cost-component breakdown for both weeks.

## Project structure

```text
delivery_ops_assessment/
├── app.py
├── requirements.txt
├── README.md
├── .streamlit/config.toml
├── data/                         # all 8 source CSVs
├── pages/                        # Streamlit pages
├── src/
│   ├── metrics.py                # reusable calculations and validation
│   ├── dashboard_context.py      # cached data context for Streamlit
│   ├── ui.py                     # shared theme and UI components
│   ├── data_loader.py
│   └── data_validation.py
├── sql/
│   ├── schema.sql
│   ├── import_data.sql
│   └── assessment_queries.sql    # PostgreSQL Q1-Q7 queries
├── outputs/
│   ├── query_results/            # exported result tables
│   ├── dashboard_screenshots/    # data-backed UI previews
│   └── analysis_summary.json
├── tests/
│   └── test_analysis.py
├── report/
│   ├── final_assessment.pdf
│   ├── strategic_analysis.md
│   ├── presentation.pptx
│   ├── presentation.pdf
│   ├── build_presentation.py
│   └── rebuild_sql_appendix.py
└── deployment/
    └── deployment_guide.md
```

## SQL

The supplied SQL uses PostgreSQL. Create the tables with:

```bash
psql "$DATABASE_URL" -f sql/schema.sql
psql "$DATABASE_URL" -f sql/import_data.sql
```

Then run `sql/assessment_queries.sql` in psql or a PostgreSQL client such as DBeaver. `import_data.sql` uses psql's `\copy` command and expects the current working directory to be the project root.

## Analysis definitions and assumptions

- **Period:** 13-26 October 2026. Week 1 is 13-19 October; Week 2 is 20-26 October.
- **Attempts:** each `Assigned` event represents one attempt. Each attempt has exactly one `Delivered`, `Hold` or `Returned` outcome.
- **Q1 roster:** all 64 agents are included for Week 1; only the 62 Active agents are included for Week 2. Every employed agent-day appears in the daily table, including zero-activity days. Hub average deliveries per agent per day divides delivered outcomes by available agent-days.
- **Utilisation:** assigned attempts divided by available agents × 40 attempts per day × 7 calendar days. Week 1 headcount includes the two agents who left at the end of that week; Week 2 does not.
- **Agent-side holds:** Late Dispatch, Not Attempted and Agent Time Shortage. All other hold reasons are customer-side.
- **Q4:** count unique orders with at least one Hold event and classify each using `orders.final_status`.
- **Q5:** return ratio is Returned outcome events divided by Assigned attempts. Tenure is measured on 26 October 2026 and must be strictly greater than 30 days.
- **Q6 working day:** an agent-day with at least one Assigned event. Fixed pay is monthly salary / 26 for each inferred workday. Variable pay is daily allowance per inferred workday plus allowance per Delivered outcome. Hold and return charges are allocated to the event week. Delivered outcomes in the same event week are the denominator. COD amount and delivery charge are not treated as operating costs because they are not in the cost sheet.
- **Q7:** uses each hub's full 14-day Assigned attempts / unique original orders ratio to translate forecast orders into attempt demand. Required agents = ceiling(forecast attempts / (7 × 40 × 85%)).
- **Riverside scenario:** the hold programme model uses the more recent Week 2 attempts-per-order rate for caution. The programme effect is assumed to grow linearly from zero to its full 50% agent-side-hold reduction over 14 calendar days, starting 27 October. The source specifies a 14-day time to full effect but does not specify the ramp curve; linear interpolation is an explicit modelling assumption.
- **New-hire ramp:** during the first seven days, a new agent is modelled at 60% of the 40-attempt standard (24 attempts/day). After ramp-up, planning throughput is 85% of standard (34 attempts/day).
- **Staff transfer:** H02 -> H01 is permitted because both are in Cluster A and H02's pre-transfer Week 2 utilisation is below 75%. H05 is also below 75%, but it cannot donate to the Cluster A/B shortage hubs because transfers are restricted to the same cluster.

## Tests

Run:

```bash
python -m pytest -q
```

The data/metric tests pass in the supplied build environment. Streamlit itself was not installed in that offline build environment, so the Streamlit server could not be launched there. Install requirements in an internet-enabled Python environment and verify `streamlit run app.py` before deployment.

## Dashboard preview and public deployment

The six PNGs in `outputs/dashboard_screenshots/` are data-backed UI previews for each Streamlit page. They are not browser captures from a running Streamlit server. The build environment used for this package did not have Streamlit installed and could not download it, so the app was syntax-checked but not launched here. After installing requirements, run `streamlit run app.py`, verify all six pages, and replace the preview images with real browser screenshots before submission.

A public, no-login Streamlit URL cannot be generated from this local project package. Deploy the project using the steps in `deployment/deployment_guide.md`, verify it in a private/incognito browser, then paste the public URL into the final PDF's dashboard-link field and the submission form. Do not submit a made-up or local-only URL.

The SQL is PostgreSQL dialect. The result tables in this package were calculated and tested with the Python analysis engine; the SQL file is included as editable PostgreSQL source and should be run in a PostgreSQL environment when you do the final end-to-end database check.
# delivery-ops-analytics
