"""Check all uploads pages for missing in-window videos, without a date cutoff.

The normal collector stops on an old page. This independent resumable scan checks
that assumption across channels in round-robin order. It appends only unseen IDs
inside the current dataset window and never refreshes existing video statistics.
"""
from __future__ import annotations

import json
import sys
import time
from collections import deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.collect_news_titles import (
    DAILY_BUDGET, OUT, PACIFIC, RECORDS, STATE as NEWS_STATE,
    clean_title, export_results, recorded_regular_calls,
)
from scripts.youtube_api import get_json, load_key

STATE = OUT / "news_titles_full_scan_state.json"
INTERVAL_SECONDS = 0.15  # At most 400 request launches per minute.


def save(state: dict) -> None:
    temp = STATE.with_suffix(".tmp")
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    # Windows readers can briefly hold the destination without delete sharing.
    for attempt in range(20):
        try:
            temp.replace(STATE)
            return
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(0.05)


def main() -> None:
    news = json.loads(NEWS_STATE.read_text(encoding="utf-8"))
    if news["status"] != "complete":
        raise SystemExit("Finish the regular uploads pass before starting the independent full scan")
    channels = json.loads((ROOT / "config/youtube_news_channels.json").read_text(encoding="utf-8"))
    day = datetime.now(PACIFIC).date().isoformat()
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {
        "start": news["start"], "end": news["end"], "channels": {},
        "calls": 0, "quota_day_pt": day, "pages": 0, "new_video_ids": 0,
        "mode": "all_upload_pages_round_robin_without_date_cutoff",
    }
    if state["start"] != news["start"] or state["end"] > news["end"]:
        raise SystemExit("Keep the full scan start and do not narrow its end date")
    state["end"] = news["end"]
    if state["quota_day_pt"] != day:
        state.update(quota_day_pt=day, calls=0)
    elif state.get("status") == "quota_exhausted":
        raise SystemExit("Ordinary quota already rejected the full scan today; resume after reset")
    seen = set()
    with RECORDS.open(encoding="utf-8-sig") as source:
        for line in source:
            seen.add(json.loads(line)["uri"])
    queue = deque()
    for channel in channels:
        cursor = state["channels"].setdefault(channel["id"], {"page_token": None, "pages": 0, "complete": False})
        if not cursor["complete"]:
            queue.append(channel)
    key = load_key()
    state["status"] = "in_progress"
    save(state)
    active = {}
    next_launch = 0.0
    stop_reason = None
    print(f"[FULL] {len(queue)} channels; {len(seen):,} known IDs; ordinary budget {recorded_regular_calls(day)}/{DAILY_BUDGET}.", flush=True)
    try:
        with ThreadPoolExecutor(max_workers=16) as pool, RECORDS.open("a", encoding="utf-8") as output:
            while queue or active:
                if queue and len(active) < 16 and not stop_reason and time.monotonic() >= next_launch:
                    current_day = datetime.now(PACIFIC).date().isoformat()
                    if current_day != day:
                        stop_reason = "date_changed"
                    elif recorded_regular_calls(day) >= DAILY_BUDGET:
                        stop_reason = "budget_limited"
                    else:
                        channel = queue.popleft()
                        token = state["channels"][channel["id"]]["page_token"]
                        state["calls"] += 1
                        save(state)
                        future = pool.submit(get_json, key, "playlistItems", part="snippet,contentDetails",
                                             playlistId=channel["uploads"], maxResults=50,
                                             fields="nextPageToken,items(snippet/title,contentDetails/videoId,contentDetails/videoPublishedAt)",
                                             **({"pageToken": token} if token else {}))
                        active[future] = (channel, token)
                        next_launch = time.monotonic() + INTERVAL_SECONDS
                if not active:
                    if stop_reason:
                        break
                    time.sleep(INTERVAL_SECONDS)
                    continue
                delay = INTERVAL_SECONDS
                if queue and len(active) < 16 and not stop_reason:
                    delay = max(0.0, next_launch - time.monotonic())
                done, _ = wait(active, timeout=delay, return_when=FIRST_COMPLETED)
                for future in done:
                    channel, token = active.pop(future)
                    cursor = state["channels"][channel["id"]]
                    try:
                        page = future.result()
                    except Exception as exc:
                        cursor["last_error"] = str(exc)
                        if "quotaExceeded" in str(exc) or ("API 429" in str(exc) and "per day" in str(exc)):
                            stop_reason = "quota_exhausted"
                            state["quota_error"] = str(exc)
                        else:
                            # Keep this page token for a later retry, without looping on a failed source.
                            print(f"[FULL] Source paused: {channel['name']}: {str(exc)[:180]}", flush=True)
                        save(state)
                        continue
                    for item in page.get("items", []):
                        details = item.get("contentDetails", {})
                        published, video_id = details.get("videoPublishedAt"), details.get("videoId")
                        if not published or not video_id:
                            continue
                        uri = "youtube:video:" + video_id
                        title = clean_title(item.get("snippet", {}).get("title", ""))
                        if (uri in seen or not title or not state["start"] <= published[:10] < state["end"]
                                or datetime.fromisoformat(published.replace("Z", "+00:00")) > datetime.now(timezone.utc)):
                            continue
                        output.write(json.dumps({"uri": uri, "source": "youtube", "record_type": "video",
                                                 "topic_query": "thoi_su", "created_at": published,
                                                 "channel_id": channel["id"], "text": title,
                                                 "collection_pass": "full_uploads_scan"}, ensure_ascii=False) + "\n")
                        seen.add(uri)
                        state["new_video_ids"] += 1
                    output.flush()
                    next_token = page.get("nextPageToken")
                    cursor["pages"] += 1
                    state["pages"] += 1
                    if next_token and next_token == token:
                        cursor["last_error"] = "Repeated page token; paused to avoid a request loop"
                    else:
                        cursor.update(page_token=next_token, complete=not next_token)
                        cursor.pop("last_error", None)
                        if next_token and not stop_reason:
                            queue.append(channel)
                    save(state)
                    if state["pages"] % 100 == 0:
                        print(f"[FULL] {state['pages']:,} pages; +{state['new_video_ids']:,} missing IDs; ordinary {recorded_regular_calls(day)}/{DAILY_BUDGET}.", flush=True)
                if stop_reason:
                    queue.clear()
        state["status"] = stop_reason or ("complete" if all(v["complete"] for v in state["channels"].values()) else "partial_sources")
    except BaseException:
        state["status"] = "interrupted"
        raise
    finally:
        state["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
        save(state)
        export_results(channels, news)
        print(f"[FULL] {state['status']}: {state['pages']:,} pages; +{state['new_video_ids']:,} IDs; checkpoint saved.", flush=True)


if __name__ == "__main__":
    main()
