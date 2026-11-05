# Reproducing the retained analysis

Start from the project root, with the existing virtual environment. Current scientific results are already saved; these commands are for deliberate reproduction.

| Purpose | Command | Main product |
|---|---|---|
| Preprocess original observations | `.venv/bin/python src/preprocess.py` | data/processed/, results/preprocessing/ |
| Timestamp-aware autocorrelation | `.venv/bin/python src/autocorrelation.py` | results/preprocessing/ and exploratory figures |
| Six primary MI/CMI estimates | `.venv/bin/python src/primary_information.py` | results/primary_information/ |
| Java timing checks only | `.venv/bin/python src/primary_information.py --integration-only` | Primary integration evidence |
| Historical surrogate-method validation | `.venv/bin/python src/validate_surrogate_methods.py` | research/surrogate_validation/ |
| Summarize that validation | `.venv/bin/python src/report_surrogate_validation.py` | Same directory; wave tests remain stopped |
| Reproduce historical sensitivity calculations | `.venv/bin/python src/sensitivity_analysis.py` | results/sensitivity_analysis/ |
| Summarize saved sensitivity results | `.venv/bin/python src/report_sensitivity_analysis.py` | Same directory |
| Generate selected presentation figures | `.venv/bin/python src/make_presentation_figures.py` | deliverables/figures/ |
| Assemble the final report | `.venv/bin/python src/consolidate_final_report.py` | deliverables/ |
| Check implementation | `.venv/bin/python -m unittest discover -s tests` | Temporary test evidence |

Primary information settings remain KSG1, k=4, normalization, max norm, exact 45-hour temporal exclusion and fixed-seed 1e−8 JIDT noise. Direction uses both components jointly. The primary zero-lag observations and all previous numerical results are retained. Final figures read saved results and saved preprocessing correlations; they do not calculate new information estimates.

The final report uses only lag and Theiler-window sensitivity; the historical neighbourhood results remain within the existing sensitivity archive for reproducibility. The historical sensitivity runner reproduces that original full set, rather than changing the numerical research record.

The failed whole-record between-site pilot and methodological assessment are retained under research/ to support the reported inference limitation. Re-running a failed pilot does not authorize wave significance claims. No validated wave p-values or confidence intervals are available.

The original proposal is [project_proposal.pdf](project_proposal.pdf). [The project guide](../README.md) identifies current deliverables. Base dependencies are requirements.txt; Word support is config/requirements-report.txt. JIDT is stored under tools/jidt/. Rebuild the pinned official jar only if needed using src/build_jidt_official.py.

Historical paths in retained CSV/JSON/logs are translated by src/artifact_paths.py using config/legacy_paths.json. Superseded documents and redundant figure generators are no longer needed by current scripts.
