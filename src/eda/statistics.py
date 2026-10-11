"""Step 03 – descriptive statistics with Spark DataFrame / SQL (plan section 9).

    spark-submit src/eda/statistics.py      -> reports/eda.json
"""
from __future__ import annotations

import argparse

import pandas as pd
from pyspark.sql import Window
from pyspark.sql import functions as F

from src.common import Timer, get_spark, load_config, reports_dir, write_json
from src.trend.timeseries import detect_gaps


def records(df, limit=None):
    pdf = df.limit(limit).toPandas() if limit else df.toPandas()
    return pdf.to_dict("records")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", nargs="*", default=[])
    cfg = load_config(parser.parse_args().set)
    spark = get_spark("03-eda", cfg)
    tr = cfg["trend"]

    with Timer() as t:
        vol = spark.read.parquet(cfg["paths"]["clean_volume"]).cache()
        mod = spark.read.parquet(cfg["paths"]["clean_model"]).select("tokens").cache()
        vol.createOrReplaceTempView("posts")

        totals = spark.sql("""
            SELECT count(*) AS posts,
                   count(DISTINCT author) AS authors,
                   min(created_at) AS first_post, max(created_at) AS last_post,
                   avg(CAST(is_reply AS INT)) AS reply_share,
                   avg(CAST(has_images AS INT)) AS image_share,
                   avg(CAST(size(hashtags) > 0 AS INT)) AS hashtag_share,
                   avg(CAST(is_high_activity_account AS INT)) AS high_activity_post_share,
                   avg(CAST(is_sensitive AS INT)) AS sensitive_share
            FROM posts""").toPandas().iloc[0].to_dict()
        totals["model_posts"] = mod.count()
        totals["distinct_hashtags"] = vol.select(F.explode("hashtags")).distinct().count()

        per_bin = vol.groupBy("bucket").agg(
            F.count("*").alias("posts"),
            F.sum(F.col("is_reply").cast("int")).alias("replies"),
            F.countDistinct("author").alias("authors"),
        ).orderBy("bucket").toPandas()
        series = per_bin.set_index(pd.to_datetime(per_bin["bucket"]))["posts"]
        gaps = detect_gaps(series, ratio=tr["gap_volume_ratio"], window=tr["gap_window_bins"],
                           freq=f"{tr['bin_minutes']}min")
        per_bin["is_gap"] = per_bin["bucket"].map(lambda b: bool(gaps.get(pd.Timestamp(b), False)))

        per_hour = vol.groupBy("hour").count().orderBy("hour")

        tags = vol.select(F.explode("hashtags").alias("hashtag"))
        top_hashtags = tags.groupBy("hashtag").count().orderBy(F.desc("count"))
        safe = vol.filter(~F.col("is_sensitive"))
        top_hashtags_safe = (safe.select(F.explode("hashtags").alias("hashtag"))
                             .groupBy("hashtag").count().orderBy(F.desc("count")))
        tags_by_hour = (vol.select("hour", F.explode("hashtags").alias("hashtag"))
                        .groupBy("hour", "hashtag").count())
        top_tags_by_hour = (tags_by_hour
                            .withColumn("rank", F.row_number().over(Window.partitionBy("hour").orderBy(F.desc("count"))))
                            .filter("rank <= 10").orderBy("hour", "rank"))

        doc_freq = (mod.select(F.explode(F.array_distinct("tokens")).alias("token"))
                    .groupBy("token").count().orderBy(F.desc("count")))
        n_model = totals["model_posts"]

        lengths = (mod.select(F.size("tokens").alias("n"))
                   .select(F.when(F.col("n") <= 5, "3-5").when(F.col("n") <= 10, "6-10")
                           .when(F.col("n") <= 20, "11-20").when(F.col("n") <= 40, "21-40").otherwise("40+")
                           .alias("tokens"))
                   .groupBy("tokens").count())

        author_activity = (vol.groupBy("author").count()
                           .select(F.when(F.col("count") == 1, "1").when(F.col("count") <= 5, "2-5")
                                   .when(F.col("count") <= 20, "6-20").when(F.col("count") <= 100, "21-100")
                                   .otherwise(">100").alias("posts_per_author"))
                           .groupBy("posts_per_author").count())

        report = {
            "totals": totals,
            "posts_per_bin": per_bin.assign(bucket=per_bin["bucket"].astype(str)).to_dict("records"),
            "gap_bins": [str(b) for b in gaps[gaps].index],
            "posts_per_hour": records(per_hour),
            "top_hashtags": records(top_hashtags, 40),
            "top_hashtags_safe": records(top_hashtags_safe, 40),
            "top_hashtags_by_hour": records(top_tags_by_hour),
            "top_tokens_by_doc_frequency": [
                {**r, "doc_share": round(r["count"] / n_model, 4)} for r in records(doc_freq, 60)],
            "token_length_distribution": records(lengths),
            "author_activity_distribution": records(author_activity),
        }
    report["runtime_s"] = t.seconds
    write_json(reports_dir(cfg) / "eda.json", report)
    print(f"[EDA] {totals['posts']:,} posts, {totals['authors']:,} authors, {len(report['gap_bins'])} gap bins, "
          f"{t.seconds}s")
    spark.stop()


if __name__ == "__main__":
    main()
