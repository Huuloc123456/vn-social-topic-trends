# Kịch bản thuyết trình, demo và câu hỏi chuẩn bị

Đề tài số 5: Phân tích xu hướng chủ đề trên mạng xã hội
Phạm vi dữ liệu: tiêu đề video YouTube từ các kênh báo, đài Việt Nam
Slide: `docs/slides/BigData-thuyet-trinh.pptx` (25 slide) · Báo cáo: `docs/BaoCao_DoAn_BigData.docx`

## Phân vai

- **Mẫn** trình bày toàn bộ phần lý thuyết và nội dung trên slide (slide 1–21 và 22–25).
- **Lộc** demo hệ thống trực tiếp (chen vào sau slide 21) và là người trả lời chính các câu hỏi về thu thập dữ liệu, HDFS, Spark và MongoDB.

| Đoạn | Người nói | Slide | Thời gian |
|---|---|---|---|
| Mở đầu và Chương 1 | Mẫn | 1–5 | 3:00 |
| Chương 2: Cơ sở lý thuyết | Mẫn | 6–10 | 4:35 |
| Chương 3: Xây dựng ứng dụng | Mẫn | 11–21 | 8:15 |
| **Demo** | **Lộc** | (giữ ở slide 21, chuyển sang trình duyệt) | 6:00 |
| Chương 4 và kết thúc | Mẫn | 22–25 | 2:00 |
| **Tổng** | | | **khoảng 23–24 phút**, chưa tính hỏi đáp |

Nếu bị giới hạn 15 phút: Mẫn đọc lướt slide 7, 8, 13 và 16 (mỗi slide 15 giây), còn Lộc rút demo xuống 4 phút bằng cách bỏ bước MongoDB và trang Các câu chuyện.

Ký hiệu trong kịch bản: **[▶]** là bấm sang slide tiếp theo; *chữ nghiêng* là thao tác, không đọc thành lời.

---

## 1. Lời thoại của Mẫn

### Slide 1 — Bìa (0:30)

> Kính chào thầy cô và các bạn. Nhóm em gồm hai thành viên: em là Đỗ Lê Thanh Mẫn và bạn Bùi Hữu Lộc, giảng viên hướng dẫn là ThS. Ngô Dương Hà. Nhóm em thực hiện Đề tài số 5: Phân tích xu hướng chủ đề trên mạng xã hội. Trong phạm vi đồ án, nhóm phân tích tiêu đề video YouTube từ các kênh báo, đài Việt Nam. Em sẽ trình bày phần nội dung, còn bạn Lộc sẽ demo trực tiếp hệ thống.

**[▶]**

### Slide 2 — Nội dung chính (0:20)

> Bài trình bày gồm bốn phần: giới thiệu đề tài, cơ sở lý thuyết, xây dựng ứng dụng và trực quan hóa dữ liệu, cuối cùng là kết luận và hướng phát triển. Phần demo nằm ở cuối chương 3.

**[▶]**

### Slide 3 — Chương 1 (0:05)

> Đầu tiên là phần giới thiệu đề tài.

**[▶]**

### Slide 4 — Bài toán (1:00)

> Mỗi ngày, các báo, đài Việt Nam đăng hàng trăm video lên YouTube. Nếu chỉ đọc từng tiêu đề, ta không trả lời được những câu hỏi như: hôm nay chủ đề nào được đưa tin nhiều nhất, chủ đề nào đang tăng nhanh so với hôm qua, và có bao nhiêu kênh cùng đưa tin.
>
> Đề tài số 5 của môn học yêu cầu thu thập dữ liệu mạng xã hội, lưu trên HDFS hoặc NoSQL, xử lý bằng Spark, áp dụng mô hình chủ đề và xây dựng dashboard theo thời gian. Nhóm chọn tiêu đề video YouTube của các kênh báo, đài vì đây là dữ liệu tiếng Việt, lấy được qua API chính thức, có thời gian đăng và liên kết gốc để kiểm chứng.
>
> *(Chỉ vào hình)* Hình trên slide là kết quả cuối cùng: bảng các chủ đề được đưa tin nhiều nhất ngày 14/10/2026 trên dashboard của nhóm.

**[▶]**

### Slide 5 — Mục tiêu và phạm vi (1:05)

> Bộ dữ liệu có 104.790 video từ 30 kênh báo, đài, trong 136 ngày, từ 01/06 đến 14/10/2026. Sau khi lọc, 93.456 tiêu đề tiếng Việt được dùng để huấn luyện mô hình.
>
> Mục tiêu của nhóm là xây dựng một quy trình chạy lại được, đi từ API, qua CSV, HDFS, Spark, MongoDB, đến dashboard; so sánh hai mô hình là Word2Vec kết hợp KMeans và LDA; sau đó thống kê chủ đề theo ngày, theo tháng và phát hiện các khoảng tăng đột biến.
>
> Về phạm vi: nhóm chỉ dùng tiêu đề, không dùng bình luận hay nội dung video; xử lý theo lô trên cụm Docker chạy trên một máy. Đây là phân tích khám phá, không phải dự báo, nên khi đọc kết quả, nhóm luôn hiểu là "chủ đề được đưa tin trong mẫu", chứ không đại diện cho toàn bộ mạng xã hội.

**[▶]**

### Slide 6 — Chương 2 (0:05)

> Tiếp theo là cơ sở lý thuyết.

**[▶]**

### Slide 7 — Dữ liệu lớn và 5V (1:00)

> Dữ liệu lớn thường được mô tả bằng năm đặc trưng, gọi là 5V. Volume là hơn một trăm nghìn tiêu đề, và con số này tăng khi thêm kênh hoặc kéo dài thời gian. Velocity là trung bình khoảng 773 video mới mỗi ngày. Variety là dữ liệu gồm văn bản, thời gian, mã kênh, liên kết và số tương tác. Veracity là các vấn đề về độ tin cậy: 12,31% video bị ẩn lượt thích, nhận diện ngôn ngữ có thể sai, tiêu đề bị trùng. Value là chuyển các tiêu đề rời rạc thành chủ đề và xu hướng.
>
> Nhóm cũng nói rõ: tệp CSV hiện chỉ khoảng 30 MB, một máy vẫn xử lý được. Nhóm dùng HDFS và Spark để triển khai đúng quy trình phân tán của môn học và sẵn sàng khi dữ liệu tăng lên.

**[▶]**

### Slide 8 — Công nghệ lưu trữ và xử lý phân tán (1:10)

> Hệ thống dùng bốn nhóm công nghệ.
>
> HDFS là hệ thống tệp phân tán của Hadoop. NameNode quản lý thông tin tệp, DataNode lưu dữ liệu theo từng block 128 MB. Cụm của nhóm có một NameNode, hai DataNode, mỗi block được sao chép hai bản.
>
> Apache Spark xử lý dữ liệu song song: driver điều phối, các executor trên worker chạy tác vụ. Nhóm dùng Spark DataFrame để làm sạch và thống kê, và thư viện MLlib để huấn luyện mô hình.
>
> MongoDB là cơ sở dữ liệu NoSQL hướng tài liệu, dùng để lưu các bảng kết quả nhỏ, giúp dashboard đọc nhanh.
>
> Cuối cùng, Docker Compose dựng toàn bộ cụm bằng một lệnh, còn Streamlit và Plotly dùng để làm dashboard tương tác.

