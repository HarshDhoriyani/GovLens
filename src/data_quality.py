"""Data profiling and quality-report generation."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from config.config import (
    ALLOWED_CATEGORIES,
    ALLOWED_STATUSES,
    ANALYSIS_END,
    ANALYSIS_START,
    CATEGORY_DEPARTMENTS,
)

EXPECTED_COLUMNS = (
    "request_id",
    "submission_date",
    "district",
    "state",
    "service_category",
    "department",
    "status",
    "resolution_days",
    "source_type",
)


def profile_data(frame: pd.DataFrame) -> dict[str, object]:
    """Count common schema and business-rule issues without changing data."""
    missing_columns = sorted(set(EXPECTED_COLUMNS) - set(frame.columns))
    if missing_columns:
        raise ValueError(f"Input is missing required columns: {missing_columns}")

    parsed_dates = pd.to_datetime(frame["submission_date"], errors="coerce")
    numeric_days = pd.to_numeric(frame["resolution_days"], errors="coerce")
    statuses = frame["status"].astype("string")
    categories = frame["service_category"].astype("string")
    unresolved_with_days = statuses.isin(("Pending", "In Progress", "Rejected")) & (
        numeric_days.notna()
    )
    inconsistent_mapping = frame.apply(
        lambda row: (
            pd.notna(row["service_category"])
            and row["service_category"] in CATEGORY_DEPARTMENTS
            and row["department"] != CATEGORY_DEPARTMENTS[row["service_category"]]
        ),
        axis=1,
    )
    out_of_period = parsed_dates.notna() & (
        (parsed_dates < pd.Timestamp(ANALYSIS_START))
        | (parsed_dates > pd.Timestamp(ANALYSIS_END))
    )

    return {
        "raw_row_count": int(len(frame)),
        "missing_values_by_column": {
            column: int(count)
            for column, count in frame[list(EXPECTED_COLUMNS)]
            .isna()
            .sum()
            .items()
        },
        "duplicate_request_ids": int(frame["request_id"].duplicated(keep="first").sum()),
        "duplicate_records": int(frame.duplicated(keep="first").sum()),
        "invalid_categories": int(
            (categories.notna() & ~categories.isin(ALLOWED_CATEGORIES)).sum()
        ),
        "invalid_statuses": int(
            (statuses.notna() & ~statuses.isin(ALLOWED_STATUSES)).sum()
        ),
        "invalid_dates": int(parsed_dates.isna().sum()),
        "out_of_period_dates": int(out_of_period.sum()),
        "negative_resolution_times": int((numeric_days < 0).sum()),
        "unresolved_requests_with_resolution_times": int(unresolved_with_days.sum()),
        "invalid_numeric_resolution_times": int(
            (frame["resolution_days"].notna() & numeric_days.isna()).sum()
        ),
        "inconsistent_category_department_mappings": int(inconsistent_mapping.sum()),
        "cleaned_row_count": None,
        "removed_records": {},
        "corrected_records": {},
    }


def render_quality_report(
    profile: Mapping[str, object], cleaned: pd.DataFrame
) -> str:
    """Format the measured quality profile and final schema as Markdown."""
    missing = profile["missing_values_by_column"]
    removed = profile["removed_records"]
    corrected = profile["corrected_records"]
    lines = [
        "# Data Quality Report",
        "",
        "> Source: reproducible synthetic demonstration data; not official statistics.",
        "",
        "## Record counts",
        "",
        f"- Raw rows: **{profile['raw_row_count']:,}**",
        f"- Cleaned rows: **{profile['cleaned_row_count']:,}**",
        f"- Removed rows: **{sum(removed.values()):,}**",
        "",
        "## Missing values in raw input",
        "",
        "| Column | Missing values |",
        "|---|---:|",
    ]
    lines.extend(f"| {column} | {count:,} |" for column, count in missing.items())
    lines.extend(
        [
            "",
            "## Issues found in raw input",
            "",
            "| Issue | Count |",
            "|---|---:|",
        ]
    )
    issue_keys = (
        "duplicate_request_ids",
        "duplicate_records",
        "invalid_categories",
        "invalid_statuses",
        "invalid_dates",
        "out_of_period_dates",
        "negative_resolution_times",
        "unresolved_requests_with_resolution_times",
        "invalid_numeric_resolution_times",
        "inconsistent_category_department_mappings",
    )
    lines.extend(f"| {key.replace('_', ' ').capitalize()} | {profile[key]:,} |" for key in issue_keys)
    lines.extend(
        [
            "",
            "## Cleaning actions",
            "",
            "Rows with duplicate IDs, invalid dates, out-of-period dates, or unsupported statuses are removed; "
            "invalid categories become `Other Services`; missing district/state values become `Unknown`; "
            "negative or non-numeric resolution days become null; unresolved requests' resolution days are "
            "cleared; and departments are aligned to the category mapping. Counts below are row/field-level "
            "actions and are not necessarily additive.",
            "",
            "| Action | Count |",
            "|---|---:|",
        ]
    )
    lines.extend(f"| {name.replace('_', ' ').capitalize()} | {count:,} |" for name, count in removed.items())
    lines.extend(f"| Corrected: {name.replace('_', ' ')} | {count:,} |" for name, count in corrected.items())
    lines.extend(["", "## Final schema and data types", "", "| Column | Type |", "|---|---|"])
    lines.extend(f"| {name} | {dtype} |" for name, dtype in cleaned.dtypes.items())
    lines.append("")
    return "\n".join(lines)
