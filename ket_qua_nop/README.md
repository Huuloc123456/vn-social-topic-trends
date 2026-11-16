# Hồ sơ kết quả đồ án

## Tài liệu nộp

- `BaoCao_DoAn_BigData.docx`: báo cáo có thể chỉnh sửa.
- `BaoCao_DoAn_BigData.pdf`: bản PDF để xem và in.
- `BigData-thuyet-trinh.pptx`: slide thuyết trình.

## Dataset và kết quả phân tích

- `du_lieu/youtube_news_videos_clean.csv`: CSV đã làm sạch, gồm **1.263.204 video**, đăng từ **01/01/2023 đến 29/10/2026 (UTC)**.
- `phan_tich/`: kết quả cuối của pipeline, gồm thông tin mô hình, chủ đề, diễn biến chủ đề, từ khóa, hashtag, sự kiện tăng đột biến và vấn đề theo ngày.

Dataset được tổng hợp từ tiêu đề video của các kênh báo chí và đài truyền hình Việt Nam đã cấu hình trong dự án. Đây không phải mẫu đại diện cho toàn bộ người dùng YouTube hoặc toàn bộ dư luận xã hội. View/like là số tích lũy tại thời điểm lấy metadata.

## Chạy lại ứng dụng

Từ thư mục gốc repo, khởi động các dịch vụ và chạy pipeline theo hướng dẫn trong [README chính](../README.md). CSV chuẩn mà pipeline đọc là `../data/exports/youtube_news_videos_clean.csv`; bản trong `du_lieu/` là bản sao đóng gói để nộp.

> CSV và JSON phân tích được giữ trong thư mục này trên máy, nhưng không đưa lên GitHub do dung lượng lớn. Báo cáo và slide được theo dõi bằng Git.
