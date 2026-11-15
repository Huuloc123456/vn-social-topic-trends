# Quy trình crawl dataset YouTube thời sự Việt Nam

## Đợt mở rộng từ đầu năm 2025 — đang chạy

Bắt đầu ngày 24/10/2026, từ bộ 479.416 dòng CSV và 487.326 video ID. Cửa sổ lọc UTC là **01/01/2025 ≤ thời gian đăng < 25/10/2026**; dữ liệu chỉ có tới thời điểm API trả về. Dùng lại 155 nguồn đã chọn, giữ ID cũ và tiêu đề giống nhau giữa các kênh. Lượt này giới hạn 6.500 trang uploads để dành phần ngân sách ngày cho metadata; có thể phải tiếp tục checkpoint sau kỳ quota khác.

Tiến trình nền tự lấy metadata và xuất lại `data/exports/youtube_news_videos_clean.csv` sau khi quét dừng. Nếu không đủ metadata, xuất các ID đã thu với ô thống kê thiếu để trống và ghi số lượng thiếu trong manifest. Trạng thái tổng hợp: `reports/youtube_2025_extension_run.json`; log uploads: `reports/crawl_2025_extension_2026-10-24.log`. Bản sao trước lượt này nằm trong thư mục ghi tại trường `backup` của báo cáo tổng hợp. Checkpoint kiểm tra sâu cũ chỉ dành cho năm 2026 đã được lưu cùng bản sao, không tái sử dụng cho cửa sổ 2025.

**Chỉ chạy tiếp sau khi tiến trình nền hiện tại đã kết thúc**, dùng đúng cửa sổ và không thêm `--refresh`:

```powershell
python -X utf8 scripts/collect_news_titles.py --start 2025-01-01 --end 2026-10-25 --max-pages 5000
python -X utf8 scripts/export_news_videos.py
```

Các snapshot dưới đây mô tả những lượt đã kết thúc trước đợt mở rộng; dashboard và pipeline phân tích chưa chạy lại.

Thư mục này lưu cách thu thập, nguồn dữ liệu và thông tin đối chiếu của các đợt crawl từ **14–21/10/2026**. Mã Python đang dùng được liên kết ở phần dưới; thông tin trong tài liệu mô tả cách chương trình thực sự chạy.

**CSV sau lượt crawl ngày 21/10/2026: 479.416 dòng sạch từ 134 kênh có dữ liệu**, trong danh mục 155 nguồn; tăng ròng **2.393 dòng**, thu thêm **2.459 video ID** so với bộ 477.023 dòng. Cửa sổ lọc: **01/01/2026 UTC ≤ thời gian đăng < 22/10/2026 UTC**; ngày cuối chưa trọn ngày. Nguồn mới: Thời báo Tài chính, Kinh tế - Tài chính Online, Tạp chí Tài chính Tiền tệ, Thiếu Niên Online và Báo Kiểm Toán. Xem [snapshot và checksum](snapshot_2026-10-21.json), [nguồn từng kênh](sources_2026-10-21.csv).

Bộ đếm ngày Pacific 21/10 ghi **9.935 lượt thường**, **100 lượt Search** và **5 lượt Batch Stats**. Đây là bộ đếm cục bộ, không phải phép đo quota Cloud. Lượt kiểm tra sâu có checkpoint riêng và không dừng theo trang ngày cũ; trạng thái `quota_exhausted`, đã kiểm tra 9.483 trang và tìm thêm 159 ID ngoài lượt thường. Số trang/request không phải số video mới: các ID đã có và video ngoài năm 2026 bị loại.

Còn **0 ID chờ metadata**; **0 dòng thiếu lượt xem**, **29.762 dòng thiếu lượt thích** được để trống. Không làm mới tương tác cũ. Giữ tiêu đề giống nhau giữa các kênh; cùng kênh/cùng tiêu đề chuẩn hóa giữ video mới nhất. Dashboard và pipeline phân tích chưa chạy lại.

**Snapshot sau lượt dùng nốt quota tối 20/10/2026: 477.023 dòng sạch từ 129 kênh có dữ liệu**, thuộc danh mục 150 kênh. Tăng ròng **167.896 dòng sạch**, thu thêm **171.285 video ID** và thêm 89 nguồn cấu hình so với bộ 309.127 dòng trước lượt này. Tổng dữ liệu gốc: **484.867 video ID**. Xem [snapshot và checksum](snapshot_2026-10-20_remaining_budget.json), [nguồn và phạm vi từng kênh](sources_2026-10-20_remaining_budget.csv).

Đã duyệt xong lịch sử của 150 nguồn được chọn từ **01/01/2026 UTC** theo điều kiện dừng của collector. Lượt cập nhật cuối bị ngắt tại nguồn có chỉ số 101/150 khi `playlistItems.list` trả HTTP 403 `quotaExceeded`; Search bổ sung thêm 19 ID rồi trả HTTP 429 do hết hạn mức ngày. Checkpoint được giữ nguyên, không đánh dấu lượt cập nhật là hoàn tất. Giờ đăng thực tế trong CSV từ **01/01/2026 07:00:00** đến **20/10/2026 20:05:10**, giờ Việt Nam; ngày cuối chưa trọn ngày.

