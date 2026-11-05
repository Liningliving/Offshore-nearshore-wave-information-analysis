"""Elapsed-time autocorrelation diagnostics; no interpolation or row thinning."""
from pathlib import Path
import argparse
import json
import os
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "ass2-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SITES = ("figure_eight_pools", "stockton")
VARIABLES = ("Ho", "Hn", "Tp_o", "Dx", "Dy")
THRESHOLD = float(np.exp(-1))
SUSTAIN_HOURS = 6


def hourly_indices(timestamps):
    """Integer elapsed hours, preserving missing hours rather than compressing them."""
    times = pd.DatetimeIndex(pd.to_datetime(timestamps, utc=True))
    if times.empty or times.hasnans or not times.is_monotonic_increasing or times.has_duplicates:
        raise ValueError("Require nonempty, sorted, unique, valid UTC timestamps")
    if not (times == times.floor("h")).all():
        raise ValueError("Hourly diagnostics require clock-hour timestamps; do not round silently")
    return np.asarray((times - times[0]) / pd.Timedelta(hours=1), dtype=np.int64)


def lagged_acf(data, max_lag):
    """Pearson correlation of observed pairs x(t), x(t+h), with lag-specific means.

    Pair endpoints must both exist; intervening hours need not exist. This is a
    descriptive, pairwise-complete ACF, without interpolation or significance bands.
    """
    hourly_indices(data.timestamp_utc)
    values = data.set_index(pd.DatetimeIndex(pd.to_datetime(data.timestamp_utc, utc=True)))
    if not np.isfinite(values[list(VARIABLES)].to_numpy()).all():
        raise ValueError("Analysis variables must be finite")
    rows = []
    for lag in range(max_lag + 1):
        positions = values.index.get_indexer(values.index + pd.Timedelta(hours=lag))
        valid = positions >= 0
        for variable in VARIABLES:
            a = values[variable].to_numpy()[valid]
            b = values[variable].to_numpy()[positions[valid]]
            r = float(np.corrcoef(a, b)[0, 1]) if len(a) >= 3 and np.std(a) > 0 and np.std(b) > 0 else np.nan
            rows.append({"variable": variable, "lag_hours": lag, "acf": r, "observed_pairs": len(a)})
    return pd.DataFrame(rows)


def decay_summary(acf, site):
    rows = []
    for variable, curve in acf.groupby("variable", sort=False):
        curve = curve.sort_values("lag_hours").reset_index(drop=True)
        # Require at least 100 pairs AND 10% of the lag-zero sample size.
        minimum_pairs = max(100, int(np.ceil(curve.observed_pairs.iloc[0] * .1)))
        supported = curve.observed_pairs.ge(minimum_pairs) & curve.acf.notna()
        positive = curve.lag_hours.gt(0)
        first = curve.loc[positive & supported & curve.acf.abs().le(THRESHOLD), "lag_hours"]
        zero = curve.loc[positive & supported & curve.acf.le(0), "lag_hours"]
        sustained = None
        for i in range(1, len(curve) - SUSTAIN_HOURS + 1):
            block = curve.iloc[i:i + SUSTAIN_HOURS]
            if (supported.iloc[i:i + SUSTAIN_HOURS].all()
                    and block.acf.abs().le(THRESHOLD).all()):
                sustained = int(block.lag_hours.iloc[0])
                break
        rows.append({"site": site, "variable": variable,
                     "first_abs_acf_below_1e_hours": int(first.iloc[0]) if len(first) else None,
                     "sustained_abs_acf_below_1e_hours": sustained,
                     "first_nonpositive_acf_hours": int(zero.iloc[0]) if len(zero) else None,
                     "minimum_pairs_required": minimum_pairs,
                     "pairs_at_selected_decay": int(curve.loc[curve.lag_hours.eq(sustained), "observed_pairs"].iloc[0]) if sustained is not None else None})
    return rows


