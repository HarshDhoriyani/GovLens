# GovLens Power BI dashboard build specification

## Report status and verified model

Power BI Desktop was not found in either inspected installation location or on
`PATH`. No `.pbix` exists. This document specifies a manual implementation
against the generated, verified project files; it does not claim a report was
built or visually validated in Power BI.

Use the exact sources, type conversions, dimensions, and three relationships
in [power_query_notes.md](power_query_notes.md). The fact table is
`service_requests`, built from the 6,000-row
`data/processed/service_requests.csv`; `raw_service_requests` and
`data_quality_summary` are disconnected support tables.

**Persistent disclosure:** place “Synthetic demonstration data — not official
statistics” in the header/footer of every page. Sample district and state
labels are fictional.

## Metric and filter contract

- Eligible requests are rows whose status is exactly `Completed`, `Pending`,
  or `In Progress`. Rejected requests and any blank/unrecognized status are
  excluded. The verified cleaned file has only four allowed statuses and no
  missing status values.
- Completion rate is completed requests divided by eligible requests. If the
  denominator is zero, the DAX measure returns `BLANK()`, matching Python
  `None` and SQL `NULLIF` behavior rather than showing a misleading 0%.
- The status-specific measures remove the status filter before applying their
  own status. Thus cards remain named-state counts even if a status slicer is
  used. Eligible and completion measures use the same denominator under
  status selections. Date, district, and category filters remain active.
- `Total Requests` counts cleaned fact rows and responds to all filters that
  reach the fact. Unfiltered, it is 6,000.
- Average resolution days includes only Completed requests with a nonblank,
  nonnegative duration. DAX `AVERAGE` ignores blanks; the explicit lower bound
  matches the Python cleaning rule.
- Unresolved backlog means Pending + In Progress; Rejected is not backlog.
- The Quality page's missing-value counts are from raw data. In the verified
  run, 2,126 resolution times are blank by design; the other eight columns
  each have zero missing values.

## Global visual system and page behavior

- **Canvas:** 16:9, 1280 × 720 reference layout. Use a white or very light gray
  background, navy headings (`#16324F`), teal accents (`#168C8C`), blue for
  completed (`#4472C4`), amber for pending (`#F2B134`), purple for in progress
  (`#8064A2`), and muted red for rejected (`#C0504D`). Keep category colors
  consistent between pages.
- Use Aptos/Segoe UI, 20–24 pt page titles, 11–13 pt chart labels, and 10–11 pt
  notes. Avoid color-only status distinctions; display labels and legends.
- Header: page title at left, disclosure underneath, slicers aligned right or
  in a consistent left rail. Footer: “GovLens portfolio prototype · Synthetic
  data · 2024–2025”.
- Format counts as whole numbers with thousands separators; completion rate
  and change percentages to one decimal place; duration to one decimal day.
- Add page navigation buttons and useful descriptive visual titles. Enable
  cross-filtering for charts on the same page except where called out.
- Date slicers use `dim_date[date]`; district and category slicers use
  dimension labels, not duplicate fact labels.

## Page 1 — Executive Overview

**Slicers:** `dim_date[date]` (Between), `dim_district[district]` (Dropdown),
`dim_service_category[service_category]` (Dropdown). No status slicer here;
status mix is shown as a chart and the main KPI row remains interpretable.

| Position | Visual type | Fields / measures | Format and interactions |
|---|---|---|---|
| Header row | Text box | “GovLens | Service Delivery Overview”; synthetic disclosure | Persistent, visible disclosure |
| KPI row (5 equal cards) | Card (new) | `[Total Requests]`; `[Completed Requests]`; `[Pending Requests]`; `[Completion Rate]`; `[Average Resolution Days]` | Counts with separators; rate 1 decimal %; duration `0.0 days`; date/district/category slicers filter all cards |
| Main left | Line chart | X: `dim_date[Month Start]`; Y: `[Total Requests]` | Sort ascending by Month Start; markers on; title “Requests submitted by month”; date axis |
| Main right | Clustered bar chart | Y: `dim_service_category[service_category]`; X: `[Total Requests]` | Descending by total; title “Requests by service category”; data labels |
| Bottom left | Donut chart | Legend: `service_requests[status]`; Values: `[Total Requests]` | Fixed status colors; show category, count, %; title “Request status distribution” |
| Bottom right | Clustered column chart | X: `dim_date[Month Start]`; Y: `[Completed Requests]`, `[Pending Requests]`, `[In Progress Requests]`, `[Rejected Requests]` | Consistent state colors; title “Monthly status mix”; legend visible |

