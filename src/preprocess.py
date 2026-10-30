"""Prepare concurrent wave observations and exploratory outputs; run from any directory."""
from pathlib import Path
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
DATA = ROOT / "raw_data"
ARCHIVE = "Wave_buoys_Observations_-_Australia_-_delayed_(National_Wave_Archive)"
PAIRS = {
    "figure_eight_pools": ("Figure8Pools", "Port Kembla", ARCHIVE + ".csv"),
    "stockton": ("Stockton", "Sydney", ARCHIVE + "-2.csv"),
}


def numeric(frame, columns):
    for column in columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")


#data cleaning and engineering
def prepare(name, token, station, filename):
    # Read the original deployment and offshore export.
    near_path, = DATA.glob(f"*{token}*/*Parameters.csv")
    near = pd.read_csv(near_path)
    off = pd.read_csv(DATA / filename, comment="#")
    assert set(off.site_name) == {station}, "Unexpected offshore station"

    numeric(near, ["Hsig", "Qflag"])
    # The hight of the wave we are using in this assi is the significant wave height!!!
    numeric(off, ["WHTH", "WPPE", "WPDI", "WAVE_quality_control"])

    #unify timestamps
    near["timestamp_utc"] = (pd.to_datetime(near.Time, format="%d-%b-%Y %H:%M:%S", errors="raise")
                             .dt.tz_localize("Etc/GMT-10").dt.tz_convert("UTC"))
    off["timestamp_utc"] = pd.to_datetime(off.TIME, utc=True, errors="raise")

    audit = {"site": name, "offshore_station": station,
             "offshore_file": str((DATA / filename).relative_to(ROOT)),
             "height_definition": "time-domain significant height (not spectral Hm0)",
             "height_columns": {"Ho": "WHTH", "Hn": "Hsig"},
             "offshore_spectral_height_nonmissing_rows": int(pd.to_numeric(off.WSSH, errors="coerce").notna().sum()),
             "direction_components": ["Dx", "Dy"], "nearshore_file": str(near_path.relative_to(ROOT))}
    for label, data in [("offshore", off), ("nearshore", near)]:
        audit[label + "_raw_rows"] = len(data)
        audit[label + "_duplicate_timestamps"] = int(data.timestamp_utc.duplicated().sum())
        audit[label + "_quality_flags"] = data["WAVE_quality_control" if label == "offshore" else "Qflag"].value_counts(dropna=False).to_dict()
        if data.timestamp_utc.duplicated().any():
            raise ValueError(f"Duplicate timestamps in {label}: resolve before matching")
    audit["concurrent_rows_before_qc"] = len(near.merge(off, on="timestamp_utc", validate="one_to_one"))
    near_good = near.loc[near.Qflag.eq(1), ["timestamp_utc", "Hsig", "Qflag"]]
    off_good = off.loc[off.WAVE_quality_control.eq(1), ["timestamp_utc", "WHTH", "WPPE", "WPDI", "WAVE_quality_control"]]
    for label, raw, good in [("nearshore", near, near_good), ("offshore", off, off_good)]:
        audit[label + "_qc_excluded"] = len(raw) - len(good)
        audit[label + "_qc_retained"] = len(good)

    joined = near_good.merge(off_good, on="timestamp_utc", how="inner", validate="one_to_one")
    # Distinguish no raw counterpart from a counterpart excluded by QC.
    for label, good, other_raw, other_good in [
        ("nearshore", near_good, off, off_good),
        ("offshore", off_good, near, near_good),
    ]:
        raw_match = good.timestamp_utc.isin(other_raw.timestamp_utc)
        qc_match = good.timestamp_utc.isin(other_good.timestamp_utc)
        audit[label + "_qc_retained_without_raw_counterpart"] = int((~raw_match).sum())
        audit[label + "_qc_retained_counterpart_excluded_by_qc"] = int((raw_match & ~qc_match).sum())
    audit["concurrent_qc_rows"] = len(joined)
    joined = joined.rename(columns={"Hsig": "Hn", "WHTH": "Ho", "WPPE": "Tp_o", "WPDI": "theta_deg"})
    complete = joined.dropna(subset=["Ho", "Hn", "Tp_o", "theta_deg"]).copy()
    audit["matched_rows_removed_missing_variables"] = len(joined) - len(complete)
    complete = complete.sort_values("timestamp_utc").reset_index(drop=True)
    assert np.isfinite(complete[["Ho", "Hn", "Tp_o", "theta_deg"]]).all().all()
    assert complete[["Ho", "Hn"]].ge(0).all().all(), "Wave heights must be nonnegative"
    assert complete.Tp_o.gt(0).all(), "Peak periods must be strictly positive"
    assert complete.theta_deg.between(0, 360).all()
    radians = np.deg2rad(complete.theta_deg)

    # Two components of ONE directional variable for subsequent CMI.
    complete["Dx"] = np.cos(radians)
    complete["Dy"] = np.sin(radians)

    assert np.allclose(complete.Dx**2 + complete.Dy**2, 1)
    if complete.empty:
        raise ValueError(f"{name}: no complete concurrent observations")
    gaps = complete.timestamp_utc.diff().dt.total_seconds().div(3600)
    gap_table = pd.DataFrame({"previous_timestamp_utc": complete.timestamp_utc.shift(),
                              "next_timestamp_utc": complete.timestamp_utc,
                              "elapsed_hours": gaps})
    gap_table = gap_table.loc[gaps.gt(1)]
    # UTC clock-hour grid: do not anchor to a possibly off-grid first observation.
    timestamps = pd.DatetimeIndex(complete.timestamp_utc)
    grid = pd.date_range(timestamps.min().ceil("h"), timestamps.max().floor("h"), freq="h")
    off_grid = timestamps != timestamps.floor("h")
    missing_slots = grid.difference(timestamps)
    audit.update(usable_rows=len(complete), first_timestamp_utc=str(timestamps.min()),
                 last_timestamp_utc=str(timestamps.max()), expected_hourly_slots=len(grid),
                 matched_timestamps_on_hourly_grid=bool(not off_grid.any()),
                 off_grid_rows=int(off_grid.sum()),
                 retained_hourly_slots=int(grid.isin(timestamps).sum()),
                 missing_hourly_slots=len(missing_slots),
                 gaps_longer_than_one_hour=len(gap_table),
                 largest_interval_hours=float(gaps.max()),
                 pearson_r=float(complete.Ho.corr(complete.Hn)))
    complete.to_csv(ROOT / "outputs/cleaned" / f"{name}.csv", index=False)
    gap_table.to_csv(ROOT / "outputs/results" / f"{name}_gaps.csv", index=False)
    complete[["Ho", "Hn", "Tp_o", "theta_deg"]].describe().to_csv(ROOT / "outputs/results" / f"{name}_descriptive_statistics.csv")
    plot(name, complete, grid)
    return audit


