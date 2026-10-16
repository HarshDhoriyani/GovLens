"""Schema validation, deterministic cleaning, and business-rule checks."""

from __future__ import annotations

import pandas as pd

from config.config import (
    ALLOWED_CATEGORIES,
    ALLOWED_STATUSES,
    ANALYSIS_END,
    ANALYSIS_START,
    CATEGORY_DEPARTMENTS,
)
from src.data_quality import EXPECTED_COLUMNS, profile_data


def clean_dataset(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    """Clean input records and return auditable row-removal/correction counts."""
    profile = profile_data(frame)
    cleaned = frame.loc[:, EXPECTED_COLUMNS].copy()
    removed: dict[str, int] = {}
    corrected: dict[str, int] = {}

    for column in ("request_id", "status", "service_category"):
        cleaned[column] = cleaned[column].astype("string").str.strip()

    valid_id = cleaned["request_id"].notna() & cleaned["request_id"].ne("")
    removed["missing_request_id"] = int((~valid_id).sum())
    cleaned = cleaned.loc[valid_id].copy()
    duplicate_id = cleaned["request_id"].duplicated(keep="first")
    removed["duplicate_request_id"] = int(duplicate_id.sum())
    cleaned = cleaned.loc[~duplicate_id].copy()

    dates = pd.to_datetime(cleaned["submission_date"], errors="coerce")
    invalid_date = dates.isna()
    removed["invalid_submission_date"] = int(invalid_date.sum())
    cleaned = cleaned.loc[~invalid_date].copy()
    dates = dates.loc[~invalid_date]
    in_period = dates.between(ANALYSIS_START, ANALYSIS_END)
    removed["outside_analysis_period"] = int((~in_period).sum())
    cleaned = cleaned.loc[in_period].copy()
    dates = dates.loc[in_period]
    cleaned["submission_date"] = dates.dt.strftime("%Y-%m-%d")

    valid_status = cleaned["status"].isin(ALLOWED_STATUSES)
    removed["unsupported_status"] = int((~valid_status).sum())
    cleaned = cleaned.loc[valid_status].copy()

    invalid_category = ~cleaned["service_category"].isin(ALLOWED_CATEGORIES)
    corrected["invalid_or_missing_category_to_other_services"] = int(invalid_category.sum())
    cleaned.loc[invalid_category, "service_category"] = "Other Services"

    for column in ("district", "state"):
        missing_value = cleaned[column].isna() | cleaned[column].astype("string").str.strip().eq("")
        corrected[f"missing_{column}_to_unknown"] = int(missing_value.sum())
        cleaned.loc[missing_value, column] = "Unknown"
        cleaned[column] = cleaned[column].astype("string").str.strip()

    numeric_days = pd.to_numeric(cleaned["resolution_days"], errors="coerce")
    invalid_numeric = cleaned["resolution_days"].notna() & numeric_days.isna()
    negative_days = numeric_days < 0
    corrected["invalid_or_negative_resolution_to_missing"] = int(
        (invalid_numeric | negative_days).sum()
    )
    numeric_days = numeric_days.mask(invalid_numeric | negative_days)
    unresolved = cleaned["status"].ne("Completed")
    corrected["unresolved_resolution_days_cleared"] = int(
        (unresolved & numeric_days.notna()).sum()
    )
    numeric_days = numeric_days.mask(unresolved)
    cleaned["resolution_days"] = numeric_days.astype("Float64")

    expected_department = cleaned["service_category"].map(CATEGORY_DEPARTMENTS)
    mapping_mismatch = cleaned["department"].ne(expected_department) | cleaned["department"].isna()
    corrected["department_aligned_to_service_category"] = int(mapping_mismatch.sum())
    cleaned["department"] = expected_department
    cleaned["source_type"] = "Synthetic"

    cleaned = cleaned.reset_index(drop=True)
    profile["cleaned_row_count"] = int(len(cleaned))
    profile["removed_records"] = removed
    profile["corrected_records"] = corrected
    return cleaned, profile
