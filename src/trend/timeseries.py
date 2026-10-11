"""Pure pandas time-series logic (plan sections 13–14). No Spark here, so it is
unit-tested locally; Spark only produces the small hourly aggregates.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def detect_gaps(volume: pd.Series, ratio: float = 0.2, window: int = 12, freq: str = "5min") -> pd.Series:
    """Flag collection gaps: bins missing from the index, or with volume below
    `ratio` × the centred rolling median, or below `ratio` × the whole-series
    median (the rolling window is unreliable at the series edges, where the
    collector starts and stops). Returns a bool Series on a complete regular
    index (missing bins are added with volume 0 and flagged)."""
    full_index = pd.date_range(volume.index.min(), volume.index.max(), freq=freq)
    s = volume.reindex(full_index, fill_value=0).astype(float)
    median = s.rolling(window, center=True, min_periods=window // 2).median()
    return (s < ratio * median) | (s < ratio * s.median()) | (s == 0)


def burst_scores(
    ratio: pd.Series,
    window: int = 12,
    min_periods: int = 6,
    std_floor_ratio: float = 0.1,
    invalid: pd.Series | None = None,
) -> pd.DataFrame:
    """z-score of each bin against the PREVIOUS `window` bins only.

    - the window excludes the current bin (shift(1)) so a spike cannot lift
      its own baseline;
    - std is floored at std_floor_ratio × the whole-series std so a flat
      window cannot produce an enormous score;
    - bins flagged `invalid` (collection gaps) are excluded from baselines and
      scored NaN, as is any bin without `min_periods` valid history.
    """
    s = ratio.astype(float).copy()
    if invalid is not None:
        invalid = invalid.reindex(s.index, fill_value=False)
        s[invalid] = np.nan
    prev = s.shift(1)
    mean = prev.rolling(window, min_periods=min_periods).mean()
    std = prev.rolling(window, min_periods=min_periods).std()
    floor = std_floor_ratio * float(np.nanstd(s.values)) if s.notna().any() else 0.0
    floor = max(floor, 1e-9)
    score = (s - mean) / np.maximum(std.fillna(0.0), floor)
    score[mean.isna()] = np.nan
    return pd.DataFrame({"ratio": s, "baseline_mean": mean, "baseline_std": std, "burst_score": score})


def mark_bursts(scores: pd.DataFrame, counts: pd.Series, threshold: float, min_volume: int,
                min_lift: float = 1.0) -> pd.Series:
    """Burst = z-score above threshold AND enough posts AND a real relative
    rise (ratio >= min_lift x baseline). On smooth 5-minute share series the
    baseline std is tiny, so z alone flags rises of a few percent."""
    lift_ok = scores["ratio"] >= min_lift * scores["baseline_mean"]
    return (scores["burst_score"] > threshold) & (counts.reindex(scores.index).fillna(0) >= min_volume) & lift_ok


def merge_events(is_burst: pd.Series, scores: pd.Series, merge_gap_bins: int = 2,
                 bin_size: pd.Timedelta = pd.Timedelta(minutes=5)) -> list[dict]:
    """Group burst bins separated by <= merge_gap_bins bins into events."""
    hours = is_burst[is_burst].index
    events: list[dict] = []
    for h in hours:
        if events and (h - events[-1]["end"]) <= merge_gap_bins * bin_size:
            events[-1]["end"] = h
        else:
            events.append({"start": h, "end": h})
    for e in events:
        span = scores.loc[e["start"]:e["end"]]
        e["peak"] = span.idxmax()
        e["max_burst_score"] = float(span.max())
        e["bins"] = int(((e["end"] - e["start"]) / bin_size) + 1)
    return events
