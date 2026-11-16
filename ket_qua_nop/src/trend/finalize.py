"""Steps 08–09 – apply the chosen final model to the whole volume set, then
build topic trends, burst events, keyword and hashtag trends (plan 13–16.7).

    spark-submit src/trend/finalize.py --run E07

Reads  hdfs:///social/models/<run>  (saved by train.py --save)
Writes reports/final/*.json  (loaded into MongoDB by export_mongo.py)
       models_local/final     local copy of the PipelineModel for the dashboard
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from pyspark.ml import PipelineModel
from pyspark.ml.clustering import DistributedLDAModel, LocalLDAModel
from pyspark.ml.functions import vector_to_array
from pyspark.sql import Window
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

from src.common import APP_ROOT, Timer, get_spark, language_stopwords, load_config, reports_dir, write_json
from src.features import final_tokens_col, vocabulary
from src.trend.timeseries import burst_scores, detect_gaps, mark_bursts, merge_events


def topic_labels(k: int, topics: list[list[str]]) -> dict[int, str]:
    """Manual labels from config/topic_labels.yaml, falling back to top terms."""
    path = APP_ROOT / "config" / "topic_labels.yaml"
    manual = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    manual = (manual or {}).get("labels", {}) or {}
    return {i: str(manual.get(i) or " · ".join(topics[i][:3])) for i in range(k)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True, help="registry id of the final model")
    p.add_argument("--secondary", default=None, help="registry id of an LDA model for the Text Analyzer")
    p.add_argument("--set", nargs="*", default=[])
    a = p.parse_args()
    cfg = load_config(a.set)
    tr, dash = cfg["trend"], cfg["dashboard"]
    spark = get_spark("08-finalize", cfg)
    out = reports_dir(cfg) / "final"
    runs = Path(cfg["paths"]["registry"]).parent / "runs"
    run_info = json.loads((runs / f"{a.run}.json").read_text(encoding="utf-8"))

    with Timer() as t:
        model = PipelineModel.load(f"{cfg['paths']['models']}/{a.run}")
        last = model.stages[-1]
        is_lda = isinstance(last, (LocalLDAModel, DistributedLDAModel))
        prep_model = PipelineModel(stages=model.stages[:-1])
        vocab = vocabulary(prep_model)
        tokens_col = final_tokens_col(prep_model)
        k = last.getK() if is_lda else len(last.clusterCenters())
        topics_terms = [t["top_terms"] for t in run_info["topics"]]
        labels = topic_labels(k, topics_terms)

        vol = spark.read.parquet(cfg["paths"]["clean_volume"])
        scored = model.transform(vol)
        feat_col = "features"
        nnz = F.udf(lambda v: int(v.numNonzeros()), "int")
        scored = scored.withColumn("_nnz", nnz(feat_col))
        if is_lda:
            scored = scored.withColumn("theta_arr", vector_to_array("theta"))
            scored = scored.withColumn("topic", F.when(F.col("_nnz") > 0, F.expr(
                "array_position(theta_arr, array_max(theta_arr)) - 1")).otherwise(F.lit(-1)))
        else:
            scored = scored.withColumn("topic", F.when(F.col("_nnz") > 0, F.col("topic")).otherwise(F.lit(-1)))
        keep = ["post_id", "author", "channel_id", "video_url", "view_count", "like_count",
                "created_at", "created_at_vn", "bucket", "day", "text", "hashtags",
                "is_sensitive", "text_hash", "topic", feat_col,
                tokens_col, "_nnz"]
        if is_lda:
            keep.append("theta_arr")
        scored = scored.select(*keep).cache()
        n_total = scored.count()
        assignable = scored.filter("_nnz > 0")
        n_assignable = assignable.count()

        # ---- topic trend per bin --------------------------------------------
        if is_lda:
            agg = (assignable.select("bucket", F.posexplode("theta_arr").alias("topic", "w"))
                   .groupBy("bucket", "topic").agg(F.sum("w").alias("count")))
        else:
            agg = assignable.groupBy("bucket", "topic").agg(F.count("*").cast("double").alias("count"))
        totals = assignable.groupBy("bucket").agg(F.count("*").alias("total"))
        trend = agg.join(totals, "bucket").withColumn("ratio", F.col("count") / F.col("total")).toPandas()
        trend["bucket"] = pd.to_datetime(trend["bucket"])

        all_bins = vol.groupBy("bucket").count().toPandas()
        all_series = all_bins.set_index(pd.to_datetime(all_bins["bucket"]))["count"].sort_index()
        freq = f"{tr['bin_minutes']}min"
        gaps = detect_gaps(all_series, ratio=tr["gap_volume_ratio"], window=tr["gap_window_bins"], freq=freq)
        idx = gaps.index

        trend_rows, events = [], []
        for topic in range(k):
            sub = trend[trend["topic"] == topic].set_index("bucket").reindex(idx)
            ratio = sub["ratio"].fillna(0.0)
            count = sub["count"].fillna(0.0)
            sc = burst_scores(ratio, window=tr["rolling_window_bins"], min_periods=tr["min_periods"],
                              std_floor_ratio=tr["std_floor_ratio"], invalid=gaps)
            flags = mark_bursts(sc, count, tr["burst_zscore_threshold"], tr["burst_min_volume"],
                                tr.get("burst_min_lift", 1.0))
            for b in idx:
                s = sc.at[b, "burst_score"]
                trend_rows.append({"topic_id": topic, "topic_label": labels[topic], "bucket": b.isoformat(),
                                   "count": round(float(count.at[b]), 2), "ratio": round(float(ratio.at[b]), 5),
                                   "burst_score": None if pd.isna(s) else round(float(s), 3),
                                   "is_burst": bool(flags.at[b]), "in_gap": bool(gaps.at[b])})
            for e in merge_events(flags, sc["burst_score"], tr["merge_gap_bins"], pd.Timedelta(minutes=tr["bin_minutes"])):
                events.append({"topic_id": topic, "topic_label": labels[topic], "start": e["start"].isoformat(),
                               "peak": e["peak"].isoformat(), "end": e["end"].isoformat(), "bins": e["bins"],
                               "max_burst_score": round(e["max_burst_score"], 3),
                               "peak_ratio": round(float(ratio.at[e["peak"]]), 5),
                               "baseline_ratio": round(float(sc.at[e["peak"], "baseline_mean"]), 5)})

        # ---- topics, sizes, representative posts ----------------------------
        if is_lda:
            sizes = (assignable.select(F.posexplode("theta_arr").alias("topic", "w")).groupBy("topic")
                     .agg(F.sum("w").alias("size")).toPandas().set_index("topic")["size"].to_dict())
        else:
            sizes = assignable.groupBy("topic").count().toPandas().set_index("topic")["count"].to_dict()

        uniq = assignable.filter(~F.col("is_sensitive")).dropDuplicates(["channel_id", "text_hash"])
        example_fields = ["text", "created_at_vn", "author", "channel_id", "video_url", "view_count", "like_count"]
        if is_lda:
            ranked = uniq.select("topic", *example_fields, "theta_arr",
                                 F.expr("theta_arr[topic]").alias("score"))
        else:
            centers = [c.tolist() for c in last.clusterCenters()]
            bc = spark.sparkContext.broadcast(centers)
            sim = F.udf(lambda v, t: float(v.dot(bc.value[t])), DoubleType())
            ranked = uniq.select("topic", *example_fields, sim(feat_col, "topic").alias("score"))
        rep = (ranked.withColumn("r", F.row_number().over(Window.partitionBy("topic").orderBy(F.desc("score"))))
               .filter(f"r <= {dash['representative_posts_per_topic']}")
               .select("topic", *example_fields, "score").toPandas())

        topic_docs = []
        total_size = sum(sizes.values())
        # Colour slot follows the entity: fixed by size rank once, here.
        size_rank = {t: r for r, t in enumerate(sorted(range(k), key=lambda t: -sizes.get(t, 0)))}
        for i in range(k):
            info = run_info["topics"][i]
            peak = max((r for r in trend_rows if r["topic_id"] == i and not r["in_gap"]), key=lambda r: r["ratio"])
            topic_docs.append({
                "topic_id": i, "topic_label": labels[i], "keywords": info["top_terms"],
                "npmi": info["npmi"], "size": round(float(sizes.get(i, 0)), 1),
                "share": round(float(sizes.get(i, 0)) / total_size, 4),
                "peak_bucket": peak["bucket"], "peak_ratio": peak["ratio"],
                "bursts": sum(1 for e in events if e["topic_id"] == i),
                "size_rank": size_rank[i],
            })
        def example_doc(row):
            return {"text": row.text, "created_at": str(row.created_at_vn) + "+07:00",
                    "author": row.author, "channel_id": row.channel_id, "video_url": row.video_url,
                    "view_count": None if pd.isna(row.view_count) else int(row.view_count),
                    "like_count": None if pd.isna(row.like_count) else int(row.like_count)}
        rep_docs = [{**example_doc(r), "topic_id": int(r.topic), "score": round(float(r.score), 4)} for r in rep.itertuples()]

        # Daily topic words and examples let the dashboard name what people
        # discussed on that day instead of reusing a whole-corpus label.
        daily = assignable.withColumn("day", F.to_date("created_at_vn"))
        daily_counts = daily.groupBy("day", "topic").agg(F.count("*").alias("count"),
                                                        F.collect_set("channel_id").alias("channel_ids"))
        daily_terms = (daily.filter(~F.col("is_sensitive"))
                       .select("day", "topic", F.explode(tokens_col).alias("term"))
                       .groupBy("day", "topic", "term").count())
        n_days = daily_terms.select("day").distinct().count()
        stop = set(language_stopwords("vi")) | {
            "ko", "không", "rồi", "cái", "mình", "nó", "làm", "thì", "là", "của", "và", "với",
            "cho", "các", "này", "đó", "những", "sẽ", "có", "em", "anh", "bạn", "ơi", "nhé", "ạ",
        }
        daily_terms = daily_terms.filter(~F.col("term").isin(sorted(stop)))
        term_df = daily_terms.groupBy("term").agg(F.countDistinct("day").alias("days"))
        day_totals = daily_terms.groupBy("day", "topic").agg(F.sum("count").alias("tokens"))
        term_ranked = (daily_terms.join(term_df, "term").join(day_totals, ["day", "topic"])
                       .withColumn("weight", (F.col("count") / F.col("tokens"))
                                   * F.log((F.lit(n_days) + 1) / (F.col("days") + 1)))
                       .withColumn("rank", F.row_number().over(Window.partitionBy("day", "topic")
                                                                 .orderBy(F.desc("weight"))))
                       .filter("rank <= 8").select("day", "topic", "term", "rank", "weight").toPandas())
        issue_terms = {}
        for (day, topic), rows in term_ranked.groupby(["day", "topic"]):
            issue_terms[(str(day), int(topic))] = [r.term for r in rows.sort_values("rank").itertuples()]

        issue_docs = (daily_counts.toPandas().rename(columns={"day": "date", "topic": "topic_id", "count": "count"}))
        issue_ranked = daily.filter(~F.col("is_sensitive"))
        examples = (issue_ranked.withColumn("rank", F.row_number().over(
                        Window.partitionBy("day", "topic").orderBy(F.col("view_count").desc_nulls_last(), "post_id")))
                    .filter("rank <= 3").select("day", "topic", "post_id", *example_fields)
                    .toPandas())
        example_map = {}
        for (day, topic), rows in examples.groupby(["day", "topic"]):
            example_map[(str(day), int(topic))] = [
                {**example_doc(r), "post_id": r.post_id} for r in rows.itertuples()
            ]
        daily_issue_docs = []
        for r in issue_docs.itertuples():
            key = (str(r.date), int(r.topic_id))
            terms = issue_terms.get(key, [])
            examples = example_map.get(key, [])
            title = next((line.strip() for line in examples[0]["text"].splitlines() if line.strip()), "") if examples else ""
            daily_issue_docs.append({"date": key[0], "topic_id": key[1], "count": int(r.count),
                                     "channel_ids": list(r.channel_ids), "channel_count": len(r.channel_ids),
                                     "keywords": terms,
                                     "label": title[:120] if title else "Chủ đề chưa rõ",
                                     "examples": examples})

        # ---- keyword trend: TF-IDF with each publication day as one document -----------
        model_set = spark.read.parquet(cfg["paths"]["clean_model"]).select("day", "tokens")
        tf = model_set.select("day", F.explode("tokens").alias("term")).groupBy("day", "term").count()
        n_days = tf.select("day").distinct().count()
        dfreq = tf.groupBy("term").agg(F.countDistinct("day").alias("df"))
        tfidf = (tf.filter("count >= 20").join(dfreq, "term")
                 .withColumn("tfidf", F.col("count") * F.log((F.lit(n_days) + 1) / (F.col("df") + 1)))
                 .withColumn("r", F.row_number().over(Window.partitionBy("day").orderBy(F.desc("tfidf"))))
                 .filter(f"r <= {dash['top_keywords']}").orderBy("day", "r").toPandas())
        freq_top = (tf.withColumn("r", F.row_number().over(Window.partitionBy("day").orderBy(F.desc("count"))))
                    .filter(f"r <= {dash['top_keywords']}").orderBy("day", "r").toPandas())

        # ---- hashtag trend per bin for the top hashtags ---------------------
        tags = vol.select("bucket", F.explode("hashtags").alias("hashtag"))
        top_tags = [r["hashtag"] for r in tags.groupBy("hashtag").count().orderBy(F.desc("count")).limit(20).collect()]
        tag_trend = (tags.filter(F.col("hashtag").isin(top_tags)).groupBy("bucket", "hashtag").count()
                     .orderBy("bucket").toPandas())

        # ---- local model copy for the Text Analyzer (plan 12.4) -------------
        local = f"file://{cfg['paths']['models_local']}/final"
        model.write().overwrite().save(local)

    meta = {"run_id": a.run, "model": run_info["model"], "k": k, "is_lda": is_lda, "vocab_size": len(vocab),
            "npmi": run_info.get("npmi"), "silhouette": run_info.get("silhouette"),
            "perplexity": run_info.get("perplexity"), "posts_scored": n_total, "posts_assignable": n_assignable,
            "labels": labels, "runtime_s": t.seconds, "config_trend": tr}
    write_json(Path(cfg["paths"]["models_local"]) / "final_meta.json", meta)
    if a.secondary:
        sec = PipelineModel.load(f"{cfg['paths']['models']}/{a.secondary}")
        sec.write().overwrite().save(f"file://{cfg['paths']['models_local']}/secondary")
        sec_info = json.loads((runs / f"{a.secondary}.json").read_text(encoding="utf-8"))
        write_json(Path(cfg["paths"]["models_local"]) / "secondary_meta.json", {
            "run_id": a.secondary, "model": sec_info["model"], "npmi": sec_info.get("npmi"),
            "labels": {t["topic"]: " · ".join(t["top_terms"][:3]) for t in sec_info["topics"]}})
    write_json(out / "model_info.json", meta)
    write_json(out / "topics.json", topic_docs)
    write_json(out / "topic_trend.json", trend_rows)
    write_json(out / "burst_events.json", sorted(events, key=lambda e: -e["max_burst_score"]))
    write_json(out / "representative_posts.json", rep_docs)
    write_json(out / "daily_issues.json", daily_issue_docs)
    write_json(out / "keyword_trend_daily.json", {
        "tfidf": tfidf.drop(columns=["r"]).to_dict("records"),
        "frequency": freq_top.drop(columns=["r"]).to_dict("records")})
    tag_trend["bucket"] = tag_trend["bucket"].astype(str)
    write_json(out / "hashtag_trend.json", tag_trend.to_dict("records"))
    print(f"[FINAL] {a.run}: {n_assignable:,}/{n_total:,} posts assigned, {len(events)} burst events, {t.seconds}s")
    spark.stop()


if __name__ == "__main__":
    main()
