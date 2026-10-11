# VN Social Topic Trends

Analyze Vietnamese-language topics and changes in discussion over time using public YouTube videos and comments. The project collects a balanced sample across several broad topics, processes the records with Apache Spark, and presents the results in a Streamlit dashboard.

This repository contains code and configuration. Collected YouTube API data, API keys, Spark outputs, and trained models stay outside Git.

## Scope

The current source is YouTube Data API v3. The collector searches for public videos in Vietnam across seven topic groups:

| Topic key | Search theme |
|---|---|
| `cong_nghe` | Technology |
| `giai_tri` | Entertainment |
| `the_thao` | Sports |
| `giao_duc` | Education |
| `suc_khoe` | Health |
| `moi_truong` | Environment |
| `kinh_te` | Economy |

For each video, the collector stores its title and description plus up to ten top-level comments returned by the API's relevance ordering. It does not collect nested replies. The query sample is useful for topic-trend analysis, but search ranking and query coverage mean it is not a census of YouTube or a representative survey of Vietnamese public opinion.

## Data and privacy

JSONL records are written under `data/raw/youtube/`. Each record includes an identifier, record type (`video` or `comment`), topic query, publication time, text, video relationship, and available interaction counts. Author identifiers are SHA-256 hashes.

Raw API data and CSV exports are intentionally excluded from Git. YouTube's Developer Policies require most stored API Data to be refreshed or deleted after 30 calendar days; some statistics have separate conditions. Review the [YouTube API Services Developer Policies](https://developers.google.com/youtube/terms/developer-policies) before collecting or retaining data. Keep the local `.env` file private and never commit API keys.

## Architecture

```text
YouTube Data API v3
        │ scripts/collect_youtube.py or scripts/expand_youtube.py
        ▼
data/raw/youtube/*.jsonl
        │ HDFS upload
        ▼
HDFS /social/raw/youtube
        │ Spark ETL: validation, deduplication, Vietnamese language filter,
        │ text normalization and model-ready tokenization
        ▼
HDFS clean datasets and samples
        │ Spark MLlib: TF-IDF, Word2Vec, KMeans, BisectingKMeans and LDA
        ▼
Topic and time-series outputs ──► MongoDB ──► Streamlit dashboard
```

The dashboard source and layout are retained. Its charts require outputs generated from the current YouTube dataset; old data and model artifacts have been removed from this repository.

## Requirements

- Windows 10/11 with Docker Desktop and WSL2, or a compatible Docker host.
- At least 12 GB RAM available to Docker for the full Spark cluster.
- Python 3.10 or newer for local collection and tests.
- A Google Cloud project with **YouTube Data API v3** enabled and an API key.
- Approximately 5 GB free disk space for Docker images, HDFS and intermediate Spark data.

## Setup

Clone the repository, create the local environment file, and add the API key:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set `YOUTUBE_API_KEY`. Do not paste the key into source files or commit `.env`.

Build and start the services from the repository root:

```bash
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up -d
```

The Compose stack contains HDFS, a Spark master and two workers, a Spark job client, and MongoDB. The dashboard is available at <http://127.0.0.1:8501> after results have been produced and exported.

## Collect YouTube data

The standard collector searches the seven topic groups over monthly date windows. The end date is exclusive; defaults are `2026-06-01` through the current UTC date plus one day.

```bash
python scripts/collect_youtube.py
```

To set a different collection interval, configure `YOUTUBE_START_DATE` and `YOUTUBE_END_DATE` in the environment before running the collector, for example:

```powershell
$env:YOUTUBE_START_DATE = "2026-06-01"
$env:YOUTUBE_END_DATE = "2026-10-01"
python scripts/collect_youtube.py
```

For a larger, resumable collection, run:

```bash
python scripts/expand_youtube.py
```

The expansion collector saves its queue and progress in `data/raw/youtube/expansion_state.json`, deduplicates records, and pauses when its daily API quota budget is reached. Run it again to resume. API quota availability is controlled by Google Cloud and may limit collection speed.

## Process and analyze

Run these commands from the repository root after collection.

1. Copy the raw YouTube JSONL files into HDFS:

   ```bash
   docker compose -f docker/docker-compose.yml exec namenode sh /scripts/upload_raw.sh
   ```

2. Clean and prepare the data, then calculate descriptive statistics:

   ```bash
   docker compose -f docker/docker-compose.yml exec spark-client spark-submit src/etl/clean.py
   docker compose -f docker/docker-compose.yml exec spark-client spark-submit src/eda/statistics.py
   ```

3. Run the experiment suite and train models. Experiment IDs are recorded in `experiments/experiment_results.csv` inside the mounted project directory:

   ```bash
   docker compose -f docker/docker-compose.yml exec spark-client sh scripts/run_experiments.sh baseline
   docker compose -f docker/docker-compose.yml exec spark-client spark-submit src/model/train.py --model w2v_kmeans --k 10 --exp Final --data full --save
   docker compose -f docker/docker-compose.yml exec spark-client spark-submit src/model/train.py --model lda --k 10 --exp Final --data full --save
   ```

4. Finalize trends with the experiment IDs produced in step 3, then export aggregates to MongoDB:

   ```bash
   docker compose -f docker/docker-compose.yml exec spark-client spark-submit src/trend/finalize.py --run WORD2VEC_RUN_ID --secondary LDA_RUN_ID
   docker compose -f docker/docker-compose.yml exec spark-client python3 -m src.export.export_mongo
   ```

5. Open or refresh <http://127.0.0.1:8501>. The dashboard reads MongoDB and the locally generated model artifacts.

The full experiment workflow, trend settings, and preprocessing rules are configured in `config/config.yaml`. HDFS, model, report, and experiment outputs are generated locally and are not tracked by Git.

## Tests

Run the unit tests from the repository root:

```bash
python -m pytest tests -q
```

## Repository layout

```text
config/                  Dataset, preprocessing and trend configuration
dashboard/               Streamlit dashboard and local model inference
docker/                  HDFS, Spark, MongoDB and dashboard services
scripts/                 YouTube collectors and pipeline utilities
src/etl/                 Spark data-quality and preprocessing pipeline
src/eda/                 Descriptive statistics
src/model/               Topic models and model evaluation
src/trend/               Topic time series, burst detection and finalization
src/export/              MongoDB export
tests/                   Unit tests for trend and model metrics
data/raw/youtube/         Local YouTube JSONL data (not committed)
data/exports/             Local CSV snapshots (not committed)
```
