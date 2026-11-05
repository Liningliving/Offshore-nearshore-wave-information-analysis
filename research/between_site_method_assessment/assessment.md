# Between-site statistical comparison: methodological note

## Why investigate a statistical test?

The central question is whether offshore–nearshore information relationships differ between Figure Eight Pools and Stockton. Comparing the estimated MI and CMI values directly answers what the two observed deployments show. A statistical test was investigated to ask a further question: whether the differences could be distinguished from sampling variation. That requires accounting for autocorrelated observations, missing timestamps, unequal sample sizes and different deployment periods. It is separate from checking that JIDT calculates the requested estimates correctly.

## What method was attempted?

Only **one candidate between-site interval method** was implemented: time-block subsampling. Within each site's synthetic record, shorter continuous time windows were selected, retaining their available observations and missing-data gaps. MI and CMI were calculated separately for these windows using the existing estimator settings and exact 45-hour Theiler exclusion. The variation in window estimates was rescaled to construct candidate intervals for the difference between full-record estimates.

The pilot used windows spanning one quarter of each record, 39 paired draws per experiment and 12 independent synthetic experiments per scenario. Scenarios included equal information with similar or different temporal persistence, and known nonzero differences. Other inference frameworks were discussed but were not implemented as between-site tests.

## Why was it not accepted?

The initial calibration was inadequate. Candidate nominal 95% intervals contained the known synthetic difference in as few as 8 of 12 experiments for some measure–scenario combinations. The resampled variation sometimes underestimated variation between independent records; differences in estimator bias also appeared relevant. These diagnostics did not establish a single cause or justify a simple correction.

Twelve experiments are too few to measure coverage precisely, but the pilot did not support using these intervals for the wave observations. This rejects neither all subsampling methods nor all possible statistical tests. No validated wave-data confidence intervals or p-values were produced, and no further statistical development is part of the final project.

## What can the project conclude?

The original primary estimates give these descriptive differences:

- Height MI: Figure Eight Pools − Stockton = **+0.868023 bits**.
- Direction CMI: Stockton − Figure Eight Pools = **+0.134605 bits**.
- Period CMI: Stockton − Figure Eight Pools = **−0.040520 bits**.

Height dependence is stronger at Figure Eight Pools, while additional directional dependence conditional on offshore height is greater at Stockton. Period CMI is small. These are deployment-specific numerical comparisons, not statistically established population differences or evidence of geomorphic causation.

The main analysis remains quality control, JIDT estimation, direct comparison, propagation-lag and Theiler-window sensitivity, and physical interpretation alongside Kinsela et al. (2024). Sensitivity checks describe robustness, not uncertainty intervals. The unsuccessful inference investigation is supplementary.

## Supporting records

The [technical supplement](supplementary_technical_assessment.md), [coverage table](pilot_coverage_by_setting.csv), [error diagnostics](pilot_error_diagnostics.csv), [methods inventory](methods_inventory.csv) and [historical audit manifest](assessment_manifest.json) preserve the evidence. Code and numerical outputs are unchanged. See the [final scientific report](../../deliverables/final_scientific_report.md) for the scientific findings and limitations.
