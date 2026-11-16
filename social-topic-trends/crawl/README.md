# Nguồn dữ liệu

Dataset được thu thập từ uploads của các kênh báo chí và đài truyền hình Việt Nam được cấu hình trong `config/youtube_news_channels.json`. `sources_current.csv` lưu danh mục nguồn đi kèm snapshot.

CSV nộp là `data/exports/youtube_news_videos_clean.csv`. Tiêu đề trùng giữa các kênh khác nhau được giữ để phản ánh độ phủ đưa tin. Trong cùng kênh, tiêu đề chuẩn hóa trùng nhau chỉ giữ video mới nhất.

Phạm vi quan sát trong snapshot: 01/01/2023–29/10/2026 UTC. Thời gian và lượt xem/lượt thích lấy từ YouTube Data API; lượt tương tác là số tích lũy tại thời điểm thu thập. Tài khoản API không cần thiết để chạy dashboard hoặc pipeline trên snapshot hiện có.
