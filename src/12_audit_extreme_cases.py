from pathlib import Path

import polars as pl


base_dir = Path(__file__).resolve().parents[1]
report_dir = base_dir / "outputs" / "reports"

input_path = report_dir / "payment_case_duration_summary.csv"
output_path = report_dir / "extreme_payment_span_cases.csv"
report_path = report_dir / "extreme_payment_span_audit.txt"

if not input_path.exists():
    raise FileNotFoundError(f"Case summary not found: {input_path}")

print("Loading loan case summary...")

case_summary = pl.read_csv(input_path)

span_stats = case_summary.select(
    pl.len().alias("total_cases"),
    pl.col("observed_span_days").min().alias("minimum_span_days"),
    pl.col("observed_span_days").quantile(0.50).alias("median_span_days"),
    pl.col("observed_span_days").quantile(0.75).alias("p75_span_days"),
    pl.col("observed_span_days").quantile(0.90).alias("p90_span_days"),
    pl.col("observed_span_days").quantile(0.95).alias("p95_span_days"),
    pl.col("observed_span_days").quantile(0.99).alias("p99_span_days"),
    pl.col("observed_span_days").max().alias("maximum_span_days"),
)

stats = span_stats.row(0, named=True)
p99 = stats["p99_span_days"]

cases_at_or_above_p99 = case_summary.filter(
    pl.col("observed_span_days") >= p99
)

extreme_cases = (
    cases_at_or_above_p99
    .sort("observed_span_days", descending=True)
    .head(100)
)

extreme_cases.write_csv(output_path)

report_lines = [
    "EXTREME PAYMENT SPAN AUDIT",
    "==========================",
    "",
    "Observed spans represent the difference between the first and last recorded payment days within a loan case.",
    "They are not confirmed loan tenures or actual calendar durations.",
    "",
    f"Total cases: {stats['total_cases']:,}",
    f"Minimum observed span: {stats['minimum_span_days']:,.0f} days",
    f"Median observed span: {stats['median_span_days']:,.0f} days",
    f"75th percentile: {stats['p75_span_days']:,.0f} days",
    f"90th percentile: {stats['p90_span_days']:,.0f} days",
    f"95th percentile: {stats['p95_span_days']:,.0f} days",
    f"99th percentile threshold: {p99:,.0f} days",
    f"Cases at or above the 99th percentile threshold: {cases_at_or_above_p99.height:,}",
    f"Extreme cases exported for review: {extreme_cases.height:,}",
    "",
    "The exported CSV contains up to 100 cases with the longest observed spans.",
]

report_path.write_text("\n".join(report_lines), encoding="utf-8")

print("\nExtreme span audit completed.")
print(span_stats.with_columns(pl.all().exclude("total_cases").round(2)))
print(f"Cases at or above the P99 threshold: {cases_at_or_above_p99.height:,}")
print(f"Extreme cases exported: {extreme_cases.height:,}")
print(f"Extreme cases saved to: {output_path}")
print(f"Audit report saved to: {report_path}")