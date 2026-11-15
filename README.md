# VN Social Topic Trends

Phân tích chủ đề và diễn biến đưa tin theo ngày/tháng từ **tiêu đề video của các kênh báo, đài Việt Nam trên YouTube**. Pipeline dùng HDFS, Apache Spark, MongoDB và dashboard Streamlit.

## Dataset đang sử dụng

Đầu vào duy nhất: `data/exports/youtube_news_videos_clean.csv`.

**Đang mở rộng lịch sử từ 01/01/2025, bắt đầu ngày 24/10/2026.** Lượt quét đang chạy nền cho 155 nguồn, giữ video đã thu; cửa sổ UTC là `[2025-01-01, 2026-10-25)`. CSV bên dưới vẫn là bản đã xuất trước lượt này, chưa phải kết quả mở rộng. Trạng thái nằm ở `reports/youtube_2025_extension_run.json`; bước tiếp theo tự lấy metadata cho ID mới rồi xuất lại CSV. [Cách tiếp tục checkpoint](crawl/README.md).

**CSV sau lượt crawl ngày 21/10/2026: 479.416 dòng sạch từ 134 kênh có dữ liệu**, trong danh mục 155 nguồn; tăng ròng **2.393 dòng**, thu thêm **2.459 video ID** so với bộ 477.023 dòng. Cửa sổ lọc: **01/01/2026 UTC ≤ thời gian đăng < 22/10/2026 UTC**; ngày cuối chưa trọn ngày. Nguồn mới: Thời báo Tài chính, Kinh tế - Tài chính Online, Tạp chí Tài chính Tiền tệ, Thiếu Niên Online và Báo Kiểm Toán. Xem [snapshot và checksum](crawl/snapshot_2026-10-21.json), [nguồn từng kênh](crawl/sources_2026-10-21.csv).

Bộ đếm ngày Pacific 21/10 ghi **9.935 lượt thường**, **100 lượt Search** và **5 lượt Batch Stats**. Đây là bộ đếm cục bộ, không phải phép đo quota Cloud. Lượt kiểm tra sâu có checkpoint riêng và không dừng theo trang ngày cũ; trạng thái `quota_exhausted`, đã kiểm tra 9.483 trang và tìm thêm 159 ID ngoài lượt thường. Số trang/request không phải số video mới: các ID đã có và video ngoài năm 2026 bị loại.

Còn **0 ID chờ metadata**; **0 dòng thiếu lượt xem**, **29.762 dòng thiếu lượt thích** được để trống. Không làm mới tương tác cũ. Giữ tiêu đề giống nhau giữa các kênh; cùng kênh/cùng tiêu đề chuẩn hóa giữ video mới nhất. Dashboard và pipeline phân tích chưa chạy lại.

**Snapshot sau lượt dùng nốt quota tối 20/10/2026: 477.023 dòng sạch từ 129 kênh có dữ liệu**, thuộc danh mục 150 kênh. Tăng ròng **167.896 dòng sạch**, thu thêm **171.285 video ID** và thêm 89 nguồn cấu hình so với bộ 309.127 dòng trước lượt này. Tổng dữ liệu gốc: **484.867 video ID**. Xem [snapshot và checksum](crawl/snapshot_2026-10-20_remaining_budget.json), [nguồn và phạm vi từng kênh](crawl/sources_2026-10-20_remaining_budget.csv).

Đã duyệt xong lịch sử của 150 nguồn được chọn từ **01/01/2026 UTC** theo điều kiện dừng của collector. Lượt cập nhật cuối bị ngắt tại nguồn có chỉ số 101/150 khi `playlistItems.list` trả HTTP 403 `quotaExceeded`; Search bổ sung thêm 19 ID rồi trả HTTP 429 do hết hạn mức ngày. Checkpoint được giữ nguyên, không đánh dấu lượt cập nhật là hoàn tất. Giờ đăng thực tế trong CSV từ **01/01/2026 07:00:00** đến **20/10/2026 20:05:10**, giờ Việt Nam; ngày cuối chưa trọn ngày.

