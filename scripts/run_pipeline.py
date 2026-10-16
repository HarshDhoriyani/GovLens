"""Run the end-to-end GovLens demonstration pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.config import (
    PROJECT_ROOT as CONFIGURED_ROOT,
    PROCESSED_DIR,
    RAW_DATA_PATH,
    REPORTS_DIR,
)
from src.analytics import calculate_metrics, create_visualizations
from src.clean_data import clean_dataset
from src.database import create_database, execute_analysis_queries
from src.export_data import export_outputs
from src.load_data import load_or_generate_raw_data


def run_pipeline() -> None:
    """Run generation/loading, validation, analysis, persistence, and exports."""
    raw = load_or_generate_raw_data(RAW_DATA_PATH)
    cleaned, profile = clean_dataset(raw)
    if cleaned.empty:
        raise ValueError("Cleaning removed every input row; refusing to publish empty outputs.")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    database_path = PROCESSED_DIR / "govlens.sqlite"
    create_database(cleaned, database_path, CONFIGURED_ROOT / "sql" / "schema.sql")
    sql_results = execute_analysis_queries(
        database_path, CONFIGURED_ROOT / "sql" / "analysis_queries.sql"
    )

    python_total = len(cleaned)
    sql_total = int(sql_results["total_requests"].iloc[0]["total_requests"])
    python_districts = cleaned.groupby("district")["request_id"].count().sort_index()
    sql_districts = (
        sql_results["request_counts_by_district"]
        .set_index("district")["total_requests"]
        .sort_index()
    )
    if python_total != sql_total or not python_districts.equals(sql_districts):
        raise AssertionError("Python and SQLite total/district request counts disagree.")
    for query_name, result in sql_results.items():
        result.to_csv(PROCESSED_DIR / f"sql_{query_name}.csv", index=False)

    export_outputs(cleaned, profile, PROCESSED_DIR, REPORTS_DIR)
    figures = create_visualizations(cleaned, REPORTS_DIR / "figures")
    metrics = calculate_metrics(cleaned)
    print(f"Raw records: {profile['raw_row_count']:,}")
    print(f"Cleaned records: {len(cleaned):,}")
    print(f"SQLite analytical queries executed: {len(sql_results)}")
    print(f"Completion rate: {metrics['completion_rate_pct']:.2f}%")
    print(f"Average completed resolution: {metrics['average_resolution_days']:.2f} days")
    print(f"Median completed resolution: {metrics['median_resolution_days']:.2f} days")
    print(f"Charts saved: {len(figures)}")
    print(f"SQLite database: {database_path.relative_to(PROJECT_ROOT)}")
    print(f"Python/SQL validation: passed")


if __name__ == "__main__":
    run_pipeline()
