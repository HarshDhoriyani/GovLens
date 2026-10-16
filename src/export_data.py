"""Export model-ready CSVs, quality reports, and computed findings."""

from pathlib import Path

import pandas as pd

from src.analytics import (
    calculate_metrics,
    category_monthly_metrics,
    grouped_metrics,
    monthly_metrics,
    render_findings,
)
from src.data_quality import render_quality_report


def export_outputs(
    cleaned: pd.DataFrame,
    profile: dict[str, object],
    processed_directory: Path,
    reports_directory: Path,
) -> None:
    """Write flat detail and aggregate CSVs used by Power BI and analysis."""
    processed_directory.mkdir(parents=True, exist_ok=True)
    reports_directory.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(processed_directory / "service_requests.csv", index=False)
    grouped_metrics(cleaned, "district").to_csv(
        processed_directory / "district_performance.csv", index=False
    )
    grouped_metrics(cleaned, "service_category").to_csv(
        processed_directory / "category_performance.csv", index=False
    )
    monthly_metrics(cleaned).to_csv(
        processed_directory / "monthly_trends.csv", index=False
    )
    category_monthly_metrics(cleaned).to_csv(
        processed_directory / "category_monthly_trends.csv", index=False
    )
    pd.DataFrame(
        [{"metric": key, "value": value} for key, value in calculate_metrics(cleaned).items()]
    ).to_csv(processed_directory / "overall_metrics.csv", index=False)
    pd.DataFrame(
        [
            {"column": name, "missing_values": count}
            for name, count in profile["missing_values_by_column"].items()
        ]
    ).to_csv(processed_directory / "data_quality_summary.csv", index=False)
    (reports_directory / "data_quality_report.md").write_text(
        render_quality_report(profile, cleaned), encoding="utf-8"
    )
    (reports_directory / "findings.md").write_text(
        render_findings(cleaned), encoding="utf-8"
    )
