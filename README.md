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

The [raw data](data/raw/) contain original offshore archive exports and nearshore deployment packages, including source CSVs, readmes and supplied images. Original filenames and contents are preserved. The complete, quality-filtered concurrent datasets are [figure_eight_pools.csv](data/processed/figure_eight_pools.csv) and [stockton.csv](data/processed/stockton.csv). Quality-filtering and coverage evidence is saved in [results/preprocessing/](https://github.com/Liningliving/information-thoery-assignment/tree/main/results/preprocessing). The preprocessing entry point is [src/preprocess.py](src/preprocess.py), run from the repository root. Historical paths recorded before file reorganization can be resolved using [src/artifact_paths.py](src/artifact_paths.py).

The primary calculations use JIDT's continuous Kraskov algorithm 1 estimators with k=4, normalization, max norm, exact 45-hour Theiler exclusion and fixed-seed tie-breaking noise. Direction is encoded jointly as (cos θ, sin θ). The final analysis includes propagation-lag and temporal-exclusion sensitivity; historical k-sensitivity results are retained separately from the main findings.

## Limitations

The implementation and exact elapsed-time exclusion have been checked, but statistical inference remains unresolved. Full-record subsampling failed synthetic calibration, and within-site surrogate testing stopped because null-method validity was not established. Numerical differences and sensitivity ranges are not statistically confirmed population differences or uncertainty intervals.

Temporal autocorrelation, unequal deployment periods and seasonal coverage, different depths/local conditions, unequal sample sizes and one site per setting limit interpretation. The results do not establish geomorphic causation. Further details are in the [scientific report](final_scientific_report.md) and [methodological assessment](research/between_site_method_assessment/assessment.md).
## Documentation and outputs

| Resource | Contents |
|---|---|
| [Scientific report](final_scientific_report.md) | Motivation, hypotheses, findings, physical interpretation and limitations |
| [Scientific report — Word](final_scientific_report.docx) | Editable manuscript export |
| [Technical workflow](docs/analysis_workflow.md) | Authoritative reproduction guide, including primary-estimator settings, tie treatment and Java integration evidence |
| [Original proposal](docs/project_proposal.pdf) | Seven-page project proposal, previously named information theory hw-2.pdf |
| [Report template](docs/templates/final_report.md) | Manuscript narrative used by `src/consolidate_final_report.py`; numerical tables are filled from existing saved results |
| [Primary estimates](results/primary_information/primary_information_summary.csv) | Six MI/CMI estimates in nats and bits, with settings and provenance |
| [Between-site contrasts](results/primary_information/between_site_contrasts.csv) | Exact numerical differences between the two sites |
| [Dataset description](results/preprocessing/verified_dataset_description.csv) | Sampling, usable counts, deployment periods and coverage |
| [Sensitivity results](results/sensitivity_analysis/all_sensitivity_results.csv) | Saved results with sample/cohort definitions |

The three selected figures are available as PNG and PDF:

- [Figure 1 — Between-site information contrasts](deliverables/figures/figure_1_between_site_contrasts.pdf)
- [Figure 2 — Temporal sensitivity](deliverables/figures/figure_2_temporal_sensitivity.pdf)
- [Figure 3 — Offshore–nearshore wave heights](deliverables/figures/figure_3_wave_heights.pdf)

The [deliverables folder](deliverables/) also contains supporting copies of the [primary values](deliverables/primary_information_summary.csv), [site differences](deliverables/between_site_contrasts.csv) and [temporal sensitivity results](deliverables/temporal_sensitivity_reused.csv). These are saved results, not new calculations. The selected figures and numerical values reuse the existing analysis; JSON manifests and checks record the report build. No validated wave-data significance is claimed; see [Limitations](#limitations).

### Results directory

| Folder | Contents and supporting documentation |
|---|---|
| [Preprocessing](https://github.com/Liningliving/information-thoery-assignment/tree/main/results/preprocessing) | Quality-filtering audit, descriptive summaries, gap tables and autocorrelation results supporting the 45-hour exclusion; [preprocessing audit](results/preprocessing/preprocessing_audit.json) and [autocorrelation report](results/preprocessing/autocorrelation_report.md) |
| [Primary information](https://github.com/Liningliving/information-thoery-assignment/tree/main/results/primary_information) | Six original concurrent MI/CMI estimates, timestamp and tie audits, and Java integration evidence; see the [technical workflow](docs/analysis_workflow.md) for implementation details |
| [Sensitivity analysis](https://github.com/Liningliving/information-thoery-assignment/tree/main/results/sensitivity_analysis) | Saved lag and Theiler-window checks for all-available and common-source cohorts; [report](results/sensitivity_analysis/report.md) and [lag sample counts](results/sensitivity_analysis/lag_sample_counts.csv) |
| [Exploratory figures](https://github.com/Liningliving/information-thoery-assignment/tree/main/results/exploratory_figures) | Original time series, distributions, height scatterplots, coverage and autocorrelation plots |

Stable site ordering across sensitivity settings is descriptive evidence, not a significance test. Retained reports, logs and CSV metadata may use earlier folder names; their numerical values and audit records are unchanged. Current Python entry points use the current paths, while `src/artifact_paths.py` resolves historical references.

## Repository structure

| Directory | Contents |
|---|---|
| `final_scientific_report.md`, `final_scientific_report.docx` | Final manuscript in Markdown and Word |
| `deliverables/` | Selected figures, presentation and supporting result copies |
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

### Rebuild the report from saved results

From the repository root, with `.venv` created as above:

```sh
.venv/bin/python -m pip install -r config/requirements-report.txt
.venv/bin/python src/consolidate_final_report.py
```

This regenerates `final_scientific_report.md`, its Word copy, supporting table copies and the report manifest. It reads the existing primary/sensitivity results, comparison tables, dataset metadata, report template and selected PNG/PDF figures. Those inputs are included in the repository. It does **not** regenerate the figures, rerun MI/CMI or perform statistical testing. Java is not required for this report-only command.

### Rebuild figures and report from saved results

```sh
.venv/bin/python src/make_presentation_figures.py
.venv/bin/python src/consolidate_final_report.py
```

These commands regenerate the three selected figures and the report using saved data/results, without running JIDT.

### Local JIDT dependency

`tools/jidt/source/` holds the pinned official JIDT checkout with unmodified estimator algorithms. `tools/jidt/build/` contains the existing `infodynamics.jar` and its build manifest and logs. These directories were previously named `vendor/jidt-official/` and `lib/jidt-official/`, respectively.

The exact build commit and hashes are recorded in [build_manifest.json](tools/jidt/build/build_manifest.json). Historical build commands retain their original paths. `src/primary_information.py` verifies the relocated JAR and source and supplies the current JAR path to the other analysis runners. The source checkout and generated Java class files are ignored by this repository; disposable compiled-class caches are recreated when needed.

Build only if needed, from the repository root:

```sh
.venv/bin/python src/build_jidt_official.py
```

### Recompute the numerical analysis

See the [ordered workflow](docs/analysis_workflow.md#2-pipeline-and-commands) for JIDT setup, preprocessing, autocorrelation, primary estimation and sensitivity commands. This is a separate operation that overwrites numerical outputs. There is no single command that reconstructs every historical artifact from empty output directories: some comparison/description tables, templates and reference hashes are versioned inputs. Reference hashes intentionally reject changed result files; a fresh numerical run must be reviewed against the saved analysis before treating it as a replacement. Keep the supplied outputs when reproducing the documented report.

Historical paths in retained execution records are resolved by `src/artifact_paths.py` using `config/legacy_paths.json`.

## Supporting methodological investigations

The `research/` folders document methodological investigations, not additional validated wave significance results.

| Investigation | Purpose and outcome |
|---|---|
| [Surrogate validation](research/surrogate_validation/report.md) | Within-site MI/CMI null-method audit and synthetic checks. Wave testing stopped at the validity gate; [wave_significance_status.csv](research/surrogate_validation/wave_significance_status.csv) records B=0 and missing wave p-values. |
| [Between-site subsampling](research/between_site_subsampling/README.md) | Original unsuccessful full-record interval pilot and its calibration evidence, including retained synthetic inputs, estimates and logs in `research/between_site_subsampling/validation/`. |
| [Between-site methodological assessment](research/between_site_method_assessment/assessment.md) | Assessment of the failed full-record interval method and practical alternatives. |

The completed descriptive findings are in `results/` and `deliverables/`. Existing synthetic evidence and provenance are retained; this documentation does not introduce another calibration study or statistical method.
