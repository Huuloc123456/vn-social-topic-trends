import numpy as np
import pandas as pd

from src.trend.timeseries import burst_scores, detect_gaps, mark_bursts, merge_events


def series(values, start="2026-06-01 07:50"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="5min"), dtype=float)


def test_spike_is_detected_and_does_not_lift_its_own_baseline():
    rng = np.random.default_rng(0)
    base = 0.10 + rng.normal(0, 0.005, 100)
    base[80] = 0.30
    out = burst_scores(series(base), window=12, min_periods=6)
    assert out["burst_score"].iloc[80] > 10
    assert abs(out["baseline_mean"].iloc[80] - 0.10) < 0.01


def test_flat_window_is_floored_not_infinite():
    s = series([0.1] * 30 + [0.11])
    out = burst_scores(s, window=12, min_periods=6, std_floor_ratio=0.1)
    assert np.isfinite(out["burst_score"].iloc[-1])


def test_no_score_without_enough_history():
    out = burst_scores(series([0.1] * 20), window=12, min_periods=6)
    assert out["burst_score"].iloc[:6].isna().all()
    assert out["burst_score"].iloc[7:].notna().all()


def test_gap_hours_are_excluded():
    s = series([0.1] * 20 + [0.9] + [0.1] * 5)
    invalid = pd.Series(False, index=s.index)
    invalid.iloc[20] = True
    out = burst_scores(s, invalid=invalid)
    assert np.isnan(out["burst_score"].iloc[20])
    assert out["burst_score"].iloc[21] < 2


def test_min_volume_blocks_small_bursts():
    idx = pd.date_range("2026-06-01 08:00", periods=3, freq="5min")
    scores = pd.DataFrame({"burst_score": [0.0, 5.0, 5.0], "ratio": [0.1, 0.2, 0.2],
                           "baseline_mean": [0.1, 0.1, 0.1]}, index=idx)
    counts = pd.Series([1000, 50, 900], index=idx)
    assert mark_bursts(scores, counts, 2.5, 200).tolist() == [False, False, True]


def test_min_lift_blocks_tiny_relative_rises():
    idx = pd.date_range("2026-06-01 08:00", periods=2, freq="5min")
    scores = pd.DataFrame({"burst_score": [6.0, 6.0], "ratio": [0.105, 0.13],
                           "baseline_mean": [0.10, 0.10]}, index=idx)
    counts = pd.Series([900, 900], index=idx)
    assert mark_bursts(scores, counts, 2.5, 200, min_lift=1.2).tolist() == [False, True]


def test_merge_events_groups_nearby_hours():
    idx = pd.date_range("2026-06-01 08:00", periods=10, freq="5min")
    flags = pd.Series([0, 1, 1, 0, 1, 0, 0, 0, 1, 0], index=idx).astype(bool)
    scores = pd.Series([0, 3, 4, 0, 5, 0, 0, 0, 3, 0], index=idx, dtype=float)
    events = merge_events(flags, scores, merge_gap_bins=2, bin_size=pd.Timedelta(minutes=5))
    assert len(events) == 2
    assert events[0]["start"] == idx[1] and events[0]["end"] == idx[4]
    assert events[0]["peak"] == idx[4] and events[0]["max_burst_score"] == 5.0


def test_detect_gaps_flags_missing_and_low_hours():
    s = series([100] * 30 + [5] + [100] * 30)
    low, missing = s.index[30], s.index[40]
    s = s.drop(missing)
    gaps = detect_gaps(s, ratio=0.2, window=12, freq="5min")
    assert gaps.loc[low] and gaps.loc[missing]
    assert gaps.sum() == 2


def test_detect_gaps_flags_collector_stop_at_series_edge():
    s = series([100] * 30 + [3, 2, 2, 1])
    gaps = detect_gaps(s, ratio=0.2, window=12, freq="5min")
    assert gaps.iloc[-4:].all()
    assert not gaps.iloc[:30].any()
