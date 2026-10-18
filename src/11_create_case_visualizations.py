from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl


base_dir = Path(__file__).resolve().parents[1]
report_dir = base_dir / "outputs" / "reports"
figure_dir = base_dir / "outputs" / "figures"

input_path = report_dir / "payment_case_duration_summary.csv"

if not input_path.exists():
    raise FileNotFoundError(f"Case summary not found: {input_path}")

figure_dir.mkdir(parents=True, exist_ok=True)

print("Loading loan case summary...")

case_summary = pl.read_csv(input_path)

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
)

group_order = [
    "1 event",
    "2-5 events",
    "6-10 events",
    "11-20 events",
    "More than 20 events",
]

event_groups = (
    event_groups
    .with_columns(
        pl.col("event_group")
        .replace_strict(
            {name: index for index, name in enumerate(group_order)}
        )
        .alias("group_order")
    )
    .sort("group_order")
)

fig, ax = plt.subplots(figsize=(10, 6))

ax.bar(
    event_groups["event_group"].to_list(),
    event_groups["len"].to_list(),
)

ax.set_title("Distribution of Payment Events per Loan Case")
ax.set_xlabel("Number of Recorded Events")
ax.set_ylabel("Number of Loan Cases")
ax.tick_params(axis="x", rotation=20)
fig.tight_layout()

event_figure_path = figure_dir / "payment_events_per_case.png"
fig.savefig(event_figure_path, dpi=300)
plt.close(fig)

observed_spans = (
    case_summary
    .get_column("observed_span_days")
    .drop_nulls()
    .to_list()
)

fig, ax = plt.subplots(figsize=(10, 6))

ax.hist(observed_spans, bins=50)

ax.set_title("Distribution of Observed Payment Spans")
ax.set_xlabel("Observed Span (Relative Days)")
ax.set_ylabel("Number of Loan Cases")
fig.tight_layout()

span_figure_path = figure_dir / "observed_payment_span_distribution.png"
fig.savefig(span_figure_path, dpi=300)
plt.close(fig)

print("\nVisualization completed.")
print(f"Loan cases analyzed: {case_summary.height:,}")
print(f"Saved figure: {event_figure_path}")
print(f"Saved figure: {span_figure_path}")