from pathlib import Path
import re

import polars as pl


base_dir = Path(__file__).resolve().parents[1]
report_dir = base_dir / "outputs" / "reports"
figure_dir = base_dir / "outputs" / "figures"

case_summary_path = report_dir / "payment_case_duration_summary.csv"
transition_path = report_dir / "payment_transition_probabilities.csv"
trace_analysis_path = report_dir / "payment_trace_analysis.txt"
extreme_audit_path = report_dir / "extreme_payment_span_audit.txt"
extreme_characteristics_path = report_dir / "extreme_case_characteristics.csv"

output_path = report_dir / "project_findings.md"

required_files = [
    case_summary_path,
    transition_path,
    trace_analysis_path,
    extreme_audit_path,
    extreme_characteristics_path,
]

missing_files = [path for path in required_files if not path.exists()]

if missing_files:
    missing_list = "\n".join(str(path) for path in missing_files)
    raise FileNotFoundError(
        f"Required analysis outputs are missing:\n{missing_list}"
    )

print("Loading existing analysis outputs...")

case_summary = pl.read_csv(case_summary_path)
transitions = pl.read_csv(transition_path)
extreme_cases = pl.read_csv(extreme_characteristics_path)

case_stats = case_summary.select(
    pl.len().alias("total_cases"),
    pl.col("event_count").sum().alias("total_events"),
    pl.col("event_count").mean().alias("mean_events"),
    pl.col("event_count").median().alias("median_events"),
    pl.col("event_count").max().alias("maximum_events"),
    pl.col("observed_span_days").median().alias("median_span"),
    pl.col("observed_span_days").quantile(0.75).alias("p75_span"),
    pl.col("observed_span_days").quantile(0.90).alias("p90_span"),
    pl.col("observed_span_days").quantile(0.95).alias("p95_span"),
    pl.col("observed_span_days").quantile(0.99).alias("p99_span"),
    pl.col("observed_span_days").max().alias("maximum_span"),
    pl.col("has_late_payment_event").sum().alias("late_cases"),
    (pl.col("activity_type_count") > 1)
    .sum()
    .alias("multiple_activity_cases"),
    (pl.col("customer_count") > 1)
    .sum()
    .alias("multiple_customer_cases"),
)

stats = case_stats.row(0, named=True)

total_cases = stats["total_cases"]
total_events = stats["total_events"]
late_cases = stats["late_cases"]

late_case_percentage = late_cases / total_cases * 100
multiple_activity_percentage = (
    stats["multiple_activity_cases"] / total_cases * 100
)

event_group_order = [
    "1 event",
    "2-5 events",
    "6-10 events",
    "11-20 events",
    "More than 20 events",
]

event_groups = (
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
    .with_columns(
        pl.col("event_group")
        .replace_strict(
            {
                name: index
                for index, name in enumerate(event_group_order)
            }
        )
        .alias("group_order")
    )
    .sort("group_order")
)

event_group_lines = [
    f"| {row['event_group']} | {row['len']:,} |"
    for row in event_groups.iter_rows(named=True)
]

transition_order = [
    "Early Payment",
    "On-time Payment",
    "Late Payment",
]

transition_lines = []

for previous_activity in transition_order:
    subset = (
        transitions
        .filter(pl.col("previous_activity") == previous_activity)
        .sort("transition_count", descending=True)
    )

    if subset.is_empty():
        continue

    transition_lines.extend(
        [
            f"\n### Transitions following {previous_activity}",
            "",
            "| Next activity | Observed transitions | Percentage |",
            "|---|---:|---:|",
        ]
    )

    for row in subset.iter_rows(named=True):
        transition_lines.append(
            f"| {row['activity']} | "
            f"{row['transition_count']:,} | "
            f"{row['transition_percentage']:.2f}% |"
        )

trace_text = trace_analysis_path.read_text(encoding="utf-8").strip()
extreme_audit_text = extreme_audit_path.read_text(
    encoding="utf-8"
).strip()

trace_variant_pattern = re.compile(
    r"^([\d,]+) cases \| ([\d.]+) mean events \| (.+)$"
)

trace_variants = []

in_top_variants = False

for line in trace_text.splitlines():
    stripped_line = line.strip()

    if stripped_line == "TOP 20 TRACE VARIANTS":
        in_top_variants = True
        continue

    if stripped_line == "TOP ACTIVITY TRANSITIONS":
        in_top_variants = False
        continue

    if not in_top_variants:
        continue

    match = trace_variant_pattern.match(stripped_line)

    if match:
        trace_variants.append(
            {
                "cases": int(match.group(1).replace(",", "")),
                "mean_events": float(match.group(2)),
                "trace": match.group(3),
            }
        )

trace_table_lines = [
    "| Cases | Mean events | Payment-category sequence |",
    "|---:|---:|---|",
]

