import pandas as pd

from config.config import ALLOWED_CATEGORIES, ALLOWED_STATUSES
from src.generate_data import generate_dataset


def test_generation_is_reproducible_and_has_unique_ids():
    first = generate_dataset(row_count=250, seed=17)
    second = generate_dataset(row_count=250, seed=17)
    pd.testing.assert_frame_equal(first, second)
    assert first["request_id"].is_unique
    assert len(first) == 250


def test_generation_has_expected_columns_and_allowed_values():
    frame = generate_dataset(row_count=100)
    assert {
        "request_id",
        "submission_date",
        "district",
        "state",
        "service_category",
        "department",
        "status",
        "resolution_days",
        "source_type",
    } <= set(frame.columns)
    assert set(frame["service_category"]) <= set(ALLOWED_CATEGORIES)
    assert set(frame["status"]) <= set(ALLOWED_STATUSES)
    assert frame["source_type"].eq("Synthetic").all()
    assert frame.loc[frame["status"].ne("Completed"), "resolution_days"].isna().all()
    assert frame["resolution_days"].dropna().ge(0).all()


def test_generation_rejects_nonpositive_row_count():
    try:
        generate_dataset(0)
    except ValueError as error:
        assert "at least 1" in str(error)
    else:
        raise AssertionError("Expected a ValueError for zero rows.")
