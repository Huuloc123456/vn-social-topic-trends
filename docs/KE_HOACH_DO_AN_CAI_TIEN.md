# KẾ HOẠCH ĐỒ ÁN CẢI TIẾN – PHÂN TÍCH XU HƯỚNG CHỦ ĐỀ TRONG DỮ LIỆU MẠNG XÃ HỘI BẰNG APACHE SPARK

> **Môn:** Nhập môn Big Data  
> **Đề tài số 5:** Phân tích xu hướng chủ đề trên mạng xã hội  
> **Nhóm:** 2 sinh viên  
> **Thời lượng:** 10 tuần  
> **Phiên bản:** v2 – đã chỉnh sửa theo đánh giá (lọc ngôn ngữ, đọc CSV, quy tắc so sánh độ đo, NPMI, burst theo giờ, chọn mô hình cuối, dashboard v0 cho GĐ1, inference trong dashboard, hạ tầng Docker, mốc nộp chính thức)  
> **Mục tiêu:** Hoàn thành đầy đủ yêu cầu học phần, có pipeline Big Data chạy thực tế, có baseline → đánh giá → cải tiến → dashboard minh họa giá trị dữ liệu.

> **Cập nhật v3 (04/10/2026) – đã triển khai.** Dữ liệu đổi từ US Election 2020 Tweets (quá thiên về một chủ đề) sang
> **Bluesky two-million posts** (Hugging Face `alpindale/two-million-bluesky-posts`, 2.107.530 bài, firehose
> 27/11/2024, ~07:50–15:40 UTC, đa chủ đề, đa ngôn ngữ). Những thay đổi so với nội dung bên dưới:
>
> | Mục | Thay đổi |
> |---|---|
> | 2, 7 | Đọc JSONL (không còn vấn đề CSV nhiều dòng); `uri` là khóa duy nhất; không có cột retweet, lượt thích, vị trí → bỏ trang địa lý. Bài ngoài khung thời gian là bài nhập lại từ kho cũ (152.667 bài). |
> | 13–14 | Dữ liệu chỉ ~8 giờ → xu hướng **trong ngày**: khung **5 phút**, nền = **60 phút trước** (12 khung), `min_periods` 6. Bùng nổ khi z > 2,5 **và** tỷ trọng ≥ 1,2 × nền **và** ≥ 100 bài (z một mình bắt cả mức tăng vài phần trăm). Khoảng trống: thấp hơn 20% trung vị trượt **hoặc** trung vị cả ngày (bắt được lúc bộ thu thập dừng ở rìa chuỗi). |
> | 16 | Thêm **Experiment 6 – Word2Vec + KMeans**: TF-IDF + KMeans dồn 90–97% bài vào một cụm (silhouette âm) vì bài ngắn → vector TF-IDF gần như trực giao. Word2Vec (vector trung bình 100 chiều) nâng NPMI từ 0,013 lên 0,10–0,15. Từ khóa cụm Word2Vec tính bằng c-TF-IDF. |
> | 16.7 | Mô hình cuối: **Word2Vec + KMeans, k = 15** (NPMI ngang k = 20, silhouette cao hơn, ít chủ đề hơn cho trình chiếu). LDA k = 8 làm mô hình phụ cho Text Analyzer. |
> | 7, 21 | Thêm cờ `is_sensitive` (1,44% bài) và **chế độ trình chiếu**: ẩn nội dung 18+ và che từ chửi thề trên màn hình; số liệu không đổi. |
> | 21 | Dashboard 6 trang theo thế giới "bàn tin trực tiếp": Bảng điểm, Các câu chuyện, Diễn biến, Từ khóa & Hashtag, Phân tích văn bản, Dữ liệu & Phương pháp. |
>
> Hướng dẫn chạy: `README.md`. Số liệu thật: `reports/`, `experiments/experiment_results.csv`.

---

# 1. Định nghĩa bài toán

## 1.1. Bài toán

Từ một tập dữ liệu lớn gồm các bài đăng mạng xã hội, hệ thống thực hiện:

1. Làm sạch và chuẩn hóa dữ liệu bằng Apache Spark.
2. Khám phá các chủ đề chính đang được thảo luận.
3. Theo dõi tỷ trọng từng chủ đề theo thời gian.
4. Phát hiện các thời điểm chủ đề tăng mạnh bất thường.
5. Phân tích hashtag và từ khóa nổi bật.
6. Trực quan hóa kết quả trên dashboard tương tác.
7. Cho phép nhập văn bản mới để xác định chủ đề gần nhất hoặc phân bố chủ đề.

## 1.2. Bối cảnh ứng dụng

Bài toán có thể hỗ trợ:

- Social listening.
- Marketing và truyền thông.
- Theo dõi sự thay đổi nội dung thảo luận theo thời gian.
- Hỗ trợ nhà phân tích dữ liệu nhận biết các chủ đề nổi bật trong một tập dữ liệu mạng xã hội lớn.

> **Lưu ý phạm vi:** Kết quả của hệ thống phản ánh xu hướng **bên trong tập dữ liệu được nghiên cứu**, không được xem là đại diện cho toàn bộ người dùng mạng xã hội hoặc toàn bộ dư luận xã hội.

## 1.3. Đầu vào

Mỗi bài đăng có thể chứa:

- Nội dung văn bản.
- Thời gian đăng.
- Hashtag.
- Lượt thích.
- Lượt chia sẻ/retweet.
- Thông tin người dùng.
- Vị trí nếu có.

## 1.4. Đầu ra

Hệ thống tạo ra:

1. Danh sách các chủ đề.
2. Các từ khóa đặc trưng của từng chủ đề.
3. Các bài đăng tiêu biểu của từng chủ đề.
4. Phân bố chủ đề theo ngày/giờ.
5. Điểm bùng nổ của chủ đề.
6. Top hashtag và từ khóa nổi bật theo thời gian.
7. Dashboard tương tác.
8. Chức năng phân tích văn bản mới.

## 1.5. Phạm vi

### Phạm vi chính

- Dữ liệu tiếng Anh.
- Xử lý theo lô – batch processing.
- HDFS làm Data Lake.
- Apache Spark dùng để xử lý và phân tích.
- MongoDB làm serving layer.
- Streamlit + Plotly làm dashboard.

### Phần mở rộng nếu còn thời gian

- Spark Structured Streaming.
- Phân tích địa lý.
- Mạng đồng xuất hiện hashtag.
- So sánh thêm mô hình khác.

Streaming **không thuộc core scope** để tránh làm dự án quá rộng.

---

# 2. Bộ dữ liệu

## 2.1. Bộ dữ liệu chính

**US Election 2020 Tweets**

Hai file dữ liệu:

- `hashtag_donaldtrump.csv`
- `hashtag_joebiden.csv`

Quy mô khoảng 1,7 triệu tweet.

Khoảng thời gian dữ liệu:

- 15/10/2020 → 08/11/2020.

Dữ liệu có các trường phù hợp với bài toán:

- thời gian đăng,
- nội dung,
- lượt tương tác,
- hashtag,
- vị trí,
- thông tin người dùng.

## 2.2. Bộ dữ liệu dự phòng

1. COVID-19 Tweets.
2. Reddit comments.

## 2.3. Liên hệ với đặc trưng Big Data – 5V

| Thành phần | Ý nghĩa trong đồ án |
|---|---|
| **Volume** | Khoảng hàng triệu bản ghi, dung lượng lớn hơn dữ liệu demo thông thường |
| **Velocity** | Số lượng bài đăng thay đổi mạnh theo giờ/ngày |
| **Variety** | Văn bản, số, thời gian, hashtag, vị trí, metadata |
| **Veracity** | Có dữ liệu trùng, spam, retweet, thiếu và không nhất quán |
| **Value** | Phát hiện chủ đề, xu hướng và thời điểm thảo luận tăng mạnh |

---

# 3. Kiến trúc hệ thống

