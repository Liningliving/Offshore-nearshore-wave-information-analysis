# Focused JIDT 45-hour integration check

**Acceptance result: FAILED for exact elapsed-hour exclusion with the supplied JIDT 1.6.1 jar.** Java integration itself works, but a 45-row window does not implement the required 45-hour eligibility rule across gaps. No main-data MI/CMI calculations or autocorrelation analysis were rerun in this check.

## Environment and settings

Java and javac are available (OpenJDK 21.0.12.1). Python successfully compiled and executed Java against `/Users/attie/Desktop/Information theory/jidt-1.6.1/infodynamics.jar` through `subprocess`. JPype is not installed; this does not prevent Python-controlled Java execution, but an in-process JPype bridge was not tested.

Jar SHA-256: `2d367c244b729877fdaf0608884cf97ae964a8035c3020215b799812143a5b11`.

The actual MI and CMI Java instances return `k=4` and `DYN_CORR_EXCL=45` from `getProperty`. Test subclasses also inspect the protected `k`, `dynCorrExclTime` and `dynCorrExcl` fields, confirming that the active values are 4, 45 and true. This is Java runtime evidence, not a Python settings dictionary. Period CMI was checked as well as direction CMI. CPU execution and zero internal noise were used for the synthetic test.

## Timestamp handling and source review

The installed 1.6.1 `KdTree.java`, lines 703–704 and 1076, tests distance between sample row indices. Its constructors do not accept observation-set or time-point arrays. Runtime reflection confirms that neither MI nor CMI has `observationSetIndices`, `observationTimePoints`, or `addObservationsTrackObservationIDs`, including inherited fields/methods. Therefore there is no actual stored timestamp-derived time index to compare in this version: the effective JIDT index is the retained row number. `observation_indices.csv` records this effective row index beside the expected elapsed-hour index.

Both Kraskov calculator implementations reject multiple observation sets with dynamic exclusion enabled. This was reproduced by loading two synthetic segments through start/add/finalise calls. Thus different-set temporal bypass cannot be exercised in this installed version: the calculation fails first.

For comparison, the [current upstream KdTree source](https://github.com/jlizier/jidt/blob/master/java/source/infodynamics/utils/KdTree.java), lines 739–740, uses:

```
set_i != set_j OR abs(time_i - time_j) > window
```

In that implementation, different observation sets bypass temporal exclusion even if their timestamps are within 45 hours. Continuous segments of one site's series must therefore retain the SAME set ID and actual elapsed-hour start indices across gaps. This is a source-level finding for upstream code, not a runtime test of an installed newer jar.

The existing `src/jidt_timing.py` follows that newer-API design: it partitions hourly runs, uses set ID 0 for every run, and uses timestamp-derived starts. It explicitly rejects a calculator lacking the tracking method. It cannot load this 1.6.1 jar, and its Python mock tests must not be treated as evidence that elapsed-hour exclusion works here. The prior Java main runner does not use that helper: it passes a single compressed array to `setObservations`, which is why it uses row-based exclusion.

## Synthetic Java runtime test

The synthetic record contains 240 observations at elapsed hours 0–79, 90–169 and 240–319: one short gap and one long gap. MI, period CMI and joint-direction CMI all execute and retain exactly 240 observations. Direction is passed to `initialise(2,1,1)` as a single two-column array `[cos(theta), sin(theta)]`, with Hn as variable 2 and Ho as the one-dimensional condition. Period CMI uses dimensions `(1,1,1)`.

The test inspects the calculators' actual joint k-d trees. An infinite-radius query exposes all temporally eligible candidate neighbours, independently of which four are ultimately nearest in value space. Every pair is compared against the required elapsed-time rule. MI, period CMI and direction CMI produce identical temporal eligibility masks.

| Elapsed-hour pair | Time separation | Retained-row separation | Required eligibility | Actual 1.6.1 eligibility |
|---|---:|---:|---|---|
| 0 → 45, continuous segment | 45 h | 45 | Excluded | Excluded: PASS |
| 0 → 46, continuous segment | 46 h | 46 | Eligible | Eligible: PASS |
| 79 → 90, short gap | 11 h | 1 | Excluded | Excluded: PASS |
| 79 → 124, across gap | 45 h | 35 | Excluded | Excluded: PASS |
| 79 → 125, across gap | 46 h | 36 | Eligible | Excluded: FAIL |
| 169 → 240, long gap | 71 h | 1 | Eligible | Excluded: FAIL |

Across all 28,680 unordered distinct pairs, **1,440 pairs were incorrectly excluded** relative to the exact-hour requirement. No pair within 45 hours was incorrectly allowed. This demonstrates conservative over-exclusion, not a correct exact-hour implementation. It does not imply conservative information estimates or p-values.

`pair_eligibility.csv` contains all pair-level results; `java_results.json` contains the settings, counts, API checks and finite synthetic MI/CMI outputs. Successful synthetic information calculation does not override the failed timestamp criterion.

## Minimal correction and scope

The main Python analysis runner now stops by default before launching Java, explaining that exact 45-hour integration has failed. Its explicit `--allow-conservative-index-window` option is available only to reproduce the previously labelled row-window approximation; it is not a fix for physical-time exclusion. `main_guard_test.json` records that the default pilot exits with status 2 before main analysis. Earlier main-data results remain on disk as approximate row-window results, not accepted exact-hour results.

No modification to the jar or estimator was attempted. Exact elapsed-hour integration requires a compatible implementation with real time-index support and the same synthetic acceptance test. Upgrading or implementing such support remains outstanding; this check does not certify any untested newer version.

The cleaned datasets and selected window files were SHA-256 checked before and after execution and are unchanged (`python_execution.json`). The common baseline remains **45 hours**. No interpolation, data removal, additional statistical analysis or change to the two-site design was made.

Reproduce only this focused check:

```
python3 src/check_theiler_integration.py
```

Exit status 1 is intentional when the exact-hour acceptance criterion fails. A Java execution/compilation error would instead be recorded as an unavailable/failed runtime test in `python_execution.json`; it would not count as proof of correctness.
