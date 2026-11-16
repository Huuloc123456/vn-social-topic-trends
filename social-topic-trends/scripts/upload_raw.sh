#!/usr/bin/env sh
# Ingest only the selected official-news CSV into HDFS.
# Run from the docker/ folder:  docker compose exec namenode sh /scripts/upload_raw.sh
# (the compose file mounts ../data at /input and ../scripts at /scripts).
set -e
test -s /input/exports/youtube_news_videos_clean.csv
hdfs dfsadmin -safemode wait
hdfs dfs -mkdir -p /social/raw/youtube_news
hdfs dfs -put -f /input/exports/youtube_news_videos_clean.csv /social/raw/youtube_news/youtube_news_videos_clean.csv
hdfs dfs -du -s -h /social/raw/youtube_news
