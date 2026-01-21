# Booking.com Data Exporter

Script thực hiện công đoạn cuối cùng: Trích xuất dữ liệu sạch từ PostgreSQL, gộp bảng và xuất ra các định dạng file tiêu chuẩn (CSV & JSON) để sử dụng.

## Công nghệ
* **Python 3.8+**
* **Pandas:** Xử lý dataframe, gộp bảng và xuất CSV.
* **SQLAlchemy:** Kết nối và truy vấn Database.
* **JSON:** Cấu trúc dữ liệu phân cấp (Nested).

## Cài đặt & Cấu hình

1. **Cài đặt thư viện:**
   `pip install pandas sqlalchemy psycopg2-binary`

2. **Cấu hình Database:**
   Sửa biến `DB_CONFIG` trong code (User, Password, Dbname).

3. **Cấu hình Output:**
   Dữ liệu sẽ được xuất ra thư mục `data/` (được định nghĩa trong biến `OUTPUT_FOLDER`).

## Luồng xử lý (Workflow)

1. **Query & Merge (Gộp dữ liệu):**
   * Thực hiện **LEFT JOIN** giữa bảng chính (`hotel_data_cleaned`) và bảng chi tiết (`room_details_cleaned`).
   * Mục đích: Lấy toàn bộ thông tin khách sạn kèm theo diện tích/tiện ích (nếu có).

2. **Export CSV (Dạng phẳng):**
   * **Xử lý:** Điền giá trị 0 cho các ô trống (Null) ở cột Rating/Review.
   * **Định dạng:** Đổi tên cột sang Title Case (VD: `hotel_name` -> `Hotel Name`).
   * **Kết quả:** File `full_data_merged.csv` (Thích hợp cho Excel, PowerBI).

3. **Export JSON (Dạng phân cấp):**
   * **Xử lý:** Group dữ liệu theo Khách sạn -> Danh sách các phòng.
   * **Cấu trúc:**
     * `info`: Thông tin chung (Tên, Địa chỉ...).
     * `stats`: Chỉ số (Sao, Điểm đánh giá...).
     * `rooms`: Danh sách mảng các phòng (Loại phòng, Giá, Tiện ích...).
   * **Kết quả:** File `final_hotel_data.json` (Thích hợp cho Web App/Mobile App).