**[▶]**

### Slide 9 — Biểu diễn văn bản và mô hình chủ đề (1:20)

> Trước khi đưa vào mô hình, tiêu đề được đưa về chữ thường, bỏ liên kết, chữ số và ký hiệu, tách thành token, bỏ từ dừng, và lọc chỉ giữ tiếng Việt bằng mô hình fastText.
>
> Nhóm so sánh hai hướng. Hướng thứ nhất là Word2Vec kết hợp KMeans. Word2Vec biến mỗi từ thành một vector 100 chiều; vector của tiêu đề là trung bình các vector từ. Sau đó KMeans chia các tiêu đề thành 10 cụm, mỗi tiêu đề thuộc đúng một cụm. Nhờ vậy, nhóm đếm được số video của từng cụm theo từng ngày. Tên cụm được lấy bằng c-TF-IDF, tức là ba từ đặc trưng nhất của cụm đó.
>
> Hướng thứ hai là LDA. LDA coi mỗi tiêu đề là hỗn hợp của nhiều chủ đề, mỗi chủ đề là một phân phối trên các từ. LDA cho biết một câu liên quan đến từng chủ đề với tỷ lệ bao nhiêu, nên nhóm dùng nó trong trang phân tích văn bản.

**[▶]**

### Slide 10 — Chỉ số đánh giá và phát hiện tăng đột biến (1:00)

> Dữ liệu không có nhãn chủ đề đúng sai, nên nhóm không tính độ chính xác mà dùng ba chỉ số. NPMI đo mức các từ khóa của một cụm thường xuất hiện cùng nhau, nằm trong khoảng từ âm 1 đến 1; đây là chỉ số áp dụng được cho cả hai mô hình. Silhouette đo mức các cụm KMeans tách khỏi nhau. Log-perplexity đánh giá LDA, càng thấp càng tốt.
>
> Để phát hiện xu hướng, nhóm tính tỷ trọng của mỗi chủ đề trong ngày rồi so với trung bình 7 ngày trước đó bằng điểm z. Một ngày được đánh dấu tăng đột biến khi z lớn hơn 2,5, có ít nhất 20 video và tỷ trọng cao hơn ít nhất 1,2 lần mức nền.

**[▶]**

### Slide 11 — Chương 3 (0:05)

> Phần tiếp theo là cách nhóm xây dựng ứng dụng.

**[▶]**

### Slide 12 — Kiến trúc tổng thể (0:50)

> *(Chỉ theo mũi tên trên sơ đồ)* Dữ liệu đi theo luồng sau: chương trình Python gọi YouTube Data API để lấy danh sách video và thông tin video, rồi xuất ra một tệp CSV. Tệp CSV được đưa lên HDFS. Spark đọc từ HDFS để làm sạch, thống kê và huấn luyện mô hình. Sau đó bước tổng hợp tính xu hướng theo ngày và ghi kết quả vào MongoDB, và dashboard đọc dữ liệu từ MongoDB.
>
> Môi trường gồm Hadoop 3.4.1, Spark 3.5.3 với hai worker, mỗi worker 4 nhân, 4 GB bộ nhớ, MongoDB 7.0 và Streamlit.

**[▶]**

### Slide 13 — Thu thập dữ liệu (0:50)

> Danh mục gồm 32 kênh báo, đài, trong đó 30 kênh có video trong khoảng thời gian thu thập. Chương trình lấy danh sách video tải lên của từng kênh, mỗi lần 50 video, có lưu điểm dừng theo kênh để chạy tiếp nếu bị gián đoạn. Sau đó lấy tiêu đề, lượt xem, lượt thích theo nhóm 50 video.
>
> Về loại trùng: có 106.449 mã video gốc; bỏ 1.659 tiêu đề bị trùng trong cùng một kênh thì còn 104.790 video. Tiêu đề giống nhau ở các kênh khác nhau vẫn được giữ, vì đó là dấu hiệu nhiều nguồn cùng đưa tin. Lượt thích bị thiếu được để trống, không thay bằng 0.

**[▶]**

### Slide 14 — Lưu trữ HDFS và cụm Spark (0:40)

> Tệp CSV gốc nằm trên HDFS ở thư mục /social/raw/youtube_news, dung lượng 28,68 MB, có hai bản sao. Dữ liệu sau khi làm sạch được lưu dạng Parquet, là định dạng lưu theo cột và có nén. Hình dưới là trang Spark Master: hai worker đang hoạt động, các job làm sạch, thống kê và huấn luyện đều đã chạy xong. Lát nữa bạn Lộc sẽ mở trực tiếp các giao diện này.

**[▶]**

### Slide 15 — Làm sạch và tách tập dữ liệu (0:50)

> Spark kiểm tra schema, dữ liệu thiếu, mã trùng và thời gian ngoài phạm vi; ở bước này không có bản ghi nào bị loại. Một điểm quan trọng là ngày được tính theo giờ Việt Nam, để video đăng lúc nửa đêm không bị xếp sang ngày khác.
>
> Nhóm tách hai tập. Tập thống kê giữ toàn bộ 104.790 video để đếm số video theo ngày. Tập huấn luyện chỉ giữ 93.456 tiêu đề tiếng Việt đủ tin cậy. Nếu lọc ngôn ngữ ngay trên tập thống kê thì số video mỗi ngày sẽ bị giảm sai, vì nhiều tin tiếng Việt chứa tên riêng nước ngoài bị nhận nhầm ngôn ngữ.

**[▶]**

### Slide 16 — Phân tích khám phá (0:40)

> Trung bình mỗi ngày có 773 video; ngày ít nhất 583, ngày nhiều nhất 920. 84,1% tiêu đề dài từ 11 đến 20 token. Chỉ 4,59% video có hashtag, và hashtag phổ biến nhất là #shorts, vốn là định dạng video chứ không phải chủ đề. Tháng 10 chỉ có 10.664 video vì mới quan sát được 14 ngày, không phải do các kênh đưa tin ít đi.

**[▶]**

### Slide 17 — Huấn luyện và lựa chọn mô hình (1:00)

> Hai mô hình được huấn luyện trên cùng 93.456 tiêu đề, cùng k bằng 10. Word2Vec kết hợp KMeans đạt NPMI 0,2245, cao hơn LDA với 0,1492, nên nhóm chọn nó làm mô hình chính cho xu hướng.
>
> Nhóm cũng thấy silhouette chỉ đạt 0,1611, nghĩa là các cụm tách nhau chưa rõ. Lý do là tiêu đề ngắn, token tách theo âm tiết, và tên kênh xuất hiện ngay trong tiêu đề. LDA vẫn được giữ trong trang phân tích văn bản để xem phân bố chủ đề.

**[▶]**

### Slide 18 — 10 cụm chủ đề (0:55)

