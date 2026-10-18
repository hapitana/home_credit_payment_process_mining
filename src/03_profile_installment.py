from pathlib import Path

import polars as pl


base_dir = Path(__file__).resolve().parents[1]
raw_dir = base_dir / "data" / "raw"
report_dir = base_dir / "outputs" / "reports"

report_dir.mkdir(parents=True, exist_ok=True)

file_path = raw_dir / "installments_payments.csv"
report_path = report_dir / "installment_profile.txt"

if not file_path.exists():
    raise FileNotFoundError(f"Input file not found: {file_path}")

print("Loading installment payment data...")

lazy_frame = pl.scan_csv(file_path)

print("Calculating payment timing indicators...")

payment_delay = (
    pl.col("DAYS_ENTRY_PAYMENT") - pl.col("DAYS_INSTALMENT")
)

profile = (
    lazy_frame
    .with_columns(
        payment_delay.alias("payment_delay_days")
    )
    .select(
        pl.len().alias("total_records"),
        pl.col("SK_ID_CURR").n_unique().alias("unique_customers"),
        pl.col("SK_ID_PREV").n_unique().alias("unique_previous_loans"),
        pl.col("DAYS_ENTRY_PAYMENT").null_count().alias(
            "missing_payment_dates"
        ),
        pl.col("AMT_PAYMENT").null_count().alias(
            "missing_payment_amounts"
        ),
        pl.col("payment_delay_days").count().alias(
            "records_with_payment_timing"
        ),
        (pl.col("payment_delay_days") < 0).sum().alias(
            "early_payment_records"
        ),
        (pl.col("payment_delay_days") == 0).sum().alias(
            "on_time_payment_records"
        ),
        (pl.col("payment_delay_days") > 0).sum().alias(
            "late_payment_records"
        ),
        pl.col("payment_delay_days").mean().alias(
            "mean_payment_delay_days"
        ),
        pl.col("payment_delay_days").median().alias(
            "median_payment_delay_days"
        ),
        pl.col("AMT_INSTALMENT").sum().alias(
            "total_scheduled_amount"
        ),
        pl.col("AMT_PAYMENT").sum().alias(
            "total_recorded_payment_amount"
        ),
    )
    .collect()
)

result = profile.to_dicts()[0]

report_lines = [
    "INSTALLMENT PAYMENT PROFILE",
    "============================",
    "",
    f"Total records: {result['total_records']:,}",
    f"Unique customers: {result['unique_customers']:,}",
    f"Unique previous loans: {result['unique_previous_loans']:,}",
    (
        "Missing payment dates: "
        f"{result['missing_payment_dates']:,}"
    ),
    (
        "Missing payment amounts: "
        f"{result['missing_payment_amounts']:,}"
    ),
    (
        "Records with payment timing: "
        f"{result['records_with_payment_timing']:,}"
    ),
    (
        "Early payment records: "
        f"{result['early_payment_records']:,}"
    ),
    (
        "On-time payment records: "
        f"{result['on_time_payment_records']:,}"
    ),
    (
        "Late payment records: "
        f"{result['late_payment_records']:,}"
    ),
    (
        "Mean payment delay (days): "
        f"{result['mean_payment_delay_days']:.2f}"
        if result["mean_payment_delay_days"] is not None
        else "Mean payment delay (days): unavailable"
    ),
    (
        "Median payment delay (days): "
        f"{result['median_payment_delay_days']:.2f}"
        if result["median_payment_delay_days"] is not None
        else "Median payment delay (days): unavailable"
    ),
    (
        "Total scheduled amount: "
        f"{result['total_scheduled_amount']:,.2f}"
    ),
    (
        "Total recorded payment amount: "
        f"{result['total_recorded_payment_amount']:,.2f}"
    ),
    "",
    "INTERPRETATION NOTES",
    "====================",
    "Negative payment delay means payment before the due date.",
    "Zero payment delay means payment on the due date.",
    "Positive payment delay means payment after the due date.",
    (
        "Missing payment dates are not automatically classified "
        "as late payments."
    ),
    (
        "These are record-level counts, not customer-level "
        "or loan-level late-payment rates."
    ),
]

report_path.write_text(
    "\n".join(report_lines),
    encoding="utf-8",
)

print("\nPayment timing summary")

for key in [
    "total_records",
    "unique_customers",
    "unique_previous_loans",
    "missing_payment_dates",
    "missing_payment_amounts",
    "records_with_payment_timing",
    "early_payment_records",
    "on_time_payment_records",
    "late_payment_records",
]:
    print(f"{key}: {result[key]:,}")

print(
    "mean_payment_delay_days: "
    f"{result['mean_payment_delay_days']}"
)
print(
    "median_payment_delay_days: "
    f"{result['median_payment_delay_days']}"
)

print("\nProfile completed.")
print(f"Report saved to: {report_path}")