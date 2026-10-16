import pandas as pd

from src.clean_data import clean_dataset
from src.generate_data import generate_dataset


def test_cleaning_reports_and_repairs_malformed_rows():
    frame = generate_dataset(row_count=30, seed=12)
    frame.loc[0, "request_id"] = frame.loc[1, "request_id"]
    frame.loc[2, "service_category"] = "Unmapped Service"
    frame.loc[3, "status"] = "Unknown Status"
    frame.loc[4, "submission_date"] = "not-a-date"
    frame.loc[5, "status"] = "Completed"
    frame.loc[5, "resolution_days"] = -4
    frame.loc[6, "district"] = None
    frame.loc[7, "department"] = "Wrong Department"
    frame.loc[8, "status"] = "Pending"
    frame.loc[8, "resolution_days"] = 3
    frame.loc[9, "submission_date"] = "2023-12-31"

    cleaned, profile = clean_dataset(frame)

    assert len(cleaned) == 26
    assert cleaned["request_id"].is_unique
    assert profile["duplicate_request_ids"] == 1
    assert profile["invalid_categories"] == 1
    assert profile["invalid_statuses"] == 1
    assert profile["invalid_dates"] == 1
    assert profile["out_of_period_dates"] == 1
    assert profile["negative_resolution_times"] == 1
    assert profile["unresolved_requests_with_resolution_times"] >= 1
    assert cleaned.loc[cleaned["request_id"].eq(frame.loc[2, "request_id"]), "service_category"].iloc[0] == "Other Services"
    assert cleaned.loc[cleaned["request_id"].eq(frame.loc[6, "request_id"]), "district"].iloc[0] == "Unknown"
    assert cleaned.loc[cleaned["request_id"].eq(frame.loc[7, "request_id"]), "department"].iloc[0] != "Wrong Department"
    assert pd.isna(
        cleaned.loc[cleaned["request_id"].eq(frame.loc[5, "request_id"]), "resolution_days"].iloc[0]
    )
    assert cleaned.loc[cleaned["status"].ne("Completed"), "resolution_days"].isna().all()


def test_cleaning_empty_eligible_population_reports_no_rate_later():
    frame = generate_dataset(row_count=10)
    frame["status"] = "Rejected"
    frame["resolution_days"] = None
    cleaned, profile = clean_dataset(frame)
    assert len(cleaned) == 10
    assert profile["removed_records"]["duplicate_request_id"] == 0