```text
                  ┌─────────────────────┐
                  │   Social Dataset    │
                  └──────────┬──────────┘
                             │
                          Ingest
                             │
                             ▼
                 ┌──────────────────────┐
                 │ HDFS /raw – Bronze   │
                 └──────────┬───────────┘
                            │
                         Spark ETL
                            │
                            ▼
              ┌──────────────────────────────┐
              │ Data Quality + Preprocessing │
              └──────────────┬───────────────┘
                             │
                             ▼
                 HDFS /clean – Silver
                   Parquet / partition=date
                             │
          ┌──────────────────┴──────────────────┐
          │                                     │
          ▼                                     ▼
   CountVectorizer                       CountVectorizer
          │                               Term Frequency
        TF-IDF                                  │
          │                                     │
      Normalizer                                LDA
          │                                     │
  KMeans / BisectingKMeans              Topic Distribution
          │                                     │
          └──────────────────┬──────────────────┘
                             │
                         Evaluation
                             │
                       Topic Labeling
                             │
                      Trend Aggregation
                             │
                       Burst Detection
                             │
                             ▼
                   MongoDB Serving Layer          Final PipelineModel
                             │                  (HDFS → models/ cục bộ)
                             ▼                            │
                   Streamlit + Plotly  ◄──────────────────┘
                   (Text Analyzer: SparkSession local[1])
```

---

# 4. Lý do chọn công nghệ

## 4.1. HDFS

- Lưu trữ dữ liệu lớn theo cơ chế phân tán.
- Cho phép Spark đọc dữ liệu song song.
- Có replication để tăng khả năng chịu lỗi.
- Phù hợp để minh họa Data Lake trong bài toán Big Data.

## 4.2. Parquet

- Định dạng lưu trữ theo cột.
- Nén dữ liệu tốt.
- Spark đọc hiệu quả.
- Partition theo ngày giúp giảm dữ liệu cần scan khi phân tích theo thời gian.

## 4.3. Apache Spark

Sử dụng:

- Spark DataFrame.
- Spark SQL.
- Spark MLlib.

Các bước chính:

- ETL.
- thống kê.
- vector hóa văn bản.
- phân cụm.
- topic modeling.
- tổng hợp dữ liệu trend.

## 4.4. MongoDB

MongoDB chỉ lưu **dữ liệu đã tổng hợp phục vụ dashboard**, không lưu toàn bộ feature vector.

Các collection chính:

```text
topics
topic_trend_daily
topic_trend_hourly
burst_events
topic_keywords
hashtag_trend_daily
daily_statistics
representative_posts
experiment_results
data_quality
```

## 4.5. Streamlit + Plotly

- Xây dashboard nhanh.
- Hỗ trợ filter tương tác.
- Dễ kết nối MongoDB.
- Phù hợp demo trong buổi thuyết trình.

---

# 5. Môi trường triển khai

Sử dụng Docker Compose trên Windows.

Các container dự kiến:

```text
namenode
datanode-1
datanode-2
spark-master
spark-worker-1
spark-worker-2
mongodb
jupyter-pyspark
```

Phần mềm:

- Apache Spark 3.5.
- Python 3.10+.
- PySpark.
- MongoDB.
- Streamlit.
- Plotly.

## 5.1. Lưu ý vận hành trên Windows

**RAM:** 8 container cần khoảng **10–12 GB RAM**. Cấu hình `.wslconfig` (WSL2) và giới hạn memory từng container:

| Container | Memory gợi ý |
|---|---:|
| namenode | 1 GB |
| datanode ×2 | 0.75 GB mỗi cái |
| spark-master | 0.5 GB |
| spark-worker ×2 | 2.5–3 GB mỗi cái |
| mongodb | 1 GB |
| jupyter-pyspark (driver) | 2 GB |

Nếu máy chỉ có 8 GB RAM: chạy 1 datanode + 1 worker khi phát triển, chỉ bật đủ 2 worker khi làm thí nghiệm scalability.

**Mạng:** NameNode trả về hostname nội bộ của datanode (vd. `datanode-1`) → client chạy **ngoài** mạng Docker (Python trên Windows) thường không đọc/ghi được HDFS.

- Mọi job Spark chạy **bên trong mạng Docker**: từ container `jupyter-pyspark` hoặc `spark-submit` trên `spark-master`.
- Không chạy PySpark trực tiếp trên Windows để đọc HDFS.

**Smoke test bắt buộc cuối tuần 2** (`scripts/smoke_test.py`):

```text
1. Spark ghi 1 DataFrame nhỏ → hdfs:///tmp/smoke
2. Spark đọc lại, đếm số dòng khớp
3. Spark ghi 1 document → MongoDB, đọc lại được
4. Spark UI hiển thị 2 worker ALIVE
```

Chỉ khi smoke test pass mới bắt đầu ETL.

## 5.2. Thông số ghi trong báo cáo

Ghi rõ trong báo cáo:

- CPU máy.
- RAM máy.
- số core cấp cho Spark.
- memory mỗi worker.
- số partition.
- phiên bản thư viện.

---

# 6. Cấu trúc repository

```text
do_an_bigdata/
│
├── config/
│   ├── config.yaml
│   └── stopwords_domain.txt
│
├── docker/
│   ├── docker-compose.yml
│   └── hadoop.env
│
├── data/
│   ├── sample/
│   └── raw/                  # gitignore
│
├── src/
│   ├── ingest/
│   │   └── 01_upload_to_hdfs.py
│   │
│   ├── etl/
│   │   └── 02_clean.py
│   │
│   ├── eda/
│   │   └── 03_statistics.py
│   │
│   ├── features/
│   │   └── 04_feature_engineering.py
│   │
│   ├── model/
│   │   ├── 05_kmeans.py
│   │   ├── 06_lda.py
│   │   └── 07_evaluate.py
│   │
│   ├── trend/
│   │   ├── 08_topic_trend.py
│   │   └── 09_burst_detection.py
│   │
│   └── export/
│       └── 10_export_mongo.py
│
├── dashboard/
│   ├── app.py
│   └── pages/
│
├── experiments/
│   └── experiment_results.csv
│
├── notebooks/
│
├── docs/
│   ├── KE_HOACH_DO_AN_CAI_TIEN.md
│   ├── bao_cao.docx
│   └── slide.pptx
│
├── scripts/
│   ├── run_pipeline.sh
│   └── smoke_test.py
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# 7. Pipeline làm sạch dữ liệu

## 7.0. Đọc dữ liệu CSV

Trường `tweet` chứa ký tự xuống dòng và dấu phẩy → đọc CSV mặc định sẽ làm **vỡ dòng**, sinh bản ghi rác.

```python
df = (spark.read
      .option("header", True)
      .option("multiLine", True)
      .option("escape", '"')
      .option("quote", '"')
      .option("mode", "PERMISSIVE")
      .option("columnNameOfCorruptRecord", "_corrupt")
      .schema(raw_schema)          # khai báo schema tường minh, không dùng inferSchema
      .csv("hdfs:///social/raw/*.csv"))
