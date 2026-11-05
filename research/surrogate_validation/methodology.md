# Step 8: surrogate-method validation — full analysis stopped

**No wave significance tests were run.** The validity gate remains unresolved, so there was no wave-data pilot and no 199-surrogate main analysis. The summary CSV has the six unchanged Step 7 estimates, B=0, and missing p-values, not invented or zero p-values. Holm adjustment and wave surrogate-distribution plots are consequently unavailable. The saved distribution plots are explicitly synthetic validation only.

## JIDT audit: source and actual Java runtime

The Step 7 jar is the unmodified official source snapshot at commit `1ca832235e64ae5b3a482dc0ead6f9b2ff2a0456`, identified by the same jar hash in its build manifest. The actual subclasses matter:

- MI `computeSignificance(B)` generates unrestricted random orderings. Its KSG1 override actually rearranges **variable 2 (Hn)** despite the base documentation describing source shuffling. It retains the custom set/time arrays while rebuilding affected search structures. This changes cross-series alignment and destroys Hn temporal ordering.
- CMI defaults to variable 1: Tp_o, or the complete two-column direction array. Ho and Hn remain fixed. Global shuffling destroys source–Ho association as well as the association under test; it is not an appropriate general conditional null.
- CMI `computeSignificance(variable, orders)` clones the calculator, reinitializes it and calls ordinary `setObservations`. This resets custom time points to compressed row indices. In contrast, the optimized single-reordering `computeAverageLocalOfObservations(variable, order)` preserves time/set metadata in this snapshot. These paths must not be conflated.
- NOISE_SEED controls estimator tie noise, not the default surrogate-order generator. Candidate validation uses explicit separately seeded donor maps and reloads each draw into a fresh calculator through the Step 7 exact-hour loader.

`jidt_runtime_surrogate_audit.csv` captures the actual arrays and tree eligibility INSIDE these surrogate calls. For an across-gap 46-hour separation, the CMI wrapper wrongly excludes the candidate while MI and optimized CMI single-ordering permit it. The 44/45-hour pairs remain excluded. This is runtime evidence, not just source inspection.

## Candidate nulls investigated

**Height MI:** test Ho independent of Hn. The candidate shifts Ho by exact hours on a complete time circle, permitting only rotations that preserve the entire retained timestamp mask, with a preselected minimum circular separation of 180 hours (four 45-hour windows). It preserves the observed values/count and, under the circular construction, within-series ordering and autocorrelation, except for the artificial wrap boundary. It assumes approximate stationarity and adequate decorrelation at the chosen shift; neither follows from the Theiler window alone. Synthetic gaps are repeated missing hours 5 and 6 every day, allowing legal multiples-of-24-hour shifts. For real irregular gaps, shifting compressed rows is not a physical-time shift, while shifting values together with their missingness masks and taking intersections changes the tested observations.

The two real timestamp masks have **zero admissible shifts** under this rule. An alternative inspected weekly-block rearrangement only swaps blocks with identical missingness patterns. It leaves all 6,867 Figure Eight Pools observations fixed and 9,688/10,522 Stockton observations fixed. It therefore fails to provide a meaningful full-record independence null. This audit uses timestamps only; it is not a propagation-lag sensitivity analysis.

