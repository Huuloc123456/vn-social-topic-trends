# KẾ HOẠCH ĐỒ ÁN – PHÂN TÍCH XU HƯỚNG CHỦ ĐỀ TRÊN MẠNG XÃ HỘI

> Môn: Nhập môn Big Data · Đề tài số 5 · Nhóm 2 sinh viên · Thời lượng 10 tuần
> Mục tiêu điểm: **≥ 8.5 ở cả 6 tiêu chí rubric** (mức “đáp ứng 85–100% yêu cầu”)

---

## 1. Định nghĩa bài toán

| Mục | Nội dung |
|---|---|
| **Bài toán** | Từ hàng triệu bài đăng mạng xã hội, tự động phát hiện **các chủ đề đang được bàn luận** và theo dõi **chủ đề nào nổi lên / suy giảm theo thời gian**. |
| **Bối cảnh ứng dụng** | Truyền thông, marketing, theo dõi dư luận (social listening), cơ quan báo chí cần biết “người dùng đang nói gì, khi nào bùng nổ”. |
| **Đầu vào** | Bài đăng / bình luận có: nội dung văn bản, thời gian đăng, hashtag, lượt tương tác, (vị trí). |
| **Đầu ra** | (1) Danh sách chủ đề + từ khóa đặc trưng, (2) phân bố chủ đề theo ngày/giờ, (3) các thời điểm “bùng nổ” chủ đề, (4) top hashtag/từ khóa xu hướng, (5) dashboard tương tác + chức năng dự đoán chủ đề cho văn bản mới. |
| **Phạm vi** | Dữ liệu tiếng Anh, xử lý theo lô (batch). Mở rộng (điểm cộng): mô phỏng streaming bằng Spark Structured Streaming. |

### Bộ dữ liệu đề xuất (chốt trong tuần 1)

| Ưu tiên | Bộ dữ liệu | Lý do chọn |
|---|---|---|
| **Chính** | **US Election 2020 Tweets** (Kaggle – 2 file `hashtag_donaldtrump.csv`, `hashtag_joebiden.csv`, ~1,7 triệu tweet, 15/10 → 08/11/2020) | Có `created_at`, text, likes, retweet, vị trí; có **sự kiện thật** (tranh luận 22/10, bầu cử 03/11, công bố kết quả 07/11) → dễ chứng minh trend phát hiện đúng. |
| Dự phòng 1 | COVID-19 Tweets (Kaggle) | Chủ đề đa dạng, trải dài nhiều tháng. |
| Dự phòng 2 | Reddit comments (Pushshift dump theo subreddit) | Dung lượng lớn (GB), thể hiện rõ tính Big Data. |

> Ghi chú “5V” cho báo cáo: Volume (triệu bản ghi, vài GB), Variety (văn bản phi cấu trúc + số + thời gian + địa lý), Velocity (hàng chục nghìn tweet/giờ vào ngày bầu cử), Veracity (bot, spam, trùng lặp, retweet), Value (nắm bắt dư luận theo thời gian thực).

---

## 2. Kiến trúc hệ thống

```
 [Kaggle CSV / crawler Reddit]
            │  (ingest: hdfs dfs -put / PySpark)
            ▼
 ┌─────────── HDFS (Data Lake) ────────────┐
 │ /social/raw      – CSV gốc (bronze)      │
 │ /social/clean    – Parquet, partition theo ngày (silver) │
 │ /social/features – TF-IDF vectors, model (gold)          │
 └──────────────────────────────────────────┘
            │  Spark (DataFrame + MLlib) trên cluster 1 master – 2 worker
            ▼
   Làm sạch → Thống kê → TF-IDF → KMeans / LDA → Trend & phát hiện bùng nổ
            │
            ▼
 MongoDB (serving layer): topics, topic_trend_daily, hashtag_trend, keyword_trend, posts_sample
            │
            ▼
 Dashboard Streamlit + Plotly (tổng quan · chủ đề · xu hướng · hashtag · dự đoán chủ đề)
```

