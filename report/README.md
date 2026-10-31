# Report and presentation assets

- `final_assessment.pdf`: assessment report with query results, strategic answers, dashboard UI previews and editable PostgreSQL SQL text.
- `presentation.pptx` / `presentation.pdf`: eight-slide executive decision deck.
- `strategic_analysis.md`: complete written Q8-Q10 recommendation and assumptions.
- `build_presentation.py`: rebuilds the editable PowerPoint deck from the supplied query-result CSVs.
- `rebuild_sql_appendix.py`: rebuilds the PDF's SQL appendix from `sql/assessment_queries.sql` as selectable raw text. It expects the current report PDF to contain the first 22 report pages before appending SQL.

The report's dashboard images are clearly labelled as UI previews rather than live browser screenshots. Replace them with browser captures and add the real public no-login URL after deploying the Streamlit app.