Đã lấy thống kê thật cho toàn bộ ID đã thu, gồm 205 ID mới dùng phương thức chính thức `videos.batchGetStats` và hạn mức riêng. Với 205 ID này, tiêu đề/ngày/kênh đến từ uploads hoặc Search; tên tác giả là tên kênh trong danh mục, nguồn được lưu ở cache. **Không thiếu lượt xem hoặc thời điểm đo**; **29.649 dòng thiếu lượt thích** được để trống theo dữ liệu API. Không làm mới chỉ số của video cũ còn hạn cache. Giữ **5.369 nhóm tiêu đề giống nhau giữa nhiều kênh**; ba ID cũ được thay trong CSV bằng video mới hơn cùng tiêu đề/cùng kênh, và toàn bộ 309.127 ID của bộ trước vẫn còn trong dữ liệu gốc. Dashboard, MongoDB và mô hình chưa chạy lại với bộ này.

### Quota và trạng thái cuối lượt này

- Bộ đếm cục bộ ghi 9.772 lượt thuộc nhóm thường, 99 lượt Search và 5 lượt Batch Stats trong ngày Pacific 20/10. Chúng không phải phép đo quota thực tế của project. API đã từ chối một truy vấn uploads và một truy vấn Search vì hạn mức ngày; không gọi lại các nhóm đó để thăm dò quota.
- Cloud từng hiển thị 9.771/10.000 truy vấn thường và 64/100 Search trước lượt Search bổ sung; giao diện có thể cập nhật chậm. Không suy ra còn lượt dùng được từ chênh lệch với bộ đếm. Quan sát và lỗi thật nằm trong `reports/youtube_cloud_quota_observation_2026-10-20.json`, `reports/youtube_quota_exhausted_2026-10-20.json`.
- Google ghi nhận Search có hạn mức riêng: [search.list](https://developers.google.com/youtube/data/reference/rest/v3/search/list). `videos.batchGetStats` chỉ lấy thống kê theo ID đã biết: [tài liệu phương thức](https://developers.google.com/youtube/data/reference/rest/v3/videos/batchGetStats). Quota thống kê còn lại không cung cấp thêm ID hoặc tiêu đề mới.
- Lịch sử các nguồn đã duyệt xong trước lượt cập nhật cuối; bằng chứng ở `reports/youtube_history_complete_before_final_refresh_2026-10-20.json`. `collection_complete` và `last_refresh_complete` trong bảng nguồn nói về lượt uploads cập nhật cuối; `history_collection_complete` nói riêng về lượt lịch sử từ tháng 1. Search bổ sung không tiến checkpoint uploads.
- `reports/youtube_channel_search_state.json` lưu truy vấn và bộ đếm Search; `reports/youtube_news_search_tail_state.json` lưu kênh đã kiểm tra và 19 ID bổ sung. Search có thể chậm lập chỉ mục hoặc trả kết quả thiếu, vì vậy không thay thế việc duyệt uploads.
- `reports/youtube_batch_stats_state.json` và `reports/youtube_batch_stats_responses.jsonl` lưu bộ đếm cùng phản hồi thống kê thật. Nguồn của metadata ghép được lưu tại `metadata_source` trong cache; không ghi dữ liệu giả hoặc số 0 thay cho ô thiếu.

### Tiếp tục và xuất dữ liệu khi hết quota

Sau kỳ cấp lại theo lịch Google, tiếp tục checkpoint hiện tại bằng **cùng cửa sổ ngày**, không thêm `--refresh`:

```powershell
python -X utf8 scripts/collect_news_titles.py --start 2026-01-01 --end 2026-10-21
python -X utf8 scripts/export_news_videos.py
```

Để mở rộng ngày kết thúc, cần hoàn tất lượt đang dở trước rồi mới chạy lượt `--refresh` với ngày kết thúc mới. Chương trình giữ nguyên page token/chỉ số nguồn khi ngắt.

Xuất CSV hoàn toàn từ dữ liệu đã lưu, không gọi API:

```powershell
python -X utf8 scripts/export_news_videos.py --cached-only
```

Nếu còn ID chưa có metadata, chế độ này dùng tiêu đề/ngày/kênh đã thu, tên kênh trong danh mục, để trống lượt xem/thích và thời điểm đo; manifest có trạng thái `partial_metadata`. Phần điền tạm không được ghi vào cache API. Lượt này đã lấy đủ thống kê cho mọi ID nên không còn dòng chờ metadata; trạng thái `partial_collection` chỉ phản ánh lượt cập nhật uploads còn dở.

Có thể dùng phương thức thống kê chính thức cho **chỉ ID chưa có cache còn hạn**, không cập nhật video cũ:

```powershell
python -X utf8 scripts/complete_pending_news_stats.py
python -X utf8 scripts/export_news_videos.py --cached-only
```

`collect_news_search_tail.py` bổ sung video mới của danh mục nguồn bằng phần Search còn lại; không thêm nguồn lạ và không thay đổi checkpoint uploads. Lượt ngày 20/10 đã gặp lỗi quota Search nên không chạy lại trong cùng ngày. Nguồn Python của hai lệnh bổ sung nằm trong thư mục `scripts/`.

Các bản CSV trước khi dùng nốt quota và trước lần xuất offline nằm trong `reports/crawl_backups/2026-10-20_185714_use_remaining/` và `reports/crawl_backups/2026-10-20_before_offline_quota_export/`. Các snapshot cũ bên dưới được giữ nguyên để đối chiếu.

**Snapshot trước lượt dùng nốt quota ngày 20/10/2026:** **313.582 video ID**, **309.127 dòng CSV sạch từ 57 kênh có dữ liệu**, trong danh mục 61 kênh. So với snapshot 250.242 dòng: thêm 18 kênh cấu hình, 59.317 video ID và 58.885 dòng sạch. Đã quét xong các nguồn được chọn về mốc tháng 1/2026 theo điều kiện dừng của collector, lấy đủ metadata cho tất cả ID đã thu; trạng thái collector và CSV là `complete`.

Đã sửa lỗi nguồn mới kế thừa mốc quét tăng thêm: 5 nguồn thêm ở lượt đầu ngày 20/10 được đưa lại về chỉ số 38 trong checkpoint và quét về 01/01/2026; giữ các ID đã có. Các lần nối nguồn tiếp theo tự đặt `scan_start` về ngày bắt đầu dataset. Các nguồn mới khác gồm Công Thương, Ninh Bình, Tuyên Quang, Sơn La, Lai Châu, Lạng Sơn, Báo Thanh Hóa, Báo Nghệ An, VietnamPlus, Thái Nguyên, ATV Kết nối yêu thương, Đầu tư Online, Đầu tư Chứng khoán, Thông tin Chính phủ, Điện Biên, Truyền hình Sơn La, Hưng Yên, LTV - Stories. Tên kênh và phạm vi thực tế nằm trong [sources_2026-10-20_expanded.csv](sources_2026-10-20_expanded.csv).

Thời điểm đăng trong CSV từ **01/01/2026 07:00:00** tới **20/10/2026 18:40:49**, giờ Việt Nam; mốc lọc là UTC, ngày cuối chưa trọn ngày. Không thiếu lượt xem; **25.386 dòng thiếu lượt thích** để trống. Giữ **2.539 nhóm tiêu đề giống nhau ở nhiều kênh**. Toàn bộ 250.242 ID của CSV trước vẫn còn trong dữ liệu gốc. Chỉ lấy metadata cho ID mới; không làm mới tương tác của các video còn hạn cache.

Xem [snapshot_2026-10-20_expanded_sources.json](snapshot_2026-10-20_expanded_sources.json) để đối chiếu checksum, số liệu và bộ đếm gọi API. Đợt này ghi nhận tổng **2.602 lượt gọi** trong ngày Pacific 20/10, còn **5.398 lượt** trước ngưỡng nội bộ 8.000; không phải phép đo quota còn lại trên Google Cloud. Pipeline phân tích và dashboard chưa chạy lại với bộ mở rộng.

**Snapshot lúc 18:16 ngày 20/10/2026:** **254.265 video ID**, **250.242 dòng CSV sạch từ 39 kênh có dữ liệu** trong danh mục 43 kênh. Tăng **2.187 ID** và **2.161 dòng sạch** so với bộ trước. Phần lịch sử Cần Thơ trước 24/02 đã được lấy nốt (586 ID), sau đó cập nhật các kênh hiện có đến ngày 20/10 và bổ sung 500 ID từ 5 kênh mới. Metadata được lấy cho tất cả ID mới; dữ liệu tương tác còn hạn của video cũ giữ nguyên cùng thời điểm đo. Các nguồn mới trong snapshot này mới được quét tới mốc cập nhật gần nhất; bản mở rộng phía trên đã hoàn tất phần lịch sử còn thiếu của chúng.

Nguồn mới có dòng sạch: Đất phương Nam (100), Yêu quê hương Minh Hải (99), Báo và phát thanh, truyền hình Cà Mau (100), Truyền hình Đắk Lắk (98), Báo và PTTH Cao Bằng (100). Các liên kết nguồn được đối chiếu từ website báo/đài rồi lấy ID và uploads playlist qua API. Liên kết tới Nguyễn TV không đủ bằng chứng chủ thể báo chí đã bị loại, không đưa dữ liệu vào CSV. Kênh không trả về kết quả từ API không được thêm chỉ dựa theo tên.

Cửa sổ hiện tại là **2026-01-01 00:00:00 UTC ≤ thời gian đăng < 2026-10-21 00:00:00 UTC**; video mới nhất đăng lúc **18:00:38 ngày 20/10/2026, giờ Việt Nam**. Collector và metadata đã hoàn tất (`complete`) cho các nguồn được chọn, không còn checkpoint lịch sử Cần Thơ đang dở. Xem [sources_2026-10-20.csv](sources_2026-10-20.csv), [snapshot_2026-10-20.json](snapshot_2026-10-20.json). Danh sách hiện tại cũng được chép sang `sources_current.csv`; bản ngày 19/10 được giữ ở `sources_2026-10-19.csv`. Pipeline phân tích và dashboard chưa chạy lại.

**Bản mới nhất sau khi dùng nốt ngân sách ngày 19/10/2026:** **252.078 video ID**, **248.081 dòng CSV sạch từ 34 kênh có dữ liệu** trong danh mục 38 kênh. Đợt bổ sung nguồn thu thêm **21.299 ID**, tăng ròng **21.081 dòng** so với snapshot 227.000 dòng. Nguồn có dữ liệu mới: Báo Hà Nội Mới (1.658 dòng), Báo Xây dựng (5.298), Tây Ninh TV (11.726), Cần Thơ mến yêu (2.399). Các kênh mới được xác định bằng liên kết YouTube trên website cơ quan báo chí rồi lấy channel ID/uploads playlist từ `channels.list`; không suy đoán kênh chỉ theo tên hiển thị. Tọa đàm VnExpress và Báo Lâm Đồng không trả về video trong cửa sổ năm 2026 đã chọn.

Đã dùng **866 lượt gọi còn lại**: tổng bộ đếm trong ngày Pacific 19/10 là **8.000** (collector và xác định kênh: 5.163; metadata: 2.837). **Không làm mới metadata của video đã có** trong đợt này. Đã lấy đủ metadata cho 252.078 ID, không thiếu lượt xem; 25.159 dòng thiếu lượt thích được để trống. Giữ 2.204 nhóm tiêu đề trùng giữa nhiều kênh. Video mới nhất đăng lúc **18:44:15 ngày 19/10/2026, giờ Việt Nam**.

**Phạm vi chưa hoàn tất:** Cần Thơ mến yêu mới quét từ **24/02/2026 20:54:36** tới 19/10/2026, giờ Việt Nam; chưa đủ từ tháng 1. Collector có trạng thái `budget_limited`, CSV có trạng thái `partial_collection`. Sau kỳ quota tiếp theo, tiếp tục với cùng khoảng `--start 2026-01-01 --end 2026-10-20` và **không** dùng `--refresh`, rồi chạy exporter. Đây là ngưỡng ngân sách của chương trình; không phải xác nhận quota còn lại thực tế trên Cloud. Pipeline phân tích và dashboard chưa chạy lại.

Xem [sources_current.csv](sources_current.csv) để đối chiếu URL nguồn, ID kênh, số dòng và phạm vi từng kênh; [snapshot_2026-10-19_more_channels.json](snapshot_2026-10-19_more_channels.json) lưu thống kê và checksum. Các snapshot cũ bên dưới được giữ nguyên để đối chiếu.

**Bản mở rộng từ đầu năm ngày 19/10/2026:** tổng **230.779 video ID** và **227.000 dòng CSV sạch từ 30 kênh**; thu thêm **120.465 ID**, tăng ròng **118.417 dòng** so với bộ 108.583 dòng trước đợt mở rộng. Đã quét đủ 32 kênh trong cấu hình, 2 kênh không trả về video trong cửa sổ đã chọn. Mốc lọc là **2026-01-01 00:00:00 UTC ≤ thời gian đăng < 2026-10-20 00:00:00 UTC**. Giờ đăng thực tế trong CSV từ **01/01/2026 07:00:06** đến **19/10/2026 14:51:05**, giờ Việt Nam; ngày đầu bắt đầu lúc 07:00 do mốc UTC, ngày cuối chưa đủ cả ngày.

Giữ **1.519 nhóm tiêu đề giống nhau giữa nhiều kênh**. Không thiếu lượt xem; **25.158 dòng thiếu lượt thích** được để trống. Toàn bộ 108.583 video ID của CSV trước vẫn có trong dữ liệu gốc. Bản trước khi mở rộng nằm ở `reports/crawl_backups/2026-10-19_140831_before_january/`. Snapshot cố định và checksum mới: [snapshot_2026-10-19_year_to_date.json](snapshot_2026-10-19_year_to_date.json). Mốc bắt đầu trong cấu hình phân tích đã đổi sang 01/01/2026; mô hình, HDFS phân tích và MongoDB/dashboard chưa được chạy lại.

**Cập nhật 19/10/2026:** thu thêm **3.851 video ID**, tổng **110.300 ID**; CSV sạch có **108.570 dòng từ 30 kênh**, tăng ròng **3.780 dòng**. Giữ **975 nhóm tiêu đề trùng giữa các kênh**; thiếu lượt thích ở 13.520 dòng, không thiếu lượt xem. Video mới nhất đăng lúc **13:45:10 ngày 19/10/2026, giờ Việt Nam**. Mốc kết thúc mới là trước 20/10/2026 UTC; ngày cuối chưa đủ cả ngày. Metadata mới được lấy ngày 19/10; metadata còn hạn của video cũ được dùng lại từ 14/10. Xem [snapshot_2026-10-19.json](snapshot_2026-10-19.json). Bảng ở mục 1 và `sources.csv` bên dưới vẫn mô tả riêng snapshot 14/10.

## 1. Kết quả của đợt crawl

| Thông tin | Kết quả |
| --- | ---: |
| Kênh trong cấu hình thu thập | 32 |
| Kênh có dữ liệu trong CSV | 30 |
| Video ID thu thập được | 106.449 |
| Dòng CSV sau làm sạch, không tính header | 104.790 |
| Nhóm tiêu đề giống nhau xuất hiện ở nhiều kênh và được giữ lại | 933 |
| Dòng thiếu lượt xem | 0 |
| Dòng thiếu lượt thích, để ô trống | 12.896 |

Khoảng lọc là **2026-06-01 00:00:00 UTC ≤ thời gian đăng < 2026-10-15 00:00:00 UTC**. Theo giờ Việt Nam, mốc bắt đầu là **01/06/2026 lúc 07:00**, mốc kết thúc cấu hình là **15/10/2026 lúc 07:00**; dữ liệu thực tế chỉ đến thời điểm crawl ngày 14/10, không có dữ liệu tương lai.

Số lượt xem/thích được lấy trong khoảng **14:08:04–14:11:27 ngày 14/10/2026, giờ Việt Nam**. Đây là số tích lũy tại lúc gọi API, không phải số tương tác trong ngày video được đăng. Thông tin chính xác tới phần giây và mã SHA-256 của CSV nằm trong [snapshot_2026-10-14.json](snapshot_2026-10-14.json). Snapshot này là bản ghi cố định; kết quả các lần chạy sau nằm trong `reports/youtube_news_videos_manifest.json`.

## 2. Mã nguồn và danh sách nguồn

| File | Vai trò |
| --- | --- |
| [collect_news_titles.py](../scripts/collect_news_titles.py) | Duyệt playlist uploads của từng kênh, lọc ngày, lưu video ID, tiêu đề và checkpoint |
| [export_news_videos.py](../scripts/export_news_videos.py) | Lấy metadata, lượt xem/thích, làm sạch và xuất CSV |
| [youtube_api.py](../scripts/youtube_api.py) | Hai hàm dùng chung `load_key()` và `get_json()`, đọc key và gọi API |
| [youtube_news_channels.json](../config/youtube_news_channels.json) | Cấu hình kênh thật sự được chương trình đọc |
| [sources.csv](sources.csv) | Bảng nguồn của đợt này: tên kênh, channel ID, URL YouTube, uploads playlist, đường dẫn đối chiếu nếu đã ghi nhận, số dòng CSV |

Các kênh gồm báo và đài như Lao Động, Nhân Dân, Thanh Niên, Tuổi Trẻ, VietNamNet, VOV, VTV24, ANTV, Nghệ An, Đồng Tháp, THVL và các nguồn khác trong bảng. Đây là **danh sách kênh đã chọn**, không phải danh mục đầy đủ mọi kênh thời sự Việt Nam.

Khi bổ sung nguồn, đối chiếu liên kết trên website báo/đài hoặc cơ quan chủ quản với channel ID trả về từ API. Không dùng tên thương hiệu trong tiêu đề video làm bằng chứng vì kênh khác có thể đăng lại. Trường `verification_reference` trong `sources.csv` được sao từ `verified_from` trong cấu hình; 14 mục nguồn cũ chưa lưu đường dẫn này. Ô trống nghĩa là cấu hình chưa ghi lại bằng chứng, không phải một kết quả xác minh mới. Đường dẫn có thể đổi hoặc không còn truy cập được.

Ở lượt bổ sung tối 20/10, một số liên kết cũ đã đổi handle hoặc chuyển tên sau khi hợp nhất báo/đài. Với URL do website cơ quan báo chí dẫn tới, đọc URL canonical của chính trang kênh để xác định ID; không lấy ID của video được đề xuất. Một số nguồn khác được đối chiếu qua huy hiệu xác minh của YouTube, tên và thông tin liên hệ của cơ quan trong hồ sơ kênh. Các danh sách tài khoản báo chí/đài được sao lại trên website khác chỉ là nguồn tìm liên kết, không phải xác nhận mới của cơ quan quản lý. Kênh đổi sang chủ thể khác, hồ sơ không còn nhận là cơ quan báo chí hoặc không đủ thông tin được loại khỏi lượt bổ sung.

Bảng `sources_current.csv` bổ sung `verification_note` và `locator_reference` để phân biệt liên kết trực tiếp từ website báo/đài, kênh có huy hiệu xác minh và các trường hợp dùng danh mục cũ kết hợp hồ sơ hiện tại. Không coi tất cả các hàng là đã được website cơ quan chủ quản xác nhận lại. Các bản bảng nguồn cố định trước đó được giữ nguyên.

Các kênh được chọn có thể có tin địa phương, tin quốc tế, văn hóa, thể thao, sức khỏe và chương trình chuyên đề. VTV5 có tiêu đề tiếng Việt cho các chương trình phát bằng tiếng dân tộc; tiền tố ngôn ngữ được giữ nguyên. Số video là số mục xuất bản trong mẫu, không phải số sự kiện độc lập hoặc số người quan tâm. Nhiều kênh có thể cùng thuộc một cơ quan báo chí.

## Kiểm tra sâu toàn bộ playlist uploads

Từ 21/10/2026, có thêm lệnh kiểm tra giả định dừng theo trang ngày cũ của collector thường:

```powershell
python -X utf8 scripts/scan_all_news_uploads.py
```

Lệnh này đọc cửa sổ ngày từ checkpoint thường đã hoàn tất, duyệt các nguồn luân phiên, không dừng khi gặp trang có video đăng trước năm 2026. Chỉ video ID chưa có và thời gian đăng nằm trong cửa sổ đã chọn mới được thêm; không tải nội dung video, không làm mới lượt xem/thích cũ. Vì nhiều trang chỉ có video đã thu hoặc ngoài cửa sổ ngày, số request có thể lớn hơn nhiều so với số ID thêm được.

Checkpoint riêng: `data/raw/youtube/news_titles_full_scan_state.json`, gồm page token và trạng thái từng nguồn. Khi dừng do quota, lần chạy sau tiếp tục các trang đang dở. Trạng thái của lượt kiểm tra sâu độc lập với trạng thái lượt cập nhật thường; một lượt thường `complete` không có nghĩa mọi trang lịch sử đã được kiểm tra.

`recorded_regular_calls()` trong collector cộng chung bộ đếm của lượt thường, lấy metadata/đối chiếu nguồn và kiểm tra sâu. Search và Batch Stats có bộ đếm riêng. Đây là kế toán request cục bộ, không thay thế phản hồi quota thực tế từ Google. Bộ kiểm tra sâu giới hạn đồng thời và nhịp gửi, ngừng cấp request mới khi nhận lỗi quota; các request đã gửi có thể hoàn tất sau lỗi đầu tiên.

Sau lượt kiểm tra sâu, lấy thống kê thật cho các ID mới còn thiếu bằng `complete_pending_news_stats.py`, rồi xuất CSV bằng `export_news_videos.py --cached-only`. Những ID không có phản hồi thống kê hợp lệ vẫn để trống và được ghi rõ trong manifest. Pipeline phân tích và dashboard không được tự chạy lại.

## 3. Crawl bằng cách nào?

### Bước A — Xác định kênh và uploads playlist

Trong giai đoạn chọn nguồn, gọi `channels.list` theo channel ID, handle hoặc username để lấy tên kênh và `contentDetails.relatedPlaylists.uploads`. Kết quả được lưu vào cấu hình; mỗi lần chạy collector không cần tìm lại kênh. Tham số và cấu trúc API được mô tả trong [tài liệu channels.list của Google](https://developers.google.com/youtube/v3/docs/channels/list).

### Bước B — Duyệt video của từng kênh

`collect_news_titles.py` gọi `playlistItems.list` theo uploads playlist:

```text
GET https://www.googleapis.com/youtube/v3/playlistItems
part=snippet,contentDetails
playlistId=<UPLOADS_PLAYLIST_ID>
maxResults=50
fields=nextPageToken,items(snippet/title,contentDetails/videoId,contentDetails/videoPublishedAt)
pageToken=<NEXT_PAGE_TOKEN>  # bỏ ở trang đầu
```

Mỗi trang tối đa 50 mục; nếu còn trang tiếp theo thì đọc `nextPageToken` để tiếp tục. Collector đi tuần tự từng kênh, loại video ID đã có và chỉ giữ video trong khoảng ngày đã chọn. Dùng `contentDetails.videoPublishedAt` làm thời gian video xuất bản, không lấy thời gian thêm video vào playlist. Xem [tài liệu playlistItems.list của Google](https://developers.google.com/youtube/v3/docs/playlistItems/list).

Sau mỗi trang, lưu dữ liệu vào JSONL rồi lưu checkpoint gồm chỉ số kênh và page token. Chương trình dừng một kênh khi hết trang hoặc khi cả trang có ngày đăng đều cũ hơn ngày bắt đầu. **Giả định hiện tại: uploads được sắp từ mới đến cũ**; nếu kênh thay đổi thứ tự hoặc đưa lại video cũ vào playlist, điều kiện dừng này có thể bỏ sót video.

### Bước C — Lấy thời gian, kênh và tương tác

`export_news_videos.py` gom các video ID từ JSONL thành nhóm 50 ID rồi gọi:

```text
GET https://www.googleapis.com/youtube/v3/videos
part=snippet,statistics
id=<VIDEO_ID_1>,<VIDEO_ID_2>,...
fields=items(id,snippet/title,snippet/publishedAt,snippet/channelId,snippet/channelTitle,statistics/viewCount,statistics/likeCount)
```

Có tối đa 4 yêu cầu đang chạy đồng thời. Mỗi nhóm thành công được lưu vào cache, kèm thời điểm nhận phản hồi. CSV dùng tiêu đề, ngày xuất bản và tên kênh từ phản hồi này; metadata có thể khác bản JSONL nếu chủ kênh đã sửa tiêu đề. Ý nghĩa các trường được mô tả trong [tài liệu videos của Google](https://developers.google.com/youtube/v3/docs/videos); phương thức gọi trong [videos.list](https://developers.google.com/youtube/v3/docs/videos/list).

Cache còn hạn được dùng lại trong 30 ngày; gọi lại exporter ngay sau đợt này sẽ xuất lại CSV mà không gọi API thêm. Muốn cập nhật lượt xem/thích ngay cần chủ động làm mới cache, không chỉ chạy lại lệnh. Cơ chế hết hạn hiện tại chỉ bỏ qua bản cache cũ khi đọc, không tự xóa mọi bản cũ khỏi ổ đĩa.

Dataset CSV này sử dụng API công khai có API key. Luồng thu thập này không dùng trình duyệt Playwright, không lấy HTML/GraphQL để thu nội dung video và không thu bình luận hay mô tả video.

### Bước D — Làm sạch và xuất

1. Chuẩn hóa Unicode NFC, giải mã HTML entity, gộp khoảng trắng; bỏ BOM, zero-width space và ký tự điều khiển không cần thiết. Giữ nội dung, dấu tiếng Việt, chữ hoa/thường và emoji của tiêu đề.
2. Loại video không còn trả về metadata hoặc thiếu tiêu đề, thời gian đăng, tên kênh; loại kênh ngoài cấu hình và video ngoài khoảng ngày.
3. Đảm bảo một dòng cho một `video_id`.
4. So sánh tiêu đề sau làm sạch bằng `casefold()`. Nếu **cùng kênh và cùng tiêu đề**, giữ video có thời gian đăng mới nhất; nếu thời gian bằng nhau, chọn theo video ID để kết quả ổn định.
5. Nếu **khác kênh nhưng cùng tiêu đề**, giữ các dòng riêng biệt. Tiêu đề khác nhau nhưng nói cùng sự kiện chưa được gom thành một vấn đề bằng bước làm sạch này.
6. Chuyển thời gian UTC sang `Asia/Ho_Chi_Minh` (UTC+7). Lượt xem/thích thiếu giữ ô trống; giá trị 0 thật giữ nguyên 0. Không sinh nhãn chủ đề, không suy đoán tác giả cá nhân hoặc điền số tương tác ước lượng.
7. Sắp theo giờ xuất bản, kênh và video ID; ghi CSV UTF-8 có BOM bằng `csv.DictWriter`. Đọc lại để kiểm tra trước khi thay file xuất chính. Nếu lấy metadata bị lỗi, giữ CSV cũ và các nhóm đã lưu trong cache để tiếp tục.

## 4. Các cột CSV

| Cột | Ý nghĩa |
| --- | --- |
| `video_id` | ID video YouTube |
| `title` | Tiêu đề video đã làm sạch |
| `published_at_utc` | Giờ xuất bản theo UTC từ `snippet.publishedAt` |
| `published_at_vn` | Cùng thời điểm, chuyển sang giờ Việt Nam |
| `author` | Tên kênh đăng từ `snippet.channelTitle`, không phải tên phóng viên |
| `channel_id` | ID kênh đăng |
| `video_url` | Link `https://www.youtube.com/watch?v=<video_id>` |
| `view_count` | Lượt xem tích lũy khi lấy metadata |
| `like_count` | Lượt thích tích lũy khi lấy metadata; có thể trống |
| `metrics_collected_at_utc` | Thời điểm lấy metadata/tương tác theo UTC |

## 5. Dữ liệu lưu ở đâu?

```text
config/youtube_news_channels.json              Cấu hình nguồn đang dùng
scripts/collect_news_titles.py                 Source collector
scripts/export_news_videos.py                  Source metadata và CSV
data/raw/youtube/news_title_records.jsonl       Video ID, tiêu đề, kênh, ngày đăng
data/raw/youtube/news_titles_state.json         Checkpoint collector
reports/youtube_news_video_details.jsonl        Cache metadata và tương tác
reports/youtube_news_details_state.json         Bộ đếm gọi API metadata
reports/youtube_news_titles_manifest.json       Tổng hợp dữ liệu gốc
reports/youtube_news_videos_manifest.json       Tổng hợp CSV hiện tại
data/exports/youtube_news_videos_clean.csv      Dataset CSV dùng để phân tích
crawl/README.md                                Tài liệu này
crawl/sources.csv                              Bảng nguồn tại đợt crawl
crawl/snapshot_2026-10-14.json                   Thống kê và checksum cố định
```

`youtube_news_titles_clean.txt` là bản xem nhanh lịch sử; collector hiện tại không xuất lại TXT. Pipeline chỉ dùng **CSV** cho phân tích theo thời gian và độ phủ qua nhiều kênh.

`.env`, raw data, CSV dataset và cache trong `reports/` được `.gitignore` loại khỏi Git. Thư mục `crawl/` chứa tài liệu, danh mục nguồn và thống kê nhỏ, không chứa API key hoặc toàn bộ nội dung video.

## 6. Cách chạy lại

Chạy từ thư mục gốc project. Bật YouTube Data API v3 trong Google Cloud, hạn chế API key cho API này và lưu key trong `.env`:

```dotenv
YOUTUBE_API_KEY=<API_KEY_CUA_BAN>
```

Hai script sử dụng thư viện chuẩn Python và timezone database. Nếu môi trường Windows báo thiếu timezone, cài `tzdata` bằng `python -m pip install tzdata`.

```powershell
python scripts/collect_news_titles.py --start 2026-01-01 --end 2026-10-21 --refresh
python scripts/export_news_videos.py
```

API key được đọc từ biến môi trường hoặc `.env`, gửi trong header `X-Goog-Api-Key`; mã không ghi key vào URL, checkpoint, cache hay CSV. Hàm HTTP đặt timeout 30 giây. Collector/exporter thử lại tối đa 3 lần cho lỗi mạng hoặc HTTP 500/502/503/504, đợi 2 rồi 4 giây giữa các lần; lỗi khác sẽ dừng.

`--refresh` chỉ dùng khi checkpoint đã hoàn tất, giữ thứ tự nguồn, cho phép ngày bắt đầu bằng hoặc sớm hơn và ngày kết thúc bằng hoặc muộn hơn lần trước. Nếu lùi ngày bắt đầu, collector quét lịch sử từng kênh tới mốc mới; nếu giữ ngày bắt đầu, chỉ quét chồng một ngày ở mốc kết thúc cũ để lấy phần ngày chưa đủ. Dữ liệu gốc được nối thêm và loại trùng theo video ID. Muốn mở rộng thêm ngày, thay `--end` bằng ngày sau ngày muốn thu thập (mốc UTC, loại trừ).

Nếu bị gián đoạn, tiếp tục **không có `--refresh`**, giữ đúng khoảng ngày đã lưu:

```powershell
python scripts/collect_news_titles.py --start 2026-01-01 --end 2026-10-21
python scripts/export_news_videos.py
```

Muốn thêm kênh, nối nguồn mới vào **cuối** `config/youtube_news_channels.json`, giữ nguyên thứ tự nguồn cũ. Sao lưu checkpoint và CSV trước mỗi đợt cập nhật; bản trước đợt 19/10 nằm ở `reports/crawl_backups/2026-10-19/`. Lệnh crawl không tự chạy pipeline phân tích hoặc cập nhật MongoDB/dashboard.

Khi nối thêm kênh, collector đặt lại `scan_start` về ngày bắt đầu dataset để lấy đủ lịch sử của nguồn mới, thay vì dùng mốc quét tăng thêm của các nguồn cũ. Ngày 20/10 đã sửa lỗi nguồn mới kế thừa mốc cập nhật gần nhất; 5 nguồn thêm ở lượt đầu ngày này được quét lại riêng từ tháng 1 và các ID đã có được giữ nguyên, không tạo bản trùng.

Một số website báo/đài dùng URL YouTube cũ dạng `/c/...`; khi cần, đối chiếu URL canonical công khai của chính liên kết đó để lấy channel ID, rồi tra cứu lại qua `channels.list`. HTML chỉ dùng để xác định địa chỉ nguồn; tiêu đề, ngày đăng và tương tác trong CSV vẫn lấy qua API. Một danh sách bên thứ ba chỉ được dùng làm gợi ý tìm kiếm, không thay cho bằng chứng sở hữu từ website báo/đài. Các nguồn không có bằng chứng đủ rõ hoặc API không trả về kênh được bỏ qua.

Khi quota còn ít, thêm `--max-pages N` để dừng sau tối đa N trang mới và giữ page token. Phải dành riêng tối đa một lượt `videos.list` cho mỗi 50 video ID mới; đếm cả các lượt gọi xác định kênh, retry và metadata chưa lấy từ đợt trước. Dừng theo tùy chọn này tạo trạng thái collector `budget_limited`; exporter được phép lấy đủ metadata của các ID đã thu và xuất CSV với trạng thái `partial_collection`. Trạng thái này cho biết lịch sử của các kênh mới chưa được quét hết, không phải CSV bị lỗi. Đợt sau tiếp tục không có `--refresh`, giữ cùng khoảng ngày, rồi xuất lại CSV. Chỉ dùng `--refresh` sau khi đã quét hết danh mục nguồn.

Collector và exporter dùng chung `DAILY_BUDGET = 10000` trong `collect_news_titles.py`, theo lịch `America/Los_Angeles`. Ngưỡng trước đó là 8.000; tối 20/10 đã đổi thành 10.000 theo yêu cầu dùng hết phần còn lại, sau khi đọc trang quota Google Cloud của project BIGDATA1 và thấy hạn mức Queries per day là 10.000. Bộ đếm cục bộ không phải phép đo quota còn lại trên Cloud và không bao gồm ứng dụng khác dùng chung project; số hiển thị trên Cloud cũng có thể cập nhật trễ. Khi API báo hết quota, giữ checkpoint/cache và tiếp tục sau kỳ cấp lại.

Ngày 20/10, Google Cloud hiển thị riêng Search Queries per day với hạn mức 100; các lượt tìm kênh được ghi trong `reports/youtube_channel_search_state.json`, tách khỏi bộ đếm collector/metadata. Tham khảo [bảng quota hiện hành của Google](https://developers.google.com/youtube/data/determine_quota_cost). Không đổi hạn mức trên Google Cloud hoặc tạo thêm project/key để tiếp tục crawl.

## 7. Cách sử dụng trong đề tài

Dùng `published_at_vn` để nhóm theo ngày hoặc tháng. Khi một vấn đề xuất hiện ở nhiều kênh, đo cả số video lẫn **số channel ID khác nhau** để hạn chế một kênh đăng nhiều làm lệch kết quả. Việc nhận diện cùng vấn đề với các tiêu đề viết khác nhau thuộc bước phân tích chủ đề, không phải bước loại trùng tiêu đề.

Đây là mẫu nội dung của các báo/đài trên YouTube. Kênh chính thống có thể đăng thêm văn hóa, giải trí hoặc chương trình chuyên đề; collector chưa phân loại từng video là thời sự. Số bài và độ phủ kênh phản ánh mức độ đưa tin trong mẫu; không tự chứng minh mức quan tâm của toàn xã hội. Lượt xem/thích là ảnh chụp một thời điểm và độ tuổi video khác nhau có thể ảnh hưởng so sánh.