**Lý do chọn công nghệ** (đưa vào báo cáo, tiêu chí CLO2):
- **HDFS**: lưu file lớn, phân tán, chịu lỗi (replication), Spark đọc song song theo block.
- **Parquet**: định dạng cột, nén tốt, partition theo `date` → truy vấn theo khoảng thời gian nhanh.
- **Spark DataFrame + MLlib**: xử lý in-memory, có sẵn Tokenizer, StopWordsRemover, CountVectorizer, IDF, KMeans, BisectingKMeans, LDA.
- **MongoDB**: dữ liệu kết quả dạng document (chủ đề + mảng từ khóa), truy vấn nhanh cho dashboard; không để dashboard đọc thẳng HDFS.

**Môi trường**: Docker Compose trên Windows (namenode, datanode ×2, spark-master, spark-worker ×2, mongodb, jupyter-pyspark). Spark 3.5, Python 3.10+, Streamlit.

### Cấu trúc repo

```
do_an_cuoi_mon_bigdata/
├─ docker/            docker-compose.yml, hadoop.env
├─ data/              sample/ (mẫu nhỏ để demo); raw/ (gitignore)
├─ src/
│  ├─ ingest/         01_upload_to_hdfs.py, (crawler_reddit.py – tùy chọn)
│  ├─ etl/            02_clean.py
│  ├─ eda/            03_statistics.py
│  ├─ model/          04_tfidf.py, 05_kmeans.py, 06_lda.py, 07_evaluate.py
│  ├─ trend/          08_topic_trend.py, 09_burst_detection.py
│  └─ export/         10_export_mongo.py
├─ dashboard/         app.py, pages/
├─ notebooks/         EDA + minh họa lý thuyết
├─ docs/              KE_HOACH_DO_AN.md, bao_cao.docx, slide.pptx
└─ README.md          hướng dẫn cài đặt & chạy từng bước
```

---

## 3. Chi tiết kỹ thuật theo từng giai đoạn pipeline

