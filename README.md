# Phân tích xu hướng chủ đề trên mạng xã hội

> **Nền tảng dữ liệu:** tiêu đề video từ các kênh báo chí và đài truyền hình Việt Nam trên YouTube. Dự án dùng HDFS, Apache Spark, MongoDB và Streamlit để xử lý dữ liệu, phân tích chủ đề theo thời gian và trực quan hóa kết quả.

## Tổng quan

Ứng dụng tổng hợp nội dung theo ngày và tháng, tìm các chủ đề được nhiều kênh đưa tin, theo dõi mức tăng giảm giữa các kỳ và hiển thị tiêu đề video đại diện. Phạm vi dữ liệu là các kênh đã cấu hình trong danh mục của dự án; kết quả không đại diện cho toàn bộ người dùng YouTube hay toàn bộ dư luận Việt Nam.

## Dataset

File đầu vào của pipeline là `data/exports/youtube_news_videos_clean.csv`.

Snapshot đang dùng cho đề tài có **1.263.204 dòng**, từ **01/01/2023 đến trước 30/10/2026 (UTC)**. Danh mục crawl gồm 155 kênh. Các tiêu đề trùng giữa nhiều kênh được giữ lại để phản ánh độ phủ đưa tin; trong cùng một kênh, các tiêu đề chuẩn hóa trùng nhau chỉ giữ video mới nhất.

CSV hiện có lượt xem và lượt thích cho các dòng được giữ. ID không truy cập được và video thiếu lượt thích bị loại trong bước xuất dữ liệu; lượt thích bằng 0 hợp lệ. Các chỉ số là số tích lũy tại thời điểm lấy metadata, không phải số tương tác phát sinh trong ngày đăng. Tác giả là tên kênh xuất bản, không phải tên phóng viên. Dataset hiện tại không chứa mô tả video hoặc bình luận.

> Snapshot này là bộ dữ liệu đầu vào được chốt để chạy phân tích và lập báo cáo trong phạm vi các nguồn, trường dữ liệu và khoảng thời gian nêu trên.

### Các trường chính

| Trường | Ý nghĩa |
| --- | --- |
| `video_id`, `video_url` | ID và đường dẫn video |
| `title` | Tiêu đề video đã làm sạch |
| `published_at_utc`, `published_at_vn` | Thời điểm đăng theo UTC và giờ Việt Nam |
| `author`, `channel_id` | Tên và ID kênh xuất bản |
| `view_count`, `like_count` | Lượt xem và lượt thích tại thời điểm lấy dữ liệu |
| `metrics_collected_at_utc` | Thời điểm lấy metadata và chỉ số tương tác |

## Chạy ứng dụng

### Yêu cầu

- Windows 10/11 hoặc môi trường hỗ trợ Docker.
- Docker Desktop chạy Linux containers và Docker Compose.
- Tối thiểu 8 GB RAM; lần build đầu cần Internet để tải image, thư viện và mô hình ngôn ngữ.

### Khởi động toàn bộ dịch vụ

Từ thư mục dự án:

```powershell
docker compose -f docker/docker-compose.yml up -d --build
```

Trên Windows có thể chạy `scripts/run.bat`. Tệp này khởi động Docker Desktop nếu cần, dựng dịch vụ và mở các trang dashboard, HDFS và Spark trong trình duyệt.

### Địa chỉ dịch vụ

| Dịch vụ | Địa chỉ |
| --- | --- |
| Dashboard | http://127.0.0.1:8501 |
| HDFS NameNode | http://127.0.0.1:9870/dfshealth.html#tab-overview |
| HDFS file browser | http://127.0.0.1:9870/explorer.html#/social/youtube_news |
| Spark Master | http://127.0.0.1:8080 |

Các trang dashboard gồm Bảng điểm, Các câu chuyện, Diễn biến, Từ khóa & Hashtag, Phân tích văn bản và Dữ liệu & Phương pháp. Nếu dashboard chưa có kết quả, hãy chạy pipeline bên dưới sau khi các dịch vụ đã khởi động.

## Cập nhật kết quả phân tích

Pipeline đưa CSV lên HDFS, làm sạch dữ liệu bằng Spark, tạo thống kê, huấn luyện Word2Vec + KMeans và LDA, tổng hợp xu hướng rồi ghi kết quả vào MongoDB:

