# Power BI handoff

**Status: manual implementation guide complete; Power BI report not built.**
Power BI Desktop was not found in the inspected environment. No `.pbix` or
dashboard screenshots exist.

Run `python scripts/run_pipeline.py` from the project root. In Power BI Desktop,
import the cleaned fact, raw input, and raw missing-value summary described in
[power_query_notes.md](power_query_notes.md). Create the three active,
single-direction dimension-to-fact relationships and eight requested DAX
measures. Then implement the four page layouts and measured quality snapshot in
[dashboard_specification.md](dashboard_specification.md). The measure formulas
are in [measures.dax](measures.dax).

Unfiltered verified metrics are 6,000 requests; 3,874 completed; 958 pending;
738 in progress; 430 rejected; 5,570 eligible; a 69.551167% completion rate;
and 8.903975 average resolution days. All rows and results are synthetic
demonstration data, not official statistics.
