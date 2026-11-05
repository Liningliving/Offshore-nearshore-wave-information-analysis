# Offshore–nearshore wave information analysis

An MSc Information Theory project comparing offshore–nearshore wave dependence at Figure Eight Pools and Stockton, New South Wales. Mutual information (MI) measures the relationship between offshore and nearshore significant wave height. Conditional mutual information (CMI) measures the additional dependence associated with offshore peak period and direction after conditioning on offshore height.

## Results

| Comparison | Observed difference (bits) |
|---|---:|
| Height MI: Figure Eight Pools − Stockton | +0.868023 |
| Period CMI: Stockton − Figure Eight Pools | −0.040520 |
| Direction CMI: Stockton − Figure Eight Pools | +0.134605 |

Height MI is greater at Figure Eight Pools, while directional CMI is greater at Stockton. Both orderings persist across the tested propagation lags and Theiler windows, although the directional contrast changes with lag. Period CMI is small and does not follow the predicted larger Stockton contribution.

These are descriptive deployment-specific estimates. No validated wave-data p-values or confidence intervals are available.

## Data and methods

| Buoy pairing | Offshore interval | Nearshore interval | Complete matched observations |
|---|---|---|---:|
| Port Kembla/Wollongong–Figure Eight Pools | Hourly | Half-hourly | 6,867 |
| Sydney–Stockton | Hourly | Half-hourly | 10,522 |

Matched observations are effectively hourly with missing-data gaps. Heights consistently use offshore WHTH and nearshore Hsig, both time-domain significant wave heights, rather than spectral Hm0. Missing observations are not interpolated, and valid extreme waves are retained.

The primary calculations use JIDT's continuous Kraskov algorithm 1 estimators with k=4, normalization, max norm, exact 45-hour Theiler exclusion and fixed-seed tie-breaking noise. Direction is encoded jointly as (cos θ, sin θ). The final analysis includes propagation-lag and temporal-exclusion sensitivity; historical k-sensitivity results are retained separately from the main findings.

## Documentation and outputs

| Resource | Contents |
|---|---|
| [Scientific report](deliverables/final_scientific_report.md) | Motivation, hypotheses, findings, physical interpretation and limitations |
| [Technical workflow](docs/analysis_workflow.md) | Estimator settings, implementation, validation evidence and reproduction commands |
| [Primary estimates](results/primary_information/primary_information_summary.csv) | Six MI/CMI estimates in nats and bits, with settings and provenance |
| [Between-site contrasts](results/primary_information/between_site_contrasts.csv) | Exact numerical differences between the two sites |
| [Dataset description](results/preprocessing/verified_dataset_description.csv) | Sampling, usable counts, deployment periods and coverage |
| [Sensitivity results](results/sensitivity_analysis/all_sensitivity_results.csv) | Saved results with sample/cohort definitions |

The three selected figures are available as PNG and PDF:

- [Figure 1 — Between-site information contrasts](deliverables/figures/figure_1_between_site_contrasts.pdf)
- [Figure 2 — Temporal sensitivity](deliverables/figures/figure_2_temporal_sensitivity.pdf)
- [Figure 3 — Offshore–nearshore wave heights](deliverables/figures/figure_3_wave_heights.pdf)

## Repository structure

| Directory | Contents |
|---|---|
| `deliverables/` | Final manuscript and selected figures |
| `data/raw/` | Original buoy files and metadata |
| `data/processed/` | Cleaned concurrent datasets |
| `results/` | Primary estimates, sensitivity, preprocessing/ACF audits and exploratory figures |
| `research/` | Surrogate-method validation and between-site inference investigations |
| `src/`, `tests/` | Analysis code, Java adapters and verification |
| `docs/` | Workflow, original proposal and manuscript template |
| `config/`, `tools/` | Dependency extras, provenance/path aliases and pinned JIDT |

## Setup and usage

Install the base Python dependencies in a virtual environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Run the verification suite from the repository root:

```sh
.venv/bin/python -m unittest discover -s tests
```

A local JDK is required for Java integration checks and estimator runs. The [workflow](docs/analysis_workflow.md) describes the pinned JIDT setup and commands for each analysis stage. Saved results can be inspected without executing the pipeline; analysis commands regenerate their corresponding outputs.

To rebuild the report, install the optional reporting dependencies and run:

```sh
.venv/bin/python -m pip install -r config/requirements-report.txt
.venv/bin/python src/consolidate_final_report.py
```

Historical paths in retained execution records are resolved by `src/artifact_paths.py` using `config/legacy_paths.json`.

## Limitations

The implementation and exact elapsed-time exclusion have been checked, but statistical inference remains unresolved. Full-record subsampling failed synthetic calibration, and within-site surrogate testing stopped because null-method validity was not established. Numerical differences and sensitivity ranges are not statistically confirmed population differences or uncertainty intervals.

Temporal autocorrelation, unequal deployment periods and seasonal coverage, different depths/local conditions, unequal sample sizes and one site per setting limit interpretation. The results do not establish geomorphic causation. Further details are in the [scientific report](deliverables/final_scientific_report.md) and [methodological assessment](research/between_site_method_assessment/assessment.md).
