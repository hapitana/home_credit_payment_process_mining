Home Credit Payment Process Mining
Project Overview
This project applies process-mining concepts and event-log analysis to installment payment records from the Home Credit Default Risk dataset. It examines payment behavior across loan cases, identifies recurring payment traces, analyzes transitions between payment-timing categories, and investigates loans with unusually long observed payment spans.
The project demonstrates a reproducible data-analysis workflow using Python, Polars, and Matplotlib, with an emphasis on data quality, event-log construction, process behavior, and transparent methodological limitations.
Repository: home_credit_payment_process_mining
Research Questions
This project addresses five exploratory questions:
1. How can installment payment records be transformed into an event log suitable for process-oriented analysis?
2. What are the distributions of recorded payment events and observed payment spans across loan cases?
3. Which payment-timing patterns and trace variants occur most frequently?
4. How do payment-timing categories transition between adjacent recorded payment events?
5. What characteristics distinguish loan cases with exceptionally long observed payment spans?
The analysis is descriptive and exploratory. It does not establish causal relationships or predict loan default.
Dataset
The project uses three CSV files associated with the Home Credit Default Risk dataset.
File
	Description
	Records
	application_train.csv
	Main application and target information
	307,511
	previous_application.csv
	Historical loan application information
	1,670,214
	installments_payments.csv
	Installment schedules and recorded payments
	13,605,401
	The primary analysis uses installments_payments.csv. The other two files are inspected for data structure and quality but are not treated as a complete application-to-payment process history.
Important variables
The installment dataset includes:
* SK_ID_CURR: Customer identifier.
* SK_ID_PREV: Previous loan identifier, used as the process case identifier.
* NUM_INSTALMENT_VERSION: Installment schedule version.
* NUM_INSTALMENT_NUMBER: Installment number.
* DAYS_INSTALMENT: Relative day of the scheduled installment.
* DAYS_ENTRY_PAYMENT: Relative day of the recorded payment.
* AMT_INSTALMENT: Scheduled installment amount.
* AMT_PAYMENT: Recorded payment amount.
Data access
The raw data is not included in this repository. Obtain the files from the Home Credit Default Risk dataset on Kaggle, subject to the dataset's access conditions and applicable terms.
Place the three CSV files in data/raw/ using the exact filenames listed above.
Methodology
The workflow consists of data inspection, quality assessment, event-log construction, trace analysis, transition analysis, duration analysis, visualization, and investigation of extreme cases.
1. Data inspection and quality assessment
The initial scripts inspect dataset dimensions, schemas, identifiers, missing values, and installment-level records.
The quality assessment identifies repeated combinations of SK_ID_PREV, NUM_INSTALMENT_NUMBER, and NUM_INSTALMENT_VERSION. These repeated keys may represent multiple payment records associated with one installment. They are therefore not automatically removed.
2. Event-log construction
An event log is constructed from installment records with a non-missing DAYS_ENTRY_PAYMENT.
The event-log design is:
Field
	Definition
	Case ID
	SK_ID_PREV
	Customer ID
	SK_ID_CURR
	Activity
	Early Payment, On-time Payment, or Late Payment
	Event time
	Artificial timestamp derived from DAYS_ENTRY_PAYMENT
	Payment delay
	DAYS_ENTRY_PAYMENT - DAYS_INSTALMENT
	Payment timing is categorized as follows:
