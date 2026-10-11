#!/usr/bin/env sh
# Step 01 – ingest: copy raw JSONL files into HDFS (bronze layer).
# Run from the docker/ folder:  docker compose exec namenode sh /scripts/upload_raw.sh
# (the compose file mounts ../data at /input and ../scripts at /scripts).
set -e
RAW_SOURCE=${RAW_SOURCE:-youtube}
hdfs dfs -mkdir -p "/social/raw/$RAW_SOURCE"
hdfs dfs -put -f "/input/raw/$RAW_SOURCE"/*.jsonl "/social/raw/$RAW_SOURCE/"
hdfs dfs -du -s -h "/social/raw/$RAW_SOURCE"
hdfs fsck /social/raw -files -blocks | tail -n 20
