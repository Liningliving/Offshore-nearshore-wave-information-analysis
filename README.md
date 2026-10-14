# Wave dependence: preprocessing and exploration

Run `python3 src/preprocess.py` from this directory (or run the script by its absolute path). Dependencies for these steps are in `requirements.txt`. Original input files are read without modification. Running the script again replaces the generated outputs.

## Method

The Port Kembla archive export is paired with Figure Eight Pools; the Sydney export ending `-2.csv` is paired with Stockton. Offshore CSV metadata lines beginning with `#` are skipped. Numeric blanks become missing values. Nearshore time is fixed AEST (UTC+10, with no daylight saving); offshore time is UTC. Both are converted to UTC before an exact, one-to-one timestamp join. Duplicate timestamps cause an error instead of silent removal.

Only nearshore `Qflag == 1` and offshore `WAVE_quality_control == 1` are retained. The pipeline then drops concurrent rows missing required variables, sorts timestamps, and checks finite values, positive heights and periods, and directions in [0, 360]. These range checks raise errors for investigation rather than automatically removing observations. There is no outlier trimming or interpolation.

The common wave-height definition is time-domain significant height: offshore `WHTH` maps to `Ho`, and nearshore `Hsig` maps to `Hn`. Offshore spectral height `WSSH` is empty, so nearshore spectral height `Hm0` is not used here. Offshore `WPPE` maps to `Tp_o` in seconds, and `WPDI` maps to `theta_deg` in degrees true. `Dx = cos(theta)` and `Dy = sin(theta)` use radians internally and together represent one two-dimensional direction variable for subsequent CMI estimation. The nearshore README quality summaries and offshore CSV QC metadata document the quality flags.

## Outputs

- `outputs/cleaned/{site}.csv`: concurrent complete observations, UTC timestamps, four analysis variables, both quality flags, and the two direction components.
- `outputs/results/preprocessing_audit.json`: input paths, quality-flag counts, duplicate counts, QC losses, unmatched counts, missing-variable losses, coverage, and Pearson correlation. Unmatched counts describe the two sides of a join; they should not be added as sequential losses from one dataset.
- `outputs/results/preprocessing_summary.csv`: one summary row per site.
- `outputs/results/{site}_descriptive_statistics.csv`: numeric descriptions; direction statistics are ordinary linear summaries, not circular statistics.
- `outputs/results/{site}_gaps.csv`: intervals greater than one hour in the retained dataset. These can reflect QC exclusion, input gaps, or missing required measurements.
- `outputs/figures/{site}_time_series.png`: matched heights, with line breaks at missing hourly slots.
- `outputs/figures/{site}_scatterplots.png`: height relationship, Pearson correlation, and period/direction colouring.
- `outputs/figures/{site}_distributions.png`: height, period, and direction histograms.
- `outputs/figures/{site}_coverage_gaps.png`: daily hourly coverage and elapsed-time distribution.

Coverage is measured against hourly timestamps between the first and last retained observations. Boundary days have partial denominators. Empty hourly slots inserted for plotting contain only NaNs and do not change the saved observations. Pearson correlation is descriptive; no significance or causal interpretation is attached. The different observation periods and sample sizes need to be considered in the later comparison. MI/CMI estimation is a subsequent step and is not implemented by this script.
