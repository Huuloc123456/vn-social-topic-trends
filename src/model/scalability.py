"""Scalability experiment (plan 19): same workload at 10/50/100% of the data,
repeated, with whatever number of workers is currently alive.

    spark-submit src/model/scalability.py                # 2 workers
    docker compose stop spark-worker-2 && spark-submit src/model/scalability.py   # 1 worker

Results accumulate in reports/scalability.json. All workers run on one laptop,
so this is a logical cluster: it shows how Spark splits jobs, not a benchmark
of independent machines (plan 19.3).
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.request

from pyspark.ml.clustering import KMeans

from src.common import get_spark, load_config, reports_dir, write_json
from src.features import drop_empty, kmeans_prep
from src.model.train import n_alive_workers


def stage_metrics(spark) -> dict:
    app = spark.sparkContext.applicationId
    url = f"{spark.sparkContext.uiWebUrl}/api/v1/applications/{app}/stages"
    with urllib.request.urlopen(url, timeout=10) as r:
        stages = json.load(r)
    return {
        "stages": len(stages),
        "tasks": sum(s["numCompleteTasks"] for s in stages),
        "shuffle_read_mb": round(sum(s["shuffleReadBytes"] for s in stages) / 2**20, 1),
        "shuffle_write_mb": round(sum(s["shuffleWriteBytes"] for s in stages) / 2**20, 1),
        "peak_executor_memory_mb": round(max((s.get("peakExecutionMemory", 0) for s in stages), default=0) / 2**20, 1),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fractions", nargs="*", type=float, default=[0.1, 0.5, 1.0])
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--set", nargs="*", default=[])
    a = p.parse_args()
    cfg = load_config(a.set)
    path = reports_dir(cfg) / "scalability.json"
    results = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    workers = n_alive_workers()

    for fraction in a.fractions:
        for rep in range(a.repeats):
            spark = get_spark(f"scalability-{fraction}-{rep}", cfg)
            start = time.perf_counter()
            docs = spark.read.parquet(cfg["paths"]["clean_model"]).select("text_clean", "tokens")
            if fraction < 1.0:
                docs = docs.sample(fraction=fraction, seed=42)
            prep = kmeans_prep(cfg, True, False).fit(docs)
            feats = drop_empty(prep.transform(docs))
            KMeans(k=10, maxIter=10, seed=42, featuresCol="features").fit(feats)
            n = feats.count()
            seconds = round(time.perf_counter() - start, 1)
            row = {"workers": workers, "fraction": fraction, "repeat": rep, "docs": n, "runtime_s": seconds,
                   **stage_metrics(spark)}
            results.append(row)
            print(f"[SCALE] workers={workers} fraction={fraction} rep={rep} docs={n:,} {seconds}s")
            spark.stop()
            write_json(path, results)


if __name__ == "__main__":
    main()
