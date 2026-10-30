# Temporal autocorrelation and Theiler window

**Subsequent integration update:** The supplied JIDT 1.6.1 jar lacks the newer elapsed-time tracking API described below. Actual MI/CMI runs use an explicitly conservative retained-row exclusion and quantify its additional exclusions across gaps. See [the completed analysis report](information_analysis_report.md). The ACF results and 45-hour physical-timescale recommendation are unchanged.

Run `python3 src/autocorrelation.py` after preprocessing. The default maximum lag is 336 hours (14 days); use `--max-lag-hours` to change it.

## Method

The five diagnostics use the matched, complete, quality-filtered observations: Ho, Hn, offshore Tp_o, and the two components Dx and Dy of one directional variable. For each integer lag h from 0 to 336 hours, correlate observed x(t) with observed x(t+h), using the exact UTC timestamps. Only endpoint pairs that both exist are used; intervening missing hours do not invalidate a pair. No missing values are filled. Pearson correlation uses the lag-specific endpoint means and variances. Consequently this is a pairwise-complete descriptive ACF, not the fixed-denominator complete-record ACF. Pair counts are saved for every lag. Missingness can affect which conditions contribute at different lags.

A supported lag has at least max(100, ceil(10% of the lag-zero sample size)) endpoint pairs. The decay estimate is the first lag starting six consecutive supported hourly lags with |ACF| <= 1/e (about 0.368). The absolute threshold avoids interpreting a strong negative correlation as decorrelation; the six-hour requirement avoids isolated crossings. These are explicit practical choices, not a unique optimal rule. A series without a crossing is reported as unresolved rather than assigned a guessed window. First threshold crossings and first nonpositive correlations are also saved; missing crossings in the CSV mean they were not observed in the searched range.

## Results

| Variable | Figure Eight Pools decay (hours) | Stockton decay (hours) |
|---|---:|---:|
| Ho | 30 | 41 |
| Hn | 29 | 45 |
| Tp_o | 16 | 17 |
| Dx | 19 | 21 |
| Dy | 16 | 19 |

All crossings meet the pair-count and six-hour requirements. Figure Eight Pools has 6,867 observations in 378 uninterrupted hourly runs; Stockton has 10,522 observations in 265 runs. The per-site window is the maximum decay across all five variables: 30 and 45 hours respectively. Use the common maximum, **45 hours**, as a baseline for both sites and all three MI/CMI measures so the comparison uses the same exclusion rule. Planned sensitivity windows are **0, 23, 45, and 90 hours**. These are settings for later estimation, not MI/CMI results.

This e-folding rule targets the dominant short-term persistence, not complete independence. Dependence remains below the threshold and may recur at longer lags; period does not reach zero within 336 hours at Figure Eight Pools. Long-term variation, seasonal structure and missingness remain limitations. Theiler exclusion does not make standard shuffled surrogates preserve autocorrelation.

## Applying the window in JIDT

The official CPU Kraskov source defines the property `DYN_CORR_EXCL`. Its neighbour searches use observation-set IDs and observation time indices: candidates in the same set whose absolute time-index separation is <= the window are excluded. It is not inherently a wall-clock duration. Ordinary `setObservations` on compressed retained rows would turn this into a row-count window.

`src/jidt_timing.py` supplies a loader for initialized MI and CMI calculators. It splits rows into consecutive hourly runs, calls `startAddObservations`, then `addObservationsTrackObservationIDs` for each run with the SAME observation-set ID (0) and its ACTUAL elapsed-hour start index, and finishes with `finaliseAddObservations`. A two-hour or multi-day gap therefore retains its real spacing. Assigning a different trial/set ID to every run would incorrectly permit neighbours across even a short gap. GPU mode is disabled because this review verified the CPU time-index path. Already aligned MI uses `TIME_DIFF=0`; future physical lags must first be matched using timestamps and the mapping regenerated on those tuples.

Example after constructing and initializing a JIDT calculator and starting JPype:

```python
from jidt_timing import load_observations
as_java = lambda a: jpype.JArray(jpype.JDouble, 2)(a.tolist())
# MI: calculator.initialise(1, 1)
load_observations(calculator, data.timestamp_utc,
                  [data[['Ho']], data[['Hn']]], 45, as_java)
# Direction CMI: calculator.initialise(2, 1, 1)
load_observations(calculator, data.timestamp_utc,
                  [data[['Dx', 'Dy']], data[['Hn']], data[['Ho']]], 45, as_java)
```

`{site}_jidt_time_indices.csv` saves a timestamp-to-elapsed-hour audit mapping. No padded values or NaNs are passed to JIDT. The helper rejects off-grid, duplicate, unsorted or invalid timestamps rather than rounding them. Both direction components remain together.

The Java source/API semantics were inspected on 30 October 2026. The repository contains no JIDT jar, so Java runtime integration has not been executed. Before MI/CMI estimation, verify that the installed JIDT version exposes this API and run an integration check of the stored observation time indices; the helper fails if the tracking method is unavailable. Python tests verify actual-time ACF pairing, sustained crossing selection, off-grid rejection and MI/CMI loader calls with gaps.

Sources:

- [MI observation loading and time tracking](https://github.com/jlizier/jidt/blob/master/java/source/infodynamics/measures/continuous/MutualInfoMultiVariateCommon.java)
- [CMI observation loading and time tracking](https://github.com/jlizier/jidt/blob/master/java/source/infodynamics/measures/continuous/ConditionalMutualInfoMultiVariateCommon.java)
- [CPU nearest-neighbour temporal exclusion](https://github.com/jlizier/jidt/blob/master/java/source/infodynamics/utils/KdTree.java)
- [Kraskov MI properties](https://github.com/jlizier/jidt/blob/master/java/source/infodynamics/measures/continuous/kraskov/MutualInfoCalculatorMultiVariateKraskov.java)
