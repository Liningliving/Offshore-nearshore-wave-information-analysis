# Analysis code by purpose

Run scripts from the project root using `.venv/bin/python src/<script>.py`. The file names describe their scientific role rather than an old numbered work plan. Numerical algorithms and estimator settings were not changed in the reorganization.

| Purpose | Entry point / helper | Results |
|---|---|---|
| Six concurrent height MI / period CMI / joint-direction CMI estimates | `primary_information.py` | `results/primary_information/` |
| Candidate surrogate null generators | `surrogate_methods.py` (importable helper) | Used by synthetic validation |
| Validate surrogate methods and inspect JIDT shuffle behaviour | `validate_surrogate_methods.py` | `research/surrogate_validation/` |
| Summarize the stopped surrogate-validation stage | `report_surrogate_validation.py` | Same directory; no accepted wave p-values |
| Lag / temporal-exclusion / archived neighbourhood robustness | `sensitivity_analysis.py` | `results/sensitivity_analysis/` |
| Summarize saved sensitivity results | `report_sensitivity_analysis.py` | Same directory |

Preprocessing (`preprocess.py`), autocorrelation (`autocorrelation.py`), timestamp handling (`jidt_timing.py`) and the official JIDT builder (`build_jidt_official.py`) retain their established names. Figure/report generators import the renamed modules. `artifact_paths.py` resolves original paths embedded in archived provenance and saved synthetic result tables.

## Java application adapters

`java/SharedEstimatorSettings.java` and `java/ElapsedHourLoader.java` are shared infrastructure. The application adapters are `PrimaryInformationMeasures.java`, `SurrogateValidationEstimator.java`, `JidtSurrogateAudit.java`, `SensitivityMeasures.java`, `SensitivitySettings.java` and `SensitivityIntegrationCheck.java`. The independent exact-hour integration check remains `ExactTheilerIntegrationCheck.java`. Python entry points compile the needed adapters automatically against the existing official jar. The official vendor source and jar are untouched.

Tests use the same names: `test_primary_information_java.py`, `test_surrogate_methods.py` and `test_sensitivity_analysis.py`. Run `python -m unittest discover -s tests` with the project virtual environment. Tests compile Java into temporary directories and do not overwrite original estimates or rerun the full studies.

Selected figure generation uses `make_presentation_figures.py` and the shared `figure_style.py`; report assembly uses `consolidate_final_report.py`. Superseded revision/figure generators have been removed.