## Page 2 — District Performance

**Slicers:** date Between, district Dropdown, category Dropdown, status
Dropdown. The four status-specific measures intentionally keep their named
status counts; `Total Requests` follows a selected status. Completion rate
always uses the full eligible population for other active filters, not just
the selected status.

| Position | Visual type | Fields / measures | Format and interactions |
|---|---|---|---|
| Upper left | Clustered bar chart | Y: `dim_district[district]`; X: `[Total Requests]` | Sort descending by requests; whole-number labels; title “Districts ranked by request volume” |
| Upper right | Bar chart | Y: `dim_district[district]`; X: `[Completion Rate]` | Sort ascending to surface lower rates; axis 0–100%; data labels; subtitle/tooltip: rejected excluded |
| Lower left | Clustered column chart | X: `dim_district[district]`; Values: `[Pending Requests]`, `[In Progress Requests]` | Status colors; title “Unresolved requests by district”; define unresolved as pending + in progress |
| Lower right | Scatter chart | X: `[Total Requests]`; Y: `[Completion Rate]`; Details: `dim_district[district]`; Size: `[Unresolved Requests]`; Tooltips: `[Completed Requests]`, `[Rejected Requests]` | Title “Volume vs. eligible-request completion”; no trendline or causal annotation |
| Optional full-width | Matrix | Rows: district; Values: `[Total Requests]`, `[Completed Requests]`, `[Pending Requests]`, `[In Progress Requests]`, `[Rejected Requests]`, `[Eligible Requests]`, `[Completion Rate]` | Conditional formatting on rate; grand total; use as a ranking/validation table |

Disable interactions only when the status slicer would make volume comparisons
hard to interpret; document any disabled visual interaction. Do not infer that
volume causes completion-rate differences.

## Page 3 — Service Analysis

**Slicers:** date Between, category Dropdown, district Dropdown, status
Dropdown. Category labels use the dimension. Status-specific measures remain
stable under the status slicer; `Total Requests` follows its selection.

| Position | Visual type | Fields / measures | Format and interactions |
|---|---|---|---|
| KPI strip | Cards | `[Total Requests]`; `[Completion Rate]`; `[Unresolved Requests]`; `[Average Resolution Days]` | Standard count/rate/day formats |
| Upper left | Clustered bar chart | Y: category; X: `[Total Requests]` | Descending; data labels; title “Requests by service category” |
| Upper right | Bar chart | Y: category; X: `[Completion Rate]` | 0–100% axis, one decimal %; title “Eligible-request completion by category” |
| Center full width | Line chart | X: `dim_date[Month Start]`; Y: `[Total Requests]`; Legend: category | Monthly volume by category; sort by date; title “Category trends over time” |
| Lower left | Stacked column chart | X: category; Values: `[Pending Requests]`, `[In Progress Requests]` | Pending amber, in-progress purple; title “Unresolved requests by category” |
| Lower right | Histogram (binned column chart) | Axis: `service_requests[resolution_days]` grouped into 5-day bins; Values: distinct count of `request_id`; visual filter `status = Completed`, `resolution_days` is not blank, and `resolution_days >= 0` | Add average reference line or tooltip `[Average Resolution Days]`; title “Completed-request resolution-time distribution”; label that long tails affect the mean |

Create the histogram bin by right-clicking `resolution_days` in the Fields
pane, selecting **New group**, and choosing **Bin** with a 5-day bin size. Use
the generated bin column only for this chart. If the Power BI version does not
support a native bin, use a column chart grouped by a Power Query-created
5-day range. The verified data's resolution distribution is right-skewed; do
not imply the mean represents a typical request.

## Page 4 — Data Quality and Methodology

