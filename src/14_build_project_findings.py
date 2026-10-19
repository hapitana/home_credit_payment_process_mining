from pathlib import Path

import polars as pl


project_root = Path(__file__).resolve().parents[1]
reports_dir = project_root / "outputs" / "reports"
output_path = reports_dir / "project_findings.md"

case_summary_path = reports_dir / "payment_case_duration_summary.csv"
transition_path = reports_dir / "payment_transition_probabilities.csv"
extreme_summary_path = reports_dir / "extreme_case_characteristics.csv"
transition_counts_path = reports_dir / "payment_transitions.csv"


def format_value(value):
    if value is None:
        return "N/A"

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if isinstance(value, int):
        return f"{value:,}"

    if isinstance(value, float):
        return f"{value:,.2f}"

    return str(value).replace("|", "\\|")


def markdown_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for row in rows:
        formatted_row = [format_value(value) for value in row]
        lines.append("| " + " | ".join(formatted_row) + " |")

    return "\n".join(lines)


def require_columns(dataframe, required_columns, filename):
    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(
            f"Missing required columns in {filename}: {missing_text}"
        )


def build_event_distribution(case_summary):
    event_distribution = [
        ("1 event", 1, 1),
        ("2-5 events", 2, 5),
        ("6-10 events", 6, 10),
        ("11-20 events", 11, 20),
        (">20 events", 21, None),
    ]

    rows = []

    for label, lower_bound, upper_bound in event_distribution:
        if upper_bound is None:
            count = case_summary.filter(
                pl.col("event_count") >= lower_bound
            ).height
        else:
            count = case_summary.filter(
                (pl.col("event_count") >= lower_bound)
                & (pl.col("event_count") <= upper_bound)
            ).height

        rows.append((label, count))

    return rows