for variant in trace_variants[:10]:
    trace_table_lines.append(
        f"| {variant['cases']:,} | "
        f"{variant['mean_events']:.2f} | "
        f"{variant['trace']} |"
    )

trace_summary = {}

for line in trace_text.splitlines():
    stripped_line = line.strip()

    for label in [
        "Total cases",
        "Unique trace variants",
        "Mean events per case",
        "Median events per case",
    ]:
        prefix = f"{label}:"

        if stripped_line.startswith(prefix):
            trace_summary[label] = stripped_line[len(prefix):].strip()

transition_count_pattern = re.compile(r"^(.+): ([\d,]+)$")
trace_transition_counts = []

in_top_transitions = False

for line in trace_text.splitlines():
    stripped_line = line.strip()

    if stripped_line == "TOP ACTIVITY TRANSITIONS":
        in_top_transitions = True
        continue

    if stripped_line == "METHODOLOGICAL NOTES":
        in_top_transitions = False
        continue

    if not in_top_transitions:
        continue

    match = transition_count_pattern.match(stripped_line)

    if match:
        trace_transition_counts.append(
            (
                match.group(1),
                int(match.group(2).replace(",", "")),
            )
        )

extreme_stats = extreme_cases.select(
    pl.len().alias("cases_reviewed"),
    pl.col("observed_span_days").median().alias("median_extreme_span"),
    pl.col("observed_span_days").max().alias("maximum_extreme_span"),
    pl.col("event_count").median().alias("median_extreme_events"),
    pl.col("event_count").max().alias("maximum_extreme_events"),
    pl.col("has_late_payment_event")
    .cast(pl.Int64)
    .sum()
    .alias("extreme_late_cases"),
).row(0, named=True)

extreme_audit_lines = []

for line in extreme_audit_text.splitlines():
    stripped_line = line.strip()

    if not stripped_line:
        continue

    if set(stripped_line) == {"="}:
        continue

    if stripped_line == "EXTREME PAYMENT SPAN AUDIT":
        continue

    if stripped_line.startswith("The exported CSV contains"):
        extreme_audit_lines.append(stripped_line)
        continue

    if ":" in stripped_line:
        label, value = stripped_line.split(":", 1)
        extreme_audit_lines.append(f"- *{label.strip()}:* {value.strip()}")

