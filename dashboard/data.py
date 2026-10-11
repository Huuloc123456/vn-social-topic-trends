"""MongoDB access for the dashboard. Every query is cached; the dashboard
never touches HDFS or the Spark cluster (plan 12.4)."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from pymongo import MongoClient

APP_ROOT = Path(__file__).resolve().parent.parent
DB_NAME = "social_topics"


@st.cache_resource
def _db():
    client = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27018"), serverSelectionTimeoutMS=3000)
    return client[DB_NAME]


def _docs(name: str, query: dict | None = None, sort: list | None = None) -> list[dict]:
    cur = _db()[name].find(query or {}, {"_id": 0})
    if sort:
        cur = cur.sort(sort)
    return list(cur)


@st.cache_data(ttl=600)
def available() -> bool:
    try:
        return _db()["topics"].estimated_document_count() > 0
    except Exception:
        return False


@st.cache_data(ttl=600)
def one(name: str) -> dict:
    docs = _docs(name)
    return docs[0] if docs else {}


@st.cache_data(ttl=600)
def frame(name: str, sort: tuple | None = None) -> pd.DataFrame:
    return pd.DataFrame(_docs(name, sort=list(sort) if sort else None))


@st.cache_data(ttl=600)
def topics() -> pd.DataFrame:
    df = frame("topics", (("topic_id", 1),))
    return df.sort_values("share", ascending=False).reset_index(drop=True)


@st.cache_data(ttl=600)
def trend() -> pd.DataFrame:
    df = frame("topic_trend")
    df["bucket"] = pd.to_datetime(df["bucket"])
    return df


@st.cache_data(ttl=600)
def bursts() -> pd.DataFrame:
    df = frame("burst_events")
    if not df.empty:
        for c in ("start", "peak", "end"):
            df[c] = pd.to_datetime(df[c])
        df = df.sort_values("peak")
    return df


@st.cache_data(ttl=600)
def posts_per_bin() -> pd.DataFrame:
    df = frame("posts_per_bin")
    df["bucket"] = pd.to_datetime(df["bucket"])
    return df.sort_values("bucket")


@st.cache_data(ttl=600)
def representative(topic_id: int) -> pd.DataFrame:
    return pd.DataFrame(_docs("representative_posts", {"topic_id": int(topic_id)}, [("score", -1)]))


@st.cache_data(ttl=3600)
def sensitive_terms() -> set[str]:
    path = APP_ROOT / "config" / "sensitive_terms.txt"
    if not path.exists():
        return set()
    return {w.strip().lower() for w in path.read_text(encoding="utf-8").splitlines()
            if w.strip() and not w.startswith("#")}


ADULT_STEMS = ("nsfw", "porn", "hentai", "onlyfans", "nude", "lewd")


def is_safe_term(term: str) -> bool:
    """Exact lexicon match, plus compound hashtags such as 'nsfwanimation'."""
    t = term.lower()
    return t not in sensitive_terms() and not any(stem in t for stem in ADULT_STEMS)


@st.cache_data(ttl=3600)
def profanity() -> set[str]:
    path = APP_ROOT / "config" / "profanity.txt"
    if not path.exists():
        return set()
    return {w.strip().lower() for w in path.read_text(encoding="utf-8").splitlines()
            if w.strip() and not w.startswith("#")}


def mask(term: str) -> str:
    """Presentation mode: 'fuck' -> 'f***' (display only)."""
    return term[0] + "*" * (len(term) - 1) if term.lower() in profanity() else term


def mask_text(text: str) -> str:
    import re

    words = profanity()
    return re.sub(r"[A-Za-z]+", lambda m: mask(m.group(0)) if m.group(0).lower() in words else m.group(0), text)
