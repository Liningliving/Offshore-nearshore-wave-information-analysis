# Offshore–nearshore wave information project

**Tutor: start with this README.** Follow the review order below for the final report, scientific figures, numerical evidence and methodological limitations. No software setup or analysis execution is needed to inspect the findings.

## Suggested review order

| Order | What to review | Where |
|---|---|---|
| 1 | Scientific question, methods, findings and limitations | [Final Word report](deliverables/final_scientific_report.docx) or [Markdown report](deliverables/final_scientific_report.md) |
| 2 | Direct site contrasts, temporal sensitivity and height scatterplots | [Figure 1: site contrasts](deliverables/figures/figure_1_between_site_contrasts.pdf), [Figure 2: temporal sensitivity](deliverables/figures/figure_2_temporal_sensitivity.pdf), [Figure 3: wave heights](deliverables/figures/figure_3_wave_heights.pdf) |
| 3 | Sampling intervals, usable N and deployment coverage | [Verified dataset description](results/preprocessing/verified_dataset_description.csv), report Table 1 |
| 4 | Six estimates and three exact site differences | [Primary results](results/primary_information/primary_information_summary.csv), [contrasts](results/primary_information/between_site_contrasts.csv) |
| 5 | Quality filtering, timestamp handling and temporal robustness | [Preprocessing audit](results/preprocessing/preprocessing_audit.json), [sensitivity results](results/sensitivity_analysis/all_sensitivity_results.csv) |
| 6 | What remains unestablished statistically | [Assessment status](deliverables/assessment_status.md), [methodological assessment](research/between_site_method_assessment/assessment.md) |
| Optional | Implementation and reproduction | [Code guide](src/README.md), [workflow](docs/analysis_workflow.md), tests/ |

**Interpretive scope:** these are descriptive comparisons of the two deployment records. No adequately validated wave-data p-values or confidence intervals were established. The final report omits k-sensitivity analysis from its main findings.

## Folder roles

The first inspection should focus on deliverables/ and results/. Data are retained separately; research/ contains supporting methodological investigations, while src/, tests/, config/ and tools/ support reproduction.

```text
ass2/
├── deliverables/        Final manuscript and selected figures
├── data/
│   ├── raw/             Original input files
│   └── processed/       Two cleaned, quality-filtered datasets
├── results/
│   ├── primary_information/
│   ├── sensitivity_analysis/
│   ├── preprocessing/   Preprocessing and autocorrelation audits
│   └── exploratory_figures/
├── research/            Statistical-method investigations and pilots
├── src/                 Python code and java/ application adapters
├── tests/               Numerical, timestamp and Java integration checks
├── docs/                Original proposal, detailed workflow and report template
├── config/              Dependencies, source hashes and historical path aliases
└── tools/jidt/          Pinned official source and compiled Java library
```

## Main numerical sources

| Purpose | File |
|---|---|
| Six primary MI/CMI estimates | [primary_information_summary.csv](results/primary_information/primary_information_summary.csv) |
| Three descriptive site differences | [between_site_contrasts.csv](deliverables/between_site_contrasts.csv) |
| Saved sensitivity results | [all_sensitivity_results.csv](results/sensitivity_analysis/all_sensitivity_results.csv) |
| Sampling and preprocessing audit | [preprocessing_audit.json](results/preprocessing/preprocessing_audit.json) |
| Outstanding assessment limitations | [assessment_status.md](deliverables/assessment_status.md) |

The primary datasets contain **6,867 Figure Eight Pools** and **10,522 Stockton** observations. Heights are matching time-domain WHTH/Hsig, not spectral Hm0. The baseline is KSG1, k=4 and exact 45-hour Theiler exclusion. The final report omits k sensitivity; historical files remain available.

## Optional: running the code

From this directory, use the project virtual environment:

```sh
.venv/bin/python -m unittest discover -s tests
```

The [detailed workflow](docs/analysis_workflow.md) explains preprocessing, estimation and reporting commands. Running analysis entry points regenerates their corresponding products; this reorganization did not rerun the full analyses. Base dependencies are in requirements.txt; optional sets are documented in [config/](config/README.md).

Historical paths in retained execution records are resolved by src/artifact_paths.py using config/legacy_paths.json. Superseded drafts, duplicate figure sets and disposable build caches have been removed. The final report, source data, scientific results and supporting inference evidence are retained.
