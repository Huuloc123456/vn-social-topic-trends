#!/usr/bin/env sh
# Run inside spark-client after scripts/upload_raw.sh has uploaded the news CSV.
set -eu
spark-submit src/etl/clean.py
spark-submit src/eda/statistics.py
spark-submit src/model/train.py --model w2v_kmeans --k 10 --exp NewsFinal --data full --save
PRIMARY=$(python3 -c 'import csv; from src.common import load_config; print(list(csv.DictReader(open(load_config()["paths"]["registry"])))[-1]["id"])')
spark-submit src/model/train.py --model lda --k 10 --exp NewsFinal --data full --save
SECONDARY=$(python3 -c 'import csv; from src.common import load_config; print(list(csv.DictReader(open(load_config()["paths"]["registry"])))[-1]["id"])')
spark-submit src/trend/finalize.py --run "$PRIMARY" --secondary "$SECONDARY"
python3 -m src.export.export_mongo