```

Kiểm tra sau khi đọc:

- Số dòng đọc được ≈ số `tweet_id` hợp lệ.
- `tweet_id`, `created_at` parse được (không null) ở ≥ 99% bản ghi.
- Số bản ghi `_corrupt` → đưa vào Data Quality Report.

## 7.1. Chuẩn hóa schema

- Ép kiểu `created_at` → timestamp.
- Tạo:
  - `date`
  - `hour`
- Chuẩn hóa kiểu dữ liệu số.
- Chuẩn hóa tên cột.

## 7.2. Xử lý trùng lặp

- Gộp dữ liệu từ hai file.
- Loại bản ghi trùng theo `tweet_id` (tweet chứa cả #Trump và #Biden xuất hiện ở cả hai file).
- Phát hiện nội dung trùng thông qua hash của text **sau khi chuẩn hóa** (bỏ URL, mention, whitespace).
- Dataset **không có cột đánh dấu retweet** → dùng heuristic: text bắt đầu bằng `RT @` → gắn cờ `is_retweet_heuristic`. Ghi rõ đây là heuristic trong báo cáo.

Quy tắc giữ/bỏ:

| Trường hợp | Xử lý |
|---|---|
| Trùng `tweet_id` | Giữ 1 bản ghi |
| Trùng text chuẩn hóa (copy-paste, spam) | Giữ 1 bản ghi cho **mô hình**; vẫn đếm đủ cho **thống kê volume** |
| Retweet heuristic | Loại khỏi tập huấn luyện mô hình, giữ trong thống kê volume |

Lý do: nội dung lặp lại hàng nghìn lần làm mô hình “học” thành một chủ đề riêng, nhưng số lần lặp vẫn phản ánh mức độ lan truyền.

## 7.3. Dữ liệu thiếu

- Bỏ bản ghi thiếu text.
- Bỏ bản ghi thiếu thời gian.
- Vị trí thiếu → `"unknown"`.

## 7.4. Dữ liệu ngoại lệ và không nhất quán

Kiểm tra:

- timestamp ngoài khoảng dữ liệu.
- text quá ngắn.
- metadata không hợp lệ.
- tên địa phương không đồng nhất.

## 7.5. Lọc ngôn ngữ

Phạm vi là tiếng Anh nhưng dataset chứa tweet **nhiều ngôn ngữ** và **không có cột ngôn ngữ**.

- Nhận diện ngôn ngữ bằng pandas UDF (`fasttext lid.176` nhanh hơn; hoặc `langdetect` với seed cố định).
- Chạy trên text đã bỏ URL/mention/hashtag để tránh nhận nhầm.
- Giữ `lang = 'en'`; text quá ngắn để nhận diện → gắn `lang = 'unknown'` và loại.
- Thống kê phân bố ngôn ngữ (top 10) → đưa vào EDA và Data Quality Report.

Lưu ý hiệu năng: nhận diện ngôn ngữ trên ~1,7 triệu dòng là bước nặng nhất của ETL → chạy **một lần**, lưu kết quả vào Parquet, không chạy lại trong các thực nghiệm.

## 7.6. Tài khoản hoạt động bất thường

Không khẳng định tài khoản hoạt động nhiều là bot.

Tạo feature:

```text
is_high_activity_account
```

Ví dụ:

- top 0.1% số bài đăng/ngày.

Thực nghiệm:

```text
Dataset đầy đủ
vs
Dataset loại nhóm high-activity
```

So sánh xem topic trend có bị thay đổi đáng kể hay không.

## 7.7. Làm sạch văn bản

- lowercase.
- bỏ URL.
- bỏ `@mention`.
- xử lý HTML entity.
- bỏ ký tự không cần thiết.
- tách hashtag.
- chuẩn hóa whitespace.

Emoji có thể:

- bỏ nếu không sử dụng sentiment;
- hoặc giữ thành feature nếu nhóm thấy có giá trị.

## 7.8. Tokenization

Sử dụng:

- `RegexTokenizer`
- `StopWordsRemover`

Stopwords gồm:

### Stopwords thông thường

Stopwords tiếng Anh.

### Domain stopwords

Ví dụ:

```text
trump
biden
rt
amp
```

Không mặc định xem việc loại domain stopword là tốt hơn.

Phải chạy thực nghiệm:

```text
A – Basic stopwords
B – Basic + domain stopwords
```

và so sánh kết quả.

## 7.9. Bigram

Thực nghiệm:

```text
Unigram
vs
Unigram + Bigram
```

Bigram có thể giúp giữ các cụm từ có ý nghĩa hơn.

## 7.10. Lưu dữ liệu

Dữ liệu clean được lưu:

```text
/social/clean/
```

dưới dạng:

```text
Parquet
partitionBy("date")
```

---

# 8. Data Quality Report

Nhóm bắt buộc lưu số liệu trước và sau từng bước làm sạch.

Ví dụ:

| Rule | Before | Removed / Fixed | After |
|---|---:|---:|---:|
| Raw records | ... | – | ... |
| Corrupt / parse error (CSV) | ... | ... | ... |
| Duplicate tweet ID | ... | ... | ... |
| Missing text | ... | ... | ... |
| Missing timestamp | ... | ... | ... |
| Invalid timestamp | ... | ... | ... |
| Non-English / unknown language | ... | ... | ... |
| **Clean dataset cho thống kê volume** | ... | – | ... |
| Duplicate text (chuẩn hóa) | ... | ... | ... |
| Retweet (heuristic `RT @`) | ... | ... | ... |
| Text quá ngắn (< `min_tokens` sau stopwords) | ... | ... | ... |
| **Clean dataset cho mô hình** | ... | – | ... |

Thứ tự các rule trong bảng = thứ tự thực thi trong code (bước “text quá ngắn” phải đặt **sau** tokenize + stopwords, nếu không số liệu sẽ sai).

Có **hai tập đầu ra**: tập cho thống kê volume/trend và tập cho huấn luyện mô hình (xem 7.2).

Tính thêm:

```text
Data Retention Rate (volume) = clean_volume_rows / raw_rows × 100%
Data Retention Rate (model)  = clean_model_rows  / raw_rows × 100%
```

Đây là minh chứng chính cho phần làm sạch và xử lý dữ liệu.

---

# 9. Thống kê mô tả – EDA

Thực hiện bằng Spark DataFrame / Spark SQL.

Các thống kê:

- Tổng số bài.
- Số bài theo ngày.
- Số bài theo giờ.
- Top hashtag.
- Top từ.
- Phân phối độ dài văn bản.
- Số bài theo người dùng.
- Phân phối hoạt động người dùng.
- Quốc gia/bang nếu dữ liệu vị trí đủ tốt.
- Lượt tương tác trung bình.
- Tỷ lệ dữ liệu thiếu.
- Số duplicate.
- Phân bố ngôn ngữ (top 10).
- Số high-activity accounts.
- Số bài theo giờ trên toàn khoảng thời gian → **phát hiện khoảng trống thu thập (gap)**: giờ/ngày có volume bất thường thấp. Các gap được liệt kê trong báo cáo và loại khỏi burst detection (xem mục 14).

---

# 10. Feature Engineering

Pipeline được tách thành hai nhánh.

## 10.1. Nhánh KMeans

```text
Tokens
↓
CountVectorizer
↓
TF-IDF
↓
L2 Normalizer
↓
KMeans / BisectingKMeans
```

TF-IDF được dùng để giảm ảnh hưởng của các từ xuất hiện quá phổ biến.

## 10.2. Nhánh LDA

```text
Tokens
↓
CountVectorizer
↓
Term Count
↓
LDA
```

**Không dùng TF-IDF làm đầu vào chính của LDA.**

LDA hoạt động trên biểu diễn tần suất từ.

---

# 11. Mô hình và thực nghiệm

## 11.1. TF-IDF

Sử dụng:

- `CountVectorizer`
- `IDF`

Tham số khảo sát:

```text
vocabSize
minDF
unigram / bigram
domain stopwords
```

Ứng dụng:

- vector hóa KMeans.
- tìm keyword đặc trưng.
- keyword trend theo ngày.

---

## 11.2. KMeans / BisectingKMeans

Mục tiêu:

- phân các bài đăng thành các nhóm chủ đề.

Khảo sát:

```text
k ∈ {5, 8, 10, 15, 20}
```

Đánh giá:

- WSSSE / elbow.
- Silhouette score (`ClusteringEvaluator`, distanceMeasure `cosine`).
- NPMI coherence (mục 11.4).
- khả năng diễn giải cluster (mục 11.6).
- runtime.

**Top terms của cluster** (cần để tính coherence và gán nhãn): lấy 10 term có **trọng số lớn nhất trong vector centroid** (centroid nằm trong không gian TF-IDF đã chuẩn hóa L2, nên trọng số cao = term đặc trưng của cụm). Ánh xạ index → term qua `CountVectorizerModel.vocabulary`.

Nhãn chủ đề chỉ gán cho **mô hình cuối** (mục 16.7), dựa trên:

- top terms.
- bài đăng gần centroid.
- nội dung representative posts.

---

## 11.3. LDA

LDA sử dụng term count từ `CountVectorizer`.

Khảo sát:

```text
k ∈ {5, 8, 10, 15, 20}
```

Đánh giá:

- log-perplexity trên tập **held-out 10%** (không dùng tập huấn luyện).
- NPMI coherence (mục 11.4).
- khả năng diễn giải topic (mục 11.6).

Top terms của topic: `LDAModel.describeTopics(10)`.

---

## 11.4. Topic coherence – NPMI (độ đo chung)

Spark MLlib **không có sẵn** coherence → nhóm tự cài đặt bằng Spark:

```text
1. Với mỗi topic/cluster: lấy top-10 term → 45 cặp (wi, wj).
2. Trên tập văn bản tham chiếu, đếm bằng Spark:
   D(wi), D(wj), D(wi, wj) = số văn bản chứa term / cặp term.
3. NPMI(wi, wj) = log[P(wi,wj) / (P(wi)·P(wj))] / (−log P(wi,wj))
   (cộng ε nhỏ để tránh log 0).
