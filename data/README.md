# Data

- **raw/**: original offshore archive exports and nearshore deployment packages, including source CSVs, readmes and supplied images. Original file names and contents are retained.
- **processed/**: figure_eight_pools.csv and stockton.csv — complete, quality-filtered concurrent observations used for the original primary analysis (N=6,867 /10,522).

Pairings are Port Kembla/Wollongong–Figure Eight Pools and Sydney–Stockton. Offshore bulk parameters are hourly; nearshore bulk parameters are half-hourly; matched observations are effectively hourly with missing gaps. Heights use offshore WHTH and nearshore Hsig, both time-domain significant heights. No interpolation or additional outlier removal was introduced by moving these files.

Quality-filtering and coverage evidence lives in ../results/preprocessing/. The preprocessing entry point is src/preprocess.py, run from the project root. Original exports were relocated without alteration; recorded historical paths can be translated using src/artifact_paths.py.