```powershell
docker compose -f docker/docker-compose.yml exec namenode sh /scripts/upload_raw.sh
docker compose -f docker/docker-compose.yml exec spark-client sh scripts/run_pipeline.sh
```

Sau khi hoàn tất, tải lại dashboard. Nếu trình duyệt vẫn hiển thị dữ liệu đã cache, khởi động lại dashboard:

```powershell
docker compose -f docker/docker-compose.yml restart dashboard
```

`config/config.yaml` lưu khoảng thời gian, tham số mô hình và ngưỡng nhận diện xu hướng. Phân tích theo ngày sử dụng giờ Việt Nam; xu hướng so sánh kỳ hiện tại với 7 ngày trước. Nhãn chủ đề được rút từ các tiêu đề đại diện và nên được người đọc đối chiếu với nội dung minh họa.

## Thu thập dữ liệu mới

> Bước này chỉ cần thực hiện khi muốn cập nhật dataset. Không cần API key để chạy dashboard hoặc phân tích CSV đã có.

1. Bật **YouTube Data API v3** trong Google Cloud.
2. Sao chép `config/.env.example` thành `.env` ở thư mục gốc dự án và điền `YOUTUBE_API_KEY`. Không đưa `.env` hoặc API key lên GitHub.
3. Chạy collector và exporter:

```powershell
python scripts/collect_news_titles.py --start 2023-01-01 --end 2026-10-30
python scripts/export_news_videos.py
```

Thời gian kết thúc là biên loại trừ. Collector duy trì checkpoint để tiếp tục sau khi bị gián đoạn; xem `crawl/README.md` trước khi thay đổi khoảng ngày hoặc danh mục nguồn. Dữ liệu thô và CSV được giữ cục bộ, không được commit lên Git.

## Cấu trúc repository

```text
config/             Danh mục kênh, cấu hình mô hình và file mẫu môi trường
crawl/              Tài liệu quy trình, nguồn thu thập và snapshot
dashboard/          Ứng dụng Streamlit và các trang trực quan hóa
docker/             Docker Compose, cấu hình Spark và Hadoop
project_docs/       Tài liệu thiết kế và yêu cầu sản phẩm
social-topic-trends/ Bản project độc lập, báo cáo, dataset và kết quả phân tích
scripts/            Collector, exporter, pipeline và tiện ích khởi động
src/                ETL, thống kê, mô hình, xu hướng và xuất MongoDB
tests/              Kiểm tra logic xử lý và phân tích
data/               CSV đầu vào và dữ liệu thô cục bộ (không commit)
models/              Mô hình đã huấn luyện cục bộ (không commit)
reports/             Kết quả phân tích cục bộ (không commit)
experiments/         Registry thực nghiệm cục bộ (không commit)
```

## Ghi chú phương pháp

- Thống kê mô tả dùng toàn bộ dòng hợp lệ; bước huấn luyện lọc tiêu đề tiếng Việt theo ngưỡng tin cậy trong cấu hình.
- Tiêu đề trùng từ các kênh khác nhau vẫn được giữ để đo độ phủ nguồn.
- Views và likes là số tích lũy tại thời điểm crawl, không thể hiện tương tác tại ngày đăng.
- Danh mục tập trung vào kênh báo chí và đài truyền hình; một số video có thể thuộc chương trình văn hóa hoặc giải trí.
- Không suy rộng kết quả thành xu hướng của toàn bộ mạng xã hội hoặc toàn thể người dân Việt Nam.

## Tài liệu liên quan

- [Project và kết quả phân tích](social-topic-trends/README.md)
- [Báo cáo đồ án (Word)](social-topic-trends/docs/BaoCao_DoAn_BigData.docx)
- [Báo cáo đồ án (PDF)](social-topic-trends/docs/BaoCao_DoAn_BigData.pdf)
- [Slide thuyết trình (PowerPoint)](social-topic-trends/docs/slides/BigData-thuyet-trinh.pptx)
- [Quy trình thu thập và phạm vi nguồn](crawl/README.md)
- [Thiết kế giao diện](project_docs/DESIGN.md)
- [Yêu cầu sản phẩm](project_docs/PRODUCT.md)
