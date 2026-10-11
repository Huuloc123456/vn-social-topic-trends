"""Step 10 – load the aggregated results into MongoDB (serving layer, plan 20).

    python -m src.export.export_mongo          (inside spark-client)

MongoDB only holds small aggregates for the dashboard, never feature vectors.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from pymongo import ASCENDING

from src.common import get_mongo_db, load_config


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def replace(db, name: str, docs, indexes: list[list[tuple]] | None = None):
    if docs is None:
        print(f"[MONGO] skip {name} (no source file)")
        return
    docs = docs if isinstance(docs, list) else [docs]
    db[name].drop()
    if docs:
        db[name].insert_many([dict(d) for d in docs])
    for keys in indexes or []:
        db[name].create_index(keys)
    print(f"[MONGO] {name}: {len(docs)} docs")


def main():
    cfg = load_config()
    db = get_mongo_db(cfg)
    rep = Path(cfg["paths"]["reports_local"])
    final = rep / "final"

    dq = load(rep / "data_quality.json")
    eda = load(rep / "eda.json")
    replace(db, "data_quality", dq)
    if eda:
        replace(db, "overview", {**eda["totals"], "gap_bins": eda["gap_bins"]})
        replace(db, "posts_per_bin", eda["posts_per_bin"], [[("bucket", ASCENDING)]])
        replace(db, "top_hashtags", eda["top_hashtags"])
        replace(db, "top_hashtags_safe", eda.get("top_hashtags_safe", []))
        replace(db, "eda_distributions", {
            "token_length": eda["token_length_distribution"],
            "author_activity": eda["author_activity_distribution"],
            "top_tokens": eda["top_tokens_by_doc_frequency"],
            "top_hashtags_by_hour": eda["top_hashtags_by_hour"],
            "posts_per_hour": eda["posts_per_hour"],
        })

    replace(db, "model_info", load(final / "model_info.json"))
    replace(db, "topics", load(final / "topics.json"), [[("topic_id", ASCENDING)]])
    replace(db, "topic_trend", load(final / "topic_trend.json"), [[("topic_id", ASCENDING), ("bucket", ASCENDING)]])
    replace(db, "burst_events", load(final / "burst_events.json"), [[("topic_id", ASCENDING)]])
    replace(db, "representative_posts", load(final / "representative_posts.json"), [[("topic_id", ASCENDING)]])
    replace(db, "keyword_trend", load(final / "keyword_trend_hourly.json"))
    replace(db, "hashtag_trend", load(final / "hashtag_trend.json"), [[("hashtag", ASCENDING), ("bucket", ASCENDING)]])
    replace(db, "scalability", load(rep / "scalability.json"))

    registry = Path(cfg["paths"]["registry"])
    if registry.exists():
        with open(registry, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        runs = Path(cfg["paths"]["registry"]).parent / "runs"
        for r in rows:
            run = load(runs / f"{r['id']}.json")
            r["topics"] = run["topics"] if run else []
        replace(db, "experiment_results", rows)


if __name__ == "__main__":
    main()
