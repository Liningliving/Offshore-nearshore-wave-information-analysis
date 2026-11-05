# Surrogate-method validation

## Outcome and scope

**Wave significance testing stopped because the candidate null methods had unresolved validity problems.** No wave-data surrogate pilot or 199-surrogate main analysis was run. The [six-test status table](wave_significance_status.csv) preserves the original primary estimates, including Stockton's negative period CMI, with zero wave surrogates and missing unadjusted and Holm-adjusted p-values. Missing p-values do not indicate non-significant results: these tests were not performed.

This investigation concerns within-site independence and conditional independence. It does not test the differences between Figure Eight Pools and Stockton. The final project retains descriptive site comparisons; no additional calibration or statistical method is proposed as part of the completed analysis. See the [scientific report](../../deliverables/final_scientific_report.md) and [between-site methodological assessment](../between_site_method_assessment/assessment.md).

## Estimator and computational checks

The saved validation used the same official-source JIDT snapshot as the primary analysis: commit `1ca832235e64ae5b3a482dc0ead6f9b2ff2a0456`. Settings remained KSG algorithm 1, k=4, normalization, max norm, exact 45-hour elapsed-time exclusion, GPU disabled, Gaussian noise of standard deviation 1e-8 after normalization, and noise seed 20261031. Direction components (Dx, Dy) were always handled jointly.

Every synthetic surrogate was loaded into a fresh Java calculator through the timestamp-aware loader, retaining the intended elapsed-hour indices, observation-set ID and observation count. Actual nearest-neighbour eligibility checks passed, including the separately audited 44/45/46-hour boundary across gaps. The saved validation records eight automated tests passing and preservation hashes for the original primary estimates, datasets and autocorrelation artifacts. These are historical validation results; no tests or estimator calculations were rerun for this report update.

The [runtime audit](jidt_runtime_surrogate_audit.csv) distinguishes JIDT code paths:

| JIDT path in the audited snapshot | Rearrangement and timestamp behaviour |
|---|---|
| MI default optimized significance path | Rearranges Hn and retains custom time/set indices; unrestricted shuffling destroys its temporal ordering |
| CMI `computeSignificance(variable, orders)` wrapper | Rearranges variable 1 by default (period or joint direction), but rebuilds compressed row-based time indices through ordinary `setObservations` |
| CMI optimized single-reordering calculation | Retains custom time/set indices |
| Explicit timestamp-aware reload used in validation | Retains the original time/set arrays for MI and CMI |

Inside the CMI significance wrapper, a candidate 46 elapsed hours away across a gap was incorrectly excluded; the timestamp-aware reload avoids that integration problem. Correct computational exclusion does not establish validity of the statistical null. Estimator noise seeds also do not control JIDT's default random-order generator; candidate donor maps used a separate seed base of 20261101.

## Candidate null methods and reasons for stopping

### Height MI

The null is independence between offshore height Ho and nearshore height Hn. Exact-hour circular shifts were considered with a minimum circular displacement of 180 hours. Such shifts approximately retain temporal structure under stationarity and circular-boundary assumptions, but preserving every retained observation also requires a compatible missingness mask.

Neither site's actual timestamp mask admits an admissible nonzero shift under this rule. Weekly rearrangements restricted to blocks with identical missingness patterns leave all 6,867 Figure Eight Pools observations and 9,688 of 10,522 Stockton observations aligned. This provides no adequate full-record independence null. Compressing missing hours would misrepresent elapsed time, while intersecting shifted timestamps would change the tested sample. See the [timestamp-mask audit](wave_timestamp_mask_audit.json).

### Period and direction CMI

The nulls are conditional independence of Tp_o and Hn given Ho, and of joint (Dx, Dy) and Hn given Ho. The investigated Runge-style local-donor method selects among five neighbours in offshore height, with direction components moving together. This surrogate neighbourhood is distinct from estimator k=4.

The method approximately preserves local source–Ho association and leaves Hn–Ho observations fixed while disrupting source–Hn pairing. Donor reuse means it is not an exact permutation and does not guarantee unchanged source marginals. It also fails to retain source temporal dynamics: in autocorrelated conditional-null simulations, mean one-hour period ACF fell from 0.974 to 0.397 and direction-cosine ACF from 0.932 to 0.330. The Theiler exclusion does not repair this null-model mismatch. Full algorithm details and the methodological reference are in the [detailed methodology](methodology.md).

## Saved synthetic pilot results

The pilot included independent and AR(1) rho=0.98 processes, known independence/conditional independence/dependence, and periodic missing hourly observations. Each scenario used 16 generated records, 1,232 retained observations per record and 20 surrogates per test: 192 synthetic tests and 4,032 Java estimator evaluations overall.

| Measure | AR(1) rho | Null rejections / 16 | Dependent-case detections / 16 |
|---|---:|---:|---:|
| Height MI | 0 | 0/16 | 16/16 |
| Height MI | 0.98 | 0/16 | 12/16 |
| Period CMI | 0 | 1/16 | 16/16 |
| Period CMI | 0.98 | 1/16 | 13/16 |
| Direction CMI | 0 | 2/16 | 16/16 |
| Direction CMI | 0.98 | 2/16 | 13/16 |

Source: [saved synthetic summary](validation/synthetic_summary.csv). Synthetic one-sided p-values used `(1 + count(surrogate >= observed)) / (20 + 1)`, with resolution 1/21. These small experiments show dependence detection but do not establish calibrated type-I error or statistically established false-positive inflation. The synthetic missingness pattern allowed shifts unavailable for the real wave records. The [distribution plot](synthetic_surrogate_distributions.png) and [temporal-preservation plot](synthetic_temporal_preservation.png) show synthetic validation only.

## Interpretation for the final project

The computational timestamp integration passed; the statistical validity gate did not. More surrogates or Holm adjustment would not resolve the null-model problems. The six primary estimates and their numerical site differences remain descriptive, without validated wave-data confidence intervals or p-values. A difference in within-site significance, even if validated, would not itself establish a significant between-site difference.

The [validation gate](validation_gate.json), [preservation checks](preservation_checks.json) and [detailed methodology](methodology.md) retain the supporting evidence. Original datasets, estimates and autocorrelation results are unchanged.

## Reproduction

The following historical commands run from the repository root using the configured Python environment and pinned JIDT setup:

```sh
# Recreate the saved synthetic investigation; not needed to read the results:
.venv/bin/python src/validate_surrogate_methods.py
# Rebuild the validation reports and synthetic plots from saved outputs:
.venv/bin/python src/report_surrogate_validation.py
```

These commands overwrite their corresponding validation outputs; they do not launch wave significance testing. See the [technical workflow](../../docs/analysis_workflow.md) for dependencies and implementation details. No numerical analysis was rerun for this documentation update.