def main():
    required_files = [
        case_summary_path,
        transition_path,
        extreme_summary_path,
        transition_counts_path,
    ]

    missing_files = [
        str(path)
        for path in required_files
        if not path.exists()
    ]

    if missing_files:
        missing_text = "\n".join(missing_files)
        raise FileNotFoundError(
            "Required input files were not found:\n" + missing_text
        )

    case_summary = pl.read_csv(case_summary_path)
    transition_probabilities = pl.read_csv(transition_path)
    extreme_summary = pl.read_csv(extreme_summary_path)
    transition_counts = pl.read_csv(transition_counts_path)

    require_columns(
        case_summary,
        [
            "case_id",
            "event_count",
            "customer_count",
            "first_payment_day",
            "last_payment_day",
            "maximum_delay_days",
            "mean_delay_days",
            "late_event_count",
            "activity_type_count",
            "observed_span_days",
            "has_late_payment_event",
        ],
        case_summary_path.name,
    )

    require_columns(
        transition_probabilities,
        [
            "previous_activity",
            "activity",
            "transition_count",
            "outgoing_transition_count",
            "transition_percentage",
        ],
        transition_path.name,
    )

    require_columns(
        extreme_summary,
        [
            "cases_reviewed",
            "minimum_span_days",
            "median_span_days",
            "maximum_span_days",
            "mean_events_per_case",
            "median_events_per_case",
            "maximum_events_per_case",
            "mean_activity_types",
            "cases_with_late_events",
        ],
        extreme_summary_path.name,
    )

    require_columns(
        transition_counts,
        [
            "previous_activity",
            "activity",
            "transition_count",
        ],
        transition_counts_path.name,
    )

    total_cases = case_summary.height
    total_events = int(case_summary["event_count"].sum())
    mean_events = float(case_summary["event_count"].mean())
    median_events = float(case_summary["event_count"].median())
    maximum_events = int(case_summary["event_count"].max())

    mean_span = float(case_summary["observed_span_days"].mean())
    median_span = float(case_summary["observed_span_days"].median())
    maximum_span = int(case_summary["observed_span_days"].max())

    cases_with_late_events = case_summary.filter(
        pl.col("has_late_payment_event")
    ).height

    cases_with_multiple_activities = case_summary.filter(
        pl.col("activity_type_count") > 1
    ).height

    cases_with_single_activity = case_summary.filter(
        pl.col("activity_type_count") == 1
    ).height

    multi_customer_cases = case_summary.filter(
        pl.col("customer_count") > 1
    ).height

    span_quantiles = case_summary.select(
        pl.col("observed_span_days").quantile(0.75).alias("p75"),
        pl.col("observed_span_days").quantile(0.90).alias("p90"),
        pl.col("observed_span_days").quantile(0.95).alias("p95"),
        pl.col("observed_span_days").quantile(0.99).alias("p99"),
    ).row(0, named=True)

    p75_span = float(span_quantiles["p75"])
    p90_span = float(span_quantiles["p90"])
    p95_span = float(span_quantiles["p95"])
    p99_span = float(span_quantiles["p99"])

    cases_at_or_above_p99 = case_summary.filter(
        pl.col("observed_span_days") >= p99_span
    ).height

    event_distribution_rows = build_event_distribution(case_summary)

    activity_counts = (
        transition_counts
        .group_by("previous_activity")
        .agg(
            pl.col("transition_count").sum().alias("outgoing_transitions")
        )
        .sort("previous_activity")
    )

    transition_probability_rows = (
        transition_probabilities
        .sort(
            ["previous_activity", "transition_percentage"],
            descending=[False, True],
        )
        .select(
            "previous_activity",
            "activity",
            "transition_count",
            "transition_percentage",
        )
        .iter_rows()
    )

    transition_probability_table = markdown_table(
        [
            "Previous Activity",
            "Next Activity",
            "Transition Count",
            "Transition Probability (%)",
        ],
        list(transition_probability_rows),
    )

    transition_count_rows = (
        transition_counts
        .sort("transition_count", descending=True)
        .select(
            "previous_activity",
            "activity",
            "transition_count",
        )
        .iter_rows()
    )

    transition_count_table = markdown_table(
        [
            "Previous Activity",
            "Next Activity",
            "Transition Count",
        ],
        list(transition_count_rows),
    )

    event_distribution_table = markdown_table(
        ["Events per Case", "Number of Cases"],
        event_distribution_rows,
    )

    extreme = extreme_summary.row(0, named=True)

    report_lines = [
        "# Home Credit Payment Process Mining",
        "",
        "## 1. Project Overview",
        "",
        "This project applies process-mining concepts to Home Credit payment "
        "records. It examines observed payment-event sequences, transitions "
        "between payment-timing categories, case-level event counts, and "
        "the observed span between recorded payment events.",
        "",
        "The analysis is descriptive. It identifies patterns in the available "
        "records and does not establish causal relationships or determine "
        "whether a loan was ultimately repaid successfully.",
        "",
        "## 2. Research Questions",
        "",
        "1. What payment-timing patterns appear in the recorded loan cases?",
        "2. How frequently do Early, On-time, and Late Payment events follow "
        "one another?",
        "3. How many payment events are recorded per loan case, and how long "
        "is the observed span between its first and last recorded payment?",
        "4. What characteristics appear among cases with exceptionally long "
        "observed payment spans?",
        "",
        "## 3. Dataset and Event Log",
        "",
        "The project uses three Home Credit dataset files:",
        "",
        "- `application_train.csv`: customer application and target information.",
        "- `previous_application.csv`: historical loan application records.",
        "- `installments_payments.csv`: installment and payment records.",
        "",
        "The event log is built from installment-payment records with a "
        "non-missing payment-entry day. Each case is identified by "
        "`SK_ID_PREV`, representing a previous loan, and each event is "
        "classified according to the difference between the payment-entry "
        "day and the scheduled installment day.",
        "",
        markdown_table(
            ["Measure", "Result"],
            [
                ("Recorded payment events", total_events),
                ("Loan cases", total_cases),
                ("Mean events per case", mean_events),
                ("Median events per case", median_events),
                ("Maximum events in one case", maximum_events),
            ],
        ),
        "",
        "## 4. Methodology",
        "",
        "### 4.1 Payment-event classification",
        "",
        "Payment delay is calculated as:",
        "",
        "`payment_delay_days = DAYS_ENTRY_PAYMENT - DAYS_INSTALMENT`",
        "",
        "- **Early Payment:** payment-entry day precedes the scheduled day.",
        "- **On-time Payment:** payment-entry day equals the scheduled day.",
        "- **Late Payment:** payment-entry day follows the scheduled day.",
        "",
        "### 4.2 Event ordering and transitions",
        "",
        "Events are ordered within each loan case using the recorded "
        "payment-entry day. Transition counts describe adjacent recorded "
        "events within the same case. Because an installment can have "
        "multiple payment records, a transition does not necessarily "
        "represent movement between two distinct installments.",
        "",
        "Transition probabilities are calculated conditionally on the "
        "previous activity. For each previous activity, the probability "
        "of a next activity is its transition count divided by the total "
        "outgoing transitions from that previous activity.",
        "",
        "### 4.3 Observed payment span",
        "",
        "Observed payment span is calculated as the last recorded payment "
        "day minus the first recorded payment day for each case. The event "
        "timestamps use an artificial reference date to preserve relative "
        "day ordering. They are not actual calendar dates.",
        "",
        "The observed span must not be interpreted as confirmed loan tenure "
        "or the complete duration of a loan.",
        "",
        "## 5. Key Findings",
        "",
        "### 5.1 Case-level payment patterns",
        "",
        markdown_table(
            ["Measure", "Result"],
            [
                ("Total loan cases", total_cases),
                ("Total recorded events", total_events),
                ("Mean events per case", mean_events),
                ("Median events per case", median_events),
                ("Maximum events per case", maximum_events),
                ("Cases with at least one late event", cases_with_late_events),
                (
                    "Cases with multiple activity types",
                    cases_with_multiple_activities,
                ),
                (
                    "Cases with only one activity type",
                    cases_with_single_activity,
                ),
                ("Cases linked to multiple customers", multi_customer_cases),
            ],
        ),
        "",
        "The event-count distribution is shown below.",
        "",
        event_distribution_table,
        "",
        "### 5.2 Observed payment spans",
        "",
        markdown_table(
            ["Measure", "Observed Span (Days)"],
            [
                ("Mean", mean_span),
                ("Median", median_span),
                ("75th percentile", p75_span),
                ("90th percentile", p90_span),
                ("95th percentile", p95_span),
                ("99th percentile threshold", p99_span),
                ("Maximum", maximum_span),
                ("Cases at or above the P99 threshold", cases_at_or_above_p99),
            ],
        ),
        "",
        "The upper tail contains cases whose recorded payment events span "
        "substantially longer periods than those of most cases. These cases "
        "are candidates for further data-quality and process investigation, "
        "not automatic evidence of delinquency or default.",
        "",
        "### 5.3 Payment-event transitions",
        "",
        "The most frequent adjacent-event transitions are listed below.",
        "",
        transition_count_table,
        "",
        "Transition probabilities conditional on the previous activity are "
        "shown below.",
        "",
        transition_probability_table,
        "",
        "These results describe observed sequences in the event log. They "
        "should not be interpreted as causal effects or as probabilities "
        "of future customer behavior.",
        "",
        "### 5.4 Extreme observed-span cases",
        "",
        markdown_table(
            ["Measure", "Result"],
            [
                ("Cases reviewed", int(extreme["cases_reviewed"])),
                ("Minimum span in reviewed cases (days)", int(extreme["minimum_span_days"])),
                ("Median span in reviewed cases (days)", float(extreme["median_span_days"])),
                ("Maximum span in reviewed cases (days)", int(extreme["maximum_span_days"])),
                ("Mean events per reviewed case", float(extreme["mean_events_per_case"])),
                ("Median events per reviewed case", float(extreme["median_events_per_case"])),
                ("Maximum events in a reviewed case", int(extreme["maximum_events_per_case"])),
                ("Mean activity types per reviewed case", float(extreme["mean_activity_types"])),
                ("Reviewed cases with late events", int(extreme["cases_with_late_events"])),
            ],
        ),
        "",
        "The extreme-case sample contains up to 100 cases selected from the "
        "longest observed spans. It is a targeted sample and is not "
        "representative of the full population of loan cases.",
        "",
        "## 6. Interpretation and Limitations",
        "",
        "The analysis provides a descriptive view of recorded payment "
        "behavior. Several limitations are important:",
        "",
        "1. **Recorded events are not necessarily distinct installments.** "
        "Repeated records may reflect multiple payment entries associated "
        "with one installment. They should not be removed without a "
        "well-supported business rule.",
        "2. **The event log is based on available payment records.** "
        "Cases with no non-missing payment-entry day are not represented "
        "in the event log.",
        "3. **Relative days are not actual calendar dates.** The artificial "
        "timestamp is used only to order events and does not identify the "
        "real-world date of a payment.",
        "4. **Observed span is not confirmed loan tenure.** The first and "
        "last recorded events may not correspond to loan origination and "
        "final settlement.",
        "5. **Payment timing alone does not establish default.** An observed "
        "late event is not sufficient to determine credit risk, loss, or "
        "final repayment outcome.",
        "6. **The analysis is descriptive rather than causal.** The results "
        "do not demonstrate why payment timing occurs or whether one event "
        "causes another.",
        "7. **The extreme-case review is selective.** Its findings should "
        "not be generalized to all cases.",
        "",
        "## 7. Reproducibility",
        "",
        "The analysis scripts are located in the `src/` directory. Input "
        "datasets are expected in `data/raw/`, derived event data in "
        "`data/processed/`, and generated reports and figures in `outputs/`.",
        "",
        "Install the pinned dependencies from the project root:",
        "",
        "```powershell",
        "python -m pip install -r requirements.txt",
        "```",
        "",
        "Run the project scripts in numerical order to reproduce the "
        "analysis. The raw datasets and generated Parquet event log are "
        "excluded from version control; users must obtain the original "
        "dataset files separately and place them in the expected directory.",
        "",
        "## 8. Future Improvements",
        "",
        "- Use a process-mining library to discover and visualize process models.",
        "- Investigate repeated installment records and partial-payment patterns.",
        "- Compare payment-event behavior across customer and loan segments.",
        "- Evaluate alternative case identifiers and event definitions.",
        "- Add sensitivity checks for missing payment records and extreme cases.",
        "- Explore predictive modeling only after defining a defensible target "
        "and a leakage-resistant validation strategy.",
        "",
        "## 9. Conclusion",
        "",
        "This project demonstrates a reproducible workflow for constructing "
        "a payment-event log, validating loan cases, examining event "
        "sequences, estimating transition probabilities, and auditing "
        "extreme observed spans. The findings are useful as exploratory "
        "evidence for further process-mining research, while the limitations "
        "highlight the need for careful event definitions and business "
        "interpretation.",
        "",
    ]

    report_text = "\n".join(report_lines)
    output_path.write_text(report_text, encoding="utf-8")

    print("Project findings report created successfully.")
    print(f"Output file: {output_path}")
    print(f"Loan cases: {total_cases:,}")
    print(f"Recorded events: {total_events:,}")
    print(f"Cases at or above P99: {cases_at_or_above_p99:,}")
    print(f"Extreme cases reviewed: {int(extreme['cases_reviewed']):,}")
    print(f"Mean events per case: {mean_events:,.2f}")
    print(f"Median observed span: {median_span:,.2f} days")


if __name__ == "__main__":
    main()