4. Coherence(topic) = trung bình NPMI của 45 cặp.
5. Coherence(model)  = trung bình coherence các topic.
```

Giá trị NPMI ∈ [−1, 1], càng cao topic càng nhất quán. Chi phí thấp: chỉ cần đếm vài trăm cặp term.

## 11.5. Quy tắc so sánh độ đo

Các độ đo **không so sánh được với nhau trong mọi trường hợp**:

| Độ đo | So sánh hợp lệ | Không so sánh |
|---|---|---|
| Silhouette | Các giá trị k **trong cùng một không gian đặc trưng** | Giữa có/không domain stopwords, uni/bigram (vector khác nhau) |
| WSSSE | Các giá trị k trong cùng cấu hình (elbow) | Giữa các cấu hình khác nhau |
| Log-perplexity | Các giá trị k của LDA **cùng vocabulary**, trên tập held-out | Giữa các vocabulary khác nhau; giữa LDA và KMeans |
| **NPMI coherence** | **Mọi cấu hình, mọi thuật toán** – nếu cùng tập tham chiếu, cùng tokenization tham chiếu, cùng top-10 | – |
| Interpretability (người chấm) | Mọi cấu hình, mọi thuật toán | – |

→ **NPMI + Interpretability** là hai độ đo chính cho Experiment 1, 2, 4.
→ Silhouette / WSSSE / perplexity chỉ dùng để chọn k bên trong một cấu hình.

**Tập tham chiếu cố định:** tập clean-model với tokenization cơ bản (lowercase + basic stopwords, **unigram**, không domain stopwords). Với cấu hình bigram, tách bigram thành 2 unigram khi tính NPMI hoặc bỏ qua cặp chứa bigram – ghi rõ lựa chọn trong báo cáo.

## 11.6. Đánh giá thủ công – Interpretability

Hai thành viên **chấm độc lập** từng topic của mỗi cấu hình ứng viên:

| Điểm | Ý nghĩa |
|---:|---|
| 3 | Đặt được nhãn rõ ràng, top terms và representative posts nhất quán |
| 2 | Đặt được nhãn nhưng có lẫn term/bài không liên quan |
| 1 | Không đặt được nhãn / trộn nhiều chủ đề |

- Interpretability = trung bình điểm các topic.
- Đo độ đồng thuận giữa 2 người (tỷ lệ trùng điểm hoặc Cohen’s kappa); topic bất đồng → thảo luận, ghi lại lý do.
- Chấm “mù”: che tên cấu hình khi chấm để tránh thiên vị.

Đây vừa là đánh giá định tính cho CLO3, vừa là minh chứng phối hợp nhóm cho CLO5.

---

# 12. Phân tích văn bản mới

## 12.1. Nếu sử dụng KMeans

Không gọi kết quả là probability.

Hiển thị:

```text
Predicted Topic: Economy
Similarity / Distance Score: ...
```

Có thể dùng:

- khoảng cách tới centroid.
- hoặc chuyển đổi thành similarity score có mô tả rõ cách tính.

## 12.2. Nếu sử dụng LDA

Hiển thị:

```text
Topic 1: 63%
Topic 4: 21%
Topic 7: 9%
...
```

Đây là phân bố chủ đề của văn bản.

## 12.3. Dashboard đề xuất

Cho văn bản mới, hiển thị đồng thời:

```text
KMeans:
Nearest Topic

LDA:
Topic Distribution
```

Qua đó minh họa sự khác nhau giữa:

- hard clustering.
- soft topic assignment.

## 12.4. Triển khai inference trong dashboard

Nạp `PipelineModel` của Spark **bắt buộc có SparkSession** → mâu thuẫn với nguyên tắc “dashboard chỉ đọc MongoDB, không phụ thuộc cluster”.

Giải pháp:

```text
1. Sau khi chốt mô hình cuối: copy PipelineModel (preprocess + KMeans, preprocess + LDA)
   từ HDFS → thư mục models/ cục bộ của container dashboard (hdfs dfs -get).
2. Dashboard tạo SparkSession ở chế độ local[1], driver memory ~1 GB.
3. Nạp model MỘT lần bằng @st.cache_resource → các lần phân tích sau chỉ mất < 1–2 giây.
4. Mỗi lần người dùng nhập văn bản: tạo DataFrame 1 dòng → model.transform() → hiển thị.
```

- Dashboard **không cần HDFS/Spark cluster** khi demo: chỉ cần MongoDB + thư mục `models/`.
- Tiền xử lý văn bản mới dùng **đúng** pipeline đã huấn luyện (cùng tokenizer, stopwords, vocabulary) → không lệch giữa train và inference.
- Ghi rõ lựa chọn này trong phần kiến trúc của báo cáo (mục 3.13–3.14).

---

# 13. Topic Trend

## 13.1. Mô hình dùng cho trend

Trend, burst và dashboard chỉ dùng **một mô hình chính** – là mô hình cuối được chọn ở mục 16.7. Mô hình còn lại chỉ xuất hiện ở trang so sánh và Text Analyzer.

Cách tính tỷ trọng topic phụ thuộc loại mô hình:

| Mô hình chính | `topic_count(topic, t)` | `topic_ratio(topic, t)` |
|---|---|---|
| KMeans / BisectingKMeans (hard) | Số bài được gán vào cluster | `topic_count / total_posts(t)` |
| LDA (soft) | **Tổng xác suất** topic của các bài: `Σ θ_d[topic]` | **Trung bình** `θ_d[topic]` của các bài trong t |

Với LDA **không dùng argmax** (gán mỗi bài 1 topic có xác suất cao nhất): tweet ngắn thường có phân bố khá phẳng, argmax làm mất thông tin và khuếch đại nhiễu.

Nên dùng `topic_ratio` để tránh khoảng thời gian có tổng số tweet quá lớn làm sai lệch việc so sánh.

## 13.2. Độ phân giải thời gian

Dataset chỉ khoảng **25 ngày** → theo ngày chỉ có ~25 điểm, quá ít cho thống kê rolling.

| Mục đích | Độ phân giải |
|---|---|
| Biểu đồ tổng quan trên dashboard | Ngày (dễ đọc) |
| Burst detection | **Giờ** (~600 điểm) |
| Drill-down trên dashboard | Giờ, lọc theo khoảng ngày |

Tổng hợp theo giờ bằng Spark: `groupBy(topic, date_trunc('hour', created_at))`. Lưu cả hai collection `topic_trend_daily` và `topic_trend_hourly`.

Tweet có tính chu kỳ ngày–đêm → so sánh giờ hiện tại với **24–72 giờ trước** (không so với vài giờ liền trước) để tránh “bùng nổ giả” mỗi sáng.

---

# 14. Burst Detection

Không chỉ kiểm tra mức tăng phần trăm.

Tính trên chuỗi `topic_ratio` theo giờ:

```text
rolling_mean_previous(t) = mean(topic_ratio[t-W .. t-1])
rolling_std_previous(t)  = std (topic_ratio[t-W .. t-1])
```

Cửa sổ **chỉ gồm các giờ trước t** (không chứa t) để điểm hiện tại không tự kéo trung bình lên.

Burst score:

```text
burst_score(t)
=
(topic_ratio(t) - rolling_mean_previous(t))
/
max(rolling_std_previous(t), std_floor)
```

`std_floor` (ε) tránh chia cho 0 / điểm số khổng lồ khi một topic gần như không đổi trong cửa sổ. Gợi ý: `std_floor = 0.1 × std toàn chuỗi của topic đó`.

Một topic được xem là bùng nổ khi:

```text
burst_score > threshold
AND
topic_count(t) >= min_volume
AND
cửa sổ [t-W, t] không chứa giờ thuộc gap dữ liệu
AND
cửa sổ có đủ >= min_periods giờ hợp lệ
```

Xử lý đầu chuỗi và khoảng trống:

- `W` giờ đầu tiên của dataset (chưa đủ lịch sử) → không tính burst, ghi `null`.
- Giờ nằm trong **gap thu thập** (phát hiện ở EDA) → loại khỏi chuỗi; burst ngay sau gap cần kiểm tra thủ công vì có thể là hiệu ứng thu thập, không phải hành vi người dùng.
- Các giờ liên tiếp cùng vượt ngưỡng của một topic → gộp thành **1 sự kiện bùng nổ** (thời điểm bắt đầu, đỉnh, kết thúc, burst score cực đại).

Ví dụ cấu hình:

```yaml
trend:
  burst_granularity: hour
  rolling_window_hours: 48
  min_periods: 24
  burst_zscore_threshold: 2.5
  std_floor_ratio: 0.1
  burst_min_volume: 200      # theo giờ
  merge_gap_hours: 2
