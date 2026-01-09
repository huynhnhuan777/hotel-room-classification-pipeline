# Booking.com Data Cleaning Pipeline (Full ETL)

Script thực hiện quy trình **ETL** để làm sạch, chuẩn hóa toàn bộ dữ liệu khách sạn (Tổng quan & Chi tiết) từ PostgreSQL.

## Công nghệ
* **Python 3.8+**
* **Pandas & Numpy:** Xử lý và tính toán dữ liệu.
* **SQLAlchemy:** Đọc/Ghi dữ liệu vào Database.
* **Regex:** Trích xuất địa chỉ và số liệu diện tích.

## Cài đặt & Cấu hình

1. **Cài đặt thư viện:**
   `pip install pandas numpy sqlalchemy psycopg2-binary`

2. **Cấu hình Database:**

Sửa biến DB_CONFIG trong code (User, Password, Dbname).

3. **Cấu hình Mapping (Tùy chọn):**

Sửa BED_MAPPING và ROOM_MAPPING nếu muốn thêm từ khóa nhận diện loại giường/phòng mới.

## Luồng xử lý (Workflow)

### Module 1: Làm sạch Tổng quan (Hotels)
1. Extract (Đọc): Lấy dữ liệu thô từ bảng hotel_scenarios.

2. Transform (Chuẩn hóa):

Phân loại: Gán nhãn loại Phòng/Giường dựa trên từ khóa.

Địa chỉ: Dùng Regex tách tên Quận/Huyện/Thành phố.

Logic giá: Tự động sửa lỗi nếu Giá gốc < Giá bán; tính % giảm giá.

Đơn vị: Chuyển đổi khoảng cách sang km; Boolean hóa các trường tiện ích.

3. Filter (Lọc):

Loại bỏ dữ liệu thiếu (Unknown/Other) trên các cột quan trọng.

Khử trùng lặp 2 lớp: Lớp cơ bản và Lớp nâng cao (theo Tên + Giá + Loại phòng).

4. Load (Lưu):

Lưu kết quả vào bảng hotel_data_cleaned.

Tự động tạo cột id và thiết lập PRIMARY KEY.

---

### Module 2: Làm sạch Chi tiết (Room Details)
1. Extract (Đọc): Lấy dữ liệu thô từ bảng room_details.

2. Transform (Chuẩn hóa):

Diện tích: Dùng Regex trích xuất số thực (Float) từ chuỗi văn bản (VD: "25 m²" -> 25.0).

Tiện ích: Chuyển về chữ thường (lowercase), loại bỏ khoảng trắng thừa.

Thời gian: Chuẩn hóa cột updated_at về định dạng Datetime.

3. Load (Lưu):

Lưu kết quả vào bảng room_details_cleaned.

Tự động thiết lập PRIMARY KEY cho cột hotel_id.