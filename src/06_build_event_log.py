from datetime import datetime
from pathlib import Path

import polars as pl


base_dir = Path(__file__).resolve().parents[1]
raw_dir = base_dir / "data" / "raw"
processed_dir = base_dir / "data" / "processed"
report_dir = base_dir / "outputs" / "reports"

processed_dir.mkdir(parents=True, exist_ok=True)
report_dir.mkdir(parents=True, exist_ok=True)

input_path = raw_dir / "installments_payments.csv"
output_path = processed_dir / "payment_event_log.parquet"
report_path = report_dir / "event_log_build_report.txt"

if not input_path.exists():
    raise FileNotFoundError(f"Input file not found: {input_path}")

print("Preparing payment event log...")

lazy_frame = pl.scan_csv(input_path)

schema = lazy_frame.collect_schema()
required_columns = [
    "SK_ID_CURR",
    "SK_ID_PREV",
    "NUM_INSTALMENT_NUMBER",
    "NUM_INSTALMENT_VERSION",
    "DAYS_INSTALMENT",
    "DAYS_ENTRY_PAYMENT",
    "AMT_INSTALMENT",
    "AMT_PAYMENT",
]

missing_columns = [
    column_name
    for column_name in required_columns
    if column_name not in schema.names()
]

if missing_columns:
    raise ValueError(
        f"Required columns are missing: {missing_columns}"
    )

payment_delay = (
    pl.col("DAYS_ENTRY_PAYMENT") - pl.col("DAYS_INSTALMENT")
)

event_log = (
    lazy_frame
    .filter(pl.col("DAYS_ENTRY_PAYMENT").is_not_null())
    .with_columns(
        payment_delay.alias("payment_delay_days")
    )
    .with_columns(
        pl.when(pl.col("payment_delay_days") < 0)
        .then(pl.lit("Early Payment"))
        .when(pl.col("payment_delay_days") == 0)
        .then(pl.lit("On-time Payment"))
        .when(pl.col("payment_delay_days") > 0)
        .then(pl.lit("Late Payment"))
        .otherwise(pl.lit("Unclassified Payment"))
        .alias("activity"),
        (
            pl.lit(datetime(2000, 1, 1))
            + pl.duration(
                days=pl.col("DAYS_ENTRY_PAYMENT").cast(pl.Int64)
            )
        ).alias("timestamp"),
    )
    .select(
        pl.col("SK_ID_PREV").alias("case_id"),
        pl.col("SK_ID_CURR").alias("customer_id"),
        pl.col("activity"),
        pl.col("timestamp"),
        pl.col("DAYS_ENTRY_PAYMENT").alias("relative_payment_day"),
        pl.col("DAYS_INSTALMENT").alias("relative_due_day"),
        pl.col("payment_delay_days"),
        pl.col("NUM_INSTALMENT_NUMBER").alias("installment_number"),
        pl.col("NUM_INSTALMENT_VERSION").alias("installment_version"),
        pl.col("AMT_INSTALMENT").alias("scheduled_amount"),
        pl.col("AMT_PAYMENT").alias("payment_amount"),
    )
)

print("Writing event log to Parquet...")
event_log.sink_parquet(
    output_path,
    compression="zstd",
)

print("Validating the generated event log...")

saved_log = pl.scan_parquet(output_path)

validation = (
    saved_log
    .select(
        pl.len().alias("event_count"),
        pl.col("case_id").n_unique().alias("case_count"),
        pl.col("customer_id").n_unique().alias("customer_count"),
        pl.col("activity").n_unique().alias("activity_count"),
        pl.col("payment_amount").null_count().alias(
            "missing_payment_amounts"
        ),
        pl.col("timestamp").null_count().alias("missing_timestamps"),
    )
    .collect()
    .to_dicts()[0]
)

report_lines = [
    "PAYMENT EVENT LOG BUILD REPORT",
    "==============================",
    "",
    f"Event count: {validation['event_count']:,}",
    f"Case count: {validation['case_count']:,}",
    f"Customer count: {validation['customer_count']:,}",
    f"Activity count: {validation['activity_count']:,}",
    (
        "Missing payment amounts: "
        f"{validation['missing_payment_amounts']:,}"
    ),
    f"Missing timestamps: {validation['missing_timestamps']:,}",
    "",
    "METHODOLOGICAL NOTES",
    "====================",
    "Each event represents a recorded payment with a non-missing payment date.",
    "Case ID is SK_ID_PREV, representing a previous loan.",
    "Repeated installment keys are retained.",
    (
        "The timestamp is derived from a relative day count using an "
        "artificial anchor date; it is not an actual calendar date."
    ),
    (
        "Payment timing categories are based on the difference between "
        "payment day and due day."
    ),
]

report_path.write_text(
    "\n".join(report_lines),
    encoding="utf-8",
)

print("\nEvent log validation")

for key, value in validation.items():
    print(f"{key}: {value:,}")

print("\nEvent log created successfully.")
print(f"Parquet file: {output_path}")
print(f"Build report: {report_path}")