Đã lấy thống kê thật cho toàn bộ ID đã thu, gồm 205 ID mới dùng phương thức chính thức `videos.batchGetStats` và hạn mức riêng. Với 205 ID này, tiêu đề/ngày/kênh đến từ uploads hoặc Search; tên tác giả là tên kênh trong danh mục, nguồn được lưu ở cache. **Không thiếu lượt xem hoặc thời điểm đo**; **29.649 dòng thiếu lượt thích** được để trống theo dữ liệu API. Không làm mới chỉ số của video cũ còn hạn cache. Giữ **5.369 nhóm tiêu đề giống nhau giữa nhiều kênh**; ba ID cũ được thay trong CSV bằng video mới hơn cùng tiêu đề/cùng kênh, và toàn bộ 309.127 ID của bộ trước vẫn còn trong dữ liệu gốc. Dashboard, MongoDB và mô hình chưa chạy lại với bộ này.

**Snapshot trước lượt dùng nốt quota ngày 20/10/2026: 309.127 dòng sạch từ 57 kênh có dữ liệu**, thuộc danh mục 61 kênh. Đã thêm **18 kênh** vào cấu hình, thu thêm **59.317 video ID**, tăng ròng **58.885 dòng sạch** so với snapshot 250.242 dòng. Có thêm VietnamPlus, Công Thương, Ninh Bình, Tuyên Quang, Thái Nguyên, Lai Châu, Lạng Sơn, Điện Biên và các nguồn trong [bảng đối chiếu mới](crawl/sources_2026-10-20_expanded.csv).

Khoảng lọc UTC vẫn là **01/01/2026 ≤ thời gian đăng < 21/10/2026**; giờ đăng thực tế trong CSV từ **01/01/2026 07:00:00** đến **20/10/2026 18:40:49**, giờ Việt Nam. Ngày cuối chưa đủ cả ngày. Đã sửa mốc quét của nguồn mới và lấy lại đủ lịch sử từ tháng 1 cho 5 nguồn thêm ở lượt đầu ngày 20/10. Toàn bộ 250.242 ID của CSV trước vẫn được giữ trong dữ liệu gốc. Xem [snapshot, thống kê và checksum](crawl/snapshot_2026-10-20_expanded_sources.json). Dashboard, MongoDB và mô hình chưa chạy lại với bộ mở rộng.

**Snapshot lúc 18:16 ngày 20/10/2026: 250.242 dòng sạch từ 39 kênh có dữ liệu**, trong danh mục 43 kênh. Tăng **2.161 dòng sạch** và **2.187 video ID** so với bộ trước. Đã quét xong lịch sử Cần Thơ về đầu năm và cập nhật video mới của các kênh hiện có; bổ sung dữ liệu từ Đất phương Nam, Yêu quê hương Minh Hải, Báo và phát thanh, truyền hình Cà Mau, Truyền hình Đắk Lắk, Báo và PTTH Cao Bằng. Khi đó 5 nguồn mới chỉ được quét tới mốc cập nhật gần nhất; đợt mở rộng tiếp theo đã lấy nốt lịch sử từ tháng 1. Một liên kết trỏ tới kênh Nguyễn TV không xác minh được chủ thể báo chí đã bị loại khỏi cấu hình, không có dữ liệu trong CSV.

Cửa sổ lọc hiện tại: **01/01/2026 UTC ≤ thời gian đăng < 21/10/2026 UTC**; video mới nhất trong CSV đăng lúc **18:00:38 ngày 20/10/2026, giờ Việt Nam**. Tất cả kênh trong cấu hình đã được duyệt xong theo điều kiện dừng của collector; metadata đã lấy đủ cho các ID đã thu. Xem [snapshot và checksum ngày 20/10](crawl/snapshot_2026-10-20.json), [nguồn và phạm vi từng kênh](crawl/sources_2026-10-20.csv). Dashboard, MongoDB và mô hình chưa chạy lại với bộ này.

**Snapshot sau đợt bổ sung nguồn tối 19/10/2026: 248.081 dòng sạch từ 34 kênh có dữ liệu**, trong danh mục 38 kênh. Thu thêm **21.299 video ID**, tăng ròng **21.081 dòng** so với snapshot 227.000 dòng; video mới nhất đăng lúc **18:44:15 ngày 19/10/2026, giờ Việt Nam**. Toàn bộ 866 lượt còn lại của ngân sách nội bộ đã được dùng, tổng 8.000 lượt trong ngày Pacific 19/10. Đây không phải phép đo quota còn lại trên Google Cloud.