> Đây là 10 cụm sau khi áp mô hình lên toàn bộ dữ liệu. Có những cụm rõ nghĩa: "tiết · thời · nay" là dự báo thời tiết, có NPMI cao nhất, 0,4945; "cup · world · vtv" là World Cup; "mưa · lũ · bão"; "giá · vàng · news"; "tố · bắt · khởi" là tin vụ án; "iran · mỹ · nga" là tin quốc tế.
>
> Ngược lại, cụm lớn nhất là "thdt · công · học" với 21,71%, nhưng có NPMI thấp nhất. Trong đó, THDT là ký hiệu của Truyền Hình Đồng Tháp; điều này cho thấy tên kênh vẫn ảnh hưởng đến cách phân cụm.

**[▶]**

### Slide 19 — Xu hướng và tăng đột biến (0:50)

> Biểu đồ thể hiện tỷ trọng của từng chủ đề theo ngày. Dùng tỷ trọng thay vì số lượng giúp tách việc chủ đề nổi lên khỏi việc tổng số video thay đổi. Hệ thống phát hiện 53 khoảng tăng đột biến. Ví dụ, ngày 02/09, cụm "hội · sĩ · liệt" chiếm 26,6%, trong khi mức bình thường là 16%; ngày 12 và 13/09, cụm "mưa · lũ · bão" lên 13,6%, so với mức nền 7,5%.

**[▶]**

### Slide 20 — Đối chiếu ngày 14/10/2026 (0:55)

> Để kiểm tra kết quả có hợp lý không, nhóm đối chiếu một ngày cụ thể. Ngày 14/10, cụm "hội · sĩ · liệt" có 105 video từ 28 kênh. Ba video được xem nhiều nhất đều về lễ truy điệu, an táng hài cốt liệt sĩ tại TP. Hồ Chí Minh.
>
> Tuy nhiên, nhóm lưu ý hai điều. Thứ nhất, 105 là số video của cả cụm, không phải 105 video cùng nói về một sự kiện. Thứ hai, cùng ngày đó, cụm "mưa · lũ · bão" lẫn cả tin hố sụt ở Trung Quốc và tin tặc tấn công siêu thị ở Pháp. Vì vậy dashboard luôn hiển thị video gốc để người dùng tự kiểm chứng.

**[▶]**

### Slide 21 — Dashboard (0:40)

> Dashboard có sáu trang: Bảng điểm, Các câu chuyện, Diễn biến, Từ khóa và Hashtag, Phân tích văn bản, và Dữ liệu và Phương pháp. Thay vì giới thiệu qua hình, mời bạn Lộc demo trực tiếp hệ thống.

*(Mẫn đứng sang bên. Lộc nhận máy và chuyển sang trình duyệt.)*

---

## 2. Kịch bản demo của Lộc (6 phút)

### Chuẩn bị trước buổi thuyết trình

**Ở nhà, ngày hôm trước**
1. Chạy `run.bat` (hoặc lệnh bên dưới) và kiểm tra các dịch vụ đều đang `Up`: namenode, datanode-1, datanode-2, spark-master, spark-worker-1, spark-worker-2, mongodb, dashboard.

   ```powershell
   docker compose -f docker/docker-compose.yml up -d
   ```

   ```powershell
   docker compose -f docker/docker-compose.yml ps
   ```

2. Quay một video màn hình khoảng 4 phút đi đúng kịch bản bên dưới, lưu sẵn trên máy và USB để dùng khi máy lỗi.
3. Tập demo ít nhất hai lần, bấm giờ.

**30 phút trước khi trình bày**
1. Bật Docker Desktop, chạy lại hai lệnh trên.
2. Mở trình duyệt, phóng to 125%, mở sẵn 5 tab theo thứ tự:
   - Tab 1: `http://127.0.0.1:9870/dfshealth.html#tab-datanode`
   - Tab 2: `http://127.0.0.1:9870/explorer.html#/social/raw/youtube_news`
   - Tab 3: `http://127.0.0.1:8080`
   - Tab 4: `http://127.0.0.1:8501` (dashboard)
   - Tab 5: `http://127.0.0.1:8501/phan-tich`
3. Trên dashboard, bật công tắc **Trình chiếu** ở góc phải để che các từ nhạy cảm. Bấm qua tất cả các trang một lần để dữ liệu được nạp vào bộ nhớ đệm.
4. Mở một cửa sổ PowerShell ở thư mục dự án, chỉnh cỡ chữ khoảng 20, dán sẵn lệnh MongoDB ở bước 3 nhưng chưa nhấn Enter.
5. Chép sẵn hai câu thử ở bước 7 vào một tệp Notepad.
6. Tắt thông báo của máy (bật Focus assist hoặc Không làm phiền).

**Không chạy lại pipeline khi demo.** Việc chạy lại mất vài phút và sẽ tạo lượt thực nghiệm mới với mã khác.

### Lời thoại và thao tác

**Mở đầu (0:10)**

> Em là Lộc. Em sẽ demo hệ thống đang chạy trên máy, theo đúng luồng dữ liệu bạn Mẫn vừa trình bày: từ nơi lưu trữ, qua nơi xử lý, đến dashboard.

**Bước 1 — HDFS (1:00)** *Tab 1, rồi Tab 2.*

> Đây là giao diện NameNode của HDFS. *(Chỉ vào bảng In operation)* Cụm có hai DataNode, cả hai đều đang hoạt động.
>
> *(Chuyển Tab 2)* Đây là thư mục /social/raw/youtube_news. Tệp CSV gốc có dung lượng 28,68 MB, cột Replication bằng 2, tức mỗi block có hai bản trên hai DataNode, hỏng một máy vẫn còn dữ liệu.
>
> *(Gõ `/social/youtube_news/clean` vào ô đường dẫn, nhấn Go, rồi mở một thư mục con)* Còn đây là dữ liệu sau khi Spark làm sạch, lưu dạng Parquet và chia thành nhiều phần để xử lý song song.

**Bước 2 — Spark (0:40)** *Tab 3.*

> Đây là Spark Master. *(Chỉ vào mục Workers)* Có hai worker đang ALIVE, mỗi worker 4 nhân và 4 GB bộ nhớ. *(Cuộn xuống Completed Applications)* Đây là các job của pipeline đã chạy xong: làm sạch dữ liệu, thống kê mô tả, huấn luyện LDA, huấn luyện Word2Vec kết hợp KMeans, và bước tổng hợp kết quả.

**Bước 3 — MongoDB (0:30)** *Chuyển sang PowerShell và nhấn Enter.*

```powershell
docker compose -f docker/docker-compose.yml exec mongodb mongosh youtube_news_topics --quiet --eval "db.topics.countDocuments() + ' chu de | ' + db.topic_trend.countDocuments() + ' dong xu huong | ' + db.burst_events.countDocuments() + ' burst'"
```

> Kết quả tổng hợp được ghi vào MongoDB: 10 chủ đề, 1.360 dòng xu hướng, tức 136 ngày nhân 10 chủ đề, và 53 khoảng tăng đột biến. Dashboard đọc trực tiếp từ đây nên không phải chạy lại Spark mỗi lần người dùng bấm.

Kết quả đúng khi chạy thử: `10 chu de | 1360 dong xu huong | 53 burst`.

**Bước 4 — Trang Bảng điểm (1:00)** *Tab 4.*

