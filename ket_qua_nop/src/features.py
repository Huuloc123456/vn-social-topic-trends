"""Feature pipelines (plan section 10): one branch for KMeans (TF-IDF + L2),
one for LDA (raw term counts). Both start from `text_clean` so the saved
PipelineModel can score new text in the dashboard with the same steps.
"""
from __future__ import annotations

from pyspark.ml import Pipeline
from pyspark.ml.feature import (
    IDF,
    CountVectorizer,
    NGram,
    Normalizer,
    RegexTokenizer,
    SQLTransformer,
    StopWordsRemover,
    Word2Vec,
)
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType

from src.common import domain_stopwords, language_stopwords


def token_stages(use_domain_sw: bool, use_bigram: bool, language: str) -> tuple[list, str]:
    stages = [
        RegexTokenizer(inputCol="text_clean", outputCol="tok_all", pattern=r"\s+", minTokenLength=2),
        StopWordsRemover(inputCol="tok_all", outputCol="tok_basic", stopWords=language_stopwords(language)),
    ]
    col = "tok_basic"
    if use_domain_sw:
        stages.append(StopWordsRemover(inputCol=col, outputCol="tok_domain",
                                       stopWords=domain_stopwords(language)))
        col = "tok_domain"
    if use_bigram:
        stages.append(NGram(n=2, inputCol=col, outputCol="tok_bigram"))
        stages.append(SQLTransformer(statement=f"SELECT *, concat({col}, tok_bigram) AS tok_final FROM __THIS__"))
        col = "tok_final"
    return stages, col


def kmeans_prep(cfg: dict, use_domain_sw: bool, use_bigram: bool) -> Pipeline:
    stages, col = token_stages(use_domain_sw, use_bigram, cfg["preprocessing"]["language"])
    f = cfg["features"]
    stages += [
        CountVectorizer(inputCol=col, outputCol="tf", vocabSize=f["vocab_size"], minDF=float(f["min_df"])),
        IDF(inputCol="tf", outputCol="tfidf"),
        Normalizer(inputCol="tfidf", outputCol="features", p=2.0),
    ]
    return Pipeline(stages=stages)


def lda_prep(cfg: dict, use_domain_sw: bool, use_bigram: bool) -> Pipeline:
    stages, col = token_stages(use_domain_sw, use_bigram, cfg["preprocessing"]["language"])
    stages.append(CountVectorizer(inputCol=col, outputCol="features",
                                  vocabSize=cfg["lda"]["vocab_size"], minDF=float(cfg["features"]["min_df"])))
    return Pipeline(stages=stages)


def w2v_prep(cfg: dict, use_domain_sw: bool, use_bigram: bool) -> Pipeline:
    """Dense document vectors: the mean of Word2Vec word vectors, L2-normalised.
    Short posts share few exact words, so sparse TF-IDF vectors are nearly
    orthogonal and KMeans collapses; word embeddings place synonyms close."""
    stages, col = token_stages(use_domain_sw, use_bigram, cfg["preprocessing"]["language"])
    w = cfg["word2vec"]
    stages += [
        Word2Vec(inputCol=col, outputCol="w2v", vectorSize=w["vector_size"], minCount=w["min_count"],
                 windowSize=w["window"], maxIter=w["max_iter"], seed=w["seed"], numPartitions=w["partitions"]),
        Normalizer(inputCol="w2v", outputCol="features", p=2.0),
    ]
    return Pipeline(stages=stages)


def final_tokens_col(prep_model) -> str:
    """Name of the token column that feeds the vectoriser."""
    for stage in prep_model.stages:
        if hasattr(stage, "getInputCol") and type(stage).__name__ in ("CountVectorizerModel", "Word2VecModel"):
            return stage.getInputCol()
    raise ValueError("no vectoriser in pipeline")


_nnz = F.udf(lambda v: int(v.numNonzeros()) if v is not None else 0, IntegerType())


def drop_empty(df, col: str = "features"):
    """Documents whose tokens all fell outside the vocabulary cannot be modelled."""
    return df.withColumn("_nnz", _nnz(col)).filter("_nnz > 0").drop("_nnz")


def vocabulary(prep_model) -> list[str]:
    for stage in prep_model.stages:
        if hasattr(stage, "vocabulary"):
            return list(stage.vocabulary)
        if type(stage).__name__ == "Word2VecModel":
            return [r["word"] for r in stage.getVectors().select("word").collect()]
    raise ValueError("no vectoriser in pipeline")


def class_tfidf_terms(df, topic_col: str, tokens_col: str, k: int, n: int) -> list[list[str]]:
    """c-TF-IDF: rank terms per cluster by tf(t,c) * log(1 + A / f(t)), where
    A is the mean token count per cluster and f(t) the term's total count.
    Used for clusters whose centroid is not in term space (Word2Vec)."""
    from pyspark.sql import Window

    tc = df.select(topic_col, F.explode(tokens_col).alias("term")).groupBy(topic_col, "term").count()
    totals = tc.groupBy(topic_col).agg(F.sum("count").alias("c_total"))
    avg_tokens = totals.agg(F.avg("c_total")).first()[0]
    ft = tc.groupBy("term").agg(F.sum("count").alias("f"))
    ranked = (tc.join(totals, topic_col).join(ft, "term")
              .withColumn("w", (F.col("count") / F.col("c_total")) * F.log(1 + F.lit(avg_tokens) / F.col("f")))
              .filter("count >= 5")
              .withColumn("r", F.row_number().over(Window.partitionBy(topic_col).orderBy(F.desc("w"))))
              .filter(f"r <= {n}").orderBy(topic_col, "r").collect())
    out = [[] for _ in range(k)]
    for row in ranked:
        out[row[topic_col]].append(row["term"])
    return out