def plot_acf(site, acf, window, destination):
    fig, axes = plt.subplots(3, 2, figsize=(12, 10))
    for ax, variable in zip(axes.flat, VARIABLES):
        curve = acf.loc[acf.variable.eq(variable)]
        ax.plot(curve.lag_hours, curve.acf, linewidth=1)
        ax.axhline(0, color="black", linewidth=.5)
        for level in (-THRESHOLD, THRESHOLD):
            ax.axhline(level, color="grey", linestyle="--", linewidth=.7)
        if window is not None:
            ax.axvline(window, color="tab:red", linestyle=":", label=f"Site window: {window} h")
            ax.legend(fontsize=8)
        ax.set(title=variable, xlabel="Actual elapsed lag (hours)", ylabel="Pairwise ACF", ylim=(-1.05, 1.05))
    ax = axes.flat[-1]
    curve = acf.loc[acf.variable.eq("Ho")]
    ax.plot(curve.lag_hours, curve.observed_pairs)
    ax.set(title="Available endpoint pairs (all variables)", xlabel="Actual elapsed lag (hours)", ylabel="Pairs")
    fig.suptitle(site.replace("_", " ").title() + ": elapsed-time autocorrelation")
    fig.tight_layout()
    fig.savefig(destination / f"{site}_autocorrelation.png", dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-lag-hours", type=int, default=336)
    args = parser.parse_args()
    if args.max_lag_hours < SUSTAIN_HOURS:
        parser.error("Maximum lag must cover the sustained-crossing interval")
    results = ROOT / "results/preprocessing"
    figures = ROOT / "results/exploratory_figures"
    results.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    summaries, diagnostics = [], []
    curves = {}
    for site in SITES:
        data = pd.read_csv(ROOT / f"data/processed/{site}.csv")
        indices = hourly_indices(data.timestamp_utc)
        acf = lagged_acf(data, args.max_lag_hours)
        acf.to_csv(results / f"{site}_autocorrelation.csv", index=False)
        curves[site] = acf
        rows = decay_summary(acf, site)
        summaries.extend(rows)
        decays = [row["sustained_abs_acf_below_1e_hours"] for row in rows]
        window = max(decays) if all(value is not None for value in decays) else None
        diagnostics.append({"site": site, "observations": len(data),
                            "uninterrupted_runs": int(1 + np.count_nonzero(np.diff(indices) != 1)),
                            "site_window_hours": window,
                            "status": "selected" if window is not None else "unresolved: extend lag range or inspect nondecaying variable"})
        # The mapping is for later JIDT loading, not a replacement cleaned dataset.
        pd.DataFrame({"timestamp_utc": data.timestamp_utc,
                      "observation_set_id": 0, "elapsed_hour_index": indices}).to_csv(
                          results / f"{site}_jidt_time_indices.csv", index=False)
        plot_acf(site, acf, window, figures)
    pd.DataFrame(summaries).to_csv(results / "autocorrelation_decay_summary.csv", index=False)
    windows = [d["site_window_hours"] for d in diagnostics]
    common = max(windows) if all(w is not None for w in windows) else None
    config = {"max_lag_hours": args.max_lag_hours,
              "acf_method": "lag-specific Pearson correlation of observed endpoint pairs separated by exact elapsed hours",
              "threshold_abs_acf": THRESHOLD, "sustained_hours": SUSTAIN_HOURS,
              "selection_rule": "First lag starting six successive supported hourly lags with |ACF| <= 1/e; maximum across Ho, Hn, Tp_o, Dx, Dy. Common baseline is maximum across sites.",
              "minimum_pair_rule": "max(100, ceil(0.1 * lag-zero pairs))",
              "sites": diagnostics, "common_baseline_window_hours": common,
              "sensitivity_windows_hours": sorted(set([0, max(1, int(np.ceil(common / 2))), common, 2 * common])) if common is not None else [],
              "jidt_property": "DYN_CORR_EXCL",
              "jidt_loading": "CPU; TIME_DIFF=0 for already aligned MI. Use addObservationsTrackObservationIDs for each consecutive hourly run, same set ID 0, startTimeIndex=actual elapsed hour. Never assign a fresh set ID at each gap.",
              "limitations": "Descriptive e-folding heuristic, not proof of independence or a significance test. Longer-lived/recurring dependence can remain; compare window sensitivity. Runtime integration must be verified against the installed JIDT version before MI/CMI estimation."}
    (results / "theiler_window_selection.json").write_text(json.dumps(config, indent=2, allow_nan=False) + "\n")
    print(pd.DataFrame(summaries).to_string(index=False))
    print(f"Common baseline Theiler window: {common} hours; per-site diagnostics: {diagnostics}")


if __name__ == "__main__":
    main()