> Đây là dashboard. Trang Bảng điểm đang chọn ngày 14/10/2026. *(Chỉ vào bảng thứ nhất)* Chủ đề được đưa tin nhiều nhất có 105 video từ 28 kênh, ngày trước đó là 100 video. Cột đầu tiên là tiêu đề video đại diện của cụm.
>
> *(Cuộn xuống phần Bài và video minh họa)* Phía dưới là video gốc, có tên kênh, thời gian đăng và lượt xem, để người xem bấm vào kiểm chứng.
>
> *(Cuộn lên, chọn "Tháng" ở mục Xem theo)* Khi chuyển sang xem theo tháng, số video được cộng theo các ngày trong tháng, còn số kênh được tính không trùng lặp.

**Bước 5 — Trang Diễn biến (0:50)** *Bấm menu Diễn biến.*

> Biểu đồ này là cơ cấu tỷ trọng các chủ đề theo từng ngày. *(Kéo thanh trượt về khoảng đầu tháng 9)* Thanh trượt chọn thời điểm. *(Cuộn xuống phần Nhật ký bùng nổ)* Đây là danh sách các khoảng tăng đột biến hệ thống phát hiện, kèm tỷ trọng tại đỉnh, mức nền và điểm z.

**Bước 6 — Trang Các câu chuyện (0:30)** *Bấm menu Các câu chuyện, chọn cụm "mưa · lũ · bão" ở mục Hồ sơ chủ đề.*

> Trang này cho xem hồ sơ từng cụm: tỷ trọng, số video, ngày đỉnh, số lần tăng đột biến, chỉ số NPMI và các video tiêu biểu.

**Bước 7 — Trang Phân tích văn bản (1:00)** *Tab 5. Dán câu thứ nhất, nhấn Ctrl+Enter và chờ vài giây.*

Câu 1: `Dự báo thời tiết ngày mai: Bắc Bộ trời rét, Nam Bộ có mưa rào`

> Em nhập một câu mới mà mô hình chưa từng thấy. Hệ thống áp dụng đúng chuỗi tiền xử lý lúc huấn luyện. Mô hình chính chọn cụm "tiết · thời · nay", độ tương đồng cosine là 0,94. *(Chỉ vào biểu đồ LDA bên dưới)* Mô hình LDA cũng dồn phần lớn xác suất vào chủ đề thời tiết.

Câu 2: `Công an bắt giữ đối tượng lừa đảo chiếm đoạt hàng tỷ đồng qua mạng`

> Với câu về vụ án, mô hình chọn cụm "tố · bắt · khởi", cosine 0,73.

*(Nếu còn thời gian, dùng thêm một trong các câu đã chạy thử:)*

| Câu | Cụm | Cosine |
|---|---|---|
| Bão số 5 gây mưa lớn, nguy cơ lũ quét và sạt lở đất tại các tỉnh miền Trung | mưa · lũ · bão | 0,80 |
| Giá vàng hôm nay tăng mạnh, vàng nhẫn vượt mốc 150 triệu đồng mỗi lượng | giá · vàng · news | 0,71 |
| Tổng thống Trump tuyên bố về xung đột giữa Nga và Ukraine | iran · mỹ · nga | 0,79 |

**Kết thúc demo (0:10)**

> Đó là toàn bộ phần demo. Xin mời bạn Mẫn trình bày phần kết luận.

*(Chuyển lại PowerPoint, bấm sang slide 22.)*

### Khi có sự cố

| Tình huống | Cách xử lý và câu nói |
|---|---|
| Trang tải chậm | "Trong lúc trang đang tải, em giải thích…" — nói tiếp ý của bước đó, không đứng im. |
| Lệnh MongoDB báo lỗi | Bỏ qua bước 3: "Phần này có trên slide 21 và trong báo cáo." Chuyển sang dashboard. |
| Dashboard không mở được | Mở video quay sẵn. Nếu không có video: quay lại PowerPoint và đi qua các slide 3, 13, 14, 18, 19, 21: "Do sự cố kết nối, em xin trình bày bằng ảnh chụp từ chính hệ thống." |
| Giảng viên tự nhập một câu ngoài chủ đề tin tức | "Mô hình chỉ biết 10 cụm học từ tin tức, nên câu ngoài miền vẫn bị gán vào cụm gần nhất, nhưng cosine sẽ thấp hơn. Đây là giới hạn nhóm đã nêu." |
| Giảng viên yêu cầu chạy Spark trực tiếp | Chạy bước thống kê (trong lần chạy đã ghi mất khoảng 25 giây), rồi mở Tab 3 để thấy job mới trong mục Running Applications. Lệnh: `docker compose -f docker/docker-compose.yml exec spark-client spark-submit src/eda/statistics.py` |

---

## Lời thoại của Mẫn sau demo

### Slide 22 — Chương 4 (0:05)

> Cảm ơn bạn Lộc. Cuối cùng là phần kết luận.

**[▶]**

### Slide 23 — Kết quả đạt được và hạn chế (1:00)

> Nhóm đã xây dựng hoàn chỉnh quy trình cho 104.790 video của 30 kênh trong 136 ngày; dựng cụm HDFS, Spark và MongoDB bằng Docker; so sánh hai mô hình và chọn Word2Vec kết hợp KMeans theo chỉ số NPMI; tạo ra 10 cụm chủ đề, 53 khoảng tăng đột biến và một dashboard sáu trang.
>
> Hệ thống vẫn còn hạn chế. Cụm chủ đề còn rộng hơn một sự kiện cụ thể, và silhouette còn thấp. Nhóm mới thử k bằng 10, chưa dùng bigram hay bộ tách từ tiếng Việt, chưa đánh giá thủ công. Nhóm chưa đo khả năng mở rộng vì các node chạy trên cùng một máy. Ngoài ra, dữ liệu chỉ gồm tiêu đề, và lượt xem là số tích lũy tại một thời điểm.

**[▶]**

### Slide 24 — Định hướng phát triển (0:40)

> Từ các hạn chế đó, nhóm đề xuất bốn hướng. Một, nâng chất lượng chủ đề bằng bộ tách từ tiếng Việt, bigram, loại ký hiệu kênh và thử nhiều giá trị k. Hai, gom các video về cùng một sự kiện để đếm chính xác. Ba, thu thập định kỳ và lưu lượt xem ở nhiều thời điểm. Bốn, chạy trên nhiều máy để đo khả năng mở rộng, và thử xử lý luồng bằng Spark Structured Streaming.

**[▶]**

### Slide 25 — Cảm ơn (0:10)

> Phần trình bày của nhóm đến đây là kết thúc. Nhóm em cảm ơn thầy cô và các bạn đã lắng nghe, và rất mong nhận được câu hỏi và góp ý.

*(Cả hai đứng cạnh nhau. Câu hỏi về thu thập dữ liệu, HDFS, Spark, MongoDB: Lộc trả lời. Câu hỏi về mô hình, chỉ số, dashboard: Mẫn trả lời.)*

---

## 3. Câu hỏi chuẩn bị

Người trả lời chính ghi trong ngoặc ở tên nhóm câu hỏi; người còn lại bổ sung nếu cần. Câu hỏi chung thì người nào đang cầm micro trả lời trước.

### Dữ liệu và thu thập (Lộc)

