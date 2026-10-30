# Wave dependence: preprocessing and exploration

> **Integration gate:** The focused Java test found that JIDT 1.6.1 fails exact 45-hour exclusion across gaps. Main analysis now stops by default. Earlier results below use the documented row-window approximation. See [the focused integration report](outputs/results/theiler_integration/report.md). Run `python3 src/check_theiler_integration.py` to reproduce the check; status 1 indicates the elapsed-hour criterion failed. The selected 45-hour baseline and cleaned data are unchanged.


Run `python3 src/preprocess.py` from this directory (or run the script by its absolute path). Dependencies for these steps are in `requirements.txt`. Original input files are read without modification. Running the script again replaces the generated outputs.

## Method

Inputs are read from `raw_data/`. The Port Kembla archive export is paired with Figure Eight Pools; the Sydney export ending `-2.csv` is paired with Stockton. Offshore CSV metadata lines beginning with `#` are skipped. Numeric blanks become missing values. Nearshore time is fixed AEST (UTC+10, with no daylight saving); offshore time is UTC. Both are converted to UTC before an exact, one-to-one timestamp join. Duplicate timestamps cause an error instead of silent removal.

Only nearshore `Qflag == 1` and offshore `WAVE_quality_control == 1` are retained. The pipeline then drops concurrent rows missing required variables, sorts timestamps, and checks finite values, nonnegative heights and strictly positive peak periods, and directions in [0, 360]. These range checks raise errors for investigation rather than automatically removing observations. There is no outlier trimming or interpolation.

