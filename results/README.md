# Completed scientific results

| Folder | What it contains | Open first |
|---|---|---|
| `primary_information/` | Six original concurrent height-MI / period-CMI / joint-direction-CMI estimates; timestamp and tie audits; Java evidence | [report](primary_information/report.md), [values](primary_information/primary_information_summary.csv) |
| `sensitivity_analysis/` | Saved lag and Theiler-window checks; original and common-source cohorts; historical k checks | [report](sensitivity_analysis/report.md), [all values](sensitivity_analysis/all_sensitivity_results.csv), [sample counts](sensitivity_analysis/lag_sample_counts.csv) |
| `preprocessing/` | Quality-filtering audit, descriptive summaries, gap tables, ACF results and the 45-hour selection | [preprocessing audit](preprocessing/preprocessing_audit.json), [ACF report](preprocessing/autocorrelation_report.md) |
| `exploratory_figures/` | Original time series, distributions, height scatterplots, coverage and autocorrelation plots | Browse PNG files |

For the final presentation figures and integrated discussion, use ../deliverables/. Robust site ordering across sensitivity settings is descriptive and does not establish significance. k-sensitivity files are preserved historical material, excluded from the final main report.

Reports/logs and CSV metadata were created under earlier folder names; their numeric values and audit records are unchanged. Current Python entry points use these new paths. Historical references resolve through src/artifact_paths.py.
