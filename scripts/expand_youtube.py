"""Resume a balanced, quota-aware expansion of the public YouTube dataset.

Run with ``python scripts/expand_youtube.py``. Progress is kept under
data/raw/youtube so interrupted runs continue without replacing prior files.
"""
from __future__ import annotations

import hashlib
import json
import os
import time as time_module
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "youtube"
STATE = OUT / "expansion_state.json"
MANIFEST = ROOT / "reports" / "youtube_expansion_manifest.json"
API = "https://www.googleapis.com/youtube/v3"
PACIFIC = ZoneInfo("America/Los_Angeles")
BASE_RECORDS = 8415
TARGET_EXTRA_RECORDS = BASE_RECORDS * 10 + 1
MAX_COMMENTS_PER_VIDEO = 10
DAILY_SEARCH_CAP = 90
DAILY_OTHER_UNIT_CAP = 8500

TOPICS = {
    "cong_nghe": ["công nghệ Việt Nam", "trí tuệ nhân tạo Việt Nam", "điện thoại ứng dụng Việt Nam", "khoa học công nghệ Việt Nam"],
    "giai_tri": ["giải trí Việt Nam", "phim Việt Nam", "âm nhạc Việt Nam", "người nổi tiếng Việt Nam"],
    "the_thao": ["thể thao Việt Nam", "bóng đá Việt Nam", "bóng chuyền Việt Nam", "thể thao học đường Việt Nam"],
    "giao_duc": ["giáo dục Việt Nam", "học sinh sinh viên Việt Nam", "tuyển sinh Việt Nam", "giáo viên Việt Nam"],
    "suc_khoe": ["sức khỏe Việt Nam", "y tế Việt Nam", "dinh dưỡng Việt Nam", "sức khỏe tinh thần Việt Nam"],
    "moi_truong": ["môi trường Việt Nam", "ô nhiễm Việt Nam", "biến đổi khí hậu Việt Nam", "năng lượng xanh Việt Nam"],
    "kinh_te": ["kinh tế Việt Nam", "thị trường Việt Nam", "việc làm Việt Nam", "giá cả Việt Nam"],
}


def load_key() -> str:
    if os.environ.get("YOUTUBE_API_KEY"):
        return os.environ["YOUTUBE_API_KEY"].strip()
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            name, sep, value = line.partition("=")
            if sep and name.strip().lstrip("\ufeff") == "YOUTUBE_API_KEY":
                return value.strip().strip("\"'")
    raise SystemExit("Missing YOUTUBE_API_KEY in environment or project .env")


def initial_queue(start: date, end: date) -> list[dict]:
    queue = []
    current = start
    while current < end:
        stop = min(current + timedelta(days=7), end)
        for topic, queries in TOPICS.items():
            for query in queries:
                queue.append({"topic": topic, "query": query, "after": current.isoformat(),
                              "before": stop.isoformat(), "page_token": None})
        current = stop
    return queue


def read_state(start: date, end: date) -> dict:
    if STATE.exists():
        state = json.loads(STATE.read_text(encoding="utf-8"))
        if state.get("start") != start.isoformat() or state.get("end") != end.isoformat():
            raise SystemExit(f"Expansion state date range differs; inspect {STATE.name} before changing dates.")
        return state
    return {
        "start": start.isoformat(), "end": end.isoformat(),
        "target_extra_records": TARGET_EXTRA_RECORDS, "extra_records": 0,
        "videos": 0, "comments": 0, "search_calls": 35, "other_units": 6708,
        "quota_day_pt": datetime.now(PACIFIC).date().isoformat(),
        "queue": initial_queue(start, end), "pending_details": [],
        "comment_done_video_ids": [],
    }


def save_state(state: dict) -> None:
    temp = STATE.with_suffix(".tmp")
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(STATE)


def existing_uris() -> set[str]:
    found = set()
    for path in OUT.glob("*.jsonl"):
        with path.open(encoding="utf-8") as source:
            for line in source:
                try:
                    found.add(json.loads(line)["uri"])
                except (json.JSONDecodeError, KeyError):
                    continue
    return found


