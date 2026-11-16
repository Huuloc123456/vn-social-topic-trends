"""Week-2 smoke test (plan 5.1): HDFS write/read, MongoDB write/read, workers alive.

    docker compose exec spark-client spark-submit scripts/smoke_test.py
"""
import json
import sys
import urllib.request

from src.common import get_mongo_db, get_spark, load_config


def main() -> int:
    cfg = load_config()
    spark = get_spark("smoke-test", cfg)
    ok = True

    df = spark.range(1000).withColumnRenamed("id", "n")
    df.write.mode("overwrite").parquet("hdfs:///tmp/smoke")
    n = spark.read.parquet("hdfs:///tmp/smoke").count()
    print(f"[1-2] HDFS write/read: {n} rows", "OK" if n == 1000 else "FAIL")
    ok &= n == 1000

    db = get_mongo_db(cfg)
    db.smoke.replace_one({"_id": "ping"}, {"_id": "ping", "value": 42}, upsert=True)
    got = db.smoke.find_one({"_id": "ping"})
    print("[3]   MongoDB write/read:", "OK" if got and got["value"] == 42 else "FAIL")
    ok &= bool(got and got["value"] == 42)
    db.smoke.drop()

    with urllib.request.urlopen("http://spark-master:8080/json/") as resp:
        workers = [w for w in json.load(resp)["workers"] if w["state"] == "ALIVE"]
    print(f"[4]   Spark workers ALIVE: {len(workers)}", "OK" if len(workers) >= 2 else "WARN (<2)")

    spark.stop()
    print("SMOKE TEST", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