**1. Vì sao chọn tiêu đề video YouTube mà không dùng bình luận?**
Tiêu đề có sẵn qua API chính thức, gắn với kênh nguồn, thời gian đăng và liên kết gốc nên kiểm chứng được. Bình luận khó thu đủ hơn, nhiều nhiễu và liên quan dữ liệu cá nhân. Đề tài 5 cho phép chọn bài đăng, bình luận hoặc hashtag; nhóm chọn bài đăng (video). Bình luận nằm trong hướng phát triển.

**2. 104.790 bản ghi có phải là dữ liệu lớn không?**
Về dung lượng thì chưa: CSV khoảng 30 MB, một máy vẫn xử lý được, và nhóm ghi rõ điều này trong báo cáo. Đồ án tập trung vào quy trình phân tán (HDFS, Spark, NoSQL) có thể mở rộng khi tăng số kênh và thời gian. Dữ liệu vẫn có các đặc trưng Variety (văn bản, thời gian, số liệu), Velocity (khoảng 773 video mới mỗi ngày) và Veracity (thiếu lượt thích, tiêu đề trùng).

**3. Thu thập thế nào, có bị giới hạn quota không?**
Lấy danh sách video tải lên của từng kênh bằng playlistItems.list (50 mục mỗi trang), rồi lấy metadata bằng videos.list theo nhóm 50 mã. Chương trình có checkpoint theo kênh để chạy tiếp khi bị dừng, và tự giới hạn 8.000 lượt gọi mỗi ngày. Quota mặc định của YouTube Data API là 10.000 đơn vị mỗi ngày, mỗi lệnh list tốn 1 đơn vị.

**4. Loại trùng như thế nào? Sao không loại tiêu đề giống nhau ở các kênh khác nhau?**
Mỗi video_id chỉ giữ một lần. Cùng kênh và cùng tiêu đề (sau khi chuẩn hóa) thì giữ video đăng mới nhất; bước này loại 1.659 bản ghi. Tiêu đề giống nhau ở các kênh khác nhau vẫn giữ, vì đó là tín hiệu nhiều nguồn cùng đưa tin (có 933 nhóm như vậy).

**5. Dữ liệu thiếu xử lý ra sao?**
Không thiếu lượt xem. Có 12.896 dòng (12,31%) thiếu lượt thích do kênh ẩn số liệu; giá trị này để trống (NULL), không thay bằng 0 để tránh làm sai thống kê.

**6. Lượt xem trong bảng là lượt xem trong ngày đăng à?**
Không. Đó là số tích lũy tại thời điểm lấy metadata (khoảng 14:08–14:11 ngày 14/10/2026). Video đăng sớm có nhiều thời gian tích lũy hơn.

**7. Có vi phạm điều khoản YouTube không?**
Nhóm dùng API chính thức, chỉ lấy metadata công khai (tiêu đề, thời gian, số liệu), không tải nội dung video. Manifest có ghi chú phải làm mới hoặc xóa metadata trong 30 ngày theo chính sách của API.

### Hạ tầng và xử lý (Lộc)

**8. Vì sao hệ số sao chép là 2?**
Cụm có 2 DataNode, nên mỗi block có một bản trên mỗi node; hỏng một node vẫn còn dữ liệu. Mặc định là 3 nhưng chỉ có 2 node thì không đặt đủ 3 bản.

**9. Vì sao lưu Parquet mà không giữ CSV?**
Parquet lưu theo cột, có nén (Snappy) và kèm schema. Spark chỉ đọc các cột cần thiết và không phải suy luận lại kiểu dữ liệu. CSV gốc vẫn được giữ trên HDFS để đối chiếu.

**10. Vì sao cần MongoDB khi đã có HDFS?**
HDFS phù hợp đọc tuần tự khối lớn, không phù hợp truy vấn nhỏ và nhanh cho giao diện. MongoDB lưu các bảng kết quả đã tổng hợp (10 chủ đề, 1.360 dòng xu hướng…) để dashboard truy vấn ngay, không phải chạy Spark mỗi lần bấm.

**11. Hai worker chạy trên một máy thì có thật sự phân tán không?**
Phân tán ở mức dịch vụ: các tiến trình chạy độc lập, trao đổi qua mạng, và Spark chia tác vụ cho 2 worker. Nhóm chưa đo khả năng tăng tốc thật trên nhiều máy; điều này đã ghi trong phần hạn chế.

**12. Vì sao tách tập thống kê và tập huấn luyện?**
Bộ lọc ngôn ngữ fastText loại 11.323 tiêu đề, nhiều trong số đó là tin Việt có tên riêng hoặc từ viết tắt bị nhận nhầm ngôn ngữ. Nếu lọc trên tập thống kê thì số video mỗi ngày sẽ giảm sai. Vì vậy thống kê dùng toàn bộ 104.790 video, còn huấn luyện chỉ dùng 93.456 tiêu đề tiếng Việt đủ tin cậy.

**13. Múi giờ xử lý thế nào?**
Spark chạy theo UTC, sau đó tạo trường giờ Việt Nam (UTC+7) để chia ngày. Nếu chia ngày theo UTC thì các video đăng trước 7 giờ sáng (giờ Việt Nam) sẽ bị xếp vào ngày hôm trước.

### Mô hình và đánh giá (Mẫn)

**14. Vì sao chọn k = 10?**
Nhóm chọn 10 để các chủ đề đủ ít cho người xem đọc được trên dashboard. Nhóm chưa thử nhiều giá trị k (theo silhouette hoặc NPMI), nên chưa chứng minh được 10 là tối ưu. Đây là hướng cải tiến đầu tiên.

**15. Silhouette 0,1611 thấp, mô hình có tốt không?**
Silhouette dương nên các cụm có tách nhau, nhưng còn chồng lấn. Nguyên nhân: tiêu đề ngắn, token tách theo âm tiết, nhiều bản tin tổng hợp nhiều sự kiện, và tên kênh xuất hiện trong tiêu đề. Kết quả phù hợp mục đích khám phá; vì vậy dashboard luôn kèm video gốc để kiểm chứng.

**16. NPMI là gì? Sao dùng NPMI để so hai mô hình?**
NPMI đo mức các từ khóa hàng đầu của một cụm thường xuất hiện cùng nhau trong một tiêu đề, giá trị từ -1 đến 1. Silhouette chỉ áp dụng cho KMeans, log-perplexity chỉ áp dụng cho LDA. NPMI áp dụng được cho cả hai, trên cùng tập tham chiếu.

**17. Vì sao Word2Vec + KMeans mà không dùng TF-IDF + KMeans?**
Tiêu đề ngắn nên vector TF-IDF rất thưa; Word2Vec cho vector dày, gom được các từ dùng trong ngữ cảnh giống nhau. Mã nguồn có sẵn nhánh TF-IDF + KMeans, nhưng trên bộ dữ liệu này nhóm mới chạy 2 cấu hình (E01, E02). Nhóm không khẳng định Word2Vec tốt hơn TF-IDF khi chưa chạy so sánh. Hiện TF-IDF được dùng để xếp từ khóa theo ngày.

**18. Có dùng bộ tách từ tiếng Việt không?**
Chưa. Token được tách theo âm tiết bằng RegexTokenizer, nên “thời tiết” thành “thời” và “tiết”; vì vậy nhãn có dạng “tiết · thời · nay”. Dùng bộ tách từ tiếng Việt hoặc bigram là hướng phát triển.