Các nguồn có dữ liệu mới là Báo Hà Nội Mới, Báo Xây dựng, Tây Ninh TV và Cần Thơ mến yêu (liên kết từ website Báo Cần Thơ). **Cần Thơ mới quét tới 24/02/2026**, chưa đủ từ tháng 1; collector dừng theo ngân sách và giữ checkpoint. Metadata đã lấy đủ cho tất cả ID đã thu, CSV có trạng thái `partial_collection` để thể hiện phạm vi nguồn còn thiếu. Xem [nguồn hiện tại và phạm vi từng kênh](crawl/sources_current.csv), [snapshot bổ sung nguồn](crawl/snapshot_2026-10-19_more_channels.json). Dashboard vẫn dùng kết quả phân tích trước.

**Bản mở rộng từ đầu năm, ngày 19/10/2026:** CSV có **227.000 dòng sạch từ 30 kênh**, tăng **118.417 dòng** so với bộ 108.583 dòng trước đợt mở rộng. Đã kiểm tra metadata của **230.779 video ID**, gồm **120.465 ID mới**. Cửa sổ lọc UTC là **01/01/2026 ≤ thời gian đăng < 20/10/2026**; thời điểm thực tế trong CSV là **01/01/2026 07:00:06–19/10/2026 14:51:05, giờ Việt Nam**. Ngày đầu bắt đầu lúc 07:00 vì mốc lọc là UTC; ngày cuối chưa đủ cả ngày. Xem [snapshot từ đầu năm và checksum](crawl/snapshot_2026-10-19_year_to_date.json).

Pipeline đã cấu hình ngày bắt đầu là 01/01/2026. **Dashboard, MongoDB và mô hình chưa được chạy lại với bộ 227.000 dòng**; dùng mục “Phân tích bộ CSV hiện tại” để cập nhật kết quả. Metadata còn hạn của video cũ được giữ nguyên; thời điểm đo views/likes nằm ở từng dòng CSV.

Snapshot ngày 14/10/2026 có **104.790 video từ 30 kênh có dữ liệu**, thuộc danh mục 32 kênh thu thập. Cửa sổ thời gian được lọc theo UTC từ 01/06/2026 tới trước 15/10/2026; dashboard nhóm ngày theo **giờ Việt Nam (UTC+7)**. Ngày cuối là dữ liệu chưa đủ cả ngày.

Snapshot lúc **13:45 ngày 19/10/2026** có **108.570 dòng từ 30 kênh**, tăng ròng **3.780 dòng**; video mới nhất đăng lúc **13:45:10 ngày 19/10/2026, giờ Việt Nam**. Đợt đó thu thêm 3.851 video ID; số dòng sạch tăng ít hơn do giữ một tiêu đề cho mỗi kênh và chọn video mới nhất. Khoảng lọc của snapshot là từ 01/06/2026 tới trước 20/10/2026 UTC. Xem [snapshot trước đợt mở rộng đầu năm](crawl/snapshot_2026-10-19.json).

| Cột | Nội dung |
| --- | --- |
| `video_id`, `video_url` | ID và liên kết video gốc |
| `title` | Tiêu đề đã làm sạch |
| `published_at_utc`, `published_at_vn` | Thời điểm xuất bản theo UTC và giờ Việt Nam |
| `author`, `channel_id` | Tên và ID kênh đăng, không phải tên phóng viên |
| `view_count`, `like_count` | Số tích lũy lúc lấy dữ liệu; số thiếu để trống |
| `metrics_collected_at_utc` | Thời điểm lấy metadata và tương tác |

Giữ video cùng tiêu đề từ **các kênh khác nhau**. Cùng video ID chỉ xuất hiện một lần; cùng kênh và cùng tiêu đề giữ video đăng mới nhất. Không thu mô tả video hoặc bình luận trong dataset hiện tại. Code không đọc các file JSONL của mẫu tìm kiếm cũ để phân tích.

[Quy trình crawl và mã nguồn](crawl/README.md) · [Danh mục nguồn](crawl/sources.csv) · [Snapshot và checksum](crawl/snapshot_2026-10-14.json).

## Kiến trúc