def write_manifest(state: dict) -> None:
    topic_counts: dict[str, int] = {}
    total = 0
    videos = comments = 0
    for path in OUT.glob("*.jsonl"):
        with path.open(encoding="utf-8") as source:
            for line in source:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                total += 1
                record_type = record.get("record_type")
                videos += record_type == "video"
                comments += record_type == "comment"
                topic = record.get("topic_query")
                if topic:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps({
        "source": "YouTube Data API v3",
        "status": state.get("status", "in_progress"),
        "started_range_utc": {"from": f"{state['start']}T00:00:00Z", "to_exclusive": f"{state['end']}T00:00:00Z"},
        "completed_at_utc": state.get("completed_at_utc"),
        "records_before_expansion": BASE_RECORDS,
        "additional_records": state["extra_records"],
        "records_total": total,
        "additional_target": TARGET_EXTRA_RECORDS,
        "additional_videos": state["videos"],
        "additional_comments": state["comments"],
        "records_by_topic": topic_counts,
        "search_calls_on_current_quota_day": state["search_calls"],
        "other_api_units_on_current_quota_day": state["other_units"],
        "region_code": "VN",
        "relevance_language": "vi",
        "max_top_level_comments_per_video": MAX_COMMENTS_PER_VIDEO,
        "author_identifiers": "SHA-256 hashed",
        "raw_file": "data/raw/youtube/expansion_records.jsonl",
        "retention_note": "YouTube API text metadata must be refreshed or deleted within 30 calendar days under current Developer Policies.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def reset_daily_counters(state: dict) -> None:
    today = datetime.now(PACIFIC).date().isoformat()
    if state["quota_day_pt"] != today:
        state["quota_day_pt"] = today
        state["search_calls"] = 0
        state["other_units"] = 0
        save_state(state)


def wait_for_reset(state: dict, reason: str) -> None:
    print(f"[YouTube] {reason}; waiting for the Pacific quota reset.", flush=True)
    quota_day = state["quota_day_pt"]
    while True:
        now = datetime.now(PACIFIC)
        if now.date().isoformat() != quota_day:
            reset_daily_counters(state)
            print("[YouTube] quota day reset; resuming.", flush=True)
            return
        reset_at = datetime.combine(now.date() + timedelta(days=1), time.min, PACIFIC)
        remaining = (reset_at - now).total_seconds()
        time_module.sleep(min(remaining, 60))


def api_call(key: str, state: dict, path: str, **params):
    search = path == "search"
    while True:
        reset_daily_counters(state)
        cap = DAILY_SEARCH_CAP if search else DAILY_OTHER_UNIT_CAP
        used = state["search_calls"] if search else state["other_units"]
        if used >= cap:
            wait_for_reset(state, f"daily {('search' if search else 'API')} safety cap reached ({used})")
            continue
        query = urllib.parse.urlencode(params)
        request = urllib.request.Request(f"{API}/{path}?{query}", headers={"X-Goog-Api-Key": key})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                result = json.load(response)
            state["search_calls" if search else "other_units"] += 1
            save_state(state)
            return result
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            lower = detail.lower()
            if exc.code in (403, 429) and any(term in lower for term in
                    ("quotaexceeded", "dailylimitexceeded", "userratelimitexceeded", "ratelimitexceeded")):
                wait_for_reset(state, f"YouTube reported a quota limit for {path}")
                continue
            raise RuntimeError(f"YouTube API {exc.code} at {path}: {detail[:500]}") from None


def author_hash(value: str | None) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest() if value else "unknown"


def api_time(day: str) -> str:
    return datetime.combine(date.fromisoformat(day), time.min, timezone.utc).isoformat().replace("+00:00", "Z")


def append_record(output, record: dict, known_uris: set[str], state: dict) -> bool:
    if record["uri"] in known_uris:
        return False
    output.write(json.dumps(record, ensure_ascii=False) + "\n")
    output.flush()
    known_uris.add(record["uri"])
    state["extra_records"] += 1
    if record["record_type"] == "video":
        state["videos"] += 1
    else:
        state["comments"] += 1
    return True


def collect_comments(key: str, state: dict, output, video_id: str, known_uris: set[str]) -> None:
    done = set(state["comment_done_video_ids"])
    if video_id in done:
        return
    try:
        result = api_call(key, state, "commentThreads", part="snippet", videoId=video_id,
                          order="relevance", maxResults=100, textFormat="plainText")
    except RuntimeError as exc:
        message = str(exc).lower()
        if "commentsdisabled" in message or "disabled comments" in message or "videonotfound" in message:
            state["comment_done_video_ids"].append(video_id)
            save_state(state)
            return
        raise
    for item in result.get("items", [])[:MAX_COMMENTS_PER_VIDEO]:
        comment = item["snippet"]["topLevelComment"]
        data = comment["snippet"]
        append_record(output, {
            "uri": f"youtube:comment:{comment['id']}", "source": "youtube", "record_type": "comment",
            "topic_query": state.get("active_topic"), "created_at": data.get("publishedAt"),
            "collected_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "author": author_hash((data.get("authorChannelId") or {}).get("value")),
            "text": data.get("textDisplay", ""), "has_images": False,
            "reply_to": f"youtube:video:{video_id}", "video_id": video_id,
            "like_count": data.get("likeCount", 0), "reply_count": item["snippet"].get("totalReplyCount", 0),
        }, known_uris, state)
    state["comment_done_video_ids"].append(video_id)
    save_state(state)


def main() -> None:
    start = date.fromisoformat(os.getenv("YOUTUBE_START_DATE", "2026-06-01"))
    end = date.fromisoformat(os.getenv("YOUTUBE_END_DATE", "2026-10-12"))
    if end <= start:
        raise SystemExit("YOUTUBE_END_DATE must be after YOUTUBE_START_DATE")
    OUT.mkdir(parents=True, exist_ok=True)
    key = load_key()
    state = read_state(start, end)
    known_uris = existing_uris()
    known_video_ids = {uri[len("youtube:video:"):] for uri in known_uris if uri.startswith("youtube:video:")}
    state["extra_records"] = sum(1 for uri in known_uris if not uri.startswith("youtube:"))
    # Count actual records created by expansion files; initial sample is excluded.
    prior_file = OUT / "expansion_records.jsonl"
    state["extra_records"] = 0
    if prior_file.exists():
        with prior_file.open(encoding="utf-8") as source:
            state["extra_records"] = sum(1 for line in source if line.strip())
    state["comment_done_video_ids"] = sorted(set(state.get("comment_done_video_ids", [])) | known_video_ids)
    state["target_extra_records"] = TARGET_EXTRA_RECORDS
    save_state(state)
    print(f"[YouTube] target: at least {TARGET_EXTRA_RECORDS:,} new records; currently {state['extra_records']:,}.", flush=True)

    with prior_file.open("a", encoding="utf-8") as output:
        while state["extra_records"] < TARGET_EXTRA_RECORDS and (state["queue"] or state["pending_details"]):
            if state["pending_details"]:
                video = state["pending_details"].pop(0)
                video_id = video["id"]
                topic = state.get("active_topic", "unknown")
                if video_id not in known_video_ids:
                    snippet = video["snippet"]
                    stats = video.get("statistics", {})
                    text = "\n".join(part for part in (snippet.get("title", ""), snippet.get("description", "")) if part)
                    append_record(output, {
                        "uri": f"youtube:video:{video_id}", "source": "youtube", "record_type": "video",
                        "topic_query": topic, "created_at": snippet.get("publishedAt"),
                        "collected_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "author": author_hash(snippet.get("channelId")), "text": text,
                        "has_images": False, "reply_to": None, "video_id": video_id,
                        "view_count": stats.get("viewCount"), "like_count": stats.get("likeCount"),
                        "comment_count": stats.get("commentCount"),
                    }, known_uris, state)
                    known_video_ids.add(video_id)
                save_state(state)
                collect_comments(key, state, output, video_id, known_uris)
                if state["videos"] % 50 == 0:
                    print(f"[YouTube] progress: {state['extra_records']:,} new records; {state['videos']:,} videos; "
                          f"{state['comments']:,} comments.", flush=True)
                save_state(state)
                continue

            task = state["queue"].pop(0)
            state["active_topic"] = task["topic"]
            result = api_call(key, state, "search", part="snippet", type="video", q=task["query"],
                              regionCode="VN", relevanceLanguage="vi", order="relevance",
                              publishedAfter=api_time(task["after"]), publishedBefore=api_time(task["before"]),
                              maxResults=50, **({"pageToken": task["page_token"]} if task["page_token"] else {}))
            video_ids = [item["id"]["videoId"] for item in result.get("items", [])]
            if result.get("nextPageToken"):
                next_task = dict(task, page_token=result["nextPageToken"])
                state["queue"].append(next_task)
            for offset in range(0, len(video_ids), 50):
                ids = video_ids[offset:offset + 50]
                if ids:
                    details = api_call(key, state, "videos", part="snippet,statistics", id=",".join(ids))
                    state["pending_details"].extend(details.get("items", []))
                    save_state(state)
            save_state(state)

    status = "target_reached" if state["extra_records"] >= TARGET_EXTRA_RECORDS else "search_queue_exhausted"
    state["status"] = status
    state["completed_at_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    save_state(state)
    write_manifest(state)
    print(f"[YouTube] {status}: {state['extra_records']:,} new records, "
          f"{state['videos']:,} videos, {state['comments']:,} comments.", flush=True)


if __name__ == "__main__":
    main()