**19. “thdt”, “skđs” trong nhãn là gì?**
THDT là ký hiệu của Truyền Hình Đồng Tháp và SKĐS là của Báo Sức khỏe & Đời sống; các kênh này thường gắn ký hiệu vào cuối tiêu đề. Điều đó cho thấy tên kênh còn ảnh hưởng đến phân cụm, và nhóm đã nêu trong phần hạn chế. Cách khắc phục là đưa các ký hiệu kênh vào danh sách từ dừng theo miền một cách có kiểm soát.

**20. Phát hiện tăng đột biến thế nào? Sao ngưỡng là 2,5?**
So tỷ trọng của chủ đề trong ngày với trung bình 7 ngày trước: z = (p − μ) / max(σ, ε). Một ngày được đánh dấu khi z > 2,5, có ít nhất 20 video và tỷ trọng ít nhất 1,2 lần mức nền. Ngưỡng 2,5 là lựa chọn của nhóm, không phải ngưỡng thống kê chuẩn; hai điều kiện còn lại giúp tránh báo động ở cụm nhỏ. Quy tắc chỉ mô tả, không giải thích nguyên nhân.

**21. 105 video ngày 14/10 có phải đều nói về lễ an táng liệt sĩ không?**
Không. 105 là số video của cả cụm “hội · sĩ · liệt”. Ba video xem nhiều nhất là về lễ an táng, nhưng hệ thống chưa có bước gom sự kiện hẹp; đây là hướng phát triển thứ hai.

**22. Phân tích văn bản mới chạy thế nào?**
Dashboard nạp PipelineModel đã lưu sau huấn luyện, áp dụng cùng chuỗi tiền xử lý cho câu nhập. KMeans cho cụm gần nhất kèm độ tương đồng cosine; LDA cho tỷ lệ của câu trên từng chủ đề.

**23. Có dự báo được xu hướng không?**
Chưa. Hệ thống chỉ mô tả và phát hiện tăng đột biến trên dữ liệu đã có (phân tích hồi cứu). Dự báo hay xử lý luồng (Spark Structured Streaming) là hướng mở rộng.

### Chung (ai cũng phải trả lời được)

**24. Mỗi bạn làm phần nào?**
- Lộc: danh mục kênh, chương trình thu thập và xuất dữ liệu, cụm Docker (HDFS, Spark, MongoDB), làm sạch và thống kê bằng Spark, tổng hợp xu hướng, xuất MongoDB.
- Mẫn: tiền xử lý văn bản, từ dừng, huấn luyện Word2Vec + KMeans và LDA, đánh giá, dashboard và trang phân tích văn bản.
- Cả hai: báo cáo, slide, thuyết trình.

**25. Làm sao chạy lại được kết quả?**
Một lệnh `scripts/run_pipeline.sh` chạy lần lượt làm sạch, thống kê, huấn luyện, tổng hợp và xuất MongoDB. Seed được cố định là 42; mỗi lượt huấn luyện ghi tham số và chỉ số vào `experiments/youtube_news/experiment_results.csv`. Snapshot CSV có checksum SHA-256 để đối chiếu.

**26. Nếu có thêm thời gian, nhóm làm gì trước?**
Cải thiện chất lượng chủ đề: tách từ tiếng Việt, bigram, loại ký hiệu kênh, thử nhiều giá trị k và đánh giá thủ công độ rõ nhãn trên mẫu tiêu đề.

### Kiến thức Big Data nền tảng (Mẫn trả lời, Lộc bổ sung)

**27. Spark khác MapReduce ở điểm nào?**
MapReduce ghi kết quả trung gian xuống đĩa sau mỗi bước map và reduce. Spark giữ dữ liệu trong bộ nhớ giữa các bước nên nhanh hơn với quy trình nhiều bước, ví dụ làm sạch rồi huấn luyện lặp nhiều vòng. Spark còn có sẵn DataFrame, SQL và MLlib, nên một chương trình làm được cả ETL lẫn học máy.

**28. RDD và DataFrame khác nhau thế nào? Nhóm dùng loại nào?**
RDD là tập dữ liệu phân tán ở mức thấp, không có schema. DataFrame tổ chức dữ liệu theo cột có schema và được bộ tối ưu Catalyst lập kế hoạch thực thi, nên thường nhanh hơn và viết gọn hơn. Nhóm dùng DataFrame cho làm sạch, thống kê, và Pipeline của MLlib cho huấn luyện.

**29. “Thực thi lười” (lazy evaluation) là gì?**
Các phép biến đổi như lọc, chọn cột, nhóm chỉ được ghi lại thành kế hoạch. Spark chỉ thực sự tính khi gặp một hành động như đếm, ghi tệp hay thu kết quả. Nhờ vậy Spark gộp và tối ưu nhiều bước trước khi chạy.

**30. Spark chịu lỗi thế nào khi một executor bị hỏng?**
Spark lưu chuỗi phép biến đổi (lineage) của dữ liệu. Khi một phân vùng bị mất, Spark tính lại phân vùng đó từ dữ liệu gốc trên HDFS theo lineage, không cần chạy lại toàn bộ.

**31. Shuffle là gì? Nhóm cấu hình bao nhiêu phân vùng?**
Shuffle là bước trao đổi dữ liệu giữa các executor khi nhóm hoặc kết nối dữ liệu theo khóa, ví dụ đếm video theo ngày và chủ đề. Đây là bước tốn chi phí nhất. Nhóm đặt `spark.sql.shuffle.partitions = 32`, vì vậy dữ liệu Parquet sau làm sạch có nhiều tệp part.

**32. Spark chạy ở chế độ nào? Sao không dùng YARN?**
Spark Standalone: một master, hai worker. Job được gửi bằng `spark-submit` từ container spark-client tới `spark://spark-master:7077`. Standalone đơn giản hơn YARN khi dựng bằng Docker trên một máy, mà vẫn thể hiện đúng mô hình master – worker.

### HDFS và lưu trữ (Lộc)

**33. Tệp CSV 28,68 MB nhỏ hơn block 128 MB thì lưu thế nào?**
Tệp nằm trong một block, block đó có 2 bản trên 2 DataNode. Block của HDFS chỉ chiếm dung lượng thật của dữ liệu, không chiếm đủ 128 MB.

**34. NameNode hỏng thì sao?**
Cụm của nhóm chỉ có một NameNode, nên NameNode là điểm lỗi duy nhất: dữ liệu vẫn nằm trên DataNode, nhưng không truy cập được cho tới khi NameNode chạy lại. Môi trường thật dùng cơ chế High Availability với một NameNode dự phòng. Đồ án chưa cấu hình phần này.

**35. Một DataNode hỏng thì sao?**
Dữ liệu vẫn đọc được từ bản sao trên DataNode còn lại. NameNode phát hiện qua heartbeat và đánh dấu các block bị thiếu bản sao. Vì cụm chỉ có 2 DataNode, phải có node mới thì mới tạo lại đủ 2 bản.

**36. HDFS khác ổ đĩa thường ở điểm nào?**
HDFS chia tệp thành block, phân tán và sao chép block trên nhiều máy, cho phép nhiều máy đọc song song và chịu lỗi khi một máy hỏng. Ổ đĩa thường chỉ nằm trên một máy. HDFS tối ưu cho tệp lớn đọc tuần tự, không tối ưu cho nhiều tệp nhỏ hoặc truy vấn ngẫu nhiên.

