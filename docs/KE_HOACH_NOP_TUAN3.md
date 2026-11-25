# KẾ HOẠCH LÀM VIỆC NHÓM – ĐỒ ÁN MÔN NHẬP MÔN BIG DATA

**Đề tài số 5:** Phân tích xu hướng chủ đề trên mạng xã hội

| Thành viên | MSSV | Vai trò |
|---|---|---|
| ………………… (SV A) | ……… | Kỹ sư dữ liệu – hạ tầng, lưu trữ, xử lý |
| ………………… (SV B) | ……… | Phân tích dữ liệu – mô hình, trực quan hóa |

---

## 1. Bài toán

Từ khoảng 2,1 triệu bài đăng mạng xã hội Bluesky, hệ thống tự động **phát hiện các chủ đề được thảo luận**, **theo dõi tỷ trọng từng chủ đề theo thời gian** và **phát hiện thời điểm chủ đề tăng đột biến**. Kết quả được trình bày trên dashboard tương tác, kèm chức năng xác định chủ đề cho một đoạn văn bản mới.

- **Ứng dụng:** theo dõi dư luận trên mạng xã hội (social listening), marketing, truyền thông.
- **Đầu vào:** nội dung bài đăng, thời gian đăng, hashtag, lượt tương tác, vị trí.
- **Đầu ra:** danh sách chủ đề và từ khóa đặc trưng; tỷ trọng chủ đề theo ngày/giờ; các sự kiện bùng nổ; top hashtag/từ khóa; dashboard.
- **Phạm vi:** bài tiếng Anh, xử lý theo lô, xu hướng trong ngày theo khung 5 phút. Kết quả chỉ phản ánh tập dữ liệu nghiên cứu.

## 2. Dữ liệu

| | Nội dung |
|---|---|
| Bộ dữ liệu | Bluesky two-million posts (Hugging Face, Apache-2.0): 2.107.530 bài, 23 file JSONL (790 MB), firehose ngày 27/11/2024 |
| Trường | nội dung, thời gian đăng, tác giả, uri, có ảnh, trả lời bài nào |
| Đặc trưng Big Data | Khối lượng lớn (2,1 triệu bản ghi); đa dạng (văn bản đa ngôn ngữ, thời gian, quan hệ trả lời); tốc độ cao (5.000–16.000 bài mỗi 5 phút); nhiều nhiễu (bài nhập lại từ kho cũ, bài chỉ có ảnh, trùng nội dung, bot) |

## 3. Công nghệ và kiến trúc

```text
CSV ─► HDFS (raw) ─► Spark: làm sạch, lọc ngôn ngữ, chất lượng dữ liệu ─► HDFS (Parquet, chia theo ngày)
   ─► Spark MLlib: TF-IDF + KMeans / BisectingKMeans; CountVectorizer + LDA
   ─► Đánh giá ─► Xu hướng theo giờ/ngày + phát hiện bùng nổ ─► MongoDB ─► Dashboard Streamlit
```

| Công nghệ | Vai trò |
|---|---|
| HDFS | Lưu trữ phân tán dữ liệu gốc và dữ liệu đã làm sạch |
| Apache Spark (DataFrame, SQL, MLlib) | Làm sạch, thống kê, vector hóa văn bản, phân cụm, mô hình chủ đề |
| MongoDB | Lưu kết quả tổng hợp phục vụ dashboard |
| Streamlit + Plotly | Dashboard tương tác |
| Docker Compose | Dựng cụm 2 datanode, 2 Spark worker, MongoDB trên máy cá nhân |

## 4. Phương pháp và đánh giá

- **Tiền xử lý:** loại trùng, xử lý dữ liệu thiếu và ngoại lệ, lọc tiếng Anh, bỏ URL/mention, tách từ, loại stopwords. Có bảng số bản ghi trước/sau từng bước.
- **Mô hình:** TF-IDF + KMeans/BisectingKMeans, Word2Vec + KMeans (phân cụm cứng) và LDA (mô hình chủ đề xác suất).
- **Đánh giá:** silhouette, log-perplexity, độ mạch lạc chủ đề NPMI, đánh giá thủ công độc lập của 2 thành viên.
- **Thực nghiệm cải tiến:** stopwords theo miền, số chủ đề k, so sánh thuật toán (bắt buộc); bigram, ảnh hưởng tài khoản hoạt động nhiều (nếu kịp); thí nghiệm khả năng mở rộng theo kích thước dữ liệu và số worker.
- **Xu hướng:** tỷ trọng chủ đề theo khung 5 phút; phát hiện bùng nổ bằng z-score so với 60 phút trước kèm ngưỡng mức tăng tương đối.

