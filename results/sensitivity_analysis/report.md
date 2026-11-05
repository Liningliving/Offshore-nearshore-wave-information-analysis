# Sensitivity analyses

The original six Step 7 estimates, cleaned data, raw data, autocorrelation results and Step 8 artifacts are unchanged. All six baselines were reproduced before sensitivity calculations: the largest difference is 2.22e-16 nats (serialization/floating-point precision; acceptance tolerance 1e-12). No significance tests or p-values were generated.

## Main findings

Across all 15 matched settings/cohorts, **height MI remains greater at Figure Eight Pools** and **direction CMI remains greater at Stockton**. Neither ordering reverses. Overall ranges across the prespecified analyses are:

| site | measure | min_bits | max_bits |
|---|---|---|---|
| figure_eight_pools | direction_cmi | 0.085080 | 0.125482 |
| figure_eight_pools | height_mi | 1.534472 | 1.618468 |
| figure_eight_pools | period_cmi | -0.018710 | 0.030538 |
| stockton | direction_cmi | 0.198232 | 0.240621 |
| stockton | height_mi | 0.673381 | 0.721617 |
| stockton | period_cmi | -0.026519 | 0.004362 |


Period CMI remains small in absolute magnitude (all estimates between -0.026519 and +0.030538 bits), but its sign is not stable:

- Stockton period CMI is negative at k=3/4/6, becoming +0.004362 bits at k=8. Across W=30/45/60 h it remains slightly negative.
- Figure Eight Pools period CMI is positive in the original-cleaned k/window analyses and all-available lag analysis. In the common-source cohort it changes from +0.017952 at zero lag to -0.001003 at 0.5 h, +0.005563 at 1 h and -0.018710 at 2 h.
- The common-source period ordering between sites reverses at 2 h, but by only about 0.000083 bits (Figure Eight Pools -0.018710 versus Stockton -0.018627). This is not a meaningful reversal of the main height/direction patterns or evidence of negative information.

Lag choice has more effect on directional CMI than the tested exclusion windows. At 2 h, all-available Figure Eight Pools directional CMI rises from 0.097002 to 0.125482 bits (about 29%), whereas Stockton falls from 0.231608 to 0.200080 bits (about 14%). Common-source comparisons retain this directional contrast: Figure Eight Pools spans 0.085080–0.114284 and Stockton 0.198232–0.234640 bits. Thus the cross-site ordering is stable, while the exact effect sizes depend on alignment. These percentages describe changes from zero lag, not inferential effect-size uncertainty.

W=30/45/60 h gives comparatively stable direction estimates (Figure Eight Pools 0.097002–0.098175; Stockton 0.229184–0.234277 bits). k sensitivity also retains the two main orderings. All negative finite-sample CMI estimates are saved without clipping; population CMI is nonnegative. No threshold was used to select a preferred setting or to classify significance.

## One-factor design and estimator

Each site is calculated separately with the same unmodified official JIDT source snapshot used by Step 7, commit `1ca832235e64ae5b3a482dc0ead6f9b2ff2a0456` and the same jar hash. All runs use KSG algorithm 1, NORMALISE=true, MAX_NORM, CPU, one worker thread, Gaussian noise 1e-8 after JIDT normalization and fixed NOISE_SEED=20261031. The source and response dimensions are (1,1) for height MI, (1,1|1) for period CMI and (2,1|1) for jointly encoded direction CMI.

Three separate analyses vary only:

- k=3,4,6,8, with W=45 h and zero lag, using identical original cleaned rows within each site.
- Physical lag=0,0.5,1,2 h, with k=4 and W=45 h, using freshly matched observations.
- W=30,45,60 h, with k=4 and zero lag, using identical original cleaned rows.

The 45-hour baseline remains primary. There is no exhaustive parameter grid, optimal-lag selection or replacement of primary results. The 90 result rows include baseline values under each analysis label; cached identical k/window calls are reused within a run. Every result records site, measure, N, k, physical lag, physical W, index units, nats/bits, estimator settings, source-time hash and JIDT provenance. `settings.json` records the fixed plan.

## Lag matching and physical interpretation

Positive tau means offshore Ho, Tp_o, Dx and Dy at t, with nearshore Hn at t+tau. Offshore archive TIME is UTC; nearshore Time is fixed AEST (UTC+10, no daylight saving). Original CSVs are read, numeric blanks coerced, both sources restricted to QC flag 1, and exact target timestamps joined one-to-one. Complete-variable rows are retained, with no interpolation, row shifting, trimming of valid extremes or additional QC rule.

The original nearshore half-hourly measurements are used, so the 0.5-hour case targets minute 30. All retained offshore source timestamps remain on clock hours; the Theiler index is therefore still in actual source hours and W=45 still means 45 hours. A separate Java test explicitly uses half-hour index ticks and W=90 ticks for 45 h, demonstrating correct conversion if source-grid resolution changes in a future analysis. A half-hour target delay alone does not require halving the source index unit.