**37. Sao chọn MongoDB mà không chọn Cassandra hay HBase?**
Kết quả tổng hợp có cấu trúc lồng nhau, ví dụ một chủ đề trong một ngày kèm danh sách kênh, từ khóa và video minh họa. Mô hình tài liệu của MongoDB lưu kiểu này tự nhiên, truy vấn linh hoạt theo trường, và dễ dùng từ Python. Cassandra hay HBase hợp với dữ liệu ghi rất nhiều theo khóa, nhu cầu mà đồ án chưa có.

### Dữ liệu (Lộc)

**38. Vì sao chọn khoảng thời gian 01/06 – 14/10/2026 và 32 kênh?**
Nhóm đặt mục tiêu khoảng 100.000 video (manifest ghi `target_rows = 100000` và đã đạt). Cửa sổ hơn bốn tháng và danh mục gồm báo, đài trung ương lẫn địa phương vừa đủ để đạt mục tiêu trong hạn mức API. Kết quả là 104.790 video.

**39. Có kênh nào không có video? Vì sao?**
Có hai kênh: VTV Online và BÁO PHÚ THỌ, cả hai có 0 bản ghi trong snapshot. Nhóm chưa xác minh nguyên nhân; trong báo cáo, nhóm ghi số 0 nghĩa là không có video trong CSV, không có nghĩa là kênh không tồn tại.

**40. Số video giữa các kênh chênh nhau nhiều, có làm lệch kết quả không?**
Có. HTV Tin Tức có 10.483 video, còn VOV2 chỉ có 290. Kênh đăng nhiều sẽ đóng góp nhiều hơn vào số video. Vì vậy dashboard có thêm chỉ số số kênh khác nhau cùng đưa tin, và cụm bị ảnh hưởng bởi ký hiệu kênh (THDT, SKĐS) đã được nêu trong phần hạn chế. Cân bằng trọng số theo kênh là một hướng cải tiến.

**41. Danh mục kênh đã được xác minh chưa?**
Chưa đầy đủ: 14 trong 32 nguồn chưa ghi liên kết xác minh trong `crawl/sources.csv`. Nhóm đã nêu điểm này trong báo cáo.

**42. Lượt xem, lượt thích có được dùng trong mô hình không?**
Không. Mô hình chỉ dùng tiêu đề. Lượt xem chỉ dùng để hiển thị và chọn video minh họa nhiều lượt xem. Vì đây là số tích lũy tại một thời điểm, nếu dùng để đo mức quan tâm thì sẽ thiên về video đăng sớm.

**43. Có nội dung nhạy cảm trong dữ liệu không?**
Bộ lọc từ khóa đánh dấu 4 video. Các video này vẫn được tính trong thống kê, nhưng không được chọn làm ví dụ khi trình chiếu. Công tắc Trình chiếu trên dashboard che các từ nhạy cảm.

**44. Muốn cập nhật dữ liệu mới thì làm thế nào?**
Chạy lại chương trình thu thập và xuất CSV, đưa CSV lên HDFS, rồi chạy `run_pipeline.sh`. Hạn chế hiện tại: chương trình thu thập không tự quét lại các kênh đã đánh dấu hoàn tất, nên khi mở rộng thời gian phải xử lý lại checkpoint. Đây là hướng phát triển “thu thập định kỳ”.

**45. Nếu dữ liệu tăng gấp 100 lần thì hệ thống có chịu được không?**
Về kiến trúc: thêm DataNode cho HDFS, thêm worker cho Spark, tăng số phân vùng. Dashboard vẫn nhanh vì chỉ đọc bảng tổng hợp nhỏ trong MongoDB. Giới hạn chính sẽ là hạn mức của YouTube API ở khâu thu thập. Nhóm chưa đo thực nghiệm khả năng mở rộng, nên đây là nhận định thiết kế, không phải kết quả đo.

### Mô hình (Mẫn)

**46. Tham số Word2Vec là gì, sao chọn như vậy?**
100 chiều, cửa sổ ngữ cảnh 5, minCount 5 (bỏ từ xuất hiện dưới 5 lần), 3 vòng lặp, seed 42. Đây là cấu hình cơ bản, đủ cho tiêu đề ngắn và chạy nhanh trên cụm nhỏ. Nhóm chưa dò tham số này.

**47. Độ tương đồng cosine là gì? Sao chuẩn hóa vector?**
Cosine đo góc giữa hai vector: càng gần 1 thì hai tiêu đề càng giống hướng nghĩa. Vector tiêu đề được chuẩn hóa về độ dài 1 (chuẩn L2). Khi đó khoảng cách Euclid mà KMeans dùng tương đương thứ tự với khoảng cách cosine, nên tiêu đề dài hay ngắn không ảnh hưởng đến kết quả.

**48. KMeans khởi tạo tâm thế nào? Có ra kết quả khác nhau mỗi lần chạy không?**
Dùng k-means|| (bản song song của k-means++) với seed 42 và tối đa 30 vòng lặp. Seed cố định giúp chạy lại giống nhau; nhưng tính toán phân tán vẫn có thể lệch rất nhỏ, và mã cụm có thể đổi thứ tự nếu huấn luyện lại.

**49. Nhãn “thdt · công · học” được tạo thế nào?**
Bằng c-TF-IDF: gom tất cả token của cụm, tính tần suất từ trong cụm, nhân với trọng số giảm cho những từ phổ biến ở mọi cụm, rồi lấy 3 từ cao nhất. Nhãn là tự động; nhóm không tự đặt tên “giáo dục” hay “kinh tế” khi chưa kiểm chứng.

**50. Có tiêu đề nào không gán được cụm không?**
Có 2 trong 104.790 video, vì sau tiền xử lý không còn từ nào nằm trong từ vựng của Word2Vec. 104.788 video còn lại đều được gán.

**51. Log-perplexity 7,3048 nghĩa là tốt hay xấu?**
Giá trị này chỉ có ý nghĩa khi so giữa các cấu hình LDA trên cùng dữ liệu (càng thấp càng tốt). Nhóm chỉ có một cấu hình LDA nên không kết luận tốt hay xấu tuyệt đối; nhóm so sánh hai mô hình bằng NPMI.

**52. Sao không dùng PhoBERT hay mô hình ngôn ngữ lớn?**
Nhóm chưa thử. Đồ án tập trung vào công cụ có sẵn trong Spark MLlib để chạy phân tán trên cụm. PhoBERT cần GPU hoặc thời gian suy luận lớn với hơn 100.000 tiêu đề. Dùng embedding từ mô hình tiếng Việt chuyên dụng là một hướng cải thiện chất lượng chủ đề.

**53. Không có nhãn chuẩn thì làm sao biết mô hình đúng?**
Bài toán là học không giám sát nên không có độ chính xác. Nhóm dùng chỉ số nội tại (NPMI, silhouette), đọc từ khóa và video tiêu biểu từng cụm, rồi đối chiếu một ngày cụ thể (14/10). Đánh giá thủ công trên mẫu tiêu đề là bước nhóm chưa làm.

**54. Tỷ trọng cụm lớn nhất khi huấn luyện là 20,23%, sao trên dashboard lại là 21,71%?**
20,23% tính trên tập huấn luyện (93.456 tiêu đề). 21,71% tính sau khi áp mô hình lên toàn bộ tập thống kê (104.788 video được gán). Hai tập khác nhau nên tỷ lệ khác nhau.

### Xu hướng và dashboard (Mẫn)

**55. Sao dùng tỷ trọng mà không dùng số video?**
Tổng số video thay đổi theo ngày trong tuần. Trung bình thứ Năm có 829 video, còn Chủ nhật chỉ có 648. Nếu đếm số video thì chủ đề nào cũng có vẻ “giảm” vào cuối tuần. Tỷ trọng cho biết cơ cấu chủ đề thật sự thay đổi.

**56. Sao so với 7 ngày trước?**
Bảy ngày bao trọn một chu kỳ tuần như ở câu 55, nên mức nền không bị lệch vì cuối tuần. Hệ thống cần ít nhất 3 ngày lịch sử mới tính điểm z.

**57. ε trong công thức z là gì?**
Là sàn của độ lệch chuẩn, bằng 10% độ lệch chuẩn của toàn chuỗi. Nếu 7 ngày trước gần như không đổi thì σ rất nhỏ, chia cho σ sẽ làm z tăng vọt dù thay đổi rất ít. Sàn ε chặn trường hợp này.

**58. Hai ngày tăng đột biến liền nhau tính là một hay hai?**
Các ngày tăng đột biến của cùng chủ đề cách nhau không quá 2 ngày được gộp thành một khoảng. Ví dụ khoảng 12–13/09 của cụm “mưa · lũ · bão”.

**59. Chủ đề “tăng nhanh nhất” trên Bảng điểm tính thế nào?**
Bằng chênh lệch số video so với kỳ trước (ngày trước hoặc tháng trước) và tỷ lệ tăng phần trăm. Khi kỳ trước bằng 0 hoặc kỳ hiện tại chưa đủ ngày (như tháng 10), nhóm lưu ý không nên đọc phần trăm như tốc độ đáng tin cậy.

**60. Sao chọn Streamlit mà không làm web bằng React hay Power BI?**
Streamlit viết hoàn toàn bằng Python, cùng ngôn ngữ với pipeline, nên nạp được mô hình Spark đã lưu để phân tích câu mới ngay trên dashboard. Làm bằng React cần thêm một backend API; Power BI không chạy được mô hình Spark tùy chỉnh.

**61. Dashboard có bị chậm khi nhiều người dùng không?**
Dashboard chỉ đọc bảng tổng hợp nhỏ từ MongoDB và có bộ nhớ đệm (phần lớn truy vấn giữ 10 phút), nên thao tác xem không gọi Spark. Riêng trang phân tích văn bản chạy mô hình trên câu nhập nên chậm hơn. Nhóm chưa kiểm thử tải nhiều người dùng.

**62. Hệ thống có an toàn không?**
Các cổng dịch vụ (HDFS, Spark, MongoDB, dashboard) chỉ mở trên địa chỉ 127.0.0.1, nên máy khác không truy cập được. Khóa API YouTube lưu trong biến môi trường hoặc tệp `.env`, không đưa lên kho mã nguồn. Hệ thống chưa có đăng nhập vì chỉ chạy trên máy cá nhân.

### Vận hành và kiểm thử (Lộc)

**63. Chạy toàn bộ pipeline mất bao lâu?**
Theo các lần chạy đã ghi: làm sạch 50,3 giây, thống kê 25,2 giây, huấn luyện Word2Vec + KMeans 59,4 giây, LDA 49,8 giây, tổng hợp 66,2 giây. Tổng khoảng 4 phút, chưa tính thời gian khởi động Spark cho từng bước và thu thập dữ liệu từ API.

**64. Có kiểm thử tự động không?**
Có, cho các hàm tính NPMI, chuỗi thời gian và phát hiện tăng đột biến trong thư mục `tests`. Khi chạy pytest: 9 bài đạt, 1 bài bỏ qua. Kiểm thử này xác nhận các hàm tính đúng, không đánh giá chất lượng chủ đề.

**65. Sao dùng Docker?**
Một tệp `docker-compose.yml` dựng cả cụm (NameNode, 2 DataNode, Spark master, 2 worker, spark-client, MongoDB, dashboard) với đúng phiên bản, nên máy khác chạy được bằng một lệnh, không phải cài Hadoop và Spark thủ công.

### Câu hỏi khó, dễ bị hỏi vặn (cả hai)

**66. Đề tài yêu cầu “mạng xã hội”, YouTube của báo, đài có phải mạng xã hội không?**
YouTube là nền tảng mạng xã hội chia sẻ video; mỗi video là một bài đăng công khai có tương tác (lượt xem, lượt thích). Nguồn của nhóm là kênh của báo, đài, nên dữ liệu phản ánh cách các cơ quan báo chí đưa tin trên mạng xã hội, không phải ý kiến người dùng. Nhóm nói rõ giới hạn này trong phần phạm vi.

**67. Kết quả này dùng được vào việc gì trong thực tế?**
Theo dõi cơ cấu đưa tin theo ngày và tháng; phát hiện nhanh chủ đề đang tăng để đọc sâu; so sánh độ phủ giữa các kênh. Đây là công cụ khám phá, hỗ trợ người đọc thu hẹp phạm vi cần kiểm chứng, chưa phải hệ thống đo dư luận.

**68. Nếu bỏ HDFS và Spark, dùng pandas trên một máy thì có được không?**
Với 30 MB hiện tại thì được, và có thể còn nhanh hơn vì không tốn chi phí khởi động cụm. Nhóm chọn HDFS và Spark để đáp ứng yêu cầu của môn học và để quy trình mở rộng được khi dữ liệu tăng. Nhóm không khẳng định Spark nhanh hơn ở quy mô hiện tại.

**69. Sao kết quả mô hình chưa tốt mà vẫn đưa lên dashboard?**
Vì dashboard luôn kèm từ khóa, số kênh và video gốc để người dùng tự kiểm chứng; nhãn được ghi rõ là tự động. Nhóm báo cáo trung thực chỉ số thấp và đã nêu hướng cải thiện, thay vì che đi.

**70. Phần nào trong đồ án là do nhóm tự làm, phần nào dùng thư viện?**
Thư viện: Hadoop, Spark MLlib (Word2Vec, KMeans, LDA), fastText, MongoDB, Streamlit. Nhóm tự viết: chương trình thu thập có checkpoint và loại trùng, quy trình ETL tách hai tập, tính NPMI, gán nhãn bằng c-TF-IDF, tính tỷ trọng và phát hiện tăng đột biến, xuất MongoDB và toàn bộ dashboard.

### Lưu ý khi trả lời

- Câu nào thuộc phần hạn chế thì nhận thẳng, kèm hướng khắc phục. Không nói những gì nhóm chưa làm (chưa thử nhiều k, chưa đo khả năng mở rộng, chưa đánh giá thủ công).
- Khi nêu số liệu, chỉ dùng số có trong báo cáo hoặc slide.
- Người nắm phần đó trả lời trước; người còn lại chỉ bổ sung, không ngắt lời.