**Slicers:** no slicers. This page reports dataset-level quality, not a
selection-dependent quality score.

| Position | Visual type | Fields / measures | Format and interactions |
|---|---|---|---|
| Header | Text box | “Data Quality & Methodology” plus synthetic-source disclosure | Clearly state fictional labels / not official performance |
| KPI row | Cards | `[Raw Records]`; `[Cleaned Records]`; `[Duplicate Request IDs]`; removed rows = raw minus cleaned | Verified run: 6,000; 6,000; 0; 0 |
| Main left | Table | `data_quality_summary[column]`, `data_quality_summary[missing_values]` | Sort descending by missing_values; show all nine fields; highlight 2,126 resolution-day nulls |
| Main right | Table or matrix (snapshot) | Entered columns `validation_check`, `records`, `result` with rows below | Counts are verified-run snapshot from `reports/data_quality_report.md`; update after each pipeline rerun |
| Lower left | Text box | Metric definitions below | Compact, readable methodology |
| Lower right | Text box | Provenance, cleaning, limitations below | Cite the project reports and fixed seed |

Create the validation snapshot using **Home > Enter data**, name it
`quality_validation_snapshot`, and use these rows from the inspected
`reports/data_quality_report.md`:

| validation_check | records | result |
|---|---:|---|
| Raw rows | 6000 | Pass |
| Cleaned rows | 6000 | Pass |
| Duplicate request IDs | 0 | Pass |
| Duplicate full rows | 0 | Pass |
| Invalid categories | 0 | Pass |
| Invalid statuses | 0 | Pass |
| Invalid dates | 0 | Pass |
| Dates outside analysis period | 0 | Pass |
| Negative resolution times | 0 | Pass |
| Unresolved requests with resolution times | 0 | Pass |
| Invalid numeric resolution values | 0 | Pass |
| Category/department mapping mismatches | 0 | Pass |

This entered table is a **snapshot**, not a live validation feed; after rerunning
the Python pipeline, refresh the missing-value CSV and replace snapshot values
from the newly generated data-quality report.

Display these methodology statements:

- **Provenance:** reproducible synthetic demonstration dataset; seed `20261016`;
  6,000 rows; submission period 2024-01-01 through 2025-12-31. Public data was
  not used. District/state names are fictional labels.
- **Completion:** Completed / (Completed + Pending + In Progress). Rejected,
  blank, and unrecognized statuses do not enter the eligible denominator.
- **Resolution days:** average of completed records with valid non-negative
  values; blanks are not zero. The raw dataset has 2,126 missing durations,
  primarily because unresolved requests do not have a duration.
- **Cleaning:** duplicate request IDs, invalid/out-of-period dates, and
  unsupported statuses are removed; invalid category is mapped to Other
  Services; negative/non-numeric duration becomes null; unresolved durations
  are cleared; department is aligned to category.
- **Limitation:** results describe only the generated sample. No actual
  government performance, service levels, causal relationship, or intervention
  effect is represented.

## Portfolio QA and screenshot checklist

Before sharing the `.pbix`, validate the unfiltered report against
`data/processed/overall_metrics.csv`:

| Measure | Verified value |
|---|---:|
| Total Requests | 6,000 |
| Completed Requests | 3,874 |
| Pending Requests | 958 |
| In Progress Requests | 738 |
| Rejected Requests | 430 |
| Eligible Requests | 5,570 |
| Completion Rate | 69.551167% (display as 69.6%) |
| Average Resolution Days | 8.903975 (display as 8.9) |

Also verify the district/category comparisons against their processed
performance CSVs; verify monthly counts against `monthly_trends.csv`; verify
missing fields against `data_quality_summary.csv`; and confirm the
validation-snapshot counts against `reports/data_quality_report.md`.
Test at least one date, district, and category selection; confirm the
completion denominator excludes rejected records and returns blank when no
eligible records remain; confirm the page disclosure remains visible.

Save the manually built report as `powerbi/GovLens.pbix` only after those
checks. Capture legible 16:9 screenshots of all four pages, including the
synthetic disclosure, and add them under `powerbi/screenshots/`. Neither a
report nor screenshots currently exist.
