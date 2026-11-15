"""Use remaining Search requests for new videos from configured news channels.

Search has a separate 100-request daily bucket. It supplements, and never advances,
the uploads checkpoint; its index may be delayed or incomplete. No new publishers
are admitted through this command.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.collect_news_titles import RECORDS, STATE, PACIFIC, clean_title, export_results
from scripts.youtube_api import get_json, load_key

SEARCH_LEDGER = ROOT / "reports/youtube_channel_search_state.json"
RUN = ROOT / "reports/youtube_news_search_tail_state.json"


def main() -> None:
    channels = json.loads((ROOT / "config/youtube_news_channels.json").read_text(encoding="utf-8"))
    checkpoint = json.loads(STATE.read_text(encoding="utf-8"))
    ledger = json.loads(SEARCH_LEDGER.read_text(encoding="utf-8"))
    day = datetime.now(PACIFIC).date().isoformat()
    if ledger.get("quota_day_pt") != day:
        raise SystemExit("Search ledger date differs; reconcile project usage before starting")
    run = json.loads(RUN.read_text(encoding="utf-8")) if RUN.exists() else {}
    if run.get("quota_day_pt") != day:
        run = {"quota_day_pt": day, "checked_channels": [], "new_video_ids": 0, "status": "running"}
    if run.get("status") == "quota_exhausted":
        raise SystemExit("Search daily quota already rejected requests today; resume after reset")
    counts = {c["id"]: c["csv_rows"] for c in json.loads(
        (ROOT / "reports/youtube_news_videos_manifest.json").read_text(encoding="utf-8"))["channels"]}
    unfinished = set(checkpoint["channels"][checkpoint["channel_index"]:])
    ordered = sorted(channels, key=lambda c: (c["id"] not in unfinished, -counts.get(c["id"], 0)))
    seen = set()
    with RECORDS.open(encoding="utf-8-sig") as source:
        for line in source:
            seen.add(json.loads(line)["uri"].rsplit(":", 1)[-1])
    key = load_key()
    try:
        with RECORDS.open("a", encoding="utf-8") as output:
            for channel in ordered:
                if ledger["calls"] >= 100:
                    run["status"] = "search_daily_budget_reached"
                    break
                if channel["id"] in run["checked_channels"]:
                    continue
                params = {"part": "snippet", "type": "video", "channelId": channel["id"],
                          "order": "date", "maxResults": 50,
                          "publishedAfter": checkpoint["start"] + "T00:00:00Z",
                          "publishedBefore": checkpoint["end"] + "T00:00:00Z"}
                ledger["calls"] += 1
                SEARCH_LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
                response = get_json(key, "search", **params)
                ledger["results"].append({"query": "new videos from " + channel["id"],
                                          "parameters": params, "items": response.get("items", [])})
                SEARCH_LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
                added = 0
                now = datetime.now(timezone.utc)
                for item in response.get("items", []):
                    snippet = item.get("snippet", {})
                    video_id = item.get("id", {}).get("videoId")
                    published = snippet.get("publishedAt", "")
                    if (not video_id or video_id in seen or snippet.get("channelId") != channel["id"]
                            or not checkpoint["start"] <= published[:10] < checkpoint["end"]
                            or datetime.fromisoformat(published.replace("Z", "+00:00")) > now):
                        continue
                    record = {"uri": "youtube:video:" + video_id, "source": "youtube",
                              "record_type": "video", "topic_query": "thoi_su", "created_at": published,
                              "channel_id": channel["id"], "text": clean_title(snippet.get("title", "")),
                              "retrieval_method": "search.list"}
                    if not record["text"]:
                        continue
                    output.write(json.dumps(record, ensure_ascii=False) + "\n")
                    seen.add(video_id)
                    added += 1
                output.flush()
                run["checked_channels"].append(channel["id"])
                run["new_video_ids"] += added
                RUN.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"[SEARCH] {ledger['calls']}/100; +{added} IDs; {channel['name']}", flush=True)
            else:
                run["status"] = "selected_channels_checked"
    except Exception as exc:
        run["status"] = "quota_exhausted" if "quota" in str(exc).lower() and (
            "API 429" in str(exc) or "quotaExceeded" in str(exc)) else "interrupted"
        run["error"] = str(exc)
        raise
    finally:
        run["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
        RUN.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
        export_results(channels, checkpoint)


if __name__ == "__main__":
    main()
