# Bản nháp hồ sơ Meta App Review — `threads-city`

Trạng thái: bản chuẩn bị nội bộ, **chưa gửi Meta**. App ID: `1114272214344336`.

## Phạm vi và điều kiện tiên quyết

- Use case: Truy cập API Threads.
- Các quyền hiện đã bật để thử nghiệm: `threads_basic`, `threads_keyword_search`, `threads_read_replies`.
- `threads_keyword_search` chỉ trả kết quả bài công khai sau khi được Meta duyệt; khi chưa duyệt, tìm kiếm bị giới hạn ở nội dung tài khoản đã xác thực.
- Theo mô tả quyền của Meta, `threads_read_replies` dùng để đọc replies trên thread của người dùng đã cấp quyền. Không mô tả quyền này là khả năng đọc replies của mọi bài công khai tìm được. Nếu bài nghiên cứu cần replies trên bài của người khác, cần xác minh endpoint/quyền chính thức hỗ trợ trước khi đưa vào mục tiêu hoặc cam kết thu thập.
- API Explorer không thay thế ứng dụng có luồng OAuth và trải nghiệm thực tế để reviewer kiểm tra. Hiện chưa có bằng chứng app client/server hoàn chỉnh, privacy policy công khai, URL xóa dữ liệu, video demo, hoặc kết quả kiểm thử end-to-end; vì vậy đây chưa phải hồ sơ sẵn sàng gửi.
- Cửa sổ dữ liệu dự kiến: 01/06/2026–11/10/2026 (Asia/Bangkok). Ngày kết thúc cần cập nhật thành ngày gửi yêu cầu và dùng tham số thời gian được API chấp nhận.

## Mô tả ứng dụng — bản nháp tiếng Anh

> `threads-city` is a student research prototype for studying how public discussion topics change over time. An authorized researcher searches public Threads posts for a balanced set of predefined topics (technology, entertainment, sports, education, health, environment, and the economy), within a stated date range. The prototype stores only the fields needed for topic and time-series analysis, removes or pseudonymizes usernames in the analysis dataset, and reports aggregate results. It does not publish, reply to, rank, or contact Threads users. Replies are accessed only for threads belonging to the Threads user who authorized the app, where permitted by the granted permission. The app is for a university course project and is not a public data-broker or user-profiling service.

**Điền/chỉnh trước khi gửi:** tên trường/môn học nếu muốn nêu; ai là người dùng của ứng dụng; nơi chạy ứng dụng; cách người dùng bắt đầu tìm kiếm/xem kết quả; và phạm vi/ngôn ngữ thực tế. Chỉ giữ các tuyên bố đúng với sản phẩm đã chạy.

## Giải trình quyền — bản nháp tiếng Anh

### `threads_keyword_search`

> We request `threads_keyword_search` so the authorized researcher can search public Threads media for a balanced set of research topics and retrieve matching posts within the project’s date window. The results are used to estimate topic frequencies and changes over time. We request only the fields needed for this purpose (post ID, text, timestamp, media type, permalink, and reply indicator where available). Usernames are excluded or pseudonymized in the analysis output. We do not use the permission to publish responses, contact users, build individual profiles, or sell/share person-level data. The researcher reviews query terms and collection scope before each run.

### `threads_read_replies`

> We request `threads_read_replies` only to retrieve replies to Threads posts owned by the Threads user who authorized the app, for an exploratory analysis of discussion around that user’s own posts. The app will show the account owner which posts and replies are being included, collect only the fields required for analysis, and exclude or pseudonymize usernames in the analysis dataset. We do not claim this permission gives access to replies on arbitrary public posts authored by other people.

**Lưu ý:** nếu ứng dụng chưa thật sự có màn hình/luồng thực hiện từng mục đích trên, không gửi nguyên văn giải trình đó. Hoặc bỏ yêu cầu quyền không dùng, hoặc hoàn thiện luồng rồi ghi hình đúng sản phẩm.

## Kịch bản screencast cần quay sau khi có bản chạy được