### 3.1 Làm sạch & tiền xử lý (Spark)
- Chuẩn hóa schema, ép kiểu `created_at` → timestamp; tạo cột `date`, `hour`.
- **Trùng lặp**: gộp 2 file (tweet có cả #Trump và #Biden bị lặp) → `dropDuplicates(["tweet_id"])`; phát hiện retweet/nội dung trùng bằng hash của text.
- **Thiếu**: bỏ bản ghi thiếu text/thời gian; điền `"unknown"` cho vị trí.
- **Ngoại lệ / không nhất quán**: thời gian ngoài khoảng thu thập, text quá ngắn (< 3 token), tài khoản đăng bất thường (nghi bot – top 0.1% số bài/ngày), chuẩn hóa tên quốc gia/bang.
- **Làm sạch văn bản**: lowercase, bỏ URL, @mention, emoji, HTML entity, số; tách hashtag ra cột mảng `hashtags`.
- **Tokenize + stopwords**: `RegexTokenizer`, `StopWordsRemover` (tiếng Anh) + **stopwords miền** (`trump`, `biden`, `rt`, `amp`… vì xuất hiện ở hầu hết tweet → che mất chủ đề); tùy chọn lemmatize (Spark NLP) và bigram (`NGram`).
- Ghi kết quả Parquet partition theo `date` lên HDFS. **Ghi lại số bản ghi trước/sau từng bước** (bảng này rất ăn điểm CLO2).

### 3.2 Thống kê mô tả
Số bài theo ngày/giờ, top hashtag, top từ, phân phối độ dài bài, phân phối hoạt động người dùng (long-tail), top quốc gia/bang, tương tác trung bình.

### 3.3 Mô hình (CLO3 – 2.5 điểm)
| # | Kỹ thuật | Mục đích | Đánh giá |
|---|---|---|---|
| 1 | **TF-IDF** (`CountVectorizer` + `IDF`, vocab ~20k, minDF) | Vector hóa; tìm **từ khóa xu hướng theo ngày** (coi mỗi ngày là 1 văn bản) | So sánh top TF-IDF với top tần suất thô |
| 2 | **KMeans / BisectingKMeans** trên TF-IDF (chuẩn hóa L2 ≈ cosine) | Phân cụm bài đăng thành chủ đề | Elbow (WSSSE) + **Silhouette** với k ∈ {5, 8, 10, 15, 20} |
| 3 | **LDA** (optimizer online) | Mô hình chủ đề xác suất | **Log-perplexity**, **topic coherence (UMass/NPMI)** tự tính bằng Spark, đánh giá thủ công nhãn chủ đề |
| 4 | **Trend & burst detection** | Tỷ trọng chủ đề theo ngày, trung bình trượt, điểm bùng nổ khi z-score > 2 | Đối chiếu mốc sự kiện thật (22/10, 03/11, 07/11) |

**Thực nghiệm cần có trong báo cáo:**
- Bảng so sánh KMeans vs BisectingKMeans vs LDA: coherence, silhouette, thời gian chạy, khả năng diễn giải.
- Ảnh hưởng tham số: k, vocabSize, có/không stopwords miền, unigram vs bigram.
- **Thí nghiệm khả năng mở rộng**: thời gian chạy với 10% / 50% / 100% dữ liệu và 1 vs 2 worker → biểu đồ (thể hiện đúng tinh thần Big Data).
- Lưu `PipelineModel` lên HDFS để tái sử dụng cho chức năng dự đoán.

### 3.4 Dashboard / ứng dụng (CLO3 – 2.5 điểm)
Streamlit + Plotly, đọc từ MongoDB:
1. **Tổng quan**: KPI (tổng bài, số ngày, số hashtag, số chủ đề), biểu đồ số bài theo ngày/giờ.
2. **Chủ đề**: thẻ từng chủ đề (nhãn do nhóm đặt, top từ, word cloud, bài đăng tiêu biểu), bản đồ khoảng cách chủ đề.
3. **Xu hướng theo thời gian**: stacked area tỷ trọng chủ đề, đánh dấu điểm bùng nổ + chú thích sự kiện; bộ lọc khoảng ngày, chủ đề.
4. **Hashtag & từ khóa**: top hashtag theo ngày, mạng đồng xuất hiện hashtag, từ khóa TF-IDF nổi bật theo ngày.
5. **Địa lý** (nếu dữ liệu đủ): bản đồ choropleth chủ đề theo bang/quốc gia.
6. **Dự đoán chủ đề**: nhập 1 câu → pipeline đã lưu trả về chủ đề + xác suất → chứng minh sản phẩm dùng được.

Mỗi biểu đồ phải kèm **1 câu insight** (“Chủ đề *gian lận bầu cử* tăng gấp 4 lần sau 04/11…”) – rubric yêu cầu “thể hiện rõ thông tin có giá trị”.

---

## 4. Bám rubric: checklist để đạt ≥ 8.5 mỗi tiêu chí

| Tiêu chí (điểm) | Việc phải làm để đạt 85–100% | Minh chứng nộp | Phụ trách |
|---|---|---|---|
| **Tính ứng dụng của kỹ thuật – CLO1 (1.0)** | Nêu rõ bài toán thực tế, người dùng mục tiêu, giá trị; lý giải vì sao cần Big Data (5V); đối chiếu kết quả với sự kiện thật | Chương 1 báo cáo, slide mở đầu, case study trên dashboard | A + B |
| **Lưu trữ & xử lý/phân tích dữ liệu – CLO2 (2.0)** | Cluster HDFS + Spark chạy thật; kiến trúc bronze/silver/gold; làm sạch đủ 4 loại (thiếu, trùng, ngoại lệ, không nhất quán); bảng số bản ghi qua từng bước; Parquet + partition; EDA đầy đủ; MongoDB serving | Ảnh NameNode UI / Spark UI, sơ đồ kiến trúc, bảng làm sạch, notebook EDA | **A** (chính) |
| **Mô hình/công nghệ xử lý – CLO3 (2.5)** | Ít nhất 2 phương pháp (KMeans + LDA) trên TF-IDF; chọn tham số có căn cứ; độ đo định lượng (silhouette, perplexity, coherence); bảng so sánh; thí nghiệm scale; nêu hạn chế | Chương lý thuyết + thực nghiệm, bảng/biểu đồ kết quả | **B** (chính) |
| **Trực quan hóa/Xây dựng ứng dụng – CLO3 (2.5)** | Dashboard ≥ 5 trang, có bộ lọc tương tác, có trend + burst, có chức năng dự đoán; insight rõ ràng; chạy demo ổn định | Link/video demo, ảnh chụp dashboard, README chạy được | **B** (chính), A hỗ trợ dữ liệu |
| **Trình bày báo cáo – CLO4 (1.0)** | Đúng cấu trúc quy định; hình/bảng đánh số, trích nguồn; không lỗi chính tả; slide 15–20 trang, thuyết trình đúng giờ, trả lời phản biện | File Word, PPT, tổng dượt 2 lần | A + B |
| **Phân công & phối hợp nhóm – CLO5 (1.0)** | Lịch họp hàng tuần + biên bản; bảng phân công và % đóng góp; lịch sử commit Git của **cả 2** thành viên; mỗi người trả lời được toàn bộ pipeline | Mục “Lịch làm việc” và “Công việc thành viên” trong báo cáo, GitHub insights | A + B |

---

## 5. Phân công vai trò

| Thành viên | Vai trò chính | Công việc |
|---|---|---|
| **SV A – Data Engineer** | Hạ tầng & dữ liệu | Docker cluster, ingest HDFS, pipeline làm sạch, EDA, export MongoDB, thí nghiệm scale, chương Cơ sở lý thuyết (HDFS/Spark/NoSQL) |
| **SV B – Data Scientist** | Mô hình & trực quan | TF-IDF, KMeans, LDA, đánh giá, trend/burst, dashboard, chương lý thuyết (TF-IDF/KMeans/LDA) |
| **Chung** | | Chọn dữ liệu, gắn nhãn chủ đề, viết báo cáo, slide, tổng dượt; **review chéo code của nhau mỗi tuần** để cả hai nắm hết hệ thống khi bị hỏi |

Quy ước: làm việc trên GitHub (nhánh `feature/*`, pull request có người kia review); họp 2 buổi/tuần (1 buổi online 30’ giữa tuần, 1 buổi tổng kết cuối tuần) và ghi biên bản ngắn vào `docs/bien_ban/`.

---

## 6. Tiến độ 10 tuần

> File hướng dẫn xếp việc “tìm bộ dữ liệu” ở tuần 8–9, nhưng đề tài này cần dữ liệu từ sớm để có baseline nộp giai đoạn 1 → nhóm **chốt dữ liệu ngay tuần 1–2** (vẫn đảm bảo đủ các sản phẩm theo từng mốc).

| Tuần | Công việc | Sản phẩm | A | B |
|---|---|---|---|---|
| **1** | Đăng ký đề tài 5; lập nhóm, phân vai; tạo repo; chọn & tải dataset chính + dự phòng | Đề tài đã đăng ký; repo | Tải dữ liệu, tạo repo | Khảo sát dataset, đọc tài liệu topic modeling |
| **2** | Dựng Docker cluster (HDFS + Spark + MongoDB + Jupyter); đưa dữ liệu lên HDFS; EDA sơ bộ | Cluster chạy; dữ liệu trên `/social/raw` | Docker, HDFS | EDA notebook sơ bộ |
| **3** | Hoàn thiện & **nộp bản kế hoạch nhóm**; pipeline làm sạch v1 → Parquet | Kế hoạch; `/social/clean` | `02_clean.py` | Danh sách stopwords miền, thử tokenize |
| **4** | Tìm hiểu lý thuyết: HDFS, Spark, TF-IDF, KMeans, LDA; ví dụ minh họa nhỏ; thống kê mô tả đầy đủ | Tài liệu tóm tắt lý thuyết + ví dụ | Lý thuyết HDFS/Spark/Mongo; `03_statistics.py` | Lý thuyết TF-IDF/KMeans/LDA + ví dụ tay |
| **5** | Baseline: TF-IDF + KMeans, LDA (k=10); biểu đồ trend thô | Kết quả baseline | Tối ưu job Spark, lưu features | `04–06` baseline |
| **6** | Đánh giá baseline (silhouette, perplexity, coherence); xác định điểm cần cải thiện; **nộp báo cáo tiến độ – Giai đoạn 1** | Báo cáo tiến độ GĐ1 | Viết phần dữ liệu & kiến trúc | Viết phần mô hình & kết quả baseline |
| **7** | Cải tiến: tuning k, bigram, stopwords miền; trend + burst detection; export MongoDB; thí nghiệm scale | Mô hình cuối; dữ liệu trên MongoDB | `10_export_mongo.py`, benchmark scale | `07–09`, gắn nhãn chủ đề |
| **8** | Xây dashboard đầy đủ; viết báo cáo bản nháp | Dashboard v1; báo cáo nháp | Trang Tổng quan, Hashtag, Địa lý | Trang Chủ đề, Xu hướng, Dự đoán |
| **9** | Hoàn thiện báo cáo, slide, README, video demo dự phòng; rà soát cấu trúc; **nộp Giai đoạn 2** lên Classroom (source, Word, PPT) | Bài nộp đầy đủ | README, kiểm tra chạy lại từ đầu | Slide, chính tả, định dạng |
| **10** | Tổng dượt; thuyết trình; trả lời phản biện | Buổi thuyết trình | Phần kiến trúc & xử lý | Phần mô hình & demo |

---

## 7. Cấu trúc báo cáo Word (theo quy định)

1. Trang bìa
2. Lịch làm việc nhóm hàng tuần (bảng mục 6 + ngày họp thực tế)
3. Công việc mỗi thành viên (bảng mục 5 + % đóng góp)
4. Mục lục
5. **Chương 1 – Giới thiệu đề tài**: bối cảnh, bài toán, mục tiêu, phạm vi, đầu vào/đầu ra, giá trị; mô tả dữ liệu & 5V
6. **Chương 2 – Cơ sở lý thuyết**: Big Data, HDFS, Spark (RDD/DataFrame, MLlib), MongoDB; tiền xử lý văn bản; TF-IDF; KMeans/BisectingKMeans; LDA; độ đo silhouette, perplexity, coherence; phát hiện bùng nổ
7. **Chương 3 – Xây dựng ứng dụng, trực quan hóa dữ liệu**: kiến trúc, môi trường, pipeline làm sạch (bảng trước/sau), EDA, thực nghiệm mô hình & so sánh, thí nghiệm scale, dashboard (ảnh + insight)
8. **Chương 4 – Kết luận & định hướng phát triển**: kết quả đạt được, hạn chế (dữ liệu 1 nguồn, chỉ tiếng Anh, LDA kém với văn bản ngắn…), hướng phát triển (Kafka + Spark Streaming realtime, BERTopic, dữ liệu tiếng Việt, phân tích cảm xúc theo chủ đề)
9. Tài liệu tham khảo
10. Phụ lục: hướng dẫn cài đặt, mã nguồn chính

---

## 8. Rủi ro & phương án

| Rủi ro | Phương án |
|---|---|
| Laptop yếu RAM khi chạy Docker cluster | Giới hạn memory container; dev trên mẫu 10%, chạy full ở máy mạnh hơn; giảm vocabSize |
| LDA chạy chậm / chủ đề khó hiểu với tweet ngắn | Gộp tweet theo hashtag hoặc theo user-ngày (document pooling); dùng KMeans làm phương án chính |
| Chủ đề bị lấn át bởi từ khóa truy vấn | Stopwords miền + so sánh trước/sau (đưa vào báo cáo như một cải tiến) |
| Dataset bị gỡ khỏi Kaggle | Tải và backup ngay tuần 1; có 2 dataset dự phòng |
| Lỗi demo khi thuyết trình | Quay video demo tuần 9; dashboard đọc MongoDB (không phụ thuộc cluster lúc demo) |
| Vi phạm quy định sao chép (điểm 0) | Tự viết code, ghi nguồn mọi tài liệu/đoạn code tham khảo |

---

## 9. Câu hỏi phản biện cần chuẩn bị

- Vì sao dùng HDFS + MongoDB mà không chỉ một hệ? Replication factor, block size là gì?
- Vì sao TF-IDF tốt hơn đếm tần suất? IDF tính thế nào trong Spark?
- Chọn k như thế nào? Silhouette/perplexity/coherence có ý nghĩa gì?
- KMeans khác LDA ở điểm nào (cứng vs mềm, hình học vs xác suất)?
- Spark chia job/stage/task ra sao? Partition ảnh hưởng tốc độ thế nào (dẫn chứng thí nghiệm scale)?
- Dữ liệu có thiên lệch gì (chỉ tweet có hashtag chính trị, người dùng Mỹ…)? Hạn chế của giải pháp?