The common wave-height definition is time-domain significant height: offshore `WHTH` maps to `Ho`, and nearshore `Hsig` maps to `Hn`. These are matching time-domain significant heights (mean of the highest third of individual waves), not spectral significant height Hm0 = 4 sqrt(m0). [Kinsela et al. (2024), Table 4 and Fig. 4](https://www.nature.com/articles/s41597-023-02865-x) distinguish the definitions and compare Hm0 offshore–nearshore. Offshore spectral height `WSSH` is entirely empty in both current exports, so nearshore spectral height `Hm0` is not used here. Reproducing that spectral comparison requires populated offshore `WSSH` and nearshore `Hm0`; do not mix `WHTH` with `Hm0` or relabel time-domain heights as Hm0. The audit records the selected columns and offshore spectral availability. Offshore `WPPE` maps to `Tp_o` in seconds, and `WPDI` maps to `theta_deg` in degrees true. `Dx = cos(theta)` and `Dy = sin(theta)` use radians internally and together represent one two-dimensional direction variable for subsequent CMI estimation. The nearshore README quality summaries and offshore CSV QC metadata document the quality flags. Offshore metadata define `WPPE` as the spectral peak period, `WPDI` as the wave-from direction at the spectral peak relative to true north, and flag 1 as Good (passed documented required QC tests).

## Outputs

- `outputs/cleaned/{site}.csv`: concurrent complete observations, UTC timestamps, four analysis variables, both quality flags, and the two direction components.
- `outputs/results/preprocessing_audit.json`: input paths, quality-flag counts, duplicate counts, QC losses, unmatched counts, missing-variable losses, coverage, and Pearson correlation. For each QC-retained source, `*_without_raw_counterpart` counts timestamps absent from the other raw file, while `*_counterpart_excluded_by_qc` counts present counterparts excluded by the QC rule. Only `*_qc_excluded` counts exclusions within that source. These two-sided counts are not sequential losses from one dataset; a QC exclusion can include missing or suspect records, not just failed tests.
- `outputs/results/preprocessing_summary.csv`: one summary row per site.
- `outputs/results/{site}_descriptive_statistics.csv`: numeric descriptions; direction statistics are ordinary linear summaries, not circular statistics.
- `outputs/results/{site}_gaps.csv`: intervals greater than one hour in the retained dataset. These can reflect QC exclusion, input gaps, or missing required measurements.
- `outputs/figures/{site}_time_series.png`: matched heights, with line breaks at missing hourly slots.
- `outputs/figures/{site}_scatterplots.png`: height relationship, Pearson correlation, and period/direction colouring.
- `outputs/figures/{site}_distributions.png`: height, period, and direction histograms.
- `outputs/figures/{site}_coverage_gaps.png`: daily hourly coverage and elapsed-time distribution.

Coverage is measured against UTC clock-hour timestamps within the first and last retained observations (ceil/floor bounds). The audit reports whether all retained timestamps lie on this grid and counts off-grid rows separately. Missing slots are counted by timestamp set difference, so off-grid rows cannot falsely fill hourly slots or produce negative missing counts. Off-grid observations remain in the cleaned output and time-series plot. Gap durations use actual elapsed time, irrespective of grid alignment. Boundary days have partial denominators. Empty hourly slots inserted for plotting contain only NaNs and do not change the saved observations. Pearson correlation is descriptive; no significance or causal interpretation is attached. The different observation periods and sample sizes need to be considered in the later comparison. MI/CMI estimation is a subsequent step and is not implemented by this script.

## Temporal autocorrelation (step 6)

Run `python3 src/autocorrelation.py` after preprocessing. This computes exact elapsed-hour, pairwise-complete ACFs for `Ho`, `Hn`, `Tp_o`, `Dx`, and `Dy`, without interpolation. It saves per-lag correlations and pair counts, decay summaries, ACF plots, timestamp mappings for JIDT, and `outputs/results/theiler_window_selection.json`. Off-grid timestamps cause an explicit error rather than silent rounding.

See [the autocorrelation report](outputs/results/autocorrelation_report.md) for the definition, selection rule, numerical results and limitations. The selected site windows are 30 h (Figure Eight Pools) and 45 h (Stockton); the common baseline is 45 h, with planned sensitivity settings 0, 23, 45 and 90 h. These are an e-folding heuristic, not proof of independence.

`src/jidt_timing.py` prepares already aligned observations for later CPU JIDT MI/CMI using actual elapsed-hour indices across gaps and a shared observation-set ID within each site. It preserves `[Dx, Dy]` as a single two-dimensional variable. The helper requires a newer time-tracking API. Subsequent integration with the locally supplied JIDT 1.6.1 jar found that API absent; see the version-specific correction and completed MI/CMI results below.

Run timing and ACF checks with `python3 -m unittest discover -s tests`.

## JIDT estimates, surrogate diagnostics and sensitivities (steps 7–9)

Implemented through the supplied **JIDT 1.6.1 Java jar**, without GUI automation or a Python JVM bridge:

```sh
python3 src/information_analysis.py --pilot
python3 src/information_analysis.py --surrogates 199
python3 src/report_information.py
```

The default jar is `/Users/attie/Desktop/Information theory/jidt-1.6.1/infodynamics.jar`; override with `--jar`. Java and javac are required. The pilot uses 9 surrogates per primary measure, followed by 199 final primary surrogate diagnostics. CMI references also compare 25/50/100 offshore-height strata and unrestricted shuffling. These are approximate diagnostics because temporal dependence and coarse conditioning limit the null models.

See [the completed analysis report](outputs/results/information_analysis_report.md), [all run results](outputs/results/information_results.csv), [primary estimates](outputs/results/primary_information_measures.csv), and [settings](outputs/results/information_settings.json). Figures include primary estimates, one-factor sensitivities and surrogate distributions. Units are saved as both nats and bits.

**Version-specific exclusion correction:** JIDT 1.6.1 lacks the actual-time tracking API used by the earlier helper. These runs use DYN_CORR_EXCL=45 retained rows as a conservative exclusion of every pair within 45 hours plus extra pairs across gaps. The extra exclusions are quantified in `information_exclusion_audit.csv`. This is not an exact elapsed-hour window and does not imply conservative p-values. The newer-API helper is not used by this runner.

Sensitivity runs compare k=3/4/6/8, index windows=0/23/45/90, and physical lags=0/0.5/1/2 hours. Lagged observations are rematched from raw timestamped records, with both all-available and common-timestamp cohorts. No interpolation or extreme-wave trimming is applied. The seven tests include real JIDT integration, analytic Gaussian MI and conditional-confounding examples.

## Official-source exact-time integration update

The unmodified official JIDT snapshot at commit `1ca832235e64ae5b3a482dc0ead6f9b2ff2a0456` compiled and passed exact elapsed-hour Java tests, including 44/45/46-hour boundaries across gaps, stored set/time indices, marginal searches and actual nearest neighbours. Both real sites retain all observations. See [the exact integration report](outputs/results/theiler_exact_integration/report.md) and [acceptance evidence](outputs/results/theiler_exact_integration/acceptance.json).

The new jar and provenance are in `lib/jidt-official/`; the original external 1.6.1 jar remains untouched. `ElapsedHourLoader.java` and `WaveInformationExact.java` provide verified exact-time application loading. The main Python runner remains stopped by default pending connection to this adapter; previous main-analysis results still use row-based exclusion. No main analysis was rerun.
