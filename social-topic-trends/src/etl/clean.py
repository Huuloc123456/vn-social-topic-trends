"""Read the selected news CSV from HDFS and prepare publication counts/model titles."""
from __future__ import annotations

import argparse

from pyspark.ml.feature import RegexTokenizer, StopWordsRemover
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType

from src.common import APP_ROOT, Timer, get_spark, language_stopwords, load_config, reports_dir, write_json
from src.langid import make_lang_udf
from src.textproc import clean_text, extract_hashtags, is_sensitive, normalized_hash, text_for_language

CSV_COLUMNS = ["video_id", "title", "published_at_utc", "published_at_vn", "author", "channel_id",
               "video_url", "view_count", "like_count", "metrics_collected_at_utc"]
RAW_SCHEMA = StructType([StructField(name, StringType()) for name in CSV_COLUMNS])


class QualityLog:
    def __init__(self):
        self.rows = []

    def add(self, rule, before, after, note=""):
        self.rows.append({"rule": rule, "before": before, "removed": before - after, "after": after, "note": note})
        print(f"[DQ] {rule}: {before:,} -> {after:,}")

    def marker(self, label, count):
        self.rows.append({"rule": label, "before": None, "removed": None, "after": count, "note": "checkpoint"})


def read_raw(spark, path):
    return (spark.read.schema(RAW_SCHEMA).option("header", True).option("enforceSchema", False).option("multiLine", True)
            .option("escape", '"').option("mode", "FAILFAST").csv(path))


def sensitive_terms():
    path = APP_ROOT / "config/sensitive_terms.txt"
    return [w.strip().lower() for w in path.read_text(encoding="utf-8").splitlines()
            if w.strip() and not w.startswith("#")]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", nargs="*", default=[])
    cfg = load_config(parser.parse_args().set)
    spark = get_spark("news-clean", cfg)
    paths, pre = cfg["paths"], cfg["preprocessing"]
    log = QualityLog()
    with Timer() as timer:
        raw = read_raw(spark, paths["raw"]).cache()
        n_raw = raw.count()
        if not n_raw:
            raise ValueError("The selected news CSV is empty")
        log.marker("News CSV records", n_raw)
        df = (raw.withColumn("created_at", F.to_timestamp("published_at_utc"))
              .withColumn("created_at_vn", F.from_utc_timestamp("created_at", "Asia/Ho_Chi_Minh")))
        valid = F.col("created_at").isNotNull()
        for column in ("video_id", "title", "channel_id", "author"):
            valid = valid & F.col(column).isNotNull() & (F.length(F.trim(column)) > 0)
        for column in ("view_count", "like_count"):
            valid = valid & (F.col(column).isNull() | F.col(column).rlike(r"^\d+$"))
        df = df.filter(valid).cache()
        log.add("Invalid news CSV record", n_raw, after := df.count())
        before = after
        df = df.dropDuplicates(["video_id"])
        log.add("Duplicate video ID", before, after := df.count())
        before = after
        df = df.filter((F.col("created_at") >= F.lit(cfg["dataset"]["start"]).cast("timestamp")) &
                       (F.col("created_at") < F.lit(cfg["dataset"]["end"]).cast("timestamp")))
        log.add("Timestamp outside collection window", before, after := df.count())
        if not after:
            raise ValueError("No valid news videos remain in the configured date range")
        detect = make_lang_udf(paths["fasttext_model"])
        df = (df.withColumn("_lang", detect(text_for_language(F.col("title"))))
              .withColumn("lang", F.col("_lang.lang")).withColumn("lang_prob", F.col("_lang.lang_prob")).drop("_lang"))
        volume = (df.withColumn("post_id", F.concat(F.lit("youtube:video:"), "video_id"))
                  .withColumn("text", F.col("title"))
                  .withColumn("view_count", F.col("view_count").cast("long"))
                  .withColumn("like_count", F.col("like_count").cast("long"))
                  .withColumn("bucket", F.date_trunc("day", "created_at_vn"))
                  .withColumn("day", F.to_date("created_at_vn"))
                  .withColumn("hashtags", extract_hashtags(F.col("text")))
                  .withColumn("text_clean", clean_text(F.col("text")))
                  .withColumn("text_hash", normalized_hash(F.col("text")))
                  .withColumn("is_sensitive", is_sensitive(F.col("text_clean"), F.col("hashtags"), sensitive_terms()))
                  .cache())
        n_volume = volume.count()
        log.marker("Clean dataset for volume statistics", n_volume)
        volume.write.mode("overwrite").parquet(paths["clean_volume"])
        lang_dist = volume.groupBy("lang").count().orderBy(F.desc("count")).toPandas()
        lang_dist["share_pct"] = (100 * lang_dist["count"] / n_volume).round(2)
        model = volume.filter((F.col("lang") == pre["language"]) & (F.col("lang_prob") >= pre["min_lang_confidence"]))
        log.add("Non-Vietnamese / unknown language (model only)", n_volume, after := model.count())
        tok = RegexTokenizer(inputCol="text_clean", outputCol="tokens_all", pattern=r"\s+", minTokenLength=2)
        sw = StopWordsRemover(inputCol="tokens_all", outputCol="tokens", stopWords=language_stopwords(pre["language"]))
        model = sw.transform(tok.transform(model)).drop("tokens_all").filter(F.size("tokens") >= pre["min_tokens"]).cache()
        n_model = model.count()
        log.add("Text too short for model", after, n_model)
        if not n_model:
            raise ValueError("No Vietnamese titles remain for model training")
        log.marker("Clean dataset for model", n_model)
        # Cross-channel repeated titles are evidence of coverage and remain in both datasets.
        model.write.mode("overwrite").parquet(paths["clean_model"])
        sample = model.sample(fraction=cfg["data"]["sample_fraction"], seed=cfg["data"]["seed"])
        sample.write.mode("overwrite").parquet(paths["sample"])
        n_sample = spark.read.parquet(paths["sample"]).count()
    write_json(reports_dir(cfg) / "data_quality.json", {
        "dataset": cfg["dataset"]["name"], "input": paths["raw"], "rules": log.rows, "raw_records": n_raw,
        "clean_volume": n_volume, "clean_model": n_model, "sample_20": n_sample,
        "retention_volume_pct": round(100 * n_volume / n_raw, 2),
        "retention_model_pct": round(100 * n_model / n_raw, 2),
        "sensitive_posts_volume": volume.filter("is_sensitive").count(),
        "language_distribution": lang_dist.to_dict("records"), "runtime_s": timer.seconds,
    })
    print(f"[DQ] news: volume {n_volume:,}; model {n_model:,}; sample {n_sample:,}")
    spark.stop()


if __name__ == "__main__":
    main()