* Early Payment: Payment delay is negative.
* On-time Payment: Payment delay is zero.
* Late Payment: Payment delay is positive.
The event timestamp is created by adding the relative payment day to an artificial base date. This preserves the relative temporal ordering of recorded payments; it does not recover the actual calendar date.
3. Trace and transition analysis
Events are ordered within each loan case to construct payment traces. The analysis identifies recurring trace variants and counts transitions between adjacent recorded payment events.
Transition probabilities are calculated conditionally on the preceding activity category. These probabilities describe observed transitions in this dataset and should not be interpreted as causal effects, default probabilities, or predictions of future payment behavior.
Because a single installment may have multiple payment records, adjacent events do not necessarily represent different installments.
4. Case duration and extreme-case analysis
For each case, the analysis calculates the number of recorded events and the observed payment span:
observed_payment_span = maximum relative payment day - minimum relative payment day
This span measures the distance between the earliest and latest recorded payment days in a case. It is not necessarily the loan's contractual tenure or actual calendar duration.
Extreme cases are selected using the 99th-percentile threshold and inspected for event counts, activity diversity, and the presence of late payment events.
5. Visualization
The project generates visualizations of:
* The distribution of payment events per loan case.
* The distribution of observed payment spans.
These figures provide an overview of variation across cases and support further exploratory investigation.
Key Findings
The following findings were obtained from the current analysis.
Event-log summary
Metric
	Result
	Original installment records
	13,605,401
	Records with a recorded payment date
	13,602,496
	Loan cases in the event log
	997,674
	Customers represented in the event log
	339,578
	Mean events per case
	13.63
	Median events per case
	10
	Maximum events in one case
	293
	The event log contains three payment-timing activities.
Activity
	Recorded events
	Early Payment
	9,309,477
	On-time Payment
	3,146,350
	Late Payment
	1,146,669
	Total
	13,602,496
	These categories describe payment timing relative to scheduled installment days. They should not be interpreted as independent customer-level classifications.
Payment transition patterns
The following table reports the observed probability of the next activity, conditional on the preceding activity.
Previous activity
	Next activity
	Conditional probability
	Early Payment
	Early Payment
	77.59%
	Early Payment
	On-time Payment
	13.75%
	Early Payment
	Late Payment
	8.67%
	On-time Payment
	On-time Payment
	57.37%
	On-time Payment
	Early Payment
	37.60%
	On-time Payment
	Late Payment
	5.04%
	Late Payment
	Early Payment
	62.39%
	Late Payment
	Late Payment
	21.62%
	Late Payment
	On-time Payment
	15.99%
	The results show that early payment is the most frequent recorded activity. Among transitions following a late payment, the next recorded activity is early payment in approximately 62.39% of cases. This is a descriptive transition pattern, not evidence that late payments cause subsequent early payments or that customers have permanently recovered from payment difficulties.
Observed payment spans
Metric
	Result
	Minimum observed span
	0 days
	Median observed span
	246 days
	75th percentile
	337 days
	90th percentile
	607 days
	95th percentile
	779 days
	99th percentile
	2,685 days
	Maximum observed span
	3,339 days
	Across all cases, 313,271 cases contain at least one late payment event, and 450,841 contain more than one payment-timing activity.
The extreme-case audit identified 100 cases at or above the reported 99th-percentile threshold. Their observed spans ranged from 2,922 to 3,339 days. The median event count among these cases was 126.5, and 64 cases contained at least one late payment event.
These extreme cases warrant further investigation, but their long observed spans alone do not establish delinquency severity, default, or financial distress.
Repository Structure
03_home_credit_process_mining/
├── data/
│   ├── raw/
│   │   ├── application_train.csv
│   │   ├── previous_application.csv
│   │   └── installments_payments.csv
│   └── processed/
│       └── payment_event_log.parquet
├── src/
│   ├── 01_inspect_data.py
│   ├── 02_explore_data.py
│   ├── 03_profile_installment.py
│   ├── 04_audit_loan_cases.py
│   ├── 05_inspect_duplicate_patterns.py
│   ├── 06_build_event_log.py
│   ├── 07_validate_event_log.py
│   ├── 08_analyze_payment_traces.py
│   ├── 09_transition_analysis.py
│   ├── 10_analyze_case_durations.py
│   ├── 11_create_case_visualizations.py
│   ├── 12_audit_extreme_cases.py
│   ├── 13_inspect_extreme_cases.py
│   └── 14_build_project_findings.py
├── outputs/
│   ├── figures/
│   │   ├── payment_events_per_case.png
│   │   └── observed_payment_span_distribution.png
│   └── reports/
├── .gitignore
├── README.md
└── requirements.txt