These delays are a small exploratory alignment range at the available temporal resolution, not established travel times. Deployment readmes locate Figure Eight Pools at about (-34.1997,151.0506) and Stockton at (-32.9021,151.7988). Historical offshore locations in [CAWCR Technical Report 041, Appendix A](https://www.cawcr.gov.au/technical-reports/CTR_041.pdf) are approximately Port Kembla (-34.48,151.03) and Sydney (-33.77,151.42). These indicate separations of roughly 30 km and 100 km respectively (geographic approximations, not propagation paths or exact contemporaneous deployments). [Kinsela et al. (2024)](https://www.nature.com/articles/s41597-023-02865-x) identifies these buoy pairings and their contrasting nearshore settings. The points are not co-located or guaranteed to lie on one wave ray, particularly Sydney–Stockton. Consequently 0–2 h is reasonable as a limited exploratory timing check, but is not demonstrated to bracket physically plausible travel times for both pairs. A mechanistic delay would require wave direction, period and bathymetry/ray-path modelling; none is inferred from an MI maximum here.

## Sample composition

All-available results use each lag's complete raw-data matches; common-source results restrict each site's offshore timestamps to the intersection across all four delays. Thus Ho/Tp_o/Dx/Dy and source-time membership are held fixed across common-cohort lags while the target Hn changes. Common-source zero-lag results are a supplementary cohort, not the original baseline. Equal N alone is not the criterion: timestamp sets are explicitly compared. The two sites are never matched to each other.

| site | cohort | lag_hours | sample_size |
|---|---|---|---|
| figure_eight_pools | all_available | 0.0 | 6867 |
| figure_eight_pools | common_source_timestamps | 0.0 | 6316 |
| figure_eight_pools | all_available | 0.5 | 6873 |
| figure_eight_pools | common_source_timestamps | 0.5 | 6316 |
| figure_eight_pools | all_available | 1.0 | 6863 |
| figure_eight_pools | common_source_timestamps | 1.0 | 6316 |
| figure_eight_pools | all_available | 2.0 | 6863 |
| figure_eight_pools | common_source_timestamps | 2.0 | 6316 |
| stockton | all_available | 0.0 | 10522 |
| stockton | common_source_timestamps | 0.0 | 10307 |
| stockton | all_available | 0.5 | 10524 |
| stockton | common_source_timestamps | 0.5 | 10307 |
| stockton | all_available | 1.0 | 10521 |
| stockton | common_source_timestamps | 1.0 | 10307 |
| stockton | all_available | 2.0 | 10522 |
| stockton | common_source_timestamps | 2.0 | 10307 |


Common N is 6,316 for Figure Eight Pools and 10,307 for Stockton. The common-cohort shift in Figure Eight Pools zero-lag period CMI from the original 0.030538 to 0.017952 bits illustrates the effect of sample composition. Some all-available lagged matches can begin earlier than the original concurrent series, because a later valid nearshore observation can match an earlier offshore time; these are documented exact raw-data matches.

## Validation and files

Before sensitivity runs, all six Step 7 baselines and zero-lag raw-data rematches were checked against the original values and timestamps. Java integration tests cover hourly and half-hourly source grids with missing gaps, W=30/45/60 h, and k=3/4/6/8 at W=45. Twelve prespecified synthetic configurations each run MI and both CMI estimators. Actual joint-tree eligibility masks are checked for every point pair, marginal counts match the same mask, and actual k-nearest neighbours obey it. This includes boundary pairs immediately below, exactly at and immediately above each W, both within runs and across gaps. Java metadata validates all retained indices/counts/set IDs, with one shared set ID 0 per site and no cross-site calculator pooling. Direction dimensions are explicitly checked as (2,1,1). All fixed seed/normalization/norm/noise settings are read back from Java.

Eleven automated tests passed, including new raw half-hour/gap matching, real-data zero-lag equivalence, common timestamps and actual Java masks. `validation/acceptance.json`, `baseline_reproduction.csv`, `lag_matching.csv` and `java_integration.csv` record the gate evidence. `preservation_checks.json` confirms original data, Step 7/8 artifacts and preprocessing/autocorrelation code are unchanged.

- `all_sensitivity_results.csv`: all 90 labelled results in nats and bits.
- `k_sensitivity.csv`, `theiler_sensitivity.csv`, `lag_sensitivity.csv`: separate result tables.
- Matching PNG plots: separate panels for each information measure; lag plots also separate cohorts.
- `lag_sample_counts.csv`, `estimate_ranges.csv`, `qualitative_pattern_checks.csv`, `period_sign_checks.csv`: descriptive audits, with no p-values.
- `inputs/`: exact matched source/target timestamps and input tuples; `runs/`: raw JIDT estimates, actual time indices and logs.

Reproduce with `python3 src/sensitivity_analysis.py`, `python3 src/report_sensitivity_analysis.py`, and `python3 -m unittest discover -s tests`. Java/JDK and the already validated official JIDT build are required.

The site records cover different years and have different temporal coverage and sizes; common-source matching only controls composition within a site. These are descriptive robustness checks, not uncertainty intervals or tests of between-site differences. Step 8's unresolved surrogate-validity issues remain; stability across settings does not establish statistical significance or geomorphic causation.
