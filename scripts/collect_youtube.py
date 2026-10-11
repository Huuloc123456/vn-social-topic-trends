"""Collect a balanced Vietnam-topic sample from public YouTube videos/comments.

Set YOUTUBE_API_KEY in the environment or in the project-root .env file, then run:
    python scripts/collect_youtube.py
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "youtube"
API = "https://www.googleapis.com/youtube/v3"
TOPICS = {
    "cong_nghe": "công nghệ Việt Nam",
    "giai_tri": "giải trí Việt Nam",
    "the_thao": "thể thao Việt Nam",
    "giao_duc": "giáo dục Việt Nam",
    "suc_khoe": "sức khỏe Việt Nam",
    "moi_truong": "môi trường Việt Nam",
    "kinh_te": "kinh tế Việt Nam",
}
MAX_COMMENTS_PER_VIDEO = 10


def load_key() -> str:
    if os.environ.get("YOUTUBE_API_KEY"):
        return os.environ["YOUTUBE_API_KEY"].strip()
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip().lstrip("\ufeff") == "YOUTUBE_API_KEY":
                return value.strip().strip("\"'")
    raise SystemExit("Missing YOUTUBE_API_KEY. Add it to .env (see .env.example).")


def get_json(key: str, path: str, **params):
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{API}/{path}?{query}", headers={"X-Goog-Api-Key": key}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"YouTube API {exc.code} at {path}: {detail[:500]}") from None


def month_windows(start: date, end_exclusive: date):
    current = start
    while current < end_exclusive:
        next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
        stop = min(next_month, end_exclusive)
        yield current, stop
        current = stop


def api_time(day: date) -> str:
    return datetime.combine(day, time.min, timezone.utc).isoformat().replace("+00:00", "Z")


def author_hash(value: str | None) -> str:
    if not value:
        return "unknown"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_video(out, video: dict, topic: str, video_ids: set[str]):
    video_id = video["id"]
    if video_id in video_ids:
        return False
    video_ids.add(video_id)
    snippet = video["snippet"]
    stats = video.get("statistics", {})
    text = "\n".join(part for part in (snippet.get("title", ""), snippet.get("description", "")) if part)
    record = {
        "uri": f"youtube:video:{video_id}",
        "source": "youtube",
        "record_type": "video",
        "topic_query": topic,
        "created_at": snippet["publishedAt"],
        "author": author_hash(snippet.get("channelId")),
        "text": text,
        "has_images": False,
        "reply_to": None,
        "video_id": video_id,
        "view_count": stats.get("viewCount"),
        "like_count": stats.get("likeCount"),
        "comment_count": stats.get("commentCount"),
    }
    out.write(json.dumps(record, ensure_ascii=False) + "\n")
    return True


def write_comments(out, key: str, video_id: str):
    try:
        result = get_json(key, "commentThreads", part="snippet", videoId=video_id,
                          order="relevance", maxResults=100, textFormat="plainText")
    except RuntimeError as exc:
        message = str(exc).lower()
        if "commentsdisabled" in message or "disabled comments" in message or "videonotfound" in message:
            return 0
        raise
    items = result.get("items", [])[:MAX_COMMENTS_PER_VIDEO]
    for item in items:
        comment = item["snippet"]["topLevelComment"]
        data = comment["snippet"]
        record = {
            "uri": f"youtube:comment:{comment['id']}",
            "source": "youtube",
            "record_type": "comment",
            "created_at": data.get("publishedAt"),
            "author": author_hash((data.get("authorChannelId") or {}).get("value")),
            "text": data.get("textDisplay", ""),
            "has_images": False,
            "reply_to": f"youtube:video:{video_id}",
            "video_id": video_id,
            "like_count": data.get("likeCount", 0),
            "reply_count": item["snippet"].get("totalReplyCount", 0),
        }
        out.write(json.dumps(record, ensure_ascii=False) + "\n")
    return len(items)


def main():
    key = load_key()
    start = date.fromisoformat(os.getenv("YOUTUBE_START_DATE", "2026-06-01"))
    end = date.fromisoformat(os.getenv("YOUTUBE_END_DATE", (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()))
    if end <= start:
        raise SystemExit("YOUTUBE_END_DATE must be after YOUTUBE_START_DATE")

    OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = OUT / f"youtube_{start:%Y%m%d}_{end:%Y%m%d}_{stamp}.jsonl"
    videos_seen: set[str] = set()
    video_count = comment_count = search_count = 0

    with target.open("w", encoding="utf-8") as out:
        for topic, query in TOPICS.items():
            for after, before in month_windows(start, end):
                result = get_json(key, "search", part="snippet", type="video", q=query,
                                  regionCode="VN", relevanceLanguage="vi", order="relevance",
                                  publishedAfter=api_time(after), publishedBefore=api_time(before),
                                  maxResults=50)
                search_count += 1
                ids = [item["id"]["videoId"] for item in result.get("items", [])]
                for offset in range(0, len(ids), 50):
                    page_ids = ids[offset:offset + 50]
                    if not page_ids:
                        continue
                    details = get_json(key, "videos", part="snippet,statistics", id=",".join(page_ids))
                    for video in details.get("items", []):
                        if write_video(out, video, topic, videos_seen):
                            video_count += 1
                            comment_count += write_comments(out, key, video["id"])
                            if video_count % 10 == 0:
                                print(f"[YouTube] progress: {video_count} videos, {comment_count} comments",
                                      flush=True)
                    out.flush()
                print(f"[YouTube] {topic} {after}..{before}: {len(ids)} videos", flush=True)

    print(f"[YouTube] saved {video_count} videos and {comment_count} top comments to {target}", flush=True)
    print(f"[YouTube] used {search_count} search.list calls (default daily limit: 100)", flush=True)


if __name__ == "__main__":
    main()
