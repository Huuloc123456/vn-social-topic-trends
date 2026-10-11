"""Text Analyzer inference (plan 12.4): a local SparkSession loads the final
PipelineModel copied to models/, so the demo needs no cluster."""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import streamlit as st

MODEL_DIR = Path(os.environ.get("MODEL_DIR", Path(__file__).resolve().parent.parent / "models"))


def model_ready() -> bool:
    return (MODEL_DIR / "final" / "metadata").exists()


@st.cache_resource(show_spinner="Đang nạp mô hình Spark cục bộ (chỉ lần đầu)…")
def _load():
    from pyspark.ml import PipelineModel
    from pyspark.sql import SparkSession

    spark = (SparkSession.builder.master("local[1]").appName("dashboard-analyzer")
             .config("spark.driver.memory", "1g").config("spark.ui.enabled", "false")
             .config("spark.hadoop.fs.defaultFS", "file:///").getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")
    final = PipelineModel.load(f"file://{MODEL_DIR / 'final'}")
    secondary = None
    if (MODEL_DIR / "secondary" / "metadata").exists():
        secondary = PipelineModel.load(f"file://{MODEL_DIR / 'secondary'}")
    meta = json.loads((MODEL_DIR / "final_meta.json").read_text(encoding="utf-8"))
    sec_meta = None
    if (MODEL_DIR / "secondary_meta.json").exists():
        sec_meta = json.loads((MODEL_DIR / "secondary_meta.json").read_text(encoding="utf-8"))
    w2v = {}
    for stage in final.stages:
        if type(stage).__name__ == "Word2VecModel":
            w2v = {r["word"]: np.asarray(r["vector"]) for r in stage.getVectors().collect()}
    return spark, final, secondary, meta, sec_meta, w2v


def analyze(text: str) -> dict:
    from pyspark.sql import functions as F

    from src.textproc import clean_text

    spark, final, secondary, meta, sec_meta, w2v = _load()
    df = spark.createDataFrame([(text,)], ["text"]).withColumn("text_clean", clean_text(F.col("text")))
    out = final.transform(df).first().asDict()
    last = final.stages[-1]
    result = {"tokens": [], "kmeans": None, "lda": None}
    tok_col = next((c for c in ("tok_final", "tok_domain", "tok_basic") if c in out), None)
    tokens = list(out.get(tok_col) or [])
    vec = out["features"]
    if hasattr(last, "clusterCenters"):
        centers = [np.asarray(c) for c in last.clusterCenters()]
        v = vec.toArray()
        if not v.any():
            result["kmeans"] = {"empty": True}
        else:
            sims = [float(v @ c / (np.linalg.norm(c) or 1)) for c in centers]
            topic = int(out["topic"])
            center = centers[topic] / (np.linalg.norm(centers[topic]) or 1)
            pulls = []
            for t in dict.fromkeys(tokens):
                if t in w2v:
                    wv = w2v[t] / (np.linalg.norm(w2v[t]) or 1)
                    pulls.append((t, float(wv @ center)))
            labels = {int(k): v for k, v in meta["labels"].items()}
            result["kmeans"] = {"topic": topic, "label": labels.get(topic, str(topic)), "similarities": sims,
                                "pulls": sorted(pulls, key=lambda p: -p[1])}
    result["tokens"] = tokens
    if secondary is not None:
        o2 = secondary.transform(df).first().asDict()
        theta = list(o2["theta"].toArray()) if "theta" in o2 else None
        if theta is not None:
            sec_labels = {int(k): v for k, v in (sec_meta or {}).get("labels", {}).items()}
            result["lda"] = {"theta": theta, "labels": sec_labels,
                             "empty": o2["features"].numNonzeros() == 0}
    return result