```

`burst_min_volume` và `burst_zscore_threshold` phải được điều chỉnh theo dataset thực tế; báo cáo nêu số sự kiện bùng nổ phát hiện được ở 2–3 mức ngưỡng để thấy độ nhạy.

---

# 15. Đối chiếu với các mốc sự kiện trong dataset

Các thời điểm trend tăng mạnh được đối chiếu với những mốc sự kiện đã biết trong phạm vi dữ liệu nghiên cứu.

Mục đích:

- kiểm tra khả năng giải thích của topic.
- kiểm tra burst detection.
- không sử dụng sự kiện để gán nhãn trước cho mô hình.

---

# 16. Thực nghiệm cải tiến

Thiết kế theo kiểu:

```text
Baseline
↓
Đánh giá
↓
Xác định vấn đề
↓
Improvement
↓
Đánh giá lại
```

## 16.1. Chiến lược chạy – tránh bùng nổ tổ hợp

Nếu chạy đủ tổ hợp: 5 giá trị k × 3 thuật toán × 2 stopwords × 2 n-gram = **60 lần chạy**; LDA trên toàn bộ ~1,7 triệu tweet có thể mất hàng chục phút mỗi lần trên laptop → không khả thi.

Nguyên tắc:

1. **Dò tham số trên mẫu cố định** 10–20% tập clean-model (`sample(fraction, seed=42)`, lưu thành Parquet riêng `/social/sample_20`) → mọi experiment dùng cùng một mẫu.
2. **Thay đổi một yếu tố mỗi lần** (one-factor-at-a-time): giữ các yếu tố khác ở giá trị tốt nhất hiện tại.
3. **Chỉ chạy toàn bộ dữ liệu** cho: cấu hình cuối (để tạo trend/dashboard) và thí nghiệm scalability.
4. Giới hạn LDA khi dò: `maxIter` 20–30, `vocabSize` ≤ 10.000; tăng lại cho lần chạy cuối.

Thứ tự thực hiện (ước tính ~20–25 lần chạy trên mẫu):

```text
Bước 1  Baseline: basic stopwords, unigram, k=10 → KMeans + LDA          (2 lần)
Bước 2  Experiment 1 – Domain stopwords, k=10 → KMeans + LDA             (2 lần)
Bước 3  Experiment 3 – k ∈ {5, 8, 10, 15, 20} với cấu hình tốt nhất       (~10 lần)
Bước 4  Experiment 4 – BisectingKMeans tại k tốt nhất                      (1–2 lần)
Bước 5  Experiment 2 – Bigram với cấu hình tốt nhất                        (2 lần)   [ưu tiên 2]
Bước 6  Experiment 5 – High-activity trên cấu hình cuối                    (2 lần)   [ưu tiên 2]
```

| Ưu tiên | Experiment | Ghi chú |
|---|---|---|
| **Bắt buộc** | 1 – Domain stopwords, 3 – Số topic, 4 – Thuật toán | Đủ điều kiện “ít nhất 3 experiment” (mục 31) |
| Nếu còn thời gian | 2 – N-gram, 5 – High-activity | Làm trong tuần 7 nếu bước 1–4 xong trước giữa tuần |

## 16.2. Experiment 1 – Domain Stopwords

```text
Basic stopwords
vs
Basic + Domain stopwords
```

Đo (theo quy tắc mục 11.5 – hai cấu hình có vector khác nhau nên **không so silhouette/perplexity**):

- **NPMI coherence** (chung một tập tham chiếu).
- **Interpretability** (2 người chấm).
- Top words của từng topic đặt cạnh nhau.
- Tỷ lệ topic bị chi phối bởi từ khóa truy vấn (vd. topic có `trump`/`biden` trong top-3).

## 16.3. Experiment 2 – N-gram

```text
Unigram
vs
Unigram + Bigram
```

Đo: NPMI (xử lý bigram theo mục 11.5), interpretability, kích thước vocabulary, runtime.

Lưu ý cài đặt: `NGram(n=2)` sinh rất nhiều bigram → bắt buộc `minDF` đủ lớn (vd. ≥ 20) cho bigram; ghép unigram + bigram bằng `concat` hai cột mảng trước `CountVectorizer`.

## 16.4. Experiment 3 – Number of Topics

```text
k = 5, 8, 10, 15, 20
```

Trong **cùng một cấu hình** đặc trưng:

- KMeans: WSSSE (elbow) + silhouette + NPMI.
- LDA: log-perplexity trên tập held-out 10% + NPMI.
- Chọn k ở vùng NPMI/interpretability cao, không chỉ theo một độ đo.

## 16.5. Experiment 4 – Algorithm

```text
KMeans
vs
BisectingKMeans
vs
LDA
```

Tại k tốt nhất của từng thuật toán. So bằng: **NPMI, interpretability, runtime, độ cân bằng kích thước topic** (topic nào chiếm > 40% dữ liệu là dấu hiệu gom rác). Silhouette chỉ so giữa KMeans và BisectingKMeans (cùng không gian TF-IDF).

## 16.6. Experiment 5 – High Activity Accounts

```text
Full dataset
vs
filtered high-activity accounts
```

Chạy trên cấu hình cuối, so sánh:

- Tương quan chuỗi `topic_ratio` theo ngày giữa hai phiên bản (Pearson).
- Số sự kiện bùng nổ bị mất / xuất hiện thêm.
- Topic nào thay đổi tỷ trọng nhiều nhất.

## 16.7. Chọn mô hình cuối (cuối tuần 7)

Mô hình cuối được chọn theo thứ tự ưu tiên:

1. **Interpretability** trung bình cao nhất (topic đặt được nhãn rõ ràng).
2. **NPMI coherence** cao nhất (chênh lệch < 0.02 xem như ngang nhau).
3. Không có topic “rác” chiếm > 40% dữ liệu.
4. Runtime chấp nhận được khi chạy toàn bộ dữ liệu.

Sau khi chọn:

- Chạy lại mô hình cuối trên **toàn bộ** tập clean-model; áp dụng lên tập clean-volume để tính trend.
- Gán nhãn chủ đề (2 thành viên thống nhất), lưu vào `config/topic_labels.yaml`.
- Ghi rõ lý do chọn trong báo cáo (bảng tổng hợp từ experiment registry).

---

# 17. Experiment Registry

Mọi lần chạy mô hình được ghi lại trong:

```text
experiments/experiment_results.csv
```

Ví dụ:

| ID | Exp | Data | Model | k | Vocab | Ngram | Domain SW | Silhouette | Perplexity | NPMI | Interp. | Runtime (s) |
|---|---|---|---|---:|---:|---|---|---:|---:|---:|---:|---:|
| E01 | Baseline | sample_20 | KMeans | 10 | 20000 | Uni | No | ... | – | ... | ... | ... |
| E02 | Baseline | sample_20 | LDA | 10 | 10000 | Uni | No | – | ... | ... | ... | ... |
| E03 | Exp1 | sample_20 | KMeans | 10 | 20000 | Uni | Yes | ... | – | ... | ... | ... |
| E04 | Exp1 | sample_20 | LDA | 10 | 10000 | Uni | Yes | – | ... | ... | ... | ... |

Cột bổ sung trong file CSV: `seed`, `min_df`, `max_iter`, `n_workers`, `git_commit`, `run_at`, `note`.

Cột `Silhouette` và `Perplexity` chỉ đọc theo quy tắc mục 11.5; cột **NPMI** và **Interp.** dùng để so sánh chéo.

Mục đích:

- tránh mất kết quả.
- chọn model cuối có căn cứ.
- dùng trực tiếp cho bảng thực nghiệm trong báo cáo.

---

# 18. Reproducibility

Các bước ngẫu nhiên cần sử dụng seed cố định khi có thể.

Ví dụ:

```text
seed = 42
```

Áp dụng cho:

- sampling.
- KMeans.
- LDA.
- train/test nếu có.

Lưu:

- config.
- phiên bản thư viện.
- model.
- metric.
- runtime.
- timestamp chạy.
- git commit hash của code tại thời điểm chạy.

---

# 19. Thí nghiệm khả năng mở rộng – Scalability

## 19.1. Theo kích thước dữ liệu

Chạy:

```text
10%
50%
100%
```

Đo:

- runtime.
- số stage.
- số task.
- shuffle read.
- shuffle write.
- memory.
- CPU nếu thu thập được.

Ghi chú: thí nghiệm này là **ngoại lệ** duy nhất (cùng cấu hình cuối) được chạy trên toàn bộ dữ liệu ngoài lần chạy mô hình cuối. Mỗi cấu hình chạy **3 lần**, báo cáo trung bình ± độ lệch; bỏ lần chạy đầu nếu bị ảnh hưởng bởi cache/khởi động JVM. Chỉ số lấy từ Spark UI / REST API (`/api/v1/applications`).

## 19.2. Theo số worker

So sánh:

```text
Configuration A:
1 Spark Worker

