# Power BI handoff

**Status: one-page Power BI report and screenshot are present.** The supplied
`GovLens.pbix` contains KPI cards and charts for status, monthly volume, service
category, district, completion rate, and pending requests. The preview image is
`screenshots/dashboard-preview.png`. The report was not independently opened or
validated in Power BI Desktop in this environment.

The four-page layouts in [dashboard_specification.md](dashboard_specification.md)
are a proposed extension, not a description of the current report. To refresh
or extend it, run `python scripts/run_pipeline.py` from the project root, then
follow [power_query_notes.md](power_query_notes.md) for the source files, model,
and measures in [measures.dax](measures.dax).

Before presenting the report as finished, open it in Power BI Desktop, verify
the data sources and visuals, and add a visible synthetic-data disclosure to
the report pages. The supplied screenshot does not currently show that
disclosure.

Unfiltered verified metrics are 6,000 requests; 3,874 completed; 958 pending;
738 in progress; 430 rejected; 5,570 eligible; a 69.551167% completion rate;
and 8.903975 average resolution days. All rows and results are synthetic
demonstration data, not official statistics.