## 5. Phân công

| Hạng mục | SV A | SV B |
|---|:---:|:---:|
| Dựng cụm Docker (HDFS, Spark, MongoDB) | **Chính** | Hỗ trợ |
| Làm sạch dữ liệu, báo cáo chất lượng dữ liệu, thống kê mô tả | **Chính** | Hỗ trợ |
| Tiền xử lý văn bản, stopwords | Hỗ trợ | **Chính** |
| Mô hình TF-IDF, KMeans, LDA, đánh giá, thực nghiệm | Hỗ trợ | **Chính** |
| Tổng hợp xu hướng, phát hiện bùng nổ, xuất MongoDB | **Chính** | Hỗ trợ |
| Thí nghiệm khả năng mở rộng | **Chính** | |
| Dashboard | Trang Tổng quan, Hashtag | Trang Chủ đề, Xu hướng, Phân tích văn bản |
| Đánh giá thủ công chủ đề, gán nhãn | Cùng làm | Cùng làm |
| Báo cáo Word, slide, thuyết trình | Cùng làm | Cùng làm |

Hai thành viên review code chéo hằng tuần qua GitHub (pull request) để cả hai nắm toàn bộ hệ thống.

## 6. Tiến độ

| Tuần | Công việc chính | Sản phẩm / Mốc nộp |
|---|---|---|
| 1 | Đăng ký đề tài, lập nhóm, tải dữ liệu, tạo repo | **Đăng ký đề tài** |
| 2 | Dựng cụm Docker, đưa dữ liệu lên HDFS, kiểm tra hệ thống | Cụm chạy ổn định, dữ liệu trên HDFS |
| 3 | Làm sạch dữ liệu, lọc ngôn ngữ, báo cáo chất lượng dữ liệu | **Nộp kế hoạch nhóm**; dữ liệu sạch dạng Parquet |
| 4 | Thống kê mô tả; tìm hiểu lý thuyết | **Tài liệu tóm tắt lý thuyết + ví dụ minh họa** |
| 5 | Mô hình baseline (KMeans, LDA); xuất kết quả sang MongoDB | Bảng kết quả baseline |
| 6 | Đánh giá baseline, thực nghiệm 1; dashboard bản đầu (3 trang) | **Nộp báo cáo tiến độ – Giai đoạn 1** |
| 7 | Thực nghiệm cải tiến, chọn mô hình cuối; xu hướng + bùng nổ | Mô hình cuối, dữ liệu xu hướng |
| 8 | Thí nghiệm mở rộng; dashboard hoàn chỉnh (5 trang); báo cáo nháp | Dashboard hoàn chỉnh |
| 9 | Hoàn thiện báo cáo, slide, hướng dẫn cài đặt, video demo | **Nộp Giai đoạn 2** (Source, Word, PPT) |
| 10 | Tổng dượt, thuyết trình | **Thuyết trình** |

## 7. Lịch làm việc nhóm

- **Họp cố định:** 2 buổi/tuần – buổi giữa tuần (online, 30 phút) cập nhật tiến độ; buổi cuối tuần tổng kết và giao việc tuần sau.
- **Biên bản họp:** ghi ngày, người tham dự, việc đã làm, việc tuần sau, vướng mắc.
- **Công cụ:** GitHub (mã nguồn, pull request), Google Drive (báo cáo, slide), nhóm chat.

## 8. Rủi ro chính và phương án

| Rủi ro | Phương án |
|---|---|
| Máy cá nhân thiếu RAM khi chạy cụm | Giới hạn bộ nhớ container; phát triển trên mẫu 10–20% dữ liệu |
| Mô hình chạy chậm | Dò tham số trên mẫu cố định, chỉ chạy toàn bộ dữ liệu cho cấu hình cuối |
| Chủ đề khó diễn giải | Stopwords theo miền, bigram, xem bài đăng tiêu biểu |
| Lỗi khi demo | Dashboard không phụ thuộc cụm Spark; quay video demo dự phòng |
