from pathlib import Path

import polars as pl


base_dir = Path(__file__).resolve().parents[1]
report_dir = base_dir / "outputs" / "reports"

input_path = report_dir / "extreme_payment_span_cases.csv"
output_path = report_dir / "extreme_case_characteristics.csv"
report_path = report_dir / "extreme_case_characteristics_report.txt"

if not input_path.exists():
    raise FileNotFoundError(f"Extreme case file not found: {input_path}")

print("Loading extreme loan cases...")

extreme_cases = pl.read_csv(input_path)

characteristics = extreme_cases.select(
    pl.len().alias("cases_reviewed"),
    pl.col("observed_span_days").min().alias("minimum_span_days"),
    pl.col("observed_span_days").median().alias("median_span_days"),
    pl.col("observed_span_days").max().alias("maximum_span_days"),
    pl.col("event_count").mean().alias("mean_events_per_case"),
    pl.col("event_count").median().alias("median_events_per_case"),
    pl.col("event_count").max().alias("maximum_events_per_case"),
    pl.col("activity_type_count").mean().alias("mean_activity_types"),
    pl.col("has_late_payment_event").sum().alias("cases_with_late_events"),
)

extreme_cases.write_csv(output_path)

stats = characteristics.row(0, named=True)

report_lines = [
    "EXTREME CASE CHARACTERISTICS REPORT",
    "===================================",
    "",
    "This report describes the exported cases with the longest observed payment spans.",
    "It does not establish why these cases have long spans.",
    "",
    f"Cases reviewed: {stats['cases_reviewed']:,}",
    f"Minimum observed span: {stats['minimum_span_days']:,.0f} days",
    f"Median observed span: {stats['median_span_days']:,.0f} days",
    f"Maximum observed span: {stats['maximum_span_days']:,.0f} days",
    f"Mean events per case: {stats['mean_events_per_case']:.2f}",
    f"Median events per case: {stats['median_events_per_case']:.2f}",
    f"Maximum events per case: {stats['maximum_events_per_case']:,}",
    f"Mean activity types per case: {stats['mean_activity_types']:.2f}",
    f"Cases with at least one late payment event: {stats['cases_with_late_events']:,}",
    "",
    "The reviewed sample is selected by observed span and is not representative of all loan cases.",
]

report_path.write_text("\n".join(report_lines), encoding="utf-8")

print("\nExtreme case inspection completed.")
print(characteristics)
print(f"Case characteristics saved to: {output_path}")
print(f"Report saved to: {report_path}")