"""Steps 05–07 – train one configuration, evaluate it, log it to the registry.

    spark-submit src/model/train.py --model kmeans --k 10 --exp Baseline \
        --set preprocessing.use_domain_sw=false

Every run writes:
  experiments/experiment_results.csv   one registry row (plan 17)
  experiments/runs/<id>.json           top terms + sizes per topic, for the
                                       manual interpretability rating (11.6)
  hdfs:///social/models/<id>           the full PipelineModel (with --save)
"""
from __future__ import annotations

import argparse
import json
import urllib.request

import numpy as np
from pyspark.ml import PipelineModel
from pyspark.ml.clustering import LDA, BisectingKMeans, KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from pyspark.ml.functions import vector_to_array
from pyspark.sql import functions as F

from src.common import APP_ROOT, Timer, append_registry, get_spark, load_config, write_json
from src.features import class_tfidf_terms, drop_empty, final_tokens_col, kmeans_prep, lda_prep, vocabulary, w2v_prep
from src.model.coherence import npmi


def n_alive_workers() -> int:
    try:
        with urllib.request.urlopen("http://spark-master:8080/json/", timeout=5) as r:
            return sum(1 for w in json.load(r)["workers"] if w["state"] == "ALIVE")
    except Exception:
        return 0


def top_terms_from_centers(centers, vocab, n):
    return [[vocab[i] for i in np.argsort(-np.asarray(c))[:n]] for c in centers]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=["kmeans", "bkm", "lda", "w2v_kmeans"], required=True)
    p.add_argument("--k", type=int, required=True)
    p.add_argument("--exp", default="adhoc", help="experiment label, e.g. Baseline, Exp1")
    p.add_argument("--data", choices=["sample", "full"], default="sample")
    p.add_argument("--save", action="store_true", help="save PipelineModel to HDFS")
    p.add_argument("--id", default=None, help="registry id (default: next E##)")
    p.add_argument("--note", default="")
    p.add_argument("--set", nargs="*", default=[])
    a = p.parse_args()

    cfg = load_config(a.set)
    pre, ev = cfg["preprocessing"], cfg["evaluation"]
    use_sw, use_bi = bool(pre["use_domain_stopwords"]), bool(pre["use_bigram"])
    spark = get_spark(f"train-{a.model}-k{a.k}", cfg)
    path = cfg["paths"]["sample"] if a.data == "sample" else cfg["paths"]["clean_model"]
    docs = spark.read.parquet(path).select("post_id", "text", "text_clean", "tokens").cache()
    top_n = ev["coherence_top_n"]
    row = {"exp": a.exp, "data": "sample_20" if a.data == "sample" else "full", "k": a.k,
           "ngram": "Uni+Bi" if use_bi else "Uni", "domain_sw": "Yes" if use_sw else "No",
           "n_workers": n_alive_workers(), "note": a.note}

    with Timer() as t:
        if a.model in ("kmeans", "bkm", "w2v_kmeans"):
            prep = (w2v_prep if a.model == "w2v_kmeans" else kmeans_prep)(cfg, use_sw, use_bi).fit(docs)
            feats = drop_empty(prep.transform(docs)).cache()
            vocab = vocabulary(prep)
            if a.model in ("kmeans", "w2v_kmeans"):
                c = cfg["kmeans"]
                algo = KMeans(k=a.k, maxIter=c["max_iter"], seed=c["seed"], featuresCol="features",
                              predictionCol="topic", initMode="k-means||")
            else:
                c = cfg["bisecting_kmeans"]
                algo = BisectingKMeans(k=a.k, maxIter=c["max_iter"], seed=c["seed"],
                                       featuresCol="features", predictionCol="topic")
            model = algo.fit(feats)
            pred = model.transform(feats).cache()
            names = {"kmeans": "KMeans", "bkm": "BisectingKMeans", "w2v_kmeans": "Word2Vec+KMeans"}
            row.update(model=names[a.model],
                       vocab=len(vocab), seed=c["seed"], max_iter=c["max_iter"], min_df=cfg["features"]["min_df"],
                       wssse=round(model.summary.trainingCost, 2))
            sample_n = ev["silhouette_sample"]
            n = pred.count()
            sil_df = pred if n <= sample_n else pred.sample(fraction=sample_n / n, seed=42)
            row["silhouette"] = round(ClusteringEvaluator(featuresCol="features", predictionCol="topic",
                                                          distanceMeasure="cosine").evaluate(sil_df), 4)
            if a.model == "w2v_kmeans":
                topics = class_tfidf_terms(pred, "topic", final_tokens_col(prep), a.k, top_n)
            else:
                topics = top_terms_from_centers(model.clusterCenters(), vocab, top_n)
            sizes = {r["topic"]: r["count"] for r in pred.groupBy("topic").count().collect()}
        else:
            c = cfg["lda"]
            prep = lda_prep(cfg, use_sw, use_bi).fit(docs)
            feats = drop_empty(prep.transform(docs)).cache()
            vocab = vocabulary(prep)
            train, heldout = feats.randomSplit([1 - ev["heldout_fraction"], ev["heldout_fraction"]], seed=c["seed"])
            model = LDA(k=a.k, maxIter=c["max_iter"], seed=c["seed"], optimizer=c["optimizer"],
                        featuresCol="features", topicDistributionCol="theta").fit(train)
            row.update(model="LDA", vocab=len(vocab), seed=c["seed"], max_iter=c["max_iter"],
                       min_df=cfg["features"]["min_df"], perplexity=round(model.logPerplexity(heldout), 4))
            topics = [[vocab[i] for i in r["termIndices"]] for r in model.describeTopics(top_n).orderBy("topic").collect()]
            pred = model.transform(feats)
            # LDA sizes = expected number of documents (sum of theta), not argmax.
            theta_sum = (pred.select(vector_to_array("theta").alias("th"))
                         .select(*[F.col("th")[i].alias(f"t{i}") for i in range(a.k)])
                         .groupBy().sum().collect()[0])
            sizes = {i: float(theta_sum[i]) for i in range(a.k)}
            n = feats.count()

        model_npmi, topic_npmi = npmi(docs, topics)
        total = sum(sizes.values())
        row.update(npmi=round(model_npmi, 4), n_docs=n, max_topic_share=round(max(sizes.values()) / total, 4))

    row["runtime_s"] = t.seconds
    run_id = append_registry(cfg, {**row, "id": a.id} if a.id else row)
    write_json(APP_ROOT / "experiments" / "runs" / f"{run_id}.json", {
        "id": run_id, **row,
        "topics": [{"topic": i, "top_terms": topics[i], "npmi": round(topic_npmi[i], 4),
                    "size": sizes.get(i, 0), "share": round(sizes.get(i, 0) / total, 4)} for i in range(a.k)],
    })
    if a.save:
        full = PipelineModel(stages=prep.stages + [model])
        full.write().overwrite().save(f"{cfg['paths']['models']}/{run_id}")
    print(f"[TRAIN] {run_id} {row['model']} k={a.k} npmi={row['npmi']} "
          f"sil={row.get('silhouette', '-')} ppl={row.get('perplexity', '-')} {t.seconds}s")
    spark.stop()


if __name__ == "__main__":
    main()
