"""Step 02 – Spark ETL: read raw source JSONL from HDFS, apply the
data-quality rules, write the two clean datasets (plan sections 7 and 8).

    spark-submit src/etl/clean.py

Outputs
  /social/clean/volume  every valid configured-language record (volume / trend statistics)
  /social/clean/model   de-duplicated, >= min_tokens (model training)
  /social/sample_20     fixed 20% sample of the model set (experiments)
  reports/data_quality.json
"""
from __future__ import annotations

import argparse

from pyspark.ml.feature import RegexTokenizer, StopWordsRemover
from pyspark.sql import Window
from pyspark.sql import functions as F
from pyspark.sql.types import BooleanType, StringType, StructField, StructType

from src.common import APP_ROOT, Timer, get_spark, language_stopwords, load_config, reports_dir, write_json
from src.langid import make_lang_udf
from src.textproc import clean_text, extract_hashtags, is_sensitive, normalized_hash, text_for_language

RAW_SCHEMA = StructType([
    StructField("text", StringType()),
    StructField("created_at", StringType()),
    StructField("author", StringType()),
    StructField("uri", StringType()),
    StructField("has_images", BooleanType()),
    StructField("reply_to", StringType()),
    StructField("_corrupt", StringType()),
])


class QualityLog:
    """Records the row count before/after each rule, in execution order."""

    def __init__(self):
        self.rows = []

    def add(self, rule: str, before: int, after: int, note: str = ""):
        self.rows.append({"rule": rule, "before": before, "removed": before - after, "after": after, "note": note})
        print(f"[DQ] {rule:<48} {before:>10,} -> {after:>10,}  (-{before - after:,})")

    def marker(self, label: str, count: int):
        self.rows.append({"rule": label, "before": None, "removed": None, "after": count, "note": "checkpoint"})
        print(f"[DQ] === {label}: {count:,}")


def read_raw(spark, path: str):
    return (
        spark.read.schema(RAW_SCHEMA)
        .option("mode", "PERMISSIVE")
        .option("columnNameOfCorruptRecord", "_corrupt")
        .json(f"{path}/*.jsonl")
        .withColumn("source_file", F.regexp_extract(F.input_file_name(), r"([^/]+)\.jsonl", 1))
    )