Configuration B:
2 Spark Workers
```

## 19.3. Lưu ý khi viết báo cáo

Nếu toàn bộ worker chạy trên cùng một laptop, phải ghi rõ:

> Đây là thí nghiệm logical cluster trên cùng một máy vật lý nhằm quan sát cơ chế phân chia job/task của Spark. Kết quả không đại diện cho benchmark của cluster nhiều máy vật lý độc lập.

Không kết luận:

> 2 worker luôn nhanh gấp đôi.

---

# 20. MongoDB Serving Layer

MongoDB chỉ chứa kết quả phục vụ dashboard.

Ví dụ collection:

Số liệu trong ví dụ chỉ để minh họa định dạng.

## `topic_trend_daily`

```json
{
  "topic_id": 3,
  "topic_label": "Voting process",
  "date": "2020-11-03",
  "count": 42310,
  "ratio": 0.27
}
```

## `topic_trend_hourly`

```json
{
  "topic_id": 3,
  "hour": "2020-11-03T21:00:00Z",
  "count": 5120,
  "ratio": 0.31,
  "burst_score": 3.4,
  "is_burst": true,
  "in_gap": false
}
```

Index: `{topic_id: 1, hour: 1}` để lọc nhanh theo topic và khoảng thời gian.

## `burst_events`

```json
{
  "topic_id": 3,
  "start": "2020-11-03T20:00:00Z",
  "peak": "2020-11-03T23:00:00Z",
  "end": "2020-11-04T03:00:00Z",
  "max_burst_score": 4.1
}
```

## `topics`

```json
{
  "topic_id": 3,
  "topic_label": "Voting process",
  "keywords": [
    "vote",
    "ballot",
    "poll",
    "election"
  ]
}
```

## `representative_posts`

Lưu một lượng mẫu nhỏ để dashboard hiển thị (vd. 10–20 bài gần centroid / có θ cao nhất mỗi topic).

## `data_quality`, `experiment_results`

Bảng Data Quality Report (mục 8) và experiment registry (mục 17) → dashboard hiển thị trực tiếp, không cần chép tay vào slide.

---

# 21. Dashboard

Dashboard core gồm **5 trang bắt buộc**, xây theo 2 phiên bản:

| Phiên bản | Thời điểm | Nội dung | Mục đích |
|---|---|---|---|
| **v0 – tối thiểu** | Hết tuần 6 (nộp GĐ1) | Page 1 Overview + Page 2 Topic (baseline) + Page 3 Trend thô theo ngày; dữ liệu đọc từ MongoDB | GĐ1 cũng chấm tiêu chí Trực quan hóa (2.5đ) → không để trống |
| **v1 – hoàn chỉnh** | Hết tuần 8 | Đủ 5 trang, burst marker, filter, Text Analyzer, insight | Nộp GĐ2 + demo |

## Page 1 – Overview

KPI:

- Tổng bài đăng.
- Tổng số ngày.
- Số hashtag.
- Số topic.
- Tỷ lệ dữ liệu sau làm sạch.

Biểu đồ:

- posts/day.
- posts/hour.
- top hashtags.

Mỗi biểu đồ phải có ít nhất một insight.

---

## Page 2 – Topic Analysis

Hiển thị:

- topic cards.
- topic label.
- top keywords.
- representative posts.
- topic size.
- word cloud nếu cần.

---

## Page 3 – Topic Trends

Hiển thị:

- stacked area chart.
- line chart từng topic.
- topic ratio.
- burst marker (từ `burst_events`).
- chuyển độ phân giải ngày ↔ giờ.
- filter:
  - date range.
  - topic.

---

## Page 4 – Keyword & Hashtag Trends

Hiển thị:

- top hashtag theo ngày.
- keyword TF-IDF nổi bật.
- hashtag trend.
- so sánh nhiều ngày.

---

## Page 5 – Text Analyzer

Người dùng nhập một câu.

Hiển thị:

```text
KMeans Topic
LDA Topic Distribution
Important Terms
```

Cách triển khai: mục 12.4 (SparkSession `local[1]` + model cục bộ, nạp bằng `st.cache_resource`).

---

# 22. Dashboard – Bonus

Nếu còn thời gian:

## Page 6 – Geographic Analysis

Chỉ làm nếu dữ liệu địa lý đủ sạch.

Có thể sử dụng:

- country.
- state.
- choropleth.

## Bonus khác

- hashtag co-occurrence network.
- structured streaming.
- realtime refresh.

---

# 23. Insight Requirement

Không chỉ đặt biểu đồ.

Mỗi biểu đồ phải có phần:

```text
Insight:
...
```

Ví dụ dạng diễn đạt:

> Topic X tăng mạnh trong khoảng ngày Y–Z, đồng thời burst score vượt ngưỡng đã thiết lập.

Insight phải dựa trên dữ liệu thực tế thu được từ pipeline.

---

# 24. Configuration

Các tham số chính được đưa vào:

```text
config/config.yaml
```

Ví dụ:

```yaml
spark:
  shuffle_partitions: 32

data:
  sample_fraction: 0.2        # dùng cho experiment
  seed: 42

preprocessing:
  language: en
  min_tokens: 3
  drop_retweets_for_model: true
  use_bigram: false
  bigram_min_df: 20
  use_domain_stopwords: true

features:
  vocab_size: 20000
  min_df: 5

kmeans:
  k: 10
  seed: 42

lda:
  k: 10
  max_iter: 30
  optimizer: online
  seed: 42

evaluation:
  coherence_top_n: 10
  heldout_fraction: 0.1

trend:
  primary_model: kmeans       # chốt ở mục 16.7
  burst_granularity: hour
  rolling_window_hours: 48
  min_periods: 24
  burst_zscore_threshold: 2.5
  std_floor_ratio: 0.1
  burst_min_volume: 200
  merge_gap_hours: 2
