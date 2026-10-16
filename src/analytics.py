"""Pandas analysis and reproducible chart generation."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid", palette="deep")


def calculate_metrics(frame: pd.DataFrame) -> dict[str, float | int | None]:
    """Calculate portfolio metrics; completion excludes rejected requests."""
    counts = frame["status"].value_counts()
    eligible = int(frame["status"].isin(("Completed", "Pending", "In Progress")).sum())
    completed = int(counts.get("Completed", 0))
    resolved_days = frame.loc[
        frame["status"].eq("Completed"), "resolution_days"
    ].dropna()
    return {
        "total_requests": int(len(frame)),
        "completed_requests": completed,
        "pending_requests": int(counts.get("Pending", 0)),
        "in_progress_requests": int(counts.get("In Progress", 0)),
        "rejected_requests": int(counts.get("Rejected", 0)),
        "eligible_requests": eligible,
        "completion_rate_pct": (completed / eligible * 100) if eligible else None,
        "average_resolution_days": (
            float(resolved_days.mean()) if not resolved_days.empty else None
        ),
        "median_resolution_days": (
            float(resolved_days.median()) if not resolved_days.empty else None
        ),
    }


def grouped_metrics(frame: pd.DataFrame, group_column: str) -> pd.DataFrame:
    """Return volume, completion, pending, and unresolved counts by group."""
    groups = frame.groupby(group_column, dropna=False)
    result = groups.agg(
        total_requests=("request_id", "count"),
        completed_requests=("status", lambda values: values.eq("Completed").sum()),
        pending_requests=("status", lambda values: values.eq("Pending").sum()),
        in_progress_requests=("status", lambda values: values.eq("In Progress").sum()),
        rejected_requests=("status", lambda values: values.eq("Rejected").sum()),
    )
    result["eligible_requests"] = (
        result["completed_requests"]
        + result["pending_requests"]
        + result["in_progress_requests"]
    )
    result["completion_rate_pct"] = np.where(
        result["eligible_requests"].gt(0),
        result["completed_requests"] / result["eligible_requests"] * 100,
        np.nan,
    )
    result["unresolved_requests"] = (
        result["pending_requests"] + result["in_progress_requests"]
    )
    return result.reset_index().sort_values("total_requests", ascending=False)


def monthly_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    """Calculate monthly volume and month-over-month percentage change."""
    monthly = (
        frame.assign(month=pd.to_datetime(frame["submission_date"]).dt.to_period("M").astype(str))
        .groupby("month", as_index=False)
        .agg(total_requests=("request_id", "count"))
        .sort_values("month")
    )
    monthly["mom_change_pct"] = monthly["total_requests"].pct_change(fill_method=None) * 100
    return monthly


def category_monthly_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    """Return request volume by month and service category."""
    return (
        frame.assign(
            month=pd.to_datetime(frame["submission_date"])
            .dt.to_period("M")
            .astype(str)
        )
        .groupby(["month", "service_category"], as_index=False)
        .agg(total_requests=("request_id", "count"))
        .sort_values(["month", "service_category"])
    )


def create_visualizations(
    frame: pd.DataFrame, output_directory: Path
) -> list[Path]:
    """Save the six requested EDA charts and return their paths."""
    output_directory.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    def save_figure(name: str) -> None:
        path = output_directory / name
        plt.tight_layout()
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        paths.append(path)

    monthly = monthly_metrics(frame)
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=monthly, x="month", y="total_requests", marker="o")
    plt.title("Monthly Service Request Volume")
    plt.xlabel("Submission month")
    plt.ylabel("Requests")
    plt.xticks(rotation=45, ha="right")
    save_figure("monthly_request_volume.png")

    category_counts = frame["service_category"].value_counts().sort_values()
    plt.figure(figsize=(9, 5))
    category_counts.plot(kind="barh", color=sns.color_palette("deep", len(category_counts)))
    plt.title("Service Requests by Category")
    plt.xlabel("Requests")
    plt.ylabel("")
    save_figure("requests_by_category.png")

    status_counts = frame["status"].value_counts()
    plt.figure(figsize=(7, 5))
    plt.pie(
        status_counts.values,
        labels=status_counts.index,
        autopct="%1.1f%%",
        startangle=90,
        colors=sns.color_palette("deep", len(status_counts)),
    )
    plt.title("Service Request Status Distribution")
    save_figure("status_distribution.png")

    district_rates = grouped_metrics(frame, "district").sort_values("completion_rate_pct")
    plt.figure(figsize=(9, 5))
    sns.barplot(
        data=district_rates,
        x="completion_rate_pct",
        y="district",
        color="#4472C4",
    )
    plt.title("Eligible-Request Completion Rate by District")
    plt.xlabel("Completion rate (%)")
    plt.ylabel("District")
    plt.xlim(0, 100)
    save_figure("district_completion_rate.png")

    category_backlog = (
        frame.loc[frame["status"].isin(("Pending", "In Progress"))]
        .groupby("service_category")
        .size()
        .sort_values()
    )
    plt.figure(figsize=(9, 5))
    category_backlog.plot(
        kind="barh", color=sns.color_palette("deep", max(1, len(category_backlog)))
    )
    plt.title("Unresolved Requests by Service Category")
    plt.xlabel("Pending + in-progress requests")
    plt.ylabel("")
    save_figure("unresolved_by_category.png")

    resolution = frame.loc[
        frame["status"].eq("Completed") & frame["resolution_days"].notna(),
        "resolution_days",
    ]
    plt.figure(figsize=(9, 5))
    sns.histplot(resolution, bins=30, kde=True, color="#4472C4")
    plt.title("Resolution-Time Distribution for Completed Requests")
    plt.xlabel("Resolution days")
    plt.ylabel("Completed requests")
    save_figure("resolution_time_distribution.png")
    return paths


def render_findings(frame: pd.DataFrame) -> str:
    """Build evidence-led findings directly from computed synthetic metrics."""
    metrics = calculate_metrics(frame)
    districts = grouped_metrics(frame, "district")
    categories = grouped_metrics(frame, "service_category")
    monthly = monthly_metrics(frame)
    highest_volume = districts.iloc[0]
    lowest_rate = districts.sort_values("completion_rate_pct").iloc[0]
    highest_rate = districts.sort_values("completion_rate_pct").iloc[-1]
    largest_backlog = categories.sort_values("unresolved_requests").iloc[-1]
    largest_category = categories.iloc[0]
    most_recent = monthly.iloc[-1]
    previous = monthly.iloc[-2]
    trend = (
        "higher" if most_recent["total_requests"] > previous["total_requests"] else "lower"
    )
    lines = [
        "# Demonstration Findings",
        "",
        "> **Synthetic data only.** These descriptive observations apply only to this generated demonstration dataset; "
        "they are not evidence about real districts, public agencies, or government performance.",
        "",
        "## Observations",
        "",
        f"1. The dataset contains **{metrics['total_requests']:,}** requests; "
        f"{metrics['completed_requests']:,} completed, {metrics['pending_requests']:,} pending, "
        f"{metrics['in_progress_requests']:,} in progress, and {metrics['rejected_requests']:,} rejected.",
        f"2. Completion rate is **{metrics['completion_rate_pct']:.1f}%** "
        "(completed divided by completed + pending + in-progress; rejected cases are excluded).",
        f"3. **{highest_volume['district']}** has the most requests ({int(highest_volume['total_requests']):,}); "
        f"**{lowest_rate['district']}** has the lowest completion rate "
        f"({lowest_rate['completion_rate_pct']:.1f}%) and **{highest_rate['district']}** the highest "
        f"({highest_rate['completion_rate_pct']:.1f}%).",
        f"4. **{largest_category['service_category']}** has the highest volume "
        f"({int(largest_category['total_requests']):,}); **{largest_backlog['service_category']}** has the largest "
        f"pending + in-progress backlog ({int(largest_backlog['unresolved_requests']):,}).",
        f"5. In the final two months, volume was {trend}: {int(previous['total_requests']):,} in "
        f"{previous['month']} and {int(most_recent['total_requests']):,} in {most_recent['month']}. "
        f"Completed requests with valid resolution times averaged {metrics['average_resolution_days']:.1f} days "
        f"(median {metrics['median_resolution_days']:.1f} days).",
        "",
        "## Follow-up questions, not causal conclusions",
        "",
        "- Investigate the synthetic lower-rate and high-backlog segments by request age, staffing, and service complexity "
        "before proposing operational changes.",
        "- Check whether category-specific resolution-time differences persist after accounting for case mix and "
        "submission month.",
        "- Review long-pending cases and define service-level targets before interpreting backlogs as delays.",
        "- No intervention was tested; the observed patterns are descriptive and do not establish causes.",
        "",
    ]
    return "\n".join(lines)
