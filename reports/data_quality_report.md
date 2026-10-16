# Data Quality Report

> Source: reproducible synthetic demonstration data; not official statistics.

## Record counts

- Raw rows: **6,000**
- Cleaned rows: **6,000**
- Removed rows: **0**

## Missing values in raw input

| Column | Missing values |
|---|---:|
| request_id | 0 |
| submission_date | 0 |
| district | 0 |
| state | 0 |
| service_category | 0 |
| department | 0 |
| status | 0 |
| resolution_days | 2,126 |
| source_type | 0 |

## Issues found in raw input

| Issue | Count |
|---|---:|
| Duplicate request ids | 0 |
| Duplicate records | 0 |
| Invalid categories | 0 |
| Invalid statuses | 0 |
| Invalid dates | 0 |
| Out of period dates | 0 |
| Negative resolution times | 0 |
| Unresolved requests with resolution times | 0 |
| Invalid numeric resolution times | 0 |
| Inconsistent category department mappings | 0 |

## Cleaning actions

Rows with duplicate IDs, invalid dates, out-of-period dates, or unsupported statuses are removed; invalid categories become `Other Services`; missing district/state values become `Unknown`; negative or non-numeric resolution days become null; unresolved requests' resolution days are cleared; and departments are aligned to the category mapping. Counts below are row/field-level actions and are not necessarily additive.

| Action | Count |
|---|---:|
| Missing request id | 0 |
| Duplicate request id | 0 |
| Invalid submission date | 0 |
| Outside analysis period | 0 |
| Unsupported status | 0 |
| Corrected: invalid or missing category to other services | 0 |
| Corrected: missing district to unknown | 0 |
| Corrected: missing state to unknown | 0 |
| Corrected: invalid or negative resolution to missing | 0 |
| Corrected: unresolved resolution days cleared | 0 |
| Corrected: department aligned to service category | 0 |

## Final schema and data types

| Column | Type |
|---|---|
| request_id | string |
| submission_date | str |
| district | string |
| state | string |
| service_category | string |
| department | str |
| status | string |
| resolution_days | Float64 |
| source_type | str |