1. Mở ứng dụng tại URL reviewer truy cập được; nêu ngắn gọn mục đích nghiên cứu và tài khoản thử nghiệm.
2. Thực hiện OAuth Threads từ đầu và cho thấy danh sách quyền app yêu cầu; không để lộ access token hay secret trong video.
3. Cho thấy màn hình nhập/chọn nhóm chủ đề cân bằng, ngày bắt đầu/kết thúc, và giới hạn kết quả.
4. Chạy tìm kiếm `threads_keyword_search`; hiển thị request/response đã che token và kết quả được phân trang/lưu.
5. Với `threads_read_replies`, dùng một thread do tài khoản tester sở hữu, mở phần replies, rồi chứng minh replies hiển thị trong ứng dụng. Không dùng post của tài khoản khác để tuyên bố quyền đọc.
6. Cho thấy cách ẩn danh trong bản xuất, thời hạn lưu, và thao tác xóa dữ liệu/ngắt kết nối tài khoản.

## Thông tin cần chuẩn bị trước khi vào App Review

- Privacy Policy URL công khai, hoạt động và khớp với cách thu thập/lưu/xóa dữ liệu thực tế.
- URL hoặc hướng dẫn xóa dữ liệu người dùng và quy trình xử lý yêu cầu xóa.
- Reviewer access/test account và hướng dẫn đăng nhập; tuyệt đối không gửi mật khẩu cá nhân hoặc token qua tài liệu này.
- Video screencast end-to-end cho từng quyền xin duyệt.
- Bản chạy được của ứng dụng, URL redirect OAuth/callback đã cấu hình, và kiểm thử API thành công bằng OAuth của app.
- Giải thích chính xác mục đích/đối tượng dùng, trường dữ liệu lấy, thời hạn lưu, quyền truy cập, quy trình ẩn danh, và lý do cần từng quyền.
- Xác nhận tuân thủ điều khoản/chính sách Meta và rà soát yêu cầu đạo đức/nghiên cứu của trường. Không gửi dữ liệu cá nhân của người khác cho Meta ngoài những gì luồng xét duyệt yêu cầu.

## Thiết kế thu thập dự kiến sau khi có phê duyệt

- Chủ đề: công nghệ, giải trí, thể thao, giáo dục, sức khỏe, môi trường, kinh tế.
- Với mỗi chủ đề, chọn trước danh sách từ khóa/hashtag bằng tiêu chí nhất quán; lưu truy vấn, thời điểm chạy, `search_type`, và tham số thời gian để có thể tái lập.
- Gọi tìm kiếm tuần tự, tôn trọng giới hạn API và phân trang; không chạy nhiều tài khoản để né hạn mức.
- Khử trùng theo post ID; kiểm tra phân bố theo chủ đề/ngày trước khi phân tích để phát hiện lệch mẫu.
- Tách dữ liệu thô khỏi bảng phân tích; bỏ username khỏi bảng phân tích, giới hạn quyền truy cập dữ liệu thô, không phát hành nội dung nguyên văn có thể tìm ngược về tác giả.
- Xóa token khỏi log; bảo quản token trong secret store cục bộ; xóa dữ liệu theo lịch lưu đã công bố và khi có yêu cầu hợp lệ.
- Ghi rõ giới hạn suy luận: tìm kiếm Threads không phải mẫu đại diện cho toàn bộ người dùng hay dư luận; không kết luận độ phổ biến dân số từ lượng bài API trả về.

## Việc còn thiếu / không được hiểu là đã hoàn tất

- [ ] Xác minh chính xác endpoint và quyền đọc replies chỉ trên nội dung thuộc phạm vi nào; điều chỉnh mục tiêu dataset theo kết quả xác minh.
- [ ] Xây dựng ứng dụng OAuth/API và kiểm thử bằng tài khoản tester.
- [ ] Điền URL privacy policy, URL xóa dữ liệu, reviewer instructions, demo credentials an toàn.
- [ ] Quay screencast thực tế (không dựng/mock response).
- [ ] Kiểm tra đủ điều kiện và yêu cầu hiện hành trong App Dashboard.
- [ ] Chỉ sau đó mới quyết định gửi App Review; bản này chưa gửi và không đảm bảo Meta sẽ phê duyệt.

## Nguồn Meta

- [Threads Keyword Search](https://developers.facebook.com/documentation/threads/keyword-search) — quyền cần có, hành vi chỉ tìm bài của người dùng đã xác thực khi chưa được duyệt, thời gian truy vấn, giới hạn và fields.
- [Threads Reply Management](https://developers.facebook.com/documentation/threads/reply-management) — tài liệu Threads liên quan đến replies.
- [Threads API overview](https://developers.facebook.com/documentation/threads) — danh mục tài liệu chính thức.
