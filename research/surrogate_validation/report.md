# Surrogate-method validation: wave significance tests stopped

**The proposed null methods have unresolved validity problems.** Following the requested stop rule, no wave-data pilot or 199-surrogate analysis was run. `wave_significance_status.csv` retains all six original Step 7 values, including negative Stockton period CMI, with B=0 and p-values/adjusted p-values missing. No wave surrogate distributions exist; the plots here show synthetic validation only.

## What passed

The exact Step 7 jar/settings were verified. Every synthetic surrogate was loaded into a fresh Java calculator with the same elapsed-hour indices and set ID. All observations were retained, and actual nearest-neighbour searches respected the 45-hour exclusion. Eight automated tests passed. Hash checks confirm Step 7 estimates, datasets and autocorrelation artifacts are unchanged.

Runtime inspection of JIDT found that MI's optimized default path rearranges Hn while preserving custom time indices. The CMI `computeSignificance` wrapper shuffles variable 1 (or 2 if requested) but rebuilds compressed row-based time indices; its single-reordering optimized method preserves them. The across-gap 46-hour candidate was incorrectly excluded inside the CMI wrapper. Explicit timestamp-aware reloads avoid this computational problem.

## Why full testing stopped

**MI:** Large exact-hour circular shifts can preserve temporal ordering under stationarity/circular-boundary assumptions, but neither real missingness mask admits a shift preserving all retained observations. Swapping weekly blocks with identical gap patterns would leave all Figure Eight Pools observations and 92% of Stockton observations aligned. Compressing gaps or changing the matched sample would not test the requested unchanged full record.

**CMI:** A Runge (2018) Algorithm 1 candidate samples local donors among five neighbours in Ho, moving both direction components together. It approximately preserves source–Ho association, but donor reuse means it is not an exact permutation, and it does not preserve source autocorrelation. In autocorrelated conditional-null simulations, period one-hour ACF fell from 0.974 to 0.397, and direction-cosine ACF from 0.932 to 0.330. The Theiler window does not fix the resulting null-model mismatch.

The synthetic pilot used 20 surrogates for each of 192 generated tests spanning known independence/conditional independence/dependence, independent and AR(1) rho=0.98 processes, and missing hourly observations. These 16 repetitions per scenario showed useful dependence detection but are too few to establish calibrated type-I error. They neither prove validity nor demonstrate statistically established false-positive inflation. No wave significance claim follows.

## Defensible next options

1. Retain the six Step 7 estimates as descriptive results.
2. Define a separately labelled regular-segment or common-overlap testing analysis; this changes the tested observations and requires its own observed statistic.
3. Develop and calibrate a conditional time-series null model that preserves predictor–height associations and residual temporal dynamics, accepting the added modelling assumptions.

More surrogates or Holm correction cannot cure a misspecified null. There are no valid wave p-values to adjust, and no between-site significance claim is made.

See [detailed methodology and validation results](methodology.md), [six-test status CSV](wave_significance_status.csv), [runtime audit](jidt_runtime_surrogate_audit.csv), [synthetic summary](validation/synthetic_summary.csv), and [validation gate](validation_gate.json). Reproduce with `python3 src/validate_surrogate_methods.py`, then `python3 src/report_surrogate_validation.py`.