```text
Kênh trong config/youtube_news_channels.json
  → scripts/collect_news_titles.py        playlist uploads, checkpoint
  → scripts/export_news_videos.py         metadata + tương tác + CSV
  → data/exports/youtube_news_videos_clean.csv
  → scripts/upload_raw.sh                 một file CSV trên HDFS
  → src/etl/clean.py                      thống kê + tiêu đề cho mô hình
  → src/eda/statistics.py                 thống kê mô tả
  → src/model/train.py                   Word2Vec + KMeans, LDA
  → src/trend/finalize.py                 chủ đề, ngày, độ phủ kênh, bài minh họa
  → src/export/export_mongo.py
  → MongoDB youtube_news_topics
  → dashboard/app.py
```

Kết quả hiện tại dùng namespace `youtube_news` riêng trên HDFS, trong `reports/`, `models/`, `experiments/` và một database MongoDB riêng. Dashboard và Text Analyzer không sử dụng kết quả đã tạo cho mẫu dữ liệu cũ.

## Khởi động

Cần Docker Desktop chạy Linux containers với WSL2. Chạy từ thư mục gốc project:

```powershell
docker compose -f docker/docker-compose.yml up -d --build
```

Hoặc mở `run.bat` để khởi động Docker/services và tự mở 9 trang trong trình duyệt mặc định: 6 trang dashboard, HDFS NameNode, duyệt dữ liệu HDFS và Spark master. Lần đầu build image tải các thư viện và mô hình nhận diện ngôn ngữ; cần kết nối mạng. `run.bat` không tự huấn luyện lại mô hình mỗi lần mở.

| Thành phần | Địa chỉ local |
| --- | --- |
| Dashboard | http://127.0.0.1:8501 |
| Spark master | http://127.0.0.1:8080 |
| Job của Phân tích văn bản | http://127.0.0.1:4041 (sau khi mở trang Phân tích văn bản) |
| HDFS NameNode | http://127.0.0.1:9870 |
| MongoDB | mongodb://127.0.0.1:27018 |

Trang **Phân tích văn bản** đăng ký application `dashboard-analyzer` trên Spark master và chạy suy luận bằng mô hình đã lưu. Trang Jobs/SQL ở cổng 4041 cho biết các job đã thực hiện; application vẫn ở trạng thái Running trong khi dashboard giữ SparkSession, kể cả khi đã trả kết quả một câu. Mỗi application này giới hạn 2 core, executor 1 GB để còn tài nguyên cho pipeline. Các trang thống kê khác đọc kết quả từ MongoDB, nên chỉ xem biểu đồ không tạo Spark job mới. Spark Master không giữ danh sách application cũ sau khi khởi động lại; phiên bản này chưa có History Server.

## Phân tích bộ CSV hiện tại

Hai lệnh sau đưa CSV hiện tại lên HDFS và chạy trọn pipeline:

```powershell
docker compose -f docker/docker-compose.yml exec namenode sh /scripts/upload_raw.sh
docker compose -f docker/docker-compose.yml exec spark-client sh scripts/run_pipeline.sh
```

Script lần lượt chạy ETL, EDA, huấn luyện Word2Vec + KMeans và LDA trên tập tiêu đề hợp lệ, tổng hợp xu hướng rồi xuất MongoDB. ID mô hình được lấy từ registry của chính dataset mới. Pipeline dừng nếu một bước lỗi; xem thông báo trước khi chạy tiếp. Script chưa có checkpoint huấn luyện: chạy lại từ đầu sẽ tạo lượt thực nghiệm mới.

### Chạy từng bước

```powershell
docker compose -f docker/docker-compose.yml exec spark-client spark-submit src/etl/clean.py
docker compose -f docker/docker-compose.yml exec spark-client spark-submit src/eda/statistics.py
docker compose -f docker/docker-compose.yml exec spark-client spark-submit src/model/train.py --model w2v_kmeans --k 10 --exp NewsFinal --data full --save
docker compose -f docker/docker-compose.yml exec spark-client spark-submit src/model/train.py --model lda --k 10 --exp NewsFinal --data full --save
```

Lấy hai ID đã in ra khi train để tổng hợp:

```powershell
docker compose -f docker/docker-compose.yml exec spark-client spark-submit src/trend/finalize.py --run WORD2VEC_RUN_ID --secondary LDA_RUN_ID
docker compose -f docker/docker-compose.yml exec spark-client python3 -m src.export.export_mongo
```

Sau khi pipeline xong, tải lại dashboard. Các truy vấn được cache; khởi động lại service dashboard nếu cần xem kết quả mới ngay:

```powershell
docker compose -f docker/docker-compose.yml restart dashboard
```

