PRAGMA foreign_keys = ON;

CREATE TABLE dim_district (
    district_id INTEGER PRIMARY KEY,
    district TEXT NOT NULL UNIQUE,
    state TEXT NOT NULL
);

CREATE TABLE dim_service_category (
    category_id INTEGER PRIMARY KEY,
    service_category TEXT NOT NULL UNIQUE,
    department TEXT NOT NULL
);

CREATE TABLE dim_date (
    date_key TEXT PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    month_start TEXT NOT NULL
);

CREATE TABLE fact_service_request (
    request_id TEXT PRIMARY KEY,
    date_key TEXT NOT NULL REFERENCES dim_date(date_key),
    district_id INTEGER NOT NULL REFERENCES dim_district(district_id),
    category_id INTEGER NOT NULL REFERENCES dim_service_category(category_id),
    status TEXT NOT NULL CHECK (
        status IN ('Completed', 'Pending', 'In Progress', 'Rejected')
    ),
    resolution_days REAL CHECK (resolution_days IS NULL OR resolution_days >= 0),
    source_type TEXT NOT NULL
);

CREATE INDEX idx_request_date ON fact_service_request(date_key);
CREATE INDEX idx_request_district ON fact_service_request(district_id);
CREATE INDEX idx_request_category ON fact_service_request(category_id);
CREATE INDEX idx_request_status ON fact_service_request(status);
