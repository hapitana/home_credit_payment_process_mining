from pathlib import Path

import polars as pl


base_dir = Path(__file__).resolve().parents[1]
processed_dir = base_dir / "data" / "processed"
report_dir = base_dir / "outputs" / "reports"

report_dir.mkdir(parents=True, exist_ok=True)

input_path = processed_dir / "payment_event_log.parquet"
variants_path = report_dir / "payment_trace_variants.csv"
transitions_path = report_dir / "payment_transitions.csv"
report_path = report_dir / "payment_trace_analysis.txt"

if not input_path.exists():
    raise FileNotFoundError(f"Input file not found: {input_path}")

print("Loading payment event log...")

event_log = pl.scan_parquet(input_path)

print("Ordering payment events within each loan...")

ordered_events = (
    event_log
    .sort(
        [
            "case_id",
            "relative_payment_day",
            "installment_number",
            "installment_version",
        ]
    )
    .with_columns(
        pl.col("activity")
        .shift(1)
        .over("case_id")
        .alias("previous_activity")
    )
)

print("Aggregating loan traces...")

traces = (
    ordered_events
    .group_by("case_id")
    .agg(
        pl.col("activity").str.join(" -> ").alias("trace"),
        pl.len().alias("event_count"),
    )
)

variants = (
    traces
    .group_by("trace")
    .agg(
        pl.len().alias("case_count"),
        pl.col("event_count").mean().alias("mean_events_per_case"),
    )
    .sort("case_count", descending=True)
)

print("Writing trace variant summary...")

variants.sink_csv(variants_path)

print("Calculating activity transitions...")

transitions = (
    ordered_events
    .filter(pl.col("previous_activity").is_not_null())
    .group_by(["previous_activity", "activity"])
    .agg(pl.len().alias("transition_count"))
    .sort("transition_count", descending=True)
)

transition_summary = transitions.collect()
transition_summary.write_csv(transitions_path)

print("Calculating overall trace statistics...")

trace_summary = (
    traces
    .select(
        pl.len().alias("total_cases"),
        pl.col("trace").n_unique().alias("unique_trace_variants"),
        pl.col("event_count").mean().alias("mean_events_per_case"),
        pl.col("event_count").median().alias("median_events_per_case"),
    )
    .collect()
    .to_dicts()[0]
)

top_variants = variants.head(20).collect()

report_lines = [
    "PAYMENT TRACE ANALYSIS",
    "======================",
    "",
    f"Total cases: {trace_summary['total_cases']:,}",
    f"Unique trace variants: {trace_summary['unique_trace_variants']:,}",
    f"Mean events per case: {trace_summary['mean_events_per_case']:.2f}",
    f"Median events per case: {trace_summary['median_events_per_case']:.2f}",
    "",
    "TOP 20 TRACE VARIANTS",
    "=====================",
]

for row in top_variants.iter_rows(named=True):
    report_lines.append(
        f"{row['case_count']:,} cases | "
        f"{row['mean_events_per_case']:.2f} mean events | "
        f"{row['trace']}"
    )

report_lines.extend(
    [
        "",
        "TOP ACTIVITY TRANSITIONS",
        "========================",
    ]
)

for row in transition_summary.head(20).iter_rows(named=True):
    report_lines.append(
        f"{row['previous_activity']} -> {row['activity']}: "
        f"{row['transition_count']:,}"
    )

report_lines.extend(
    [
        "",
        "METHODOLOGICAL NOTES",
        "====================",
        (
            "Trace variants are sequences of payment timing categories, "
            "not complete loan application workflows."
        ),
        (
            "Events are ordered by relative payment day, installment "
            "number, and installment version."
        ),
        (
            "The secondary sort fields make ordering reproducible, "
            "but do not establish the true order of events with "
            "identical payment days."
        ),
    ]
)

report_path.write_text(
    "\n".join(report_lines),
    encoding="utf-8",
)

print("\nTrace analysis summary")

for key, value in trace_summary.items():
    if isinstance(value, float):
        print(f"{key}: {value:.2f}")
    else:
        print(f"{key}: {value:,}")

print("\nTop 10 trace variants")
print(top_variants.head(10))

print("\nTop activity transitions")
print(transition_summary.head(10))

print("\nAnalysis completed.")
print(f"Trace variants saved to: {variants_path}")
print(f"Transitions saved to: {transitions_path}")
print(f"Report saved to: {report_path}")