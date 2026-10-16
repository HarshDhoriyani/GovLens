import sqlite3

from src.analytics import calculate_metrics
from src.clean_data import clean_dataset
from src.database import execute_analysis_queries, load_analysis_queries, create_database
from src.generate_data import generate_dataset


def test_database_creation_all_queries_and_python_agreement(tmp_path):
    cleaned, _ = clean_dataset(generate_dataset(row_count=350, seed=22))
    database_path = tmp_path / "govlens.sqlite"
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    create_database(cleaned, database_path, root / "sql" / "schema.sql")
    results = execute_analysis_queries(
        database_path, root / "sql" / "analysis_queries.sql"
    )
    assert len(load_analysis_queries(root / "sql" / "analysis_queries.sql")) == 14
    assert int(results["total_requests"].iloc[0]["total_requests"]) == len(cleaned)
    assert results["request_counts_by_district"]["total_requests"].sum() == len(cleaned)
    assert abs(
        results["resolution_time_summary"].iloc[0]["average_resolution_days"]
        - calculate_metrics(cleaned)["average_resolution_days"]
    ) < 1e-9

    with sqlite3.connect(database_path) as connection:
        foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
        assert not foreign_key_errors


def test_database_can_be_rebuilt_at_same_path(tmp_path):
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    database_path = tmp_path / "govlens.sqlite"
    cleaned, _ = clean_dataset(generate_dataset(row_count=25, seed=4))
    create_database(cleaned, database_path, root / "sql" / "schema.sql")
    create_database(cleaned, database_path, root / "sql" / "schema.sql")
    results = execute_analysis_queries(
        database_path, root / "sql" / "analysis_queries.sql"
    )
    assert int(results["total_requests"].iloc[0]["total_requests"]) == 25


def test_complete_pipeline_rerun_reuses_raw_input(tmp_path, monkeypatch):
    from pathlib import Path

    from scripts import run_pipeline

    project_root = Path(__file__).resolve().parents[1]
    raw_path = tmp_path / "data" / "raw" / "service_requests_synthetic.csv"
    processed_path = tmp_path / "data" / "processed"
    reports_path = tmp_path / "reports"
    monkeypatch.setattr(run_pipeline, "RAW_DATA_PATH", raw_path)
    monkeypatch.setattr(run_pipeline, "PROCESSED_DIR", processed_path)
    monkeypatch.setattr(run_pipeline, "REPORTS_DIR", reports_path)
    monkeypatch.setattr(run_pipeline, "CONFIGURED_ROOT", project_root)
    monkeypatch.setattr(run_pipeline, "PROJECT_ROOT", tmp_path)

    run_pipeline.run_pipeline()
    first_raw = raw_path.read_bytes()
    run_pipeline.run_pipeline()

    assert raw_path.read_bytes() == first_raw
    assert (processed_path / "govlens.sqlite").is_file()
    assert (processed_path / "category_monthly_trends.csv").is_file()
    assert (reports_path / "findings.md").is_file()