```

Thông số thực tế sẽ được điều chỉnh thông qua experiment.

---

# 25. Bám rubric

> **Quan trọng:** theo tài liệu học phần, “Cả 2 giai đoạn đều được chấm theo cùng Rubric” → **Giai đoạn 1 cũng chấm đủ 6 tiêu chí**, kể cả Trực quan hóa. Mỗi tiêu chí phải có sản phẩm tương ứng ngay từ GĐ1.

| Tiêu chí | Điểm | Sản phẩm tại GĐ1 (hết tuần 6) | Sản phẩm tại GĐ2 (tuần 9) |
|---|---:|---|---|
| CLO1 – Tính ứng dụng | 1.0 | Chương 1 hoàn chỉnh: bài toán, dữ liệu, 5V, phạm vi, bias | Bổ sung giá trị thực tế qua insight từ dashboard |
| CLO2 – Lưu trữ & xử lý | 2.0 | Cluster chạy, raw/clean trên HDFS, Data Quality Report, EDA | Scalability, MongoDB đầy đủ collection |
| CLO3 – Mô hình | 2.5 | Baseline KMeans + LDA có số liệu (NPMI, silhouette, perplexity), Exp1, vấn đề cần cải tiến | Exp 1/3/4 (+2/5), mô hình cuối, trend + burst |
| CLO3 – Trực quan hóa | 2.5 | **Dashboard v0** (3 trang) đọc MongoDB | Dashboard v1 đủ 5 trang + Text Analyzer |
| CLO4 – Báo cáo | 1.0 | Báo cáo tiến độ **theo đúng cấu trúc** báo cáo quy định (các chương chưa xong ghi rõ “đang thực hiện”) | Báo cáo + slide hoàn chỉnh |
| CLO5 – Nhóm | 1.0 | Biên bản họp tuần 1–6, bảng phân công, commit cả 2 người | Cập nhật đến tuần 9, % đóng góp |

## CLO1 – Tính ứng dụng kỹ thuật – 1.0 điểm

Phải có:

- bài toán thực tế.
- người dùng mục tiêu.
- đầu vào.
- đầu ra.
- giá trị.
- phạm vi.
- Big Data 5V.
- hạn chế và bias.

Minh chứng:

- Chương 1 báo cáo.
- slide mở đầu.
- dashboard.

---

## CLO2 – Lưu trữ và xử lý/phân tích dữ liệu – 2.0 điểm

Phải có:

- HDFS cluster chạy thật.
- Spark xử lý thật.
- raw/clean architecture.
- Parquet.
- partition.
- xử lý missing.
- duplicate.
- outlier.
- inconsistency.
- Data Quality Report.
- EDA.
- MongoDB serving layer.

Minh chứng:

- Hadoop NameNode UI.
- Spark UI.
- Docker containers.
- Data Quality table.
- architecture diagram.
- screenshots.

---

## CLO3 – Mô hình/công nghệ xử lý – 2.5 điểm

Phải có:

- TF-IDF.
- KMeans.
- BisectingKMeans hoặc phương án so sánh.
- LDA.
- Silhouette (chọn k trong cùng cấu hình).
- Perplexity (held-out, cùng vocabulary).
- **NPMI coherence** tự cài đặt bằng Spark – độ đo so sánh chéo.
- **Interpretability** do 2 người chấm độc lập.
- quy tắc so sánh độ đo (mục 11.5).
- parameter tuning trên mẫu cố định (mục 16.1).
- lý do chọn mô hình cuối (mục 16.7).
- experiment comparison.
- scalability experiment.
- limitations.

---

## CLO3 – Trực quan hóa/xây dựng ứng dụng – 2.5 điểm

Core dashboard:

1. Overview.
2. Topic Analysis.
3. Topic Trends.
4. Keyword & Hashtag.
5. Text Analyzer.

Yêu cầu:

- dashboard v0 tại GĐ1, v1 tại GĐ2.
- filter tương tác.
- insight.
- dữ liệu từ MongoDB.
- Text Analyzer chạy không cần cluster (mục 12.4).
- demo ổn định + video dự phòng.

---

## CLO4 – Trình bày báo cáo – 1.0 điểm

- Đúng cấu trúc yêu cầu.
- hình/bảng đánh số.
- nguồn trích dẫn rõ.
- không lỗi chính tả.
- slide ngắn gọn.
- tổng dượt trước khi trình bày.

---

## CLO5 – Phân công và phối hợp nhóm – 1.0 điểm

- GitHub.
- branch `feature/*`.
- pull request.
- review chéo.
- biên bản họp (`docs/bien_ban/tuan_XX.md`: ngày, người dự, việc đã làm, việc tuần sau, vướng mắc).
- commit của cả hai thành viên.
- chấm interpretability độc lập + đo đồng thuận (mục 11.6).
- cả hai phải hiểu toàn bộ pipeline.

---

# 26. Phân công vai trò

| Thành viên | Vai trò chính | Công việc |
|---|---|---|
| **SV A – Data Engineer** | Hạ tầng & dữ liệu | Docker, HDFS, ETL, Data Quality, EDA, MongoDB, benchmark |
| **SV B – Data Scientist** | Mô hình & dashboard | TF-IDF, KMeans, LDA, evaluation, trend, burst, dashboard |
| **Cả hai** | Hoàn thiện sản phẩm | chọn data, review code, topic labeling, report, slide, rehearsal |

Nguyên tắc:

- Không tách rời hoàn toàn.
- Mỗi tuần review code chéo.
- Mỗi người phải giải thích được toàn bộ pipeline.

---

# 27. Tiến độ 10 tuần

Mốc chính thức theo tài liệu học phần (cột **Mốc**). Tài liệu ghi GĐ1 là “Tuần 5,6” ở phần mô tả nhưng “Tuần 6–7” ở bảng kế hoạch → nhóm **nhắm hết tuần 6** và xác nhận lại ngày chính xác với giảng viên ngay tuần 1.

| Tuần | Mốc | Công việc | Definition of Done | A | B |
|---|---|---|---|---|---|
| **1** | Đăng ký đề tài | Chốt scope, tải + backup dataset (chính & dự phòng), repo, phân vai | Dataset đọc được; schema mô tả; repo có cấu trúc; lịch họp cố định | Dataset + Git + biên bản | Khảo sát topic modeling, đọc cột dữ liệu |
| **2** | | Docker + HDFS + Spark + MongoDB; raw lên HDFS | **Smoke test pass** (mục 5.1); đọc CSV `multiLine` đúng số dòng | Infrastructure | EDA sơ bộ trên mẫu; khảo sát ngôn ngữ |
| **3** | **Nộp kế hoạch nhóm** | ETL + lọc ngôn ngữ + Data Quality | 2 tập Parquet clean-volume / clean-model; bảng DQ; `sample_20` | ETL + DQ | Stopwords, tokenize, danh sách domain stopwords |
| **4** | **Tóm tắt lý thuyết + ví dụ minh họa** | EDA đầy đủ (gồm gap); lý thuyết | Báo cáo EDA; tài liệu lý thuyết có ví dụ tính tay nhỏ (TF-IDF 3 câu, KMeans 2D, NPMI 1 cặp từ) | EDA + lý thuyết HDFS/Spark/Mongo | Lý thuyết TF-IDF/KMeans/LDA/NPMI; cài đặt NPMI |
| **5** | | Baseline + export MongoDB v0 | KMeans + LDA chạy trên `sample_20`, có NPMI/silhouette/perplexity trong registry; MongoDB có `topics`, `topic_trend_daily`, `daily_statistics`, `data_quality` | Feature pipeline + export Mongo | Baseline + evaluation |
| **6** | **Nộp GĐ1** | Exp1; chấm interpretability lần 1; dashboard v0; báo cáo tiến độ | Bảng baseline vs Exp1; dashboard v0 3 trang; báo cáo tiến độ đúng cấu trúc | Dashboard v0 (Overview) + phần dữ liệu/kiến trúc | Dashboard v0 (Topic, Trend) + phần mô hình |
| **7** | | Exp3, Exp4 (+2/5 nếu kịp); chọn mô hình cuối; trend theo giờ + burst | Mô hình cuối chạy full data; nhãn topic chốt; `topic_trend_hourly`, `burst_events` trên MongoDB | Tổng hợp theo giờ, burst detection, export Mongo | Experiments, chọn mô hình, gán nhãn |
| **8** | | Scalability; dashboard v1; báo cáo nháp | 5 trang chạy ổn định; Text Analyzer chạy không cần cluster; bảng scalability | Scalability + trang Overview/Keyword + đóng gói model | Trang Topic/Trend/Analyzer + insight |
| **9** | **Nộp GĐ2** (Classroom: Source, Word, PPT) | Hoàn thiện tài liệu | Word + PPT + README; **chạy lại toàn bộ từ đầu theo README** thành công; video demo dự phòng | README + kiểm thử end-to-end | Slide + định dạng báo cáo |
| **10** | **Thuyết trình** | Tổng dượt 2 lần; phản biện | Demo hoàn chỉnh, đúng giờ | Kiến trúc & xử lý | Mô hình & demo |

Mỗi người luân phiên demo phần của người kia trong buổi tổng dượt để chắc chắn cả hai trả lời được mọi câu hỏi.

---

# 28. Cấu trúc báo cáo Word

## 1. Trang bìa

## 2. Lịch làm việc nhóm hàng tuần

- lịch thực tế.
- ngày họp.
- nội dung.
- người tham dự.

## 3. Công việc của mỗi thành viên

- vai trò.
- công việc.
- % đóng góp.

## 4. Mục lục

## 5. Chương 1 – Giới thiệu đề tài

- bối cảnh.
- bài toán.
- mục tiêu.
- phạm vi.
- đầu vào.
- đầu ra.
- giá trị.
- dataset.
- 5V.
- bias và giới hạn phạm vi.

## 6. Chương 2 – Cơ sở lý thuyết

- Big Data.
- HDFS.
- Spark.
- DataFrame.
- Spark MLlib.
- MongoDB.
- NLP preprocessing.
- CountVectorizer.
- TF-IDF.
- KMeans.
- BisectingKMeans.
- LDA.
- Silhouette.
- Perplexity.
- Coherence.
- Trend analysis.
- Z-score / burst detection.

## 7. Chương 3 – Xây dựng ứng dụng và trực quan hóa

### 3.1. Kiến trúc

### 3.2. Môi trường triển khai

### 3.3. Dữ liệu

### 3.4. Data Quality

### 3.5. ETL

### 3.6. EDA

### 3.7. Feature Engineering

### 3.8. Baseline

### 3.9. Improvement Experiments

### 3.10. Model Comparison

### 3.11. Scalability Experiment

### 3.12. Trend & Burst Detection

### 3.13. MongoDB

### 3.14. Dashboard

## 8. Chương 4 – Kết luận và định hướng

- kết quả đạt được.
- giới hạn.
- dataset bias.
- short-text limitation.
- logical cluster limitation.
- hướng phát triển:
  - Spark Structured Streaming.
  - dữ liệu tiếng Việt.
  - sentiment theo topic.
  - BERTopic.
  - cluster nhiều máy vật lý.

## 9. Tài liệu tham khảo

## 10. Phụ lục

- hướng dẫn cài đặt.
- hướng dẫn chạy.
- source chính.
- config.
- screenshots.

---

# 29. Rủi ro và phương án

| Rủi ro | Phương án |
|---|---|
| GĐ1 bị chấm thấp tiêu chí Trực quan hóa | Dashboard v0 bắt buộc hết tuần 6 |
| CSV vỡ dòng do text nhiều dòng | `multiLine` + `escape`, đối chiếu số dòng với số `tweet_id` |
| Tweet không phải tiếng Anh lọt vào mô hình | Bước lọc ngôn ngữ (mục 7.5) + thống kê phân bố ngôn ngữ |
| Client ngoài Docker không truy cập được datanode | Chạy mọi job trong mạng Docker; smoke test tuần 2 |
| Laptop thiếu RAM | Giới hạn RAM Docker; 1 worker khi phát triển; sample 10–20%; giảm vocabSize |
| Quá nhiều lần chạy thực nghiệm | Dò trên `sample_20`, one-factor-at-a-time, ưu tiên Exp 1/3/4 (mục 16.1) |
| LDA chạy chậm | Giảm vocab; giảm iteration; document pooling nếu cần |
| So sánh độ đo sai cách | Chỉ so chéo bằng NPMI + interpretability (mục 11.5) |
| Burst giả do ít điểm dữ liệu / gap / chu kỳ ngày-đêm | Burst theo giờ, cửa sổ 48h, `std_floor`, loại gap (mục 14) |
| Text Analyzer phụ thuộc cluster khi demo | SparkSession `local[1]` + model cục bộ (mục 12.4) |
| Topic khó diễn giải | Domain stopwords; bigram; representative posts |
| Dataset chứa nhiều bài trùng | Dedup bằng tweet ID + text hash |
| High-activity accounts làm lệch trend | Đánh dấu và chạy ablation |
| Dữ liệu địa lý kém | Geographic page chuyển thành bonus |
| Dashboard chậm | MongoDB chỉ lưu aggregate |
| Demo lỗi | Video demo dự phòng |
| Model kết quả không ổn định | seed cố định + experiment registry |
| 2 worker không nhanh hơn | Giải thích giới hạn cùng máy vật lý |
| Phạm vi kết luận quá rộng | Chỉ kết luận trong dataset nghiên cứu |
| Copy/code tham khảo | Tự triển khai và ghi nguồn rõ ràng |

---

# 30. Câu hỏi phản biện cần chuẩn bị

## Big Data / Architecture

- Vì sao dùng HDFS?
- Vì sao không lưu tất cả bằng MongoDB?
- HDFS block là gì?
- Replication factor là gì?
- Vì sao sử dụng Parquet?
- Partition khác Spark partition như thế nào?

## Spark

- Job, stage và task là gì?
- Transformation và action khác nhau thế nào?
- Lazy evaluation là gì?
- Shuffle xảy ra khi nào?
- Tại sao partition ảnh hưởng tốc độ?

## NLP

- Vì sao phải tokenize?
- Stopword là gì?
- Vì sao cần domain stopwords?
- Bigram có lợi gì?

## TF-IDF

- TF là gì?
- IDF là gì?
- Vì sao TF-IDF khác frequency?

## KMeans

- KMeans hoạt động thế nào?
- Chọn k bằng cách nào?
- Silhouette score nói lên điều gì?
- Vì sao normalize vector?

## LDA

- LDA khác KMeans thế nào?
- Vì sao LDA dùng CountVectorizer thay vì TF-IDF?
- Perplexity là gì? Vì sao không so perplexity giữa hai vocabulary khác nhau?
- Topic coherence là gì? NPMI tính thế nào?
- Vì sao trend của LDA dùng trung bình xác suất thay vì argmax?

## Đánh giá

- Vì sao không so silhouette giữa có/không domain stopwords?
- Interpretability chấm thế nào để tránh chủ quan?
- Vì sao dò tham số trên mẫu 20% mà vẫn tin được kết quả khi chạy toàn bộ?
- Dựa vào đâu để chọn mô hình cuối?

## Trend

- Vì sao dùng topic ratio thay vì raw count?
- Burst score được tính thế nào? Vì sao cửa sổ không chứa điểm hiện tại?
- Tại sao cần minimum volume và `std_floor`?
- Vì sao phát hiện burst theo giờ mà không theo ngày?
- Khoảng trống dữ liệu ảnh hưởng burst thế nào?

## Scalability

- 1 worker và 2 worker khác nhau thế nào?
- Tại sao 2 worker trên cùng laptop không phải distributed benchmark hoàn chỉnh?

## Data Bias

- Dataset có đại diện cho toàn bộ người dùng mạng xã hội không?
- Có bias do hashtag không?
- Lọc tiếng Anh làm mất những gì?
- Vì sao loại retweet khi huấn luyện nhưng vẫn giữ khi đếm volume?
- High-activity account ảnh hưởng kết quả thế nào?

---

# 31. Tiêu chí hoàn thành tối thiểu

Dự án chỉ được xem là hoàn thành khi:

```text
[ ] Docker cluster chạy
[ ] HDFS chứa raw data
[ ] Clean data lưu Parquet
[ ] Có Data Quality Report
[ ] Có EDA Spark
[ ] Smoke test HDFS + Spark + MongoDB pass
[ ] Lọc ngôn ngữ + số liệu trong Data Quality Report
[ ] KMeans chạy và có Silhouette
[ ] LDA chạy và có Perplexity (held-out)
[ ] NPMI coherence tự cài đặt cho cả KMeans và LDA
[ ] Interpretability do 2 người chấm độc lập
[ ] Có ít nhất 3 experiment cải tiến (1, 3, 4)
[ ] Mô hình cuối được chọn có lý do ghi rõ
[ ] Có Experiment Registry
[ ] Có Trend Analysis
[ ] Có Burst Detection theo giờ
[ ] MongoDB serving chạy
[ ] Dashboard v0 nộp kèm GĐ1
[ ] Dashboard đủ 5 trang core
[ ] Text Analyzer chạy khi tắt cluster
[ ] README chạy được từ đầu
[ ] Báo cáo Word hoàn chỉnh
[ ] Slide hoàn chỉnh
[ ] Có video demo dự phòng
[ ] Hai thành viên đều có Git commit
[ ] Hai thành viên đều trả lời được câu hỏi phản biện
```

---

# 32. Kết luận định hướng thực hiện

Pipeline trọng tâm của đồ án:

```text
RAW SOCIAL DATA
        ↓
       HDFS
        ↓
   SPARK CLEANING
        ↓
 DATA QUALITY REPORT
        ↓
     PARQUET
        ↓
 FEATURE ENGINEERING
        ↓
 ┌───────────────┐
 │               │
TF-IDF          COUNT
 │               │
KMeans          LDA
 │               │
 └───────┬───────┘
         ↓
    EVALUATION
         ↓
BASELINE → IMPROVEMENT
         ↓
     TOPIC TREND
         ↓
  BURST DETECTION
         ↓
      MONGODB
         ↓
     DASHBOARD
```

Nguyên tắc quan trọng của nhóm:

> **Không chạy theo số lượng công nghệ. Ưu tiên pipeline hoàn chỉnh, có số liệu đánh giá, có bằng chứng cải tiến và giải thích được lý do của từng lựa chọn kỹ thuật.**
