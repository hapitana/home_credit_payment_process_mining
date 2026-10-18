Home Credit Payment Process Mining



Project Overview



This project applies process mining and event-log analysis techniques to payment records from the Home Credit Default Risk dataset. It explores payment timing patterns, observed case sequences, transitions between payment categories, and unusually long observed payment spans.



The project demonstrates a reproducible data analytics workflow using Python, Polars, and Parquet, with an emphasis on data quality, event-log construction, descriptive analysis, and transparent methodological limitations.



Research Objectives



The project addresses the following exploratory questions:



1\. How are recorded payment events distributed across loan cases?

2\. What payment-category sequences and trace variants occur most frequently?

3\. How often do payment categories change between adjacent recorded events?

4\. How much variation exists in the observed payment span across cases?

5\. Which extreme-span cases require further data-quality and contextual investigation?



These questions are descriptive. The analysis does not establish causal relationships or predict loan default.



Dataset



The analysis uses three source tables from the Home Credit Default Risk dataset:



\- "application\_train.csv"

\- "previous\_application.csv"

\- "installments\_payments.csv"



The current event log is constructed from "installments\_payments.csv". The other tables are retained for potential future extensions.



The source data are not included in this repository because of their size. Users must obtain the dataset from its original authorized distribution source and place the required files in "data/raw/".



Methodology



1\. Data inspection and quality assessment



The workflow inspects dataset schemas, missing values, identifier uniqueness, and repeated installment keys.



Repeated records are not automatically removed. Multiple records can represent multiple payment entries associated with an installment, so deduplication requires a defensible interpretation of the source data.



2\. Event-log construction



The payment event log uses the following fields:



\- Case ID: "SK\_ID\_PREV"

\- Customer ID: "SK\_ID\_CURR"

\- Event timing: "DAYS\_ENTRY\_PAYMENT"

\- Activity: Early Payment, On-time Payment, or Late Payment



Payment delay is calculated as:



"DAYS\_ENTRY\_PAYMENT - DAYS\_INSTALMENT"



Negative values indicate payment before the scheduled date, zero indicates payment on the scheduled date, and positive values indicate payment after the scheduled date.



The event-log timestamp is an artificial datetime representation derived from relative payment days. It is used to support event ordering and must not be interpreted as an actual calendar date.



Records without a recorded payment-entry day are excluded from the event log.



3\. Trace and transition analysis



The workflow examines case-level activity sequences, trace variants, and transitions between adjacent recorded events within each case.



Transition probabilities are calculated conditionally on the preceding activity. They describe observed sequences rather than causal mechanisms.



Because one installment may have multiple payment records, adjacent events do not necessarily represent different installments.



4\. Case-duration analysis



The observed payment span is calculated as the maximum relative payment day minus the minimum relative payment day within a case.



This measure describes the span of recorded payment events. It is not necessarily equivalent to contractual loan tenure or actual elapsed calendar time.



5\. Extreme-case audit



Cases with exceptionally long observed spans are identified and examined separately. Extreme observations are retained unless a defensible data-quality reason supports their exclusion.



Key Findings



The current analysis produced the following descriptive results:



Metric| Result

Recorded payment events| 13,602,496

Loan cases in the event log| 997,674

Customers represented in the event log| 339,578

Unique observed trace variants| 196,042

Mean events per case| 13.63

Median events per case| 10

Cases with at least one late-payment event| 313,271

Cases with multiple payment categories| 450,841

Mean observed payment span| 325.86 days

Median observed payment span| 246 days

Maximum observed payment span| 3,339 days



Payment-category distribution



Activity| Recorded events

Early Payment| 9,309,477

On-time Payment| 3,146,350

Late Payment| 1,146,669



Early Payment is the most frequently recorded category. These counts describe recorded payment entries and should not be interpreted as the percentage of loans that are financially healthy or low-risk.



Selected transition probabilities



Previous activity| Next activity| Probability

Early Payment| Early Payment| 77.59%

Early Payment| On-time Payment| 13.75%

Early Payment| Late Payment| 8.67%

On-time Payment| On-time Payment| 57.37%

On-time Payment| Early Payment| 37.60%

On-time Payment| Late Payment| 5.04%

Late Payment| Early Payment| 62.39%

Late Payment| Late Payment| 21.62%

Late Payment| On-time Payment| 15.99%



Percentages may not sum to exactly 100% because of rounding.



Visualizations



The project includes:



\- "outputs/figures/payment\_events\_per\_case.png"

\- "outputs/figures/observed\_payment\_span\_distribution.png"



These figures summarize the distribution of recorded events per case and the variation in observed payment spans.



Project Structure



03\_home\_credit\_process\_mining/

├── data/

│   ├── raw/

│   └── processed/

├── outputs/

│   ├── figures/

│   └── reports/

├── src/

│   ├── 01\_inspect\_data.py

│   ├── 02\_explore\_data.py

│   ├── 03\_profile\_installment.py

│   ├── 04\_audit\_loan\_cases.py

│   ├── 05\_inspect\_duplicate\_patterns.py

│   ├── 06\_build\_event\_log.py

│   ├── 07\_validate\_event\_log.py

│   ├── 08\_analyze\_payment\_traces.py

│   ├── 09\_transition\_analysis.py

│   ├── 10\_analyze\_case\_durations.py

│   ├── 11\_create\_case\_visualizations.py

│   ├── 12\_audit\_extreme\_cases.py

│   ├── 13\_inspect\_extreme\_cases.py

│   └── 14\_build\_project\_findings.py

├── .gitignore

└── README.md



Reproducibility



Requirements



The project was developed with Python and Polars. The analysis also uses supporting data and visualization libraries.



Install the dependencies used by the scripts in your Python environment. Check the imports in each script to confirm the complete dependency list before reproducing the workflow.



Run the analysis



1\. Obtain the authorized source dataset and place the required CSV files in "data/raw/".

2\. Run the numbered scripts in "src/" sequentially from the project root.

3\. Review the generated reports in "outputs/reports/".

4\. Review the figures in "outputs/figures/".



The later scripts depend on outputs generated by earlier scripts. Existing generated files may be overwritten when scripts are rerun.



The raw data and generated Parquet event log are excluded from Git tracking by ".gitignore".



Limitations



1\. The current event log represents recorded payment entries, not a fully reconstructed loan lifecycle.

2\. Repeated installment keys may represent multiple payment records; their precise semantics require further validation.

3\. The artificial timestamps preserve relative timing but do not represent actual calendar dates.

4\. Payment categories are derived from payment timing and are not formal default, delinquency-severity, or credit-risk labels.

5\. Transition probabilities and trace patterns are descriptive and do not imply causation.

6\. The extreme-span audit identifies observations for further investigation; it does not establish that these observations are erroneous.

7\. The findings depend on the source dataset, its recording practices, and the analysis scope.



Future Work



Potential extensions include:



\- Validating installment-level payment semantics and partial-payment behavior.

\- Comparing payment sequences across customer or loan characteristics.

\- Integrating reliable application and previous-loan attributes.

\- Evaluating alternative event definitions and sensitivity to event-log construction choices.

\- Investigating whether carefully defined process features provide additional information for a separately validated credit-risk modeling task.



Conclusion



This project demonstrates how payment-level records can be transformed into an event log and analyzed through process-oriented descriptive techniques. It provides a foundation for further work on financial process analytics, event-log quality, payment behavior, and responsible credit-risk research.



The findings should be interpreted as exploratory evidence about recorded payment patterns, not as causal conclusions or direct measures of borrower creditworthiness.

