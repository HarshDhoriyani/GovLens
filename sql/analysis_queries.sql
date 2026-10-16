-- Query: total_requests | Count all cleaned requests.
SELECT COUNT(*) AS total_requests
FROM fact_service_request;

-- Query: request_counts_by_category | Count requests by service category.
SELECT c.service_category, COUNT(*) AS total_requests
FROM fact_service_request AS f
JOIN dim_service_category AS c USING (category_id)
GROUP BY c.service_category
ORDER BY total_requests DESC, c.service_category;

-- Query: request_counts_by_district | Count requests by district and state.
SELECT d.district, d.state, COUNT(*) AS total_requests
FROM fact_service_request AS f
JOIN dim_district AS d USING (district_id)
GROUP BY d.district, d.state
ORDER BY total_requests DESC, d.district;

-- Query: status_distribution | Count requests by recorded status.
SELECT status, COUNT(*) AS total_requests
FROM fact_service_request
GROUP BY status
ORDER BY total_requests DESC, status;

-- Query: completion_by_district | Completed / (completed + pending + in progress); rejected excluded.
SELECT
    d.district,
    COUNT(*) AS total_requests,
    SUM(CASE WHEN f.status = 'Completed' THEN 1 ELSE 0 END) AS completed_requests,
    SUM(CASE WHEN f.status IN ('Completed', 'Pending', 'In Progress') THEN 1 ELSE 0 END)
        AS eligible_requests,
    ROUND(
        100.0 * SUM(CASE WHEN f.status = 'Completed' THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN f.status IN ('Completed', 'Pending', 'In Progress') THEN 1 ELSE 0 END), 0),
        2
    ) AS completion_rate_pct
FROM fact_service_request AS f
JOIN dim_district AS d USING (district_id)
GROUP BY d.district
ORDER BY completion_rate_pct DESC, d.district;

-- Query: completion_by_category | Completion rate by category with rejected requests excluded.
SELECT
    c.service_category,
    SUM(CASE WHEN f.status = 'Completed' THEN 1 ELSE 0 END) AS completed_requests,
    SUM(CASE WHEN f.status IN ('Completed', 'Pending', 'In Progress') THEN 1 ELSE 0 END)
        AS eligible_requests,
    ROUND(
        100.0 * SUM(CASE WHEN f.status = 'Completed' THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN f.status IN ('Completed', 'Pending', 'In Progress') THEN 1 ELSE 0 END), 0),
        2
    ) AS completion_rate_pct
FROM fact_service_request AS f
JOIN dim_service_category AS c USING (category_id)
GROUP BY c.service_category
ORDER BY completion_rate_pct DESC, c.service_category;

-- Query: monthly_request_trends | Monthly volume and completed count.
SELECT
    d.month_start AS month,
    COUNT(*) AS total_requests,
    SUM(CASE WHEN f.status = 'Completed' THEN 1 ELSE 0 END) AS completed_requests
FROM fact_service_request AS f
JOIN dim_date AS d ON f.date_key = d.date_key
GROUP BY d.month_start
ORDER BY month;

-- Query: pending_by_department | Pending requests grouped by responsible department.
SELECT c.department, COUNT(*) AS pending_requests
FROM fact_service_request AS f
JOIN dim_service_category AS c USING (category_id)
WHERE f.status = 'Pending'
GROUP BY c.department
HAVING COUNT(*) > 0
ORDER BY pending_requests DESC, c.department;

-- Query: districts_ranked_by_volume | Rank districts by request volume.
WITH district_volume AS (
    SELECT d.district, COUNT(*) AS total_requests
    FROM fact_service_request AS f
    JOIN dim_district AS d USING (district_id)
    GROUP BY d.district
)
SELECT
    district,
    total_requests,
    RANK() OVER (ORDER BY total_requests DESC) AS volume_rank
FROM district_volume
ORDER BY volume_rank, district;

-- Query: unresolved_backlog_by_category | Pending plus in-progress cases, excluding rejected requests.
SELECT c.service_category, COUNT(*) AS unresolved_requests
FROM fact_service_request AS f
JOIN dim_service_category AS c USING (category_id)
WHERE f.status IN ('Pending', 'In Progress')
GROUP BY c.service_category
ORDER BY unresolved_requests DESC, c.service_category;

-- Query: resolution_time_summary | Average and median valid resolution time for completed cases.
WITH ranked_resolution AS (
    SELECT
        resolution_days,
        ROW_NUMBER() OVER (ORDER BY resolution_days) AS row_number,
        COUNT(*) OVER () AS row_count
    FROM fact_service_request
    WHERE status = 'Completed' AND resolution_days IS NOT NULL
),
median_resolution AS (
    SELECT AVG(resolution_days) AS median_resolution_days
    FROM ranked_resolution
    WHERE row_number IN ((row_count + 1) / 2, (row_count + 2) / 2)
)
SELECT
    AVG(f.resolution_days) AS average_resolution_days,
    (SELECT median_resolution_days FROM median_resolution) AS median_resolution_days,
    COUNT(f.resolution_days) AS completed_with_valid_resolution
FROM fact_service_request AS f
WHERE f.status = 'Completed';

-- Query: monthly_volume_change | Month-over-month volume difference and percentage using LAG.
WITH monthly AS (
    SELECT d.month_start AS month, COUNT(*) AS total_requests
    FROM fact_service_request AS f
    JOIN dim_date AS d ON f.date_key = d.date_key
    GROUP BY d.month_start
),
with_previous AS (
    SELECT
        month,
        total_requests,
        LAG(total_requests) OVER (ORDER BY month) AS previous_month_requests
    FROM monthly
)
SELECT
    month,
    total_requests,
    previous_month_requests,
    total_requests - previous_month_requests AS month_over_month_change,
    ROUND(
        100.0 * (total_requests - previous_month_requests)
        / NULLIF(previous_month_requests, 0),
        2
    ) AS month_over_month_change_pct
FROM with_previous
ORDER BY month;

-- Query: high_volume_low_completion_districts | Flag districts with at least 600 requests and below 65% completion.
SELECT
    d.district,
    COUNT(*) AS total_requests,
    ROUND(
        100.0 * SUM(CASE WHEN f.status = 'Completed' THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN f.status IN ('Completed', 'Pending', 'In Progress') THEN 1 ELSE 0 END), 0),
        2
    ) AS completion_rate_pct
FROM fact_service_request AS f
JOIN dim_district AS d USING (district_id)
GROUP BY d.district
HAVING COUNT(*) >= 600 AND completion_rate_pct < 65
ORDER BY total_requests DESC;

-- Query: monthly_category_trends | Monthly volume by service category.
SELECT
    d.month_start AS month,
    c.service_category,
    COUNT(*) AS total_requests
FROM fact_service_request AS f
JOIN dim_date AS d ON f.date_key = d.date_key
JOIN dim_service_category AS c USING (category_id)
GROUP BY d.month_start, c.service_category
ORDER BY month, c.service_category;