**Period and direction CMI:** test Tp_o independent of Hn given Ho, or (Dx,Dy) jointly independent of Hn given Ho. The candidate implements [Runge (2018), Algorithm 1](https://proceedings.mlr.press/v84/runge18a.html): for each target, choose among its five nearest neighbours in scalar Ho, including itself; visit targets and donor lists in random order, prefer unused donors, and permit reuse when exhausted. This k_perm=5 is the surrogate neighbourhood, distinct from the unchanged estimator k=4. Direction columns always move together. The scheme approximately retains local source–Ho relationships, leaves the Hn–Ho sample unchanged, and disrupts source–Hn pairing. It does not guarantee a bijection: about 7.4% donor reuse and 21.7–21.8% unchanged source rows occurred in validation. Exact source marginals are therefore not guaranteed, and some original pairing remains. No claim of exact conditional exchangeability is made.

Pointwise local donors do **not** preserve source temporal dynamics. In autocorrelated synthetic conditional-null cases, mean one-hour period autocorrelation fell from 0.974 to 0.397; the direction cosine component fell from 0.932 to 0.330. Period–Ho correlation was approximately preserved (0.568 to 0.567). Small conditioning distances and preserved correlation do not prove preservation of the full conditional law. A Theiler window excludes close estimator neighbours; it does not repair a misspecified surrogate distribution.

## Synthetic validation

The validation includes independent and dependent Gaussian AR(1) series with rho=0 and 0.98, 5,000-hour burn-in, and the same periodic missing-hour mask. In conditional cases X=0.8Z+Ex and Y=0.8Z+Ey under the true conditional null, with independent innovation streams; under dependence, 0.8Ex is added to Y. Direction is (cos(1.2Z+Ex), sin(1.2Z+Ex)), so its components remain joint. MI uses independent Ex/Ey under the null and Y=0.8Ex+Ey under dependence.

Each scenario has 16 independent generated records, 1,232 retained observations and **20 candidate surrogates** per record: 192 synthetic tests and 4,032 actual Java estimator evaluations. Seed base is 20261101; each dataset starts from base + int(rho*1000)*100 + replicate, with the loop order and all donor maps saved. The estimator always retains the original Step 7 settings, including noise seed 20261031. Synthetic p-values use `(1 + count(null >= observed))/(20+1)`; their resolution is 1/21. These are candidate-method checks, not wave results.

| measure | rho | truth | tests | rejections | mean_source_acf | mean_surrogate_acf |
|---|---|---|---|---|---|---|
| direction | 0.0 | dependent | 16 | 16 | 0.002 | 0.005 |
| direction | 0.0 | null_hypothesis | 16 | 2 | 0.002 | 0.003 |
| direction | 0.98 | dependent | 16 | 13 | 0.932 | 0.329 |
| direction | 0.98 | null_hypothesis | 16 | 2 | 0.932 | 0.330 |
| mi | 0.0 | dependent | 16 | 16 | -0.002 | -0.003 |
| mi | 0.0 | null_hypothesis | 16 | 0 | -0.002 | -0.003 |
| mi | 0.98 | dependent | 16 | 12 | 0.976 | 0.974 |
| mi | 0.98 | null_hypothesis | 16 | 0 | 0.976 | 0.974 |
| period | 0.0 | dependent | 16 | 16 | -0.001 | -0.004 |
| period | 0.0 | null_hypothesis | 16 | 1 | -0.001 | -0.004 |
| period | 0.98 | dependent | 16 | 13 | 0.974 | 0.399 |
| period | 0.98 | null_hypothesis | 16 | 1 | 0.974 | 0.397 |


Every observed and candidate-surrogate Java load verified the full intended time/set arrays and counts. Actual k=4 neighbour eligibility was checked at approximately 20 evenly spaced target rows per calculation. The underlying exact 44/45/46-hour boundary implementation was separately audited in Java. Thus computational timing integration passes, but this does not validate the statistical null.

These small checks show detection of known dependence and some null rejections; they do not establish calibrated type-I error. For example, direction nulls rejected in 2/16 independent and 2/16 autocorrelated records. With only 16 repetitions, this is insufficient to conclude either nominal calibration or statistically established inflation. The documented loss of temporal structure remains unresolved for the wave conditional tests. No wave pilot is warranted merely because the synthetic examples sometimes behave sensibly.

## Original estimates and status

| site | measure | sample_size | nats | bits | status |
|---|---|---|---|---|---|
| figure_eight_pools | I(Ho;Hn) | 6867 | 1.072950521 | 1.547940396 | not_tested_validity_gate_unresolved |
| figure_eight_pools | I(Tp_o;Hn|Ho) | 6867 | 0.021167053 | 0.030537603 | not_tested_validity_gate_unresolved |
| figure_eight_pools | I((Dx,Dy);Hn|Ho) | 6867 | 0.067237007 | 0.097002497 | not_tested_validity_gate_unresolved |
| stockton | I(Ho;Hn) | 10522 | 0.471282925 | 0.679917538 | not_tested_validity_gate_unresolved |
| stockton | I(Tp_o;Hn|Ho) | 10522 | -0.006919212 | -0.009982313 | not_tested_validity_gate_unresolved |
| stockton | I((Dx,Dy);Hn|Ho) | 10522 | 0.160538110 | 0.231607535 | not_tested_validity_gate_unresolved |


Stockton's negative period CMI is preserved unchanged. No within-site significant finding, no Holm-adjusted finding, and no significant between-site difference is claimed. A difference in within-site p-values would not itself test a between-site contrast.

## Simplest defensible next options

1. **Retain Step 7 as descriptive results.** This satisfies the current observation/design constraints without reporting unsupported p-values.
2. **Approve a clearly separate, regular-segment or common-overlap testing analysis.** This can support temporal shifts or suitable block resampling, but changes the tested sample and requires recomputing its corresponding observed statistic. It must not be presented as a p-value for the unchanged full-record estimates.
3. **Develop a conditional time-series null model**, generating predictors conditional on offshore-height histories while modelling residual temporal dynamics. Validate null calibration with substantially more simulations and plausible persistence/missingness regimes before wave testing. This adds modelling assumptions; it has not been implemented here.

Simply increasing B to 199, applying Holm, adding the Theiler exclusion, or labelling global/local permutations as temporal surrogates would not resolve the null-model issues. A future approximate local-permutation analysis could only be labelled exploratory, with its limitations explicit; it would not satisfy a claim of validated time-series conditional significance at this stage.

## Files and reproduction

`wave_significance_status.csv`: six preserved estimates, null hypotheses, candidate methods/settings/seeds, B=0, missing surrogate summaries/p-values, and reasons for stopping. `validation/`: synthetic design, data, donor maps, every estimate, calibration summaries and Java logs. `wave_timestamp_mask_audit.json`: gap-pattern feasibility. `validation_gate.json`: explicit stop state. `preservation_checks.json`: hashes confirming original raw/cleaned files, autocorrelation and Step 7 artifacts are unchanged.

```
python3 src/validate_surrogate_methods.py
python3 src/report_surrogate_validation.py
python3 -m unittest discover -s tests
```

The validation command cannot launch wave significance testing. Eight automated tests pass, including the pre-existing actual Java timing test and new candidate-generator tests. No lag/k sensitivity, interpolation, extra outlier removal or research-design change was performed.