## Quy tắc xử lý và phân tích

- **Thống kê:** giữ toàn bộ video hợp lệ trong CSV, kể cả tiêu đề chưa đủ độ tin cậy tiếng Việt. Không loại kênh chỉ vì đăng nhiều.
- **Huấn luyện:** fastText lid.176 lọc tiêu đề tiếng Việt với độ tin cậy ≥ 0,5; bỏ văn bản quá ngắn sau stopwords. Tiêu đề giống nhau từ các kênh khác nhau vẫn được giữ.
- **Xu hướng:** đếm video theo ngày đăng tại Việt Nam; so sánh tỷ trọng với 7 ngày trước, không sử dụng khung 5 phút của dữ liệu cũ. Tham số ở `config/config.yaml`.
- **Theo ngày/tháng:** có số video, số kênh khác nhau cùng đưa tin, mức thay đổi so với kỳ trước, từ khóa và video đại diện. Nhãn lấy từ video minh họa, cần đối chiếu trước khi coi đó là một sự kiện xác định.
- **Tương tác:** views/likes là số tích lũy tại thời điểm crawl. Không xem chúng là số tương tác trong ngày xuất bản.
- **Trình chiếu:** bộ lọc nội dung nhạy cảm chỉ ảnh hưởng ví dụ và từ hiển thị, không tự loại video khỏi thống kê.

Đây là mẫu theo kênh báo/đài, không đại diện toàn bộ mạng xã hội hoặc dư luận Việt Nam. Một kênh báo/đài có thể đăng thêm chương trình văn hóa, giải trí; chưa có bộ lọc kiểm chứng từng video là thời sự. Ngày/tháng đang thu thập dở không nên so trực tiếp với một kỳ đầy đủ mà không ghi rõ giới hạn.

## Crawl thêm

Lưu `YOUTUBE_API_KEY` trong `.env` hoặc biến môi trường; không đưa key vào Git. Bật YouTube Data API v3 trong Google Cloud. Chạy collector rồi exporter:

```powershell
python scripts/collect_news_titles.py --start 2026-01-01 --end 2026-10-22 --refresh
python scripts/export_news_videos.py
```

`--refresh` bắt đầu đợt cập nhật từ checkpoint đã hoàn tất: giữ thứ tự kênh, cho phép lùi ngày bắt đầu hoặc tăng ngày kết thúc và giữ dữ liệu đã có. Khi lùi ngày bắt đầu, chương trình quét lịch sử tới mốc mới; khi giữ ngày bắt đầu, chỉ quét chồng một ngày ở mốc kết thúc cũ. Nếu bị gián đoạn, bỏ `--refresh` và dùng đúng khoảng ngày đã lưu để tiếp tục. Nối kênh mới vào cuối danh mục. Cache metadata còn hạn được dùng lại trong 30 ngày, vì vậy chỉ lấy views/likes cho video mới hoặc hết hạn cache; số cũ giữ thời điểm trong `metrics_collected_at_utc`. Xem các giới hạn và cách lưu dữ liệu trong [crawl/README.md](crawl/README.md).

## Thư mục quan trọng

```text
crawl/                         Quy trình, bảng nguồn, snapshot của đợt crawl
config/                        Dataset, nguồn, stopwords, tham số mô hình/xu hướng
scripts/                       Collector thời sự, API helper, ingest và lệnh pipeline
src/etl/, src/eda/              Xử lý CSV và thống kê Spark
src/model/, src/trend/          Huấn luyện, đánh giá và phân tích thời gian
src/export/                    Xuất kết quả nhỏ sang MongoDB
dashboard/                     Dashboard Streamlit
data/exports/                  CSV đầu vào, không đưa vào Git
data/raw/youtube/               Dữ liệu và checkpoint collector, không dùng trực tiếp cho ETL
reports/youtube_news/           Báo cáo và kết quả tổng hợp dataset mới
models/youtube_news/            Mô hình phục vụ Text Analyzer
experiments/youtube_news/       Registry và kết quả thực nghiệm dataset mới
tests/                         Kiểm tra các thuật toán dùng chung
```

API key, dataset, checkpoint, cache và mô hình được `.gitignore` loại khỏi Git. Dữ liệu thu thập cũ trên máy không bị xóa bởi việc đổi nguồn phân tích; chúng không được ingest vào pipeline mới.
