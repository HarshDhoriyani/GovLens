"""SQLite persistence and execution of the documented analytical queries."""

from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd


def create_database(
    frame: pd.DataFrame, database_path: Path, schema_path: Path
) -> None:
    """Build the star-schema SQLite database using parameterized inserts."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()

    districts = frame[["district", "state"]].drop_duplicates().sort_values("district")
    categories = (
        frame[["service_category", "department"]]
        .drop_duplicates()
        .sort_values("service_category")
    )
    dates = pd.to_datetime(frame["submission_date"]).drop_duplicates().sort_values()

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        district_ids = {
            name: index for index, name in enumerate(districts["district"], start=1)
        }
        category_ids = {
            name: index for index, name in enumerate(categories["service_category"], start=1)
        }
        connection.executemany(
            "INSERT INTO dim_district (district_id, district, state) VALUES (?, ?, ?)",
            [
                (district_ids[row.district], row.district, row.state)
                for row in districts.itertuples(index=False)
            ],
        )
        connection.executemany(
            "INSERT INTO dim_service_category (category_id, service_category, department) "
            "VALUES (?, ?, ?)",
            [
                (
                    category_ids[row.service_category],
                    row.service_category,
                    row.department,
                )
                for row in categories.itertuples(index=False)
            ],
        )
        connection.executemany(
            "INSERT INTO dim_date (date_key, year, month, month_start) VALUES (?, ?, ?, ?)",
            [
                (
                    value.strftime("%Y-%m-%d"),
                    value.year,
                    value.month,
                    value.strftime("%Y-%m-01"),
                )
                for value in dates
            ],
        )
        connection.executemany(
            """
            INSERT INTO fact_service_request (
                request_id, date_key, district_id, category_id, status,
                resolution_days, source_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row.request_id,
                    row.submission_date,
                    district_ids[row.district],
                    category_ids[row.service_category],
                    row.status,
                    None if pd.isna(row.resolution_days) else float(row.resolution_days),
                    row.source_type,
                )
                for row in frame.itertuples(index=False)
            ],
        )
        connection.commit()


def load_analysis_queries(query_path: Path) -> dict[str, str]:
    """Read named SELECT statements from analysis_queries.sql."""
    content = query_path.read_text(encoding="utf-8")
    sections = re.split(r"(?m)^-- Query:\s*([a-z0-9_]+)\s*\|.*$", content)
    queries = {
        sections[index]: sections[index + 1].strip().rstrip(";").strip()
        for index in range(1, len(sections), 2)
    }
    if not queries:
        raise ValueError(f"No named queries found in {query_path}")
    return queries


def execute_analysis_queries(
    database_path: Path, query_path: Path
) -> dict[str, pd.DataFrame]:
    """Execute every named analytical query and return its result frame."""
    queries = load_analysis_queries(query_path)
    with closing(sqlite3.connect(database_path)) as connection:
        return {
            name: pd.read_sql_query(query, connection)
            for name, query in queries.items()
        }
