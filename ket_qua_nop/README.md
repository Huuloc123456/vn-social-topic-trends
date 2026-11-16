# Phân tích xu hướng chủ đề trên mạng xã hội

Đây là bản project độc lập để nộp, giữ cấu trúc chính của mã nguồn gốc và chứa snapshot dữ liệu cùng kết quả phân tích đã chạy.

## Cấu trúc

```text
config/                 Cấu hình, danh mục kênh, từ điển tiếng Việt
crawl/                  Phạm vi và danh mục nguồn dữ liệu
dashboard/              Dashboard Streamlit
data/exports/            Dataset CSV đã làm sạch
docker/                 Docker Compose, Spark và Hadoop
docs/                   Báo cáo Word/PDF và slide PowerPoint
models/youtube_news/     Mô hình dùng cho Phân tích văn bản
project_docs/            Thiết kế và yêu cầu sản phẩm
reports/youtube_news/    Kết quả phân tích cuối
scripts/                 Khởi động, thu thập và chạy pipeline
src/                     ETL, thống kê, mô hình, xu hướng, MongoDB
tests/                   Kiểm tra logic
```

Các snapshot crawl theo ngày, log, bản backup, cache và artefact dựng thử đã được bỏ khỏi bản nộp. CSV trong `data/exports/` là bản dữ liệu chính; CSV được giữ trong thư mục nộp cục bộ nhưng không đưa lên GitHub. Mã nguồn, mô hình inference, báo cáo, slide và JSON kết quả phân tích được theo dõi trong repo.

## Dataset và kết quả

`data/exports/youtube_news_videos_clean.csv` có **1.263.204 video**, thời gian đăng từ **01/01/2023 đến 29/10/2026 UTC**. Các trường gồm tiêu đề, thời gian đăng, tên/ID kênh, đường dẫn video, lượt xem, lượt thích và thời điểm lấy metadata.

Dataset được tổng hợp từ tiêu đề video của các kênh báo chí và đài truyền hình Việt Nam đã cấu hình. Đây không phải mẫu đại diện cho toàn bộ người dùng YouTube hoặc toàn bộ dư luận xã hội. Lượt xem/lượt thích là số tích lũy tại thời điểm lấy metadata.

Kết quả pipeline đã có trong `reports/youtube_news/`: dữ liệu chất lượng, thống kê tổng quan và các file cuối trong `final/` (chủ đề, diễn biến theo ngày, từ khóa, hashtag, vấn đề ngày, sự kiện tăng đột biến và video đại diện).

## Chạy project

Yêu cầu: Windows 10/11, Docker Desktop với Linux containers và tối thiểu 8 GB RAM.

1. Từ thư mục `ket_qua_nop/`, chạy `scripts/run.bat` để khởi động Docker Compose và mở dashboard, HDFS, Spark.
2. Kết quả phân tích đã lưu trong `reports/youtube_news/`. Để nạp lại vào MongoDB sau khi khởi động dịch vụ:

   ```powershell
   docker compose -f docker/docker-compose.yml exec spark-client python3 -m src.export.export_mongo
   ```

3. Muốn chạy lại toàn bộ phân tích với CSV hiện có:

   ```powershell
   docker compose -f docker/docker-compose.yml exec namenode sh /scripts/upload_raw.sh
   docker compose -f docker/docker-compose.yml exec spark-client sh scripts/run_pipeline.sh
   ```

Mở dashboard tại `http://127.0.0.1:8501`. Ứng dụng và pipeline không cần API key khi dùng snapshot này. Muốn thu thập dữ liệu mới, hãy tạo `.env` từ `config/.env.example` và tự điền YouTube API key; không đưa `.env` lên Git.

## Tài liệu nộp

- [Báo cáo Word](docs/BaoCao_DoAn_BigData.docx)
- [Báo cáo PDF](docs/BaoCao_DoAn_BigData.pdf)
- [Slide thuyết trình](docs/slides/BigData-thuyet-trinh.pptx)
