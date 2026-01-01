# Phân Tích Dữ Liệu Khách Sạn (Hotel Data Analysis)
Bước này sử dụng Python (Pandas, Matplotlib, Seaborn) để phân tích và trực quan hóa dữ liệu khách sạn, nhằm tìm ra mối liên hệ giữa giá cả, vị trí, diện tích và xếp hạng sao.

Dưới đây là mô tả chi tiết các bước xử lý và trực quan hóa dữ liệu trong Notebook.

1. **Chuẩn bị Dữ liệu (Data Preparation)**
**Chức năng:**

Import các thư viện cần thiết: pandas (xử lý dữ liệu), matplotlib & seaborn (vẽ biểu đồ).

Đọc dữ liệu từ file full_data_merged.csv.

Tạo các cột tính toán mới: Chuyển đổi giá từ VNĐ sang đơn vị "Triệu VNĐ" để các con số trên biểu đồ gọn gàng, dễ đọc hơn.

**Lý do thực hiện:**

Bước đệm bắt buộc để đảm bảo dữ liệu sạch và đúng định dạng trước khi vẽ. Việc chia đơn vị tiền tệ giúp tránh các số quá lớn (ví dụ: 5.000.000 -> 5.0) gây rối mắt trên trục toạ độ.

2. **Trực quan hóa Dữ liệu (Data Visualization)**
**2.1. Biểu đồ 1: Số lượng Khách sạn/Phòng theo Quận**
Loại biểu đồ: Bar Chart (Biểu đồ cột ngang).

Chức năng: Thống kê số lượng phòng khách sạn hiện có tại từng Quận trong tập dữ liệu.

**Lý do chọn:**

Dữ liệu "Quận" là biến định danh (Categorical).

Sử dụng biểu đồ cột ngang tối ưu hơn cột dọc vì tên các Quận thường khá dài. Khi vẽ ngang, nhãn trục (labels) sẽ không bị chồng chéo, giúp người xem dễ dàng so sánh số lượng giữa các khu vực.

**2.2. Biểu đồ 2: Tương quan giữa Giá và Diện tích**
Loại biểu đồ: Scatter Plot (Biểu đồ phân tán).

Chức năng: Biểu diễn mối quan hệ giữa hai biến liên tục: Diện tích phòng (Area_m2) và Giá phòng (Final Price). Kích thước và màu sắc điểm biểu diễn số Sao (Stars).

**Lý do chọn:**

Scatter plot là công cụ tốt nhất để quan sát sự tương quan (correlation) và phân bố của từng điểm dữ liệu riêng lẻ.

Việc kết hợp thêm biến thứ 3 là Số Sao (thông qua hue và size) giúp giải thích các ngoại lệ: Tại sao có những phòng diện tích nhỏ nhưng giá lại rất cao? (Trả lời: Do là khách sạn 5 sao).

**2.3. Biểu đồ 3: Phân bố Giá theo Xếp hạng Sao**
Loại biểu đồ: Box Plot (Biểu đồ hộp).

Chức năng: So sánh khoảng giá (thấp nhất, cao nhất, trung vị) của các nhóm khách sạn từ 1 đến 5 sao.

**Lý do chọn:**

Thay vì chỉ dùng giá trung bình (Mean) dễ bị sai lệch bởi các giá trị cực đoan, Box Plot cho cái nhìn toàn diện về sự phân tán dữ liệu.

Giúp phát hiện nhanh các Outliers (giá trị ngoại lai) - ví dụ: các khách sạn 3 sao nhưng có giá đắt ngang 5 sao, hoặc các khách sạn 5 sao giá rẻ bất ngờ.

**2.4. Biểu đồ 4: Ma trận Tương quan (Correlation Matrix)**
Loại biểu đồ: Heatmap (Bản đồ nhiệt).

Chức năng: Hiển thị hệ số tương quan Pearson giữa tất cả các biến số (Giá, Rating, Review Count, Khoảng cách, Diện tích...).

**Lý do chọn:**

Cung cấp cái nhìn tổng quan cho toàn bộ bộ dữ liệu.

Màu sắc (đậm/nhạt, nóng/lạnh) giúp não bộ nhận diện nhanh chóng các mối quan hệ tuyến tính mạnh (ví dụ: Diện tích càng lớn thì Giá càng cao) mà không cần đọc từng con số.

3. **Yêu cầu cài đặt (Requirements)**
Để chạy notebook này, cần cài đặt các thư viện sau:

pip install pandas matplotlib seaborn