import pandas as pd
import pytest

from src.analytics import (
    calculate_metrics,
    category_monthly_metrics,
    grouped_metrics,
    monthly_metrics,
)
from src.generate_data import generate_dataset


def test_completion_rate_excludes_rejected_requests():
    frame = pd.DataFrame(
        {
            "request_id": ["1", "2", "3", "4"],
            "status": ["Completed", "Pending", "In Progress", "Rejected"],
            "resolution_days": [2, None, None, None],
        }
    )
    metrics = calculate_metrics(frame)
    assert metrics["eligible_requests"] == 3
    assert metrics["completion_rate_pct"] == pytest.approx(100 / 3)
    assert metrics["average_resolution_days"] == 2


def test_completion_rate_handles_zero_eligible_requests():
    frame = pd.DataFrame(
        {
            "request_id": ["1"],
            "status": ["Rejected"],
            "resolution_days": [None],
        }
    )
    metrics = calculate_metrics(frame)
    assert metrics["completion_rate_pct"] is None
    assert metrics["average_resolution_days"] is None


def test_grouped_and_monthly_metrics_have_expected_shapes():
    frame = generate_dataset(row_count=300)
    district = grouped_metrics(frame, "district")
    monthly = monthly_metrics(frame)
    assert len(district) == frame["district"].nunique()
    assert district["total_requests"].sum() == len(frame)
    assert len(monthly) > 1
    assert monthly["mom_change_pct"].iloc[0] != monthly["mom_change_pct"].iloc[0]
    category_monthly = category_monthly_metrics(frame)
    assert category_monthly["total_requests"].sum() == len(frame)
    assert {"month", "service_category", "total_requests"} <= set(category_monthly.columns)