# plot for statistical and visual inspection of the data
def plot(name, data, grid):
    title = name.replace("_", " ").title()
    destination = ROOT / "outputs/figures"
    plt.rcParams.update({"figure.dpi": 120, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(12, 4))

    # Reindex only to draw breaks in lines: no values are interpolated or saved.
    plot_grid = grid.union(pd.DatetimeIndex(data.timestamp_utc)).sort_values()
    series = data.set_index("timestamp_utc").reindex(plot_grid)
    ax.plot(plot_grid, series.Ho, label="Offshore", linewidth=.6)
    ax.plot(plot_grid, series.Hn, label="Nearshore", linewidth=.6, alpha=.8)
    ax.set(title=f"{title}: concurrent wave heights", ylabel="Significant height (m)", xlabel="Time (UTC)")
    ax.legend(); fig.autofmt_xdate(); fig.tight_layout()
    fig.savefig(destination / f"{name}_time_series.png"); plt.close(fig)

    # offshore vs nearshore scatter and histograms
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    axes[0].scatter(data.Ho, data.Hn, s=3, alpha=.25)
    limit = max(data.Ho.max(), data.Hn.max())
    axes[0].plot([0, limit], [0, limit], "k--", linewidth=.8, label="Equal heights")
    axes[0].legend(); axes[0].set_title(f"Pearson r = {data.Ho.corr(data.Hn):.3f}")
    for ax, column, cmap, label in [(axes[1], "Tp_o", "viridis", "Offshore peak period (s)"),
                                    (axes[2], "theta_deg", "twilight", "Offshore peak direction (degrees)")]:
        kwargs = {"vmin": 0, "vmax": 360} if column == "theta_deg" else {}
        points = ax.scatter(data.Ho, data.Hn, c=data[column], cmap=cmap, s=4, alpha=.6, **kwargs)
        fig.colorbar(points, ax=ax, label=label)
    for ax in axes:
        ax.set(xlabel="Offshore height (m)", ylabel="Nearshore height (m)")
    fig.suptitle(title); fig.tight_layout()
    fig.savefig(destination / f"{name}_scatterplots.png"); plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    bins = np.histogram_bin_edges(np.concatenate([data.Ho, data.Hn]), bins=40)
    axes[0].hist(data.Ho, bins=bins, alpha=.6, label="Offshore")
    axes[0].hist(data.Hn, bins=bins, alpha=.6, label="Nearshore")
    axes[0].set_xlabel("Significant height (m)"); axes[0].legend()
    axes[1].hist(data.Tp_o, bins=40); axes[1].set_xlabel("Offshore peak period (s)")
    axes[2].hist(data.theta_deg, bins=np.linspace(0, 360, 37)); axes[2].set(xlabel="Offshore peak direction (degrees)", xlim=(0, 360))
    for ax in axes: ax.set_ylabel("Observations")
    fig.suptitle(title); fig.tight_layout()
    fig.savefig(destination / f"{name}_distributions.png"); plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(12, 6))
    available = pd.Series(grid.isin(data.timestamp_utc).astype(int), index=grid)
    daily = available.resample("D").agg(["sum", "count"])
    axes[0].plot(daily.index, daily["sum"] / daily["count"] * 100, linewidth=.8)
    axes[0].set(ylabel="Available hourly slots (%)", ylim=(0, 105), title="Daily coverage (boundary days use only in-range hours)")
    intervals = data.timestamp_utc.diff().dt.total_seconds().div(3600).dropna()
    axes[1].hist(intervals, bins=np.arange(.5, intervals.max() + 1.5, 1))
    axes[1].set(xlabel="Elapsed time between retained observations (hours)", ylabel="Count", yscale="log")
    fig.suptitle(title); fig.autofmt_xdate(); fig.tight_layout()
    fig.savefig(destination / f"{name}_coverage_gaps.png"); plt.close(fig)


def main():
    for folder in ["cleaned", "figures", "results"]:
        (ROOT / "outputs" / folder).mkdir(parents=True, exist_ok=True)
    audits = [prepare(name, *configuration) for name, configuration in PAIRS.items()]
    (ROOT / "outputs/results/preprocessing_audit.json").write_text(json.dumps(audits, indent=2) + "\n")
    pd.DataFrame([{k: v for k, v in audit.items() if not isinstance(v, dict)} for audit in audits]).to_csv(ROOT / "outputs/results/preprocessing_summary.csv", index=False)
    for audit in audits:
        print(f"{audit['site']}: N={audit['usable_rows']}, Pearson r={audit['pearson_r']:.4f}")


if __name__ == "__main__":
    main()
