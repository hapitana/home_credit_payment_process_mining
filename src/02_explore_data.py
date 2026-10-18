from pathlib import Path

import polars as pl


base_dir = Path(__file__).resolve().parents[1]
raw_dir = base_dir / "data" / "raw"
report_dir = base_dir / "outputs" / "reports"

report_dir.mkdir(parents=True, exist_ok=True)

file_names = [
    "application_train.csv",
    "previous_application.csv",
    "installments_payments.csv",
]

key_columns = {
    "application_train.csv": ["SK_ID_CURR", "TARGET"],
    "previous_application.csv": ["SK_ID_CURR", "SK_ID_PREV"],
    "installments_payments.csv": [
        "SK_ID_CURR",
        "SK_ID_PREV",
        "NUM_INSTALMENT_NUMBER",
        "NUM_INSTALMENT_VERSION",
    ],
}

report_lines = []

for file_name in file_names:
    file_path = raw_dir / file_name

    print(f"\nInspecting data quality: {file_name}")

    lazy_frame = pl.scan_csv(file_path)
    schema = lazy_frame.collect_schema()
    column_names = schema.names()

    row_count = lazy_frame.select(pl.len()).collect().item()

    null_counts = (
        lazy_frame
        .select(pl.all().null_count())
        .collect()
        .to_dicts()[0]
    )

    missing_summary = []

    for column_name in column_names:
        missing_count = null_counts[column_name]
        missing_percentage = (
            missing_count / row_count * 100
            if row_count > 0
            else 0.0
        )

        if missing_count > 0:
            missing_summary.append(
                (
                    column_name,
                    missing_count,
                    missing_percentage,
                )
            )

    missing_summary.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    report_lines.append(f"\nFILE: {file_name}")
    report_lines.append(f"Number of rows: {row_count:,}")
    report_lines.append(f"Number of columns: {len(column_names)}")
    report_lines.append("\nMissing values by column:")

    for column_name, missing_count, missing_percentage in missing_summary:
        report_lines.append(
            f"{column_name}: {missing_count:,} "
            f"({missing_percentage:.2f}%)"
        )

    print(f"Number of rows: {row_count:,}")
    print(f"Number of columns: {len(column_names)}")
    print(f"Columns with missing values: {len(missing_summary)}")

    print("\nTop 15 columns with missing values:")

    for column_name, missing_count, missing_percentage in (
        missing_summary[:15]
    ):
        print(
            f"{column_name}: {missing_count:,} "
            f"({missing_percentage:.2f}%)"
        )

    print("\nIdentifier checks:")

    for column_name in key_columns[file_name]:
        if column_name not in column_names:
            continue

        key_stats = (
            lazy_frame
            .select(
                pl.col(column_name).null_count().alias("null_count"),
                pl.col(column_name).n_unique().alias("unique_count"),
            )
            .collect()
        )

        null_count = key_stats["null_count"][0]
        unique_count = key_stats["unique_count"][0]

        print(f"{column_name}:")
        print(f"  Unique values: {unique_count:,}")
        print(f"  Missing values: {null_count:,}")

        report_lines.append(
            f"\n{column_name}: "
            f"{unique_count:,} unique values, "
            f"{null_count:,} missing values"
        )

report_path = report_dir / "data_quality_report.txt"

report_path.write_text(
    "\n".join(report_lines),
    encoding="utf-8",
)

print("\nData quality inspection completed.")
print(f"Report saved to: {report_path}")