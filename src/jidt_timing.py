"""Preserve elapsed-hour indices when loading already aligned MI/CMI into JIDT.

Requires the CPU Kraskov calculator and addObservationsTrackObservationIDs API.
No JVM dependency is imported until the conversion callback is used by the caller.
"""
import numpy as np
from autocorrelation import hourly_indices


def timed_blocks(timestamps):
    """Yield (row_start, row_stop, elapsed_hour_start) for consecutive hourly runs."""
    indices = hourly_indices(timestamps)
    starts = np.r_[0, np.flatnonzero(np.diff(indices) != 1) + 1]
    stops = np.r_[starts[1:], len(indices)]
    for start, stop in zip(starts, stops):
        yield int(start), int(stop), int(indices[start])


def load_observations(calculator, timestamps, arrays, window_hours, to_java):
    """Load initialized MI (two arrays) or CMI (three arrays), without estimating.

    `arrays` are finite n-by-d arrays in the same row order as timestamps.
    `to_java` converts an n-by-d numpy array to Java double[][], e.g.
    lambda a: jpype.JArray(jpype.JDouble, 2)(a.tolist()).
    Direction is one n-by-2 array with columns [Dx, Dy].
    The calculator must be initialized with matching dimensions before calling.
    For lagged analyses first align on actual timestamps, then call this helper.
    """
    if isinstance(window_hours, bool) or int(window_hours) != window_hours or window_hours < 0:
        raise ValueError("Window must be a nonnegative integer number of hours")
    blocks = list(timed_blocks(timestamps))
    if len(arrays) not in (2, 3):
        raise ValueError("Provide two MI arrays or three CMI arrays")
    values = [np.asarray(a, dtype=float) for a in arrays]
    if any(a.ndim != 2 or len(a) != len(timestamps) or not np.isfinite(a).all() for a in values):
        raise ValueError("Require finite n-by-d arrays aligned with timestamps")
    if not hasattr(calculator, "addObservationsTrackObservationIDs"):
        raise RuntimeError("JIDT version lacks elapsed-time tracking API; do not fall back to compressed rows")
    calculator.setProperty("DYN_CORR_EXCL", str(int(window_hours)))
    calculator.setProperty("USE_GPU", "false")
    if len(values) == 2:
        calculator.setProperty("TIME_DIFF", "0")
    calculator.startAddObservations()
    for start, stop, hour in blocks:
        # Same observation-set ID across ALL runs of a site: short gaps do not
        # create independent trials. startTimeIndex preserves their true spacing.
        calculator.addObservationsTrackObservationIDs(
            *[to_java(a[start:stop]) for a in values], 0, hour)
    calculator.finaliseAddObservations()