def sensitive_terms() -> list[str]:
    path = APP_ROOT / "config" / "sensitive_terms.txt"
    return [w.strip().lower() for w in path.read_text(encoding="utf-8").splitlines()
            if w.strip() and not w.startswith("#")]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", nargs="*", default=[], help="config overrides section.key=value")
    args = parser.parse_args()
    cfg = load_config(args.set)
    spark = get_spark("02-clean", cfg)
    paths, pre = cfg["paths"], cfg["preprocessing"]
    bin_minutes = cfg["trend"]["bin_minutes"]
    log = QualityLog()

    with Timer() as t:
        raw = read_raw(spark, paths["raw"]).repartition(32).cache()
        n_raw = raw.count()
        log.marker("Raw records", n_raw)

        # created_at is parsed from ISO-8601 timestamps returned by the API.
        df = raw.withColumn("created_ts", F.to_timestamp("created_at"))

        # 1. Corrupt / unparsable: JSON parser error, or created_at present
        #    but not a timestamp.
        before = n_raw
        broken = F.col("_corrupt").isNotNull() | (F.col("created_at").isNotNull() & F.col("created_ts").isNull())
        df = df.filter(~broken).drop("_corrupt").cache()
        log.add("Corrupt / parse error (JSON)", before, after := df.count(),
                "parser error or created_at not a timestamp")

        # 2. Duplicate source record: uri is unique within the selected source.
        before = after
        df = df.dropDuplicates(["uri"]).cache()
        log.add("Duplicate post (uri)", before, after := df.count())

        # 3. Missing / empty text (image-only posts).
        before = after
        df = df.filter(F.col("text").isNotNull() & (F.length(F.trim("text")) > 0))
        log.add("Missing / empty text", before, after := df.count(), "image-only posts")

        # 4. Missing timestamp.
        before = after
        df = df.filter(F.col("created_ts").isNotNull())
        log.add("Missing timestamp", before, after := df.count())

        # 5. Keep records only inside the configured collection window.
        before = after
        start, end = cfg["dataset"]["start"], cfg["dataset"]["end"]
        df = df.filter((F.col("created_ts") >= F.lit(start).cast("timestamp"))
                       & (F.col("created_ts") < F.lit(end).cast("timestamp")))
        log.add("Timestamp outside collection window", before, after := df.count(), f"{start} .. {end} UTC")

        # 6. Language: keep the configured language (fastText lid.176).
        before = after
        detect = make_lang_udf(paths["fasttext_model"])
        df = (df.withColumn("_lang", detect(text_for_language(F.col("text"))))
                .withColumn("lang", F.col("_lang.lang"))
                .withColumn("lang_prob", F.col("_lang.lang_prob"))
                .drop("_lang").cache())
        n_lang_total = df.count()
        lang_dist = df.groupBy("lang").count().orderBy(F.desc("count")).limit(15).toPandas()
        lang_dist["share_pct"] = (100 * lang_dist["count"] / n_lang_total).round(2)
        df = df.filter((F.col("lang") == pre["language"]) & (F.col("lang_prob") >= pre["min_lang_confidence"]))
        log.add("Non-Vietnamese / unknown language", before, after := df.count(),
                f"fastText lid.176, prob >= {pre['min_lang_confidence']}")

        # Normalisation and derived columns.
        bucket_seconds = bin_minutes * 60
        df = (
            df.select(
                F.col("uri").alias("post_id"),
                F.col("author"),
                F.col("created_ts").alias("created_at"),
                F.col("text"),
                F.coalesce("has_images", F.lit(False)).alias("has_images"),
                F.col("reply_to").isNotNull().alias("is_reply"),
                "lang", "lang_prob", "source_file",
            )
            .withColumn("bucket", F.from_unixtime(
                (F.unix_timestamp("created_at") / bucket_seconds).cast("long") * bucket_seconds).cast("timestamp"))
            .withColumn("hour", F.date_format("created_at", "HH"))
            .withColumn("hashtags", extract_hashtags(F.col("text")))
            .withColumn("text_clean", clean_text(F.col("text")))
            .withColumn("text_hash", normalized_hash(F.col("text")))
        )
        df = df.withColumn("is_sensitive", is_sensitive(F.col("text_clean"), F.col("hashtags"), sensitive_terms()))

        # High-activity accounts: flagged, not removed, never called bots (7.6).
        per_author = df.groupBy("author").count()
        threshold = per_author.approxQuantile("count", [pre["high_activity_quantile"]], 0.0001)[0]
        heavy = (per_author.filter(F.col("count") > threshold).select("author")
                 .withColumn("is_high_activity_account", F.lit(True)))
        df = (df.join(F.broadcast(heavy), "author", "left")
                .withColumn("is_high_activity_account", F.coalesce("is_high_activity_account", F.lit(False))))

        volume = df.cache()
        n_volume = volume.count()
        log.marker("Clean dataset for volume statistics", n_volume)
        volume.write.mode("overwrite").partitionBy("hour").parquet(paths["clean_volume"])

        # ---- model set -------------------------------------------------------
        # 7. Duplicate normalised text (copy-paste, spam, bots): keep one.
        before = n_volume
        w = Window.partitionBy("text_hash").orderBy("created_at")
        model = (volume.withColumn("_rn", F.row_number().over(w))
                 .withColumn("dup_count", F.count("*").over(Window.partitionBy("text_hash")))
                 .filter("_rn = 1").drop("_rn").cache())
        log.add("Duplicate text (normalised)", before, after := model.count(), "kept once for the model")

        # 8. Too short after tokenisation + basic stopwords.
        before = after
        tok = RegexTokenizer(inputCol="text_clean", outputCol="tokens_all", pattern=r"\s+", minTokenLength=2)
        sw = StopWordsRemover(inputCol="tokens_all", outputCol="tokens",
                              stopWords=language_stopwords(pre["language"]))
        model = sw.transform(tok.transform(model)).drop("tokens_all")
        model = model.filter(F.size("tokens") >= pre["min_tokens"]).cache()
        log.add(f"Text too short (< {pre['min_tokens']} tokens after stopwords)", before, after := model.count())
        n_model = after
        log.marker("Clean dataset for model", n_model)
        model.write.mode("overwrite").partitionBy("hour").parquet(paths["clean_model"])

        sample = model.sample(fraction=cfg["data"]["sample_fraction"], seed=cfg["data"]["seed"])
        sample.write.mode("overwrite").parquet(paths["sample"])
        n_sample = spark.read.parquet(paths["sample"]).count()

    report = {
        "dataset": cfg["dataset"]["name"],
        "rules": log.rows,
        "raw_records": n_raw,
        "clean_volume": n_volume,
        "clean_model": n_model,
        "sample_20": n_sample,
        "retention_volume_pct": round(100 * n_volume / n_raw, 2),
        "retention_model_pct": round(100 * n_model / n_raw, 2),
        "high_activity_threshold_posts": threshold,
        "high_activity_accounts": heavy.count(),
        "sensitive_posts_volume": volume.filter("is_sensitive").count(),
        "language_distribution": lang_dist.to_dict("records"),
        "runtime_s": t.seconds,
    }
    write_json(reports_dir(cfg) / "data_quality.json", report)
    print(f"[DQ] done in {t.seconds}s – volume {n_volume:,}, model {n_model:,}, sample {n_sample:,}")
    spark.stop()


if __name__ == "__main__":
    main()
