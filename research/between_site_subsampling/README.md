# Original full-record between-site inference pilot

This retains the original synthetic calibration evidence for the physical-time block-subsampling confidence-interval candidate. It failed its calibration screen; no wave confidence intervals or p-values were accepted.

- [Calibration summary](validation/calibration_summary.csv)
- [Per-experiment interval checks](validation/candidate_interval_checks.csv)
- [Inference gate](inference_gate.json)
- [Methodological assessment](../between_site_method_assessment/assessment.md)

validation/ retains synthetic inputs, block definitions, estimates and logs needed to verify that finding. Original path strings are preserved in the evidence and resolved through config/legacy_paths.json. The application runner is src/between_site_pilot.py; it is retained for reproducibility, not as an accepted inference method.
