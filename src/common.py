"""Shared helpers: configuration, Spark session, MongoDB, experiment registry."""
from __future__ import annotations

import copy
import csv
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

APP_ROOT = Path(os.environ.get("APP_ROOT", "/app"))
CONFIG_PATH = APP_ROOT / "config" / "config.yaml"


def load_config(overrides: list[str] | None = None) -> dict:
    """Load config.yaml, then apply `section.key=value` overrides."""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    for item in overrides or []:
        key, _, raw = item.partition("=")
        node = cfg
        *parents, leaf = key.split(".")
        for p in parents:
            node = node.setdefault(p, {})
        node[leaf] = yaml.safe_load(raw)
    return cfg


def domain_stopwords(language: str = "en") -> list[str]:
    localized = APP_ROOT / "config" / f"stopwords_domain_{language}.txt"
    path = localized if localized.exists() else APP_ROOT / "config" / "stopwords_domain.txt"
    words = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            words.append(line.lower())
    return words


def language_stopwords(language: str) -> list[str]:
    if language == "vi":
        path = APP_ROOT / "config" / "stopwords_vi.txt"
        return [w.strip() for w in path.read_text(encoding="utf-8").splitlines()
                if w.strip() and not w.startswith("#")]
    from pyspark.ml.feature import StopWordsRemover
    return StopWordsRemover.loadDefaultStopWords(language)


def get_spark(app_name: str, cfg: dict):
    from pyspark.sql import SparkSession

    return (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.shuffle.partitions", cfg["spark"]["shuffle_partitions"])
        .getOrCreate()
    )


def get_mongo_db(cfg: dict):
    from pymongo import MongoClient

    client = MongoClient(os.environ.get("MONGO_URI", "mongodb://mongodb:27017"))
    return client[cfg["mongo"]["database"]]


def reports_dir(cfg: dict) -> Path:
    path = Path(cfg["paths"]["reports_local"])
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=APP_ROOT, stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        return "unknown"


REGISTRY_FIELDS = [
    "id", "exp", "data", "model", "k", "vocab", "ngram", "domain_sw", "silhouette", "wssse",
    "perplexity", "npmi", "interpretability", "runtime_s", "seed", "min_df", "max_iter",
    "n_docs", "n_workers", "max_topic_share", "git_commit", "run_at", "note",
]


def append_registry(cfg: dict, row: dict) -> str:
    """Append one experiment run to experiments/experiment_results.csv; returns its id."""
    path = Path(cfg["paths"]["registry"])
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if path.exists():
        with open(path, encoding="utf-8", newline="") as f:
            existing = list(csv.DictReader(f))
    run_id = row.get("id") or f"E{len(existing) + 1:02d}"
    full = {field: "" for field in REGISTRY_FIELDS}
    full.update({k: v for k, v in row.items() if k in full})
    full.update(id=run_id, git_commit=git_commit(), run_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    write_header = not path.exists()
    with open(path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REGISTRY_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(full)
    return run_id


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.seconds = round(time.perf_counter() - self.start, 1)


def cfg_snapshot(cfg: dict) -> dict:
    return copy.deepcopy(cfg)
