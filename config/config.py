"""Shared project configuration."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RANDOM_SEED = 20261016
SYNTHETIC_RECORD_COUNT = 6_000
ANALYSIS_START = "2024-01-01"
ANALYSIS_END = "2025-12-31"
ALLOWED_STATUSES = ("Completed", "Pending", "In Progress", "Rejected")
ALLOWED_CATEGORIES = (
    "Water Supply",
    "Sanitation",
    "Roads and Infrastructure",
    "Electricity",
    "Public Health",
    "Other Services",
)
CATEGORY_DEPARTMENTS = {
    "Water Supply": "Water Services",
    "Sanitation": "Sanitation Services",
    "Roads and Infrastructure": "Public Works",
    "Electricity": "Energy Services",
    "Public Health": "Health Services",
    "Other Services": "General Services",
}
DISTRICT_STATES = {
    "Aster": "Sample State North",
    "Birch": "Sample State North",
    "Cedar": "Sample State East",
    "Delta": "Sample State East",
    "Elm": "Sample State South",
    "Fern": "Sample State South",
}

RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "service_requests_synthetic.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
