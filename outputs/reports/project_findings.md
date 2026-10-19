# Home Credit Payment Process Mining

## 1. Project Overview

This project applies process-mining concepts to Home Credit payment records. It examines observed payment-event sequences, transitions between payment-timing categories, case-level event counts, and the observed span between recorded payment events.

The analysis is descriptive. It identifies patterns in the available records and does not establish causal relationships or determine whether a loan was ultimately repaid successfully.

## 2. Research Questions

1. What payment-timing patterns appear in the recorded loan cases?
2. How frequently do Early, On-time, and Late Payment events follow one another?
3. How many payment events are recorded per loan case, and how long is the observed span between its first and last recorded payment?
4. What characteristics appear among cases with exceptionally long observed payment spans?

## 3. Dataset and Event Log

The project uses three Home Credit dataset files:

- `application_train.csv`: customer application and target information.
- `previous_application.csv`: historical loan application records.
- `installments_payments.csv`: installment and payment records.

The event log is built from installment-payment records with a non-missing payment-entry day. Each case is identified by `SK_ID_PREV`, representing a previous loan, and each event is classified according to the difference between the payment-entry day and the scheduled installment day.

| Measure | Result |
| --- | --- |
| Recorded payment events | 13,602,496 |
| Loan cases | 997,674 |
| Mean events per case | 13.63 |
| Median events per case | 10.00 |
| Maximum events in one case | 293 |

## 4. Methodology

### 4.1 Payment-event classification

Payment delay is calculated as:

`payment_delay_days = DAYS_ENTRY_PAYMENT - DAYS_INSTALMENT`

- **Early Payment:** payment-entry day precedes the scheduled day.
- **On-time Payment:** payment-entry day equals the scheduled day.
- **Late Payment:** payment-entry day follows the scheduled day.

### 4.2 Event ordering and transitions

Events are ordered within each loan case using the recorded payment-entry day. Transition counts describe adjacent recorded events within the same case. Because an installment can have multiple payment records, a transition does not necessarily represent movement between two distinct installments.

Transition probabilities are calculated conditionally on the previous activity. For each previous activity, the probability of a next activity is its transition count divided by the total outgoing transitions from that previous activity.

### 4.3 Observed payment span

Observed payment span is calculated as the last recorded payment day minus the first recorded payment day for each case. The event timestamps use an artificial reference date to preserve relative day ordering. They are not actual calendar dates.

The observed span must not be interpreted as confirmed loan tenure or the complete duration of a loan.

## 5. Key Findings

### 5.1 Case-level payment patterns

| Measure | Result |
| --- | --- |
| Total loan cases | 997,674 |
| Total recorded events | 13,602,496 |
| Mean events per case | 13.63 |
| Median events per case | 10.00 |
| Maximum events per case | 293 |
| Cases with at least one late event | 313,271 |
| Cases with multiple activity types | 450,841 |
| Cases with only one activity type | 546,833 |
| Cases linked to multiple customers | 0 |

The event-count distribution is shown below.

| Events per Case | Number of Cases |
| --- | --- |
| 1 event | 28,098 |
| 2-5 events | 186,217 |
| 6-10 events | 354,292 |
| 11-20 events | 293,449 |
| >20 events | 135,618 |

### 5.2 Observed payment spans

| Measure | Observed Span (Days) |
| --- | --- |
| Mean | 325.86 |
| Median | 246.00 |
| 75th percentile | 337.00 |
| 90th percentile | 607.00 |
| 95th percentile | 779.00 |
| 99th percentile threshold | 2,685.00 |
| Maximum | 3,339 |
| Cases at or above the P99 threshold | 9,998 |

The upper tail contains cases whose recorded payment events span substantially longer periods than those of most cases. These cases are candidates for further data-quality and process investigation, not automatic evidence of delinquency or default.

### 5.3 Payment-event transitions

The most frequent adjacent-event transitions are listed below.

| Previous Activity | Next Activity | Transition Count |
| --- | --- | --- |
| Early Payment | Early Payment | 6,627,059 |
| On-time Payment | On-time Payment | 1,720,770 |
| Early Payment | On-time Payment | 1,174,016 |
| On-time Payment | Early Payment | 1,127,767 |
| Early Payment | Late Payment | 740,139 |
| Late Payment | Early Payment | 663,836 |
| Late Payment | Late Payment | 229,983 |
| Late Payment | On-time Payment | 170,153 |
| On-time Payment | Late Payment | 151,099 |

Transition probabilities conditional on the previous activity are shown below.

| Previous Activity | Next Activity | Transition Count | Transition Probability (%) |
| --- | --- | --- | --- |
| Early Payment | Early Payment | 6,627,059 | 77.59 |
| Early Payment | On-time Payment | 1,174,016 | 13.75 |
| Early Payment | Late Payment | 740,139 | 8.67 |
| Late Payment | Early Payment | 663,836 | 62.39 |
| Late Payment | Late Payment | 229,983 | 21.62 |
| Late Payment | On-time Payment | 170,153 | 15.99 |
| On-time Payment | On-time Payment | 1,720,770 | 57.37 |
| On-time Payment | Early Payment | 1,127,767 | 37.60 |
| On-time Payment | Late Payment | 151,099 | 5.04 |

These results describe observed sequences in the event log. They should not be interpreted as causal effects or as probabilities of future customer behavior.

### 5.4 Extreme observed-span cases

| Measure | Result |
| --- | --- |
| Cases reviewed | 100 |
| Minimum span in reviewed cases (days) | 2,922 |
| Median span in reviewed cases (days) | 2,924.00 |
| Maximum span in reviewed cases (days) | 3,339 |
| Mean events per reviewed case | 131.29 |
| Median events per reviewed case | 126.50 |
| Maximum events in a reviewed case | 204 |
| Mean activity types per reviewed case | 2.62 |
| Reviewed cases with late events | 64 |

The extreme-case sample contains up to 100 cases selected from the longest observed spans. It is a targeted sample and is not representative of the full population of loan cases.

## 6. Interpretation and Limitations

The analysis provides a descriptive view of recorded payment behavior. Several limitations are important:

1. **Recorded events are not necessarily distinct installments.** Repeated records may reflect multiple payment entries associated with one installment. They should not be removed without a well-supported business rule.
2. **The event log is based on available payment records.** Cases with no non-missing payment-entry day are not represented in the event log.
3. **Relative days are not actual calendar dates.** The artificial timestamp is used only to order events and does not identify the real-world date of a payment.
4. **Observed span is not confirmed loan tenure.** The first and last recorded events may not correspond to loan origination and final settlement.
5. **Payment timing alone does not establish default.** An observed late event is not sufficient to determine credit risk, loss, or final repayment outcome.
6. **The analysis is descriptive rather than causal.** The results do not demonstrate why payment timing occurs or whether one event causes another.
7. **The extreme-case review is selective.** Its findings should not be generalized to all cases.

## 7. Reproducibility

The analysis scripts are located in the `src/` directory. Input datasets are expected in `data/raw/`, derived event data in `data/processed/`, and generated reports and figures in `outputs/`.

Install the pinned dependencies from the project root:

```powershell
python -m pip install -r requirements.txt
```

Run the project scripts in numerical order to reproduce the analysis. The raw datasets and generated Parquet event log are excluded from version control; users must obtain the original dataset files separately and place them in the expected directory.

## 8. Future Improvements

- Use a process-mining library to discover and visualize process models.
- Investigate repeated installment records and partial-payment patterns.
- Compare payment-event behavior across customer and loan segments.
- Evaluate alternative case identifiers and event definitions.
- Add sensitivity checks for missing payment records and extreme cases.
- Explore predictive modeling only after defining a defensible target and a leakage-resistant validation strategy.

## 9. Conclusion

This project demonstrates a reproducible workflow for constructing a payment-event log, validating loan cases, examining event sequences, estimating transition probabilities, and auditing extreme observed spans. The findings are useful as exploratory evidence for further process-mining research, while the limitations highlight the need for careful event definitions and business interpretation.