The structure above describes the intended project layout. Raw data, generated Parquet files, and selected large intermediate outputs are excluded from Git to keep the repository manageable. Some files shown in the structure must therefore be generated locally.
Technologies
* Python — analysis and workflow orchestration.
* Polars — tabular data processing and aggregation.
* Matplotlib — data visualization.
* Parquet — storage of the processed event log.
* Git and GitHub — version control and project publication.
The project uses Polars rather than pandas for its tabular data-processing workflow.
Reproducibility
Requirements
The project dependencies are specified in requirements.txt. The current pinned versions include:
* Polars 2.0.0
* Matplotlib 3.11.2
Python 3.14.7 was used in the development environment. Compatibility with other Python versions has not yet been independently verified.
Setup
Run these commands from the project root.
Create and activate a virtual environment:
python -m venv .venv
.\.venv\Scripts\Activate.ps1


Install the project dependencies:
python -m pip install -r requirements.txt


Place the three raw CSV files in data/raw/.
Run the analysis
Execute the scripts in numerical order from the project root:
python .\src\01_inspect_data.py
python .\src\02_explore_data.py
python .\src\03_profile_installment.py
python .\src\04_audit_loan_cases.py
python .\src\05_inspect_duplicate_patterns.py
python .\src\06_build_event_log.py
python .\src\07_validate_event_log.py
python .\src\08_analyze_payment_traces.py
python .\src\09_transition_analysis.py
python .\src\10_analyze_case_durations.py
python .\src\11_create_case_visualizations.py
python .\src\12_audit_extreme_cases.py
python .\src\13_inspect_extreme_cases.py
python .\src\14_build_project_findings.py


Run the scripts sequentially because later stages depend on outputs created by earlier stages. The raw data must be available locally before starting. Generated files are written to data/processed/ and outputs/.
The scripts have passed a Python syntax compilation check in the development environment. A clean-environment, end-to-end execution has not yet been established as part of the published repository.
Limitations
This project has several important limitations.
1. Partial process coverage. The event log focuses on recorded installment payments. It does not reconstruct the full process from application and approval through disbursement, repayment completion, and loan closure.
2. Relative time only. The dataset's day variables are relative-day measures. The artificial event timestamp preserves ordering but is not an actual calendar timestamp.
3. Repeated installment keys. Multiple records can share the same loan, installment number, and schedule version. These records may represent multiple payment entries, so interpreting each event as a separate installment would be incorrect.
4. Activity abstraction. Early, on-time, and late payment categories are derived from the difference between recorded payment and scheduled installment days. They do not capture all aspects of payment amount, outstanding balance, or contractual delinquency.
5. Descriptive analysis. Transition frequencies and probabilities describe observed records. They do not establish causal relationships, customer risk, or future default likelihood.
6. Extreme-case interpretation. Long observed spans may reflect the structure and coverage of recorded data. Further investigation is needed before assigning substantive explanations to these cases.
7. No full process-mining conformance analysis. The current project emphasizes event-log preparation, trace variants, transitions, durations, and exploratory audits. It does not claim to provide a complete conformance-checking or process-discovery evaluation.
Future Improvements
Potential extensions include:
* Incorporating additional loan lifecycle events where suitable data is available.
* Distinguishing scheduled installments from individual payment transactions more explicitly.
* Investigating payment amounts, partial payments, and outstanding balances.
* Comparing payment patterns across customer and loan characteristics, subject to data quality and appropriate controls.
* Applying formal process discovery and conformance-checking methods.
* Evaluating whether process features provide useful incremental information for credit-risk analysis, with suitable validation and safeguards.
These extensions would require additional methodological work and should not be treated as results already established by the current project.
Research and Portfolio Relevance
This project demonstrates practical skills in data quality assessment, event-log engineering, temporal ordering, sequence analysis, transition-probability estimation, exploratory visualization, and reproducible analytical documentation.
It also illustrates the importance of distinguishing observable transaction records from inferred business processes. This foundation can support further research at the intersection of financial services, process mining, financial inclusion, and data-driven credit analysis.
The project is an exploratory portfolio study and is not presented as a validated credit-scoring system or a causal research study.
License and Data Use
The source data is not redistributed in this repository. Users should obtain the dataset from its original distribution platform and comply with its applicable terms. No separate license for the underlying dataset is implied by this project's code or documentation.
________________


Author: Adyan Setiawan Hapitana
Project: Home Credit Payment Process Mining
Focus areas: Process Mining · Financial Data Analytics · FinTech · Credit Processes