findings = [
    "# Home Credit Payment Process Mining",
    "",
    "## 1. Project Overview",
    "",
    "This project examines recorded payment behavior using the Home Credit "
    "dataset. It applies event-log construction, case-level profiling, trace "
    "analysis, transition analysis, and descriptive duration analysis.",
    "",
    "The current scope focuses on payment records from "
    "installments_payments.csv. It does not reconstruct the complete loan "
    "lifecycle from application through approval, disbursement, and closure.",
    "",
    "## 2. Data and Event Log",
    "",
    f"- Loan cases represented in the event log: *{total_cases:,}*",
    f"- Recorded payment events: *{total_events:,}*",
    f"- Mean events per case: *{stats['mean_events']:.2f}*",
    f"- Median events per case: *{stats['median_events']:.0f}*",
    f"- Maximum events in a case: *{stats['maximum_events']:,}*",
    "",
    "The case identifier is SK_ID_PREV, representing a previous loan. "
    "The customer identifier is SK_ID_CURR. Recorded events are categorized "
    "as Early Payment, On-time Payment, or Late Payment using the difference "
    "between payment-entry days and scheduled installment days.",
    "",
    "The event-log timestamp is an artificial date derived from relative "
    "payment days. It preserves event ordering and is not an actual calendar "
    "date.",
    "",
    "## 3. Payment Event Distribution",
    "",
    "| Event-count group | Loan cases |",
    "|---|---:|",
    *event_group_lines,
    "",
    "Event counts should not be interpreted as completed installment counts, "
    "because a single installment can have multiple recorded payment entries.",
    "",
    "## 4. Payment Transition Analysis",
    "",
    "Transition percentages describe the distribution of the next recorded "
    "payment category conditional on the previous recorded category. They are "
    "descriptive transition frequencies, not causal effects or customer-level "
    "default probabilities.",
    "",
    *transition_lines,
    "",
    "## 5. Observed Payment Spans",
    "",
    "| Metric | Result |",
    "|---|---:|",
    f"| Median observed span | {stats['median_span']:,.0f} days |",
    f"| 75th percentile | {stats['p75_span']:,.0f} days |",
    f"| 90th percentile | {stats['p90_span']:,.0f} days |",
    f"| 95th percentile | {stats['p95_span']:,.0f} days |",
    f"| 99th percentile | {stats['p99_span']:,.0f} days |",
    f"| Maximum observed span | {stats['maximum_span']:,.0f} days |",
    "",
    "Observed span is the difference between the first and last recorded "
    "payment days in a case. It is not confirmed loan tenure or the time "
    "between actual loan opening and closure.",
    "",
    "## 6. Late Payment Events",
    "",
    f"- Cases with at least one late payment event: *{late_cases:,}*",
    f"- Share of all cases: *{late_case_percentage:.2f}%*",
    f"- Cases containing multiple payment activity types: "
    f"**{stats['multiple_activity_cases']:,} "
    f"({multiple_activity_percentage:.2f}%)**",
    f"- Cases linked to multiple customer identifiers: "
    f"*{stats['multiple_customer_cases']:,}*",
    "",
    "A late payment event is a recorded payment with "
    "payment_delay_days > 0. This does not establish that the customer "
    "defaulted or that the loan was classified as non-performing.",
    "",
    "## 7. Extreme Case Audit",
    "",
    f"- Cases reviewed in the extreme-span sample: "
    f"*{extreme_stats['cases_reviewed']:,}*",
    f"- Median span within that sample: "
    f"*{extreme_stats['median_extreme_span']:,.0f} days*",
    f"- Maximum span within that sample: "
    f"*{extreme_stats['maximum_extreme_span']:,.0f} days*",
    f"- Median events per case in that sample: "
    f"*{extreme_stats['median_extreme_events']:,.1f}*",
    f"- Maximum events per case in that sample: "
    f"*{extreme_stats['maximum_extreme_events']:,}*",
    f"- Sample cases with at least one late payment event: "
    f"*{extreme_stats['extreme_late_cases']:,}*",
    "",
    "The extreme-case sample was selected by observed payment span. It is "
    "not representative of the full dataset, and the analysis does not "
    "establish why these cases have long spans.",
    "",
    "## 8. Trace Analysis",
    "",
    f"- Cases included in trace analysis: "
    f"*{trace_summary.get('Total cases', 'Not available')}*",
    f"- Unique observed trace variants: "
    f"*{trace_summary.get('Unique trace variants', 'Not available')}*",
    f"- Mean events per case: "
    f"*{trace_summary.get('Mean events per case', 'Not available')}*",
    f"- Median events per case: "
    f"*{trace_summary.get('Median events per case', 'Not available')}*",
    "",
    "The following table lists up to ten frequent trace variants. Each trace "
    "is a sequence of recorded payment categories within a loan case.",
    "",
    *trace_table_lines,
    "",
    "The most frequent traces are dominated by Early Payment categories. "
    "These sequences describe the recorded event log and should not be "
    "interpreted as full loan workflows or proof of customer behavior across "
    "all installments.",
    "",
    "### Most Frequent Adjacent Activity Transitions",
    "",
    "| Adjacent activity transition | Count |",
    "|---|---:|",
    *[
        f"| {transition} | {count:,} |"
        for transition, count in trace_transition_counts
    ],
    "",
    "Events are ordered by relative payment day, installment number, and "
    "installment version. The secondary sort fields make ordering "
    "reproducible, but do not establish the true order of events with "
    "identical payment days. Repeated payment entries may mean that adjacent "
    "events do not correspond to distinct installments.",
    "",
    "## 9. Limitations",
    "",
    "1. The event log focuses on payment records rather than the full loan "
    "lifecycle.",
    "2. Event timestamps encode relative days and are not actual calendar dates.",
    "3. Multiple records may exist for one installment, including partial or "
    "multiple payment entries.",
    "4. Payment categories are derived from recorded timing differences and "
    "should not be treated as formal credit-risk or default labels.",
    "5. Transition percentages are descriptive and do not imply causation.",
    "6. Extreme cases require contextual investigation; they should not be "
    "removed without a defensible data-quality reason.",
    "",
    "## 10. Reproducibility and Outputs",
    "",
    "Key outputs include:",
    "",
    "- data/processed/payment_event_log.parquet",
    "- outputs/reports/payment_trace_variants.csv",
    "- outputs/reports/payment_transitions.csv",
    "- outputs/reports/payment_transition_probabilities.csv",
    "- outputs/reports/payment_case_duration_summary.csv",
    "- outputs/reports/extreme_payment_span_cases.csv",
    "- outputs/figures/payment_events_per_case.png",
    "- outputs/figures/observed_payment_span_distribution.png",
    "",
    "## 11. Conclusion",
    "",
    "The analysis demonstrates how payment-level data can be transformed "
    "into an event log and used to examine case variation, payment-category "
    "transitions, observed spans, and extreme cases. The findings are "
    "exploratory and descriptive. Further work should validate installment "
    "semantics, examine payment sequences at the installment level, and "
    "extend the event log only where reliable lifecycle events are available.",
    "",
    "## Appendix: Extreme-Span Audit",
    "",
    *extreme_audit_lines,
    "",
]

output_path.write_text("\n".join(findings) + "\n", encoding="utf-8")

print("\nProject findings report completed.")
print(f"Loan cases analyzed: {total_cases:,}")
print(f"Payment events summarized: {total_events:,}")
print(f"Cases with late payment events: {late_cases:,}")
print(f"Report saved to: {output_path}")