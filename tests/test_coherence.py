import math

import pytest

pytest.importorskip("pyspark")  # module imports pyspark; the math itself is pure

from src.model.coherence import npmi_from_counts  # noqa: E402


def test_words_that_always_cooccur_score_one():
    n = 100
    single = {"vote": 10, "ballot": 10}
    pair = {("ballot", "vote"): 10}
    assert npmi_from_counts(n, single, pair, [["vote", "ballot"]])[0] == pytest.approx(1.0, abs=1e-6)


def test_independent_words_score_near_zero():
    n = 10000
    single = {"a": 1000, "b": 1000}
    pair = {("a", "b"): 100}  # P(a,b) = P(a)P(b)
    assert abs(npmi_from_counts(n, single, pair, [["a", "b"]])[0]) < 1e-6


def test_never_cooccurring_words_score_minus_one():
    assert npmi_from_counts(100, {"a": 5, "b": 5}, {}, [["a", "b"]])[0] == -1.0


def test_unknown_words_are_skipped():
    assert math.isnan(npmi_from_counts(100, {}, {}, [["x", "y"]])[0])
