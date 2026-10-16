# Power BI data import, transformations, and model

## Use the verified pipeline outputs

Run the pipeline from the GovLens project root before importing or refreshing:

```powershell
python scripts/run_pipeline.py
```

The primary, one-row-per-request fact table is:

```text
data/processed/service_requests.csv
```

Also import these two supporting files:

```text
data/raw/service_requests_synthetic.csv
data/processed/data_quality_summary.csv
```

Use `service_requests.csv` for all dashboard performance measures. Import the
raw file as a disconnected `raw_service_requests` table only for raw row and
duplicate-ID comparisons. Import the quality file as disconnected
`data_quality_summary`; its missing counts describe the raw input before
cleaning. Do not import the pre-aggregated performance CSVs into the same model:
they duplicate fact-table calculations and can create misleading filter paths.
The SQLite database has already been verified by the Python/SQL pipeline; CSV
import is the simplest portable Power BI Desktop route.

In Power BI Desktop, use **Home > Get data > Text/CSV > Transform Data** for
each file. Select each file using the file picker; do not copy a machine-specific
path into the report. Rename the queries exactly as above. Keep the raw and
quality tables loaded so their Data Quality visuals can use them. In Power
Query, use **Close & Apply** after setting the types below.

## Actual CSV columns and Power Query types

The inspected cleaned CSV has 6,000 rows and exactly these columns:

| Column | Power BI type | Treatment |
|---|---|---|
| `request_id` | Text | Preserve the synthetic ID, e.g. `GL-000001` |
| `submission_date` | Date | Parse the verified `yyyy-MM-dd` strings as Date |
| `district` | Text | Fictional demonstration district |
| `state` | Text | Fictional `Sample State ...` label |
| `service_category` | Text | Service category label |
| `department` | Text | Category-mapped department label |
| `status` | Text | Completed, Pending, In Progress, or Rejected |
| `resolution_days` | Decimal number | Keep nulls; do not replace null with zero |
| `source_type` | Text | Synthetic |

`raw_service_requests.csv` has the same nine columns. Set its types the same
way so the request-ID duplicate measure is numeric and date relationships do
not compare text to dates. The currently verified raw file has zero null dates
and statuses. The clean fact has 2,126 null `resolution_days` values; these are
expected because unresolved requests do not have resolution times.

The quality-summary CSV has columns `column` (Text) and `missing_values` (Whole
number), with one row for each of the nine raw fields.

Do not replace, filter away, or impute missing `resolution_days`. Hide
`source_type` from report authors only if its synthetic disclosure remains
visible on every report page. No row filters are required for the verified
generated data.

## Build dimensions from the fact query

### `dim_district`

In Power Query, right-click `service_requests` and choose **Reference**. Rename
the query to `dim_district`, keep only `district` and `state`, then choose
**Remove Rows > Remove Duplicates**. Confirm one row per district (six in the
verified data).

Equivalent Power Query M after creating a reference:

```powerquery
let
    Source = service_requests,
    KeepColumns = Table.SelectColumns(Source, {"district", "state"}),
    DistinctDistricts = Table.Distinct(KeepColumns),
    SortedRows = Table.Sort(DistinctDistricts, {{"district", Order.Ascending}})
in
    SortedRows
```

### `dim_service_category`

Reference `service_requests`, retain `service_category` and `department`,
remove duplicates, and name the query `dim_service_category` (six rows in the
verified data).

```powerquery
let
    Source = service_requests,
    KeepColumns = Table.SelectColumns(Source, {"service_category", "department"}),
    DistinctCategories = Table.Distinct(KeepColumns),
    SortedRows = Table.Sort(
        DistinctCategories,
        {{"service_category", Order.Ascending}}
    )
in
    SortedRows
```

### `dim_date`

After applying the fact query's Date type, use **Modeling > New table** and
create a contiguous date dimension with this DAX calculated table:

```DAX
dim_date =
VAR FirstDate =
    MINX ( ALL ( 'service_requests' ), 'service_requests'[submission_date] )
VAR LastDate =
    MAXX ( ALL ( 'service_requests' ), 'service_requests'[submission_date] )
RETURN
    ADDCOLUMNS (
        CALENDAR ( FirstDate, LastDate ),
        "Year", YEAR ( [Date] ),
        "Month Number", MONTH ( [Date] ),
        "Month", FORMAT ( [Date], "MMM" ),
        "Month Start", DATE ( YEAR ( [Date] ), MONTH ( [Date] ), 1 ),
        "Year Month", FORMAT ( [Date], "yyyy-MM" ),
        "Year Month Sort", YEAR ( [Date] ) * 100 + MONTH ( [Date] )
    )
```

Rename its `[Date]` column to `date`. In **Column tools**, sort `dim_date[Month]`
by `dim_date[Month Number]` and `dim_date[Year Month]` by
`dim_date[Year Month Sort]`. Choose **Table tools > Mark as date table** and
select `dim_date[date]`. The generated fact dates span 2024-01-01 through
2025-12-31.

## Relationships

In Model view, create only these active, one-to-many, single-direction
relationships (dimension filters fact):

| One side | Many side | Cardinality / direction |
|---|---|---|
| `dim_date[date]` | `service_requests[submission_date]` | 1:*; single, date to fact |
| `dim_district[district]` | `service_requests[district]` | 1:*; single, district to fact |
| `dim_service_category[service_category]` | `service_requests[service_category]` | 1:*; single, category to fact |

There are no relationships from `raw_service_requests` or
`data_quality_summary` to the fact or dimensions; leave both tables
disconnected. Do not relate dimensions to each other or create bidirectional
relationships. The disconnected raw table supports a distinct-ID quality
check; the quality summary supplies missing-value counts.

## Refresh and validation

After rerunning the pipeline, use **Home > Refresh** in Desktop. If any file
source has moved, edit that query's **Source** step using the file picker.
Recheck that `service_requests` remains one row per `request_id`, dates are
Date values, resolution duration is Decimal, and null durations remain blank.
Validate unfiltered cards against `data/processed/overall_metrics.csv`:
6,000 total; 3,874 completed; 958 pending; 738 in progress; 430 rejected;
5,570 eligible; 69.551167% completion; 8.903975 average resolution days.
The raw `data_quality_summary.csv` should show 2,126 missing resolution days
and zero missing values in each of the other eight columns.

The Quality page's issue counts are snapshots from
`reports/data_quality_report.md`; review that report after each pipeline run.
Do not imply those displayed validation results refresh dynamically unless you
replace the snapshot with newly verified report values.

## Add the measures

In Report or Data view, select `service_requests`, choose **Modeling > New
measure**, and add each definition from `powerbi/measures.dax` as a separate
measure. The `.dax` file contains successive named definitions; do not paste
the whole file into a single formula bar. Set `[Completion Rate]` to Percentage
with one decimal place and `[Average Resolution Days]` to Decimal number with
one decimal place. Set all request-count and duplicate/removed-record measures
to Whole number with a thousands separator.
