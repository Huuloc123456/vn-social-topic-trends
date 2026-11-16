import csv
import json
from datetime import datetime, timezone

from scripts import export_news_videos as exporter


def _record(video_id, channel_id, title, published):
    return {
        "record_type": "video",
        "uri": f"youtube:video:{video_id}",
        "channel_id": channel_id,
        "text": title,
        "created_at": published,
    }


def _detail(video_id, channel_id, channel, title, published, likes, source="videos.list"):
    return {
        "id": video_id,
        "snippet": {
            "title": title,
            "publishedAt": published,
            "channelId": channel_id,
            "channelTitle": channel,
        },
        "statistics": {"viewCount": "20", "likeCount": likes},
        "collected_at_utc": "2026-11-14T00:00:00Z",
        "metadata_source": source,
    }


def test_streamed_index_export_keeps_latest_per_channel_and_cross_channel_duplicates(tmp_path, monkeypatch):
    monkeypatch.setattr(exporter, "ROOT", tmp_path)
    monkeypatch.setattr(exporter, "RECORDS", tmp_path / "raw.jsonl")
    monkeypatch.setattr(exporter, "CACHE", tmp_path / "cache.jsonl")
    monkeypatch.setattr(exporter, "EXPORT", tmp_path / "out.csv")
    monkeypatch.setattr(exporter, "REPORT", tmp_path / "manifest.json")

    videos = [
        _detail("one-old", "channel-one", "Kênh một", "Tin nóng", "2026-01-01T10:00:00Z", "3"),
        _detail("one-new", "channel-one", "Kênh một", " tin nóng ", "2026-01-02T10:00:00Z", "4"),
        _detail("two-same", "channel-two", "Kênh hai", "TIN NÓNG", "2026-01-01T11:00:00Z", "0",
                "videos.batchGetStats"),
        _detail("two-no-likes", "channel-two", "Kênh hai", "Tin khác", "2026-01-03T10:00:00Z", None),
    ]
    exporter.RECORDS.write_text("".join(json.dumps(_record(
        video["id"], video["snippet"]["channelId"], video["snippet"]["title"],
        video["snippet"]["publishedAt"])) + "\n" for video in videos), encoding="utf-8")
    exporter.CACHE.write_text("".join(json.dumps(video) + "\n" for video in videos), encoding="utf-8")

    connection = exporter.sqlite3.connect(tmp_path / "index.sqlite3")
    try:
        requested, pending = exporter.build_index(connection, datetime(2026, 11, 15, tzinfo=timezone.utc))
        assert (requested, pending) == (4, 0)

        result = exporter.export(connection, [
            {"id": "channel-one", "name": "Kênh một"},
            {"id": "channel-two", "name": "Kênh hai"},
        ], {"start": "2023-01-01", "end": "2026-10-30", "status": "complete"}, "complete")
        assert result == 2
    finally:
        connection.close()

    with exporter.EXPORT.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    manifest = json.loads(exporter.REPORT.read_text(encoding="utf-8"))

    assert {row["video_id"] for row in rows} == {"one-new", "two-same"}
    assert manifest["metadata_checked"] == 4
    assert manifest["eligible_video_ids_before_like_filter"] == 4
    assert manifest["video_ids_excluded_missing_like_count"] == 1
    assert manifest["title_groups_retained_across_channels"] == 1
    assert manifest["batch_stats_video_ids"] == 1
    assert manifest["batch_stats_csv_rows"] == 1
    assert manifest["missing_like_count"] == 0
