"""Generate deterministic, clearly synthetic service-request records."""

from __future__ import annotations

import numpy as np
import pandas as pd

from config.config import (
    ALLOWED_CATEGORIES,
    CATEGORY_DEPARTMENTS,
    DISTRICT_STATES,
    RANDOM_SEED,
    SYNTHETIC_RECORD_COUNT,
)


def generate_dataset(
    row_count: int = SYNTHETIC_RECORD_COUNT, seed: int = RANDOM_SEED
) -> pd.DataFrame:
    """Return reproducible demonstration data with one row per request."""
    if row_count < 1:
        raise ValueError("row_count must be at least 1")

    rng = np.random.default_rng(seed)
    districts = np.array(list(DISTRICT_STATES))
    district_weights = np.array([0.22, 0.19, 0.17, 0.16, 0.14, 0.12])
    categories = np.array(ALLOWED_CATEGORIES)
    category_weights = np.array([0.23, 0.18, 0.20, 0.16, 0.13, 0.10])
    district_completion = {
        "Aster": 0.57,
        "Birch": 0.62,
        "Cedar": 0.65,
        "Delta": 0.68,
        "Elm": 0.72,
        "Fern": 0.76,
    }
    category_adjustment = {
        "Water Supply": -0.02,
        "Sanitation": -0.01,
        "Roads and Infrastructure": -0.08,
        "Electricity": 0.02,
        "Public Health": 0.04,
        "Other Services": 0.00,
    }

    district_values = rng.choice(districts, size=row_count, p=district_weights)
    category_values = rng.choice(categories, size=row_count, p=category_weights)
    day_offsets = rng.integers(0, 731, size=row_count)
    submission_dates = (
        pd.Timestamp("2024-01-01") + pd.to_timedelta(day_offsets, unit="D")
    )

    statuses: list[str] = []
    resolution_days: list[float | None] = []
    category_resolution_medians = {
        "Water Supply": 6.5,
        "Sanitation": 5.5,
        "Roads and Infrastructure": 13.0,
        "Electricity": 4.5,
        "Public Health": 7.0,
        "Other Services": 6.0,
    }
    for district, category in zip(district_values, category_values, strict=True):
        completed_probability = float(
            np.clip(
                district_completion[district] + category_adjustment[category],
                0.40,
                0.82,
            )
        )
        rejected_probability = 0.07
        in_progress_probability = 0.12
        pending_probability = 1.0 - (
            completed_probability + rejected_probability + in_progress_probability
        )
        status = str(
            rng.choice(
                ("Completed", "Pending", "In Progress", "Rejected"),
                p=(
                    completed_probability,
                    pending_probability,
                    in_progress_probability,
                    rejected_probability,
                ),
            )
        )
        statuses.append(status)
        if status == "Completed":
            days = max(
                0,
                int(
                    round(
                        rng.lognormal(
                            mean=np.log(category_resolution_medians[category]),
                            sigma=0.65,
                        )
                    )
                ),
            )
            resolution_days.append(float(days))
        else:
            resolution_days.append(None)

    frame = pd.DataFrame(
        {
            "request_id": [f"GL-{number:06d}" for number in range(1, row_count + 1)],
            "submission_date": submission_dates.strftime("%Y-%m-%d"),
            "district": district_values,
            "state": [DISTRICT_STATES[district] for district in district_values],
            "service_category": category_values,
            "department": [
                CATEGORY_DEPARTMENTS[category] for category in category_values
            ],
            "status": statuses,
            "resolution_days": resolution_days,
            "source_type": "Synthetic",
        }
    )
    return frame
