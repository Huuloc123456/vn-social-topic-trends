"""NPMI topic coherence computed with Spark (plan 11.4).

Reference corpus: the `tokens` column of the clean model set (lowercase,
basic stopwords, unigrams) – the same for every configuration, so NPMI is
comparable across stopword lists, n-grams and algorithms (plan 11.5).
Bigram terms ("climate change") are split into their unigrams.
"""
from __future__ import annotations

import math
from itertools import combinations

from pyspark.sql import functions as F

EPS = 1e-12


def _unigrams(term: str) -> list[str]:
    return term.split(" ")


def npmi_from_counts(n_docs: int, df_single: dict, df_pair: dict, topics: list[list[str]]) -> list[float]:
    """Pure function: average NPMI over the term pairs of each topic."""
    scores = []
    for terms in topics:
        values = []
        for a, b in combinations(terms, 2):
            pa = df_single.get(a, 0) / n_docs
            pb = df_single.get(b, 0) / n_docs
            pab = df_pair.get(tuple(sorted((a, b))), 0) / n_docs
            if pa == 0 or pb == 0:
                continue
            if pab == 0:
                values.append(-1.0)
                continue
            pmi = math.log((pab + EPS) / (pa * pb))
            values.append(pmi / (-math.log(pab + EPS)))
        scores.append(sum(values) / len(values) if values else float("nan"))
    return scores


def npmi(reference_df, topics: list[list[str]], tokens_col: str = "tokens") -> tuple[float, list[float]]:
    """Returns (model NPMI, per-topic NPMI) for topics given as top-term lists."""
    topics_uni = []
    for terms in topics:
        seen = []
        for t in terms:
            for u in _unigrams(t):
                if u not in seen:
                    seen.append(u)
        topics_uni.append(seen[: len(terms)])
    vocab = sorted({w for t in topics_uni for w in t})

    docs = reference_df.select(
        F.array_sort(F.array_distinct(F.array_intersect(F.col(tokens_col), F.array(*[F.lit(w) for w in vocab]))))
        .alias("t")
    ).cache()
    n_docs = docs.count()
    single = {r["w"]: r["c"] for r in docs.select(F.explode("t").alias("w")).groupBy("w")
              .agg(F.count("*").alias("c")).collect()}
    pairs = (docs.filter(F.size("t") >= 2)
             .select(F.explode("t").alias("a"), F.col("t"))
             .select("a", F.explode("t").alias("b"))
             .filter(F.col("a") < F.col("b"))
             .groupBy("a", "b").count().collect())
    pair_counts = {(r["a"], r["b"]): r["count"] for r in pairs}
    docs.unpersist()

    per_topic = npmi_from_counts(n_docs, single, pair_counts, topics_uni)
    valid = [s for s in per_topic if not math.isnan(s)]
    return (sum(valid) / len(valid) if valid else float("nan")), per_topic
