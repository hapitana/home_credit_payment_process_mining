# Home Credit Payment Process Mining

## 1. Project Overview

This project examines recorded payment behavior using the Home Credit dataset. It applies event-log construction, case-level profiling, trace analysis, transition analysis, and descriptive duration analysis.

The current scope focuses on payment records from installments_payments.csv. It does not reconstruct the complete loan lifecycle from application through approval, disbursement, and closure.

## 2. Data and Event Log

- Loan cases represented in the event log: *997,674*
- Recorded payment events: *13,602,496*
- Mean events per case: *13.63*
- Median events per case: *10*
- Maximum events in a case: *293*

The case identifier is SK_ID_PREV, representing a previous loan. The customer identifier is SK_ID_CURR. Recorded events are categorized as Early Payment, On-time Payment, or Late Payment using the difference between payment-entry days and scheduled installment days.

The event-log timestamp is an artificial date derived from relative payment days. It preserves event ordering and is not an actual calendar date.

## 3. Payment Event Distribution

| Event-count group | Loan cases |
|---|---:|
| 1 event | 28,098 |
| 2-5 events | 186,217 |
| 6-10 events | 354,292 |
| 11-20 events | 293,449 |
| More than 20 events | 135,618 |

Event counts should not be interpreted as completed installment counts, because a single installment can have multiple recorded payment entries.

## 4. Payment Transition Analysis

Transition percentages describe the distribution of the next recorded payment category conditional on the previous recorded category. They are descriptive transition frequencies, not causal effects or customer-level default probabilities.


### Transitions following Early Payment

| Next activity | Observed transitions | Percentage |
|---|---:|---:|
| Early Payment | 6,627,059 | 77.59% |
| On-time Payment | 1,174,016 | 13.75% |
| Late Payment | 740,139 | 8.67% |

### Transitions following On-time Payment

| Next activity | Observed transitions | Percentage |
|---|---:|---:|
| On-time Payment | 1,720,770 | 57.37% |
| Early Payment | 1,127,767 | 37.60% |
| Late Payment | 151,099 | 5.04% |

### Transitions following Late Payment

| Next activity | Observed transitions | Percentage |
|---|---:|---:|
| Early Payment | 663,836 | 62.39% |
| Late Payment | 229,983 | 21.62% |
| On-time Payment | 170,153 | 15.99% |

## 5. Observed Payment Spans

| Metric | Result |
|---|---:|
| Median observed span | 246 days |
| 75th percentile | 337 days |
| 90th percentile | 607 days |
| 95th percentile | 779 days |
| 99th percentile | 2,685 days |
| Maximum observed span | 3,339 days |

Observed span is the difference between the first and last recorded payment days in a case. It is not confirmed loan tenure or the time between actual loan opening and closure.

## 6. Late Payment Events

- Cases with at least one late payment event: *313,271*
- Share of all cases: *31.40%*
- Cases containing multiple payment activity types: **450,841 (45.19%)**
- Cases linked to multiple customer identifiers: *0*

A late payment event is a recorded payment with payment_delay_days > 0. This does not establish that the customer defaulted or that the loan was classified as non-performing.

## 7. Extreme Case Audit

- Cases reviewed in the extreme-span sample: *100*
- Median span within that sample: *2,924 days*
- Maximum span within that sample: *3,339 days*
- Median events per case in that sample: *126.5*
- Maximum events per case in that sample: *204*
- Sample cases with at least one late payment event: *64*

The extreme-case sample was selected by observed payment span. It is not representative of the full dataset, and the analysis does not establish why these cases have long spans.

## 8. Trace Analysis

- Cases included in trace analysis: *997,674*
- Unique observed trace variants: *196,042*
- Mean events per case: *13.63*
- Median events per case: *10.00*

The following table lists up to ten frequent trace variants. Each trace is a sequence of recorded payment categories within a loan case.

| Cases | Mean events | Payment-category sequence |
|---:|---:|---|
| 87,551 | 6.00 | Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment |
| 57,017 | 12.00 | Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment |
| 52,811 | 4.00 | Early Payment -> Early Payment -> Early Payment -> Early Payment |
| 52,492 | 10.00 | Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment |
| 42,420 | 5.00 | Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment |
| 30,526 | 8.00 | Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment |
| 27,549 | 3.00 | Early Payment -> Early Payment -> Early Payment |
| 26,750 | 9.00 | Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment |
| 26,148 | 7.00 | Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment -> Early Payment |
| 22,897 | 1.00 | Early Payment |

The most frequent traces are dominated by Early Payment categories. These sequences describe the recorded event log and should not be interpreted as full loan workflows or proof of customer behavior across all installments.

### Most Frequent Adjacent Activity Transitions

| Adjacent activity transition | Count |
|---|---:|
| Early Payment -> Early Payment | 6,627,059 |
| On-time Payment -> On-time Payment | 1,720,770 |
| Early Payment -> On-time Payment | 1,174,016 |
| On-time Payment -> Early Payment | 1,127,767 |
| Early Payment -> Late Payment | 740,139 |
| Late Payment -> Early Payment | 663,836 |
| Late Payment -> Late Payment | 229,983 |
| Late Payment -> On-time Payment | 170,153 |
| On-time Payment -> Late Payment | 151,099 |

Events are ordered by relative payment day, installment number, and installment version. The secondary sort fields make ordering reproducible, but do not establish the true order of events with identical payment days. Repeated payment entries may mean that adjacent events do not correspond to distinct installments.

## 9. Limitations

1. The event log focuses on payment records rather than the full loan lifecycle.
2. Event timestamps encode relative days and are not actual calendar dates.
3. Multiple records may exist for one installment, including partial or multiple payment entries.
4. Payment categories are derived from recorded timing differences and should not be treated as formal credit-risk or default labels.
5. Transition percentages are descriptive and do not imply causation.
6. Extreme cases require contextual investigation; they should not be removed without a defensible data-quality reason.

## 10. Reproducibility and Outputs

Key outputs include:

- data/processed/payment_event_log.parquet
- outputs/reports/payment_trace_variants.csv
- outputs/reports/payment_transitions.csv
- outputs/reports/payment_transition_probabilities.csv
- outputs/reports/payment_case_duration_summary.csv
- outputs/reports/extreme_payment_span_cases.csv
- outputs/figures/payment_events_per_case.png
- outputs/figures/observed_payment_span_distribution.png

## 11. Conclusion

The analysis demonstrates how payment-level data can be transformed into an event log and used to examine case variation, payment-category transitions, observed spans, and extreme cases. The findings are exploratory and descriptive. Further work should validate installment semantics, examine payment sequences at the installment level, and extend the event log only where reliable lifecycle events are available.

## Appendix: Extreme-Span Audit

- *Total cases:* 997,674
- *Minimum observed span:* 0 days
- *Median observed span:* 246 days
- *75th percentile:* 337 days
- *90th percentile:* 607 days
- *95th percentile:* 779 days
- *99th percentile:* 2,685 days
- *Maximum observed span:* 3,339 days
- *Cases at or above the 99th percentile threshold:* 100
The exported CSV contains up to 100 cases with the longest observed spans.

