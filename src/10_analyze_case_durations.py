from pathlib import Path

import polars as pl


base_dir = Path(__file__).resolve().parents[1]
data_path = base_dir / "data" / "processed" / "payment_event_log.parquet"
report_dir = base_dir / "outputs" / "reports"

case_summary_path = report_dir / "payment_case_duration_summary.csv"
report_path = report_dir / "payment_case_duration_report.txt"

if not data_path.exists():
    raise FileNotFoundError(f"Event log not found: {data_path}")

report_dir.mkdir(parents=True, exist_ok=True)

print("Loading the payment event log...")

events = pl.scan_parquet(data_path)

case_summary = (
    events
    .group_by("case_id")
    .agg(
        pl.len().alias("event_count"),
        pl.col("customer_id").n_unique().alias("customer_count"),
        pl.col("relative_payment_day").min().alias("first_payment_day"),
        pl.col("relative_payment_day").max().alias("last_payment_day"),
        pl.col("payment_delay_days").max().alias("maximum_delay_days"),
        pl.col("payment_delay_days").mean().alias("mean_delay_days"),
        pl.col("payment_delay_days")
        .filter(pl.col("payment_delay_days") > 0)
        .len()
        .alias("late_event_count"),
        pl.col("activity").n_unique().alias("activity_type_count"),
    )
    .with_columns(
        (
            pl.col("last_payment_day") - pl.col("first_payment_day")
        ).alias("observed_span_days"),
        (
            pl.col("maximum_delay_days") > 0
        ).alias("has_late_payment_event"),
    )
    .sort("case_id")
    .collect()
)

case_summary.write_csv(case_summary_path)

total_cases = case_summary.height

report_lines = [
    "PAYMENT CASE DURATION AND PATTERN REPORT",
    "========================================",
    "",
    "The observed span is the difference between the first and last recorded payment days within each loan case.",
    "Payment days are relative day values, not actual calendar dates.",
    "A late payment event is a recorded event with payment_delay_days greater than zero.",
    "",
    f"Total loan cases: {total_cases:,}",
    f"Mean events per case: {case_summary['event_count'].mean():.2f}",
    f"Median events per case: {case_summary['event_count'].median():.2f}",
    f"Maximum events in a case: {case_summary['event_count'].max():,}",
    f"Mean observed span in days: {case_summary['observed_span_days'].mean():.2f}",
    f"Median observed span in days: {case_summary['observed_span_days'].median():.2f}",
    f"Maximum observed span in days: {case_summary['observed_span_days'].max():,.0f}",
    f"Cases with at least one late payment event: {case_summary['has_late_payment_event'].sum():,}",
    f"Cases with multiple activity types: {(case_summary['activity_type_count'] > 1).sum():,}",
    f"Cases linked to more than one customer: {(case_summary['customer_count'] > 1).sum():,}",
    "",
    "Event-count distribution:",
]

for row in (
    case_summary
    .select(
        pl.when(pl.col("event_count") == 1)
        .then(pl.lit("1 event"))
        .when(pl.col("event_count") <= 5)
        .then(pl.lit("2-5 events"))
        .when(pl.col("event_count") <= 10)
        .then(pl.lit("6-10 events"))
        .when(pl.col("event_count") <= 20)
        .then(pl.lit("11-20 events"))
        .otherwise(pl.lit("More than 20 events"))
        .alias("event_group")
    )
    .group_by("event_group")
    .len()
    .sort("event_group")
    .iter_rows(named=True)
):
    report_lines.append(
        f"  {row['event_group']}: {row['len']:,} cases"
    )

report_path.write_text("\n".join(report_lines), encoding="utf-8")

print("\nCase duration analysis completed.")
print(f"Total loan cases: {total_cases:,}")
print(f"Mean observed span: {case_summary['observed_span_days'].mean():.2f} days")
print(f"Cases with late payment events: {case_summary['has_late_payment_event'].sum():,}")
print(f"Case summary saved to: {case_summary_path}")
print(f"Report saved to: {report_path}")