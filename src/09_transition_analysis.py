from pathlib import Path

import polars as pl


base_dir = Path(__file__).resolve().parents[1]
report_dir = base_dir / "outputs" / "reports"

input_path = report_dir / "payment_transitions.csv"
output_path = report_dir / "payment_transition_probabilities.csv"
report_path = report_dir / "payment_transition_probability_report.txt"

if not input_path.exists():
    raise FileNotFoundError(f"Input file not found: {input_path}")

print("Loading existing transition counts...")

transitions = pl.read_csv(input_path)

transitions = (
    transitions
    .with_columns(
        pl.col("transition_count").cast(pl.Int64)
    )
    .with_columns(
        pl.col("transition_count")
        .sum()
        .over("previous_activity")
        .alias("outgoing_transition_count")
    )
    .with_columns(
        (
            pl.col("transition_count")
            / pl.col("outgoing_transition_count")
            * 100
        ).alias("transition_percentage")
    )
    .sort(
        ["previous_activity", "transition_count"],
        descending=[False, True],
    )
)

transitions.write_csv(output_path)

report_lines = [
    "PAYMENT TRANSITION PROBABILITY REPORT",
    "=====================================",
    "",
    (
        "Percentages describe the distribution of observed next "
        "payment categories, conditional on the previous category."
    ),
    "",
]

for previous_activity in [
    "Early Payment",
    "On-time Payment",
    "Late Payment",
]:
    subset = transitions.filter(
        pl.col("previous_activity") == previous_activity
    )

    if subset.is_empty():
        continue

    total_count = subset["outgoing_transition_count"][0]

    report_lines.append(
        f"Previous activity: {previous_activity}"
    )
    report_lines.append(
        f"Observed outgoing transitions: {total_count:,}"
    )

    for row in subset.iter_rows(named=True):
        report_lines.append(
            f"  Next activity: {row['activity']} | "
            f"Count: {row['transition_count']:,} | "
            f"Percentage: {row['transition_percentage']:.2f}%"
        )

    report_lines.append("")

report_path.write_text(
    "\n".join(report_lines),
    encoding="utf-8",
)

print("\nTransition probabilities")

print(
    transitions.select(
        "previous_activity",
        "activity",
        "transition_count",
        "transition_percentage",
    )
)

print("\nAnalysis completed.")
print(f"Results saved to: {output_path}")
print(f"Report saved to: {report_path}")