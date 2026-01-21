# Booking.com Async Scraper (Full Pipeline)

Hệ thống tự động thu thập dữ liệu khách sạn từ Booking.com, bao gồm 2 module: cào danh sách tìm kiếm và cào chi tiết phòng.

## Công nghệ sử dụng
* **Python 3.8+**
* **Playwright (Async):** Xử lý trang dynamic, scroll, click modal và chặn media.
* **PostgreSQL & SQLAlchemy:** Lưu trữ dữ liệu.
* **Pandas:** Xử lý và làm sạch dữ liệu.

## Cài đặt

1. **Cài đặt thư viện Python:**
   pip install pandas playwright sqlalchemy psycopg2-binary

2. **Cài đặt trình duyệt Chromium:**
    playwright install chromium

3. **Cấu hình Database:**
Mở các file script, tìm biến DB_CONFIG.

Cập nhật thông tin user, password, dbname tương ứng với PostgreSQL của bạn.

**Module 1: Scrape Danh Sách (Search)**
Dùng để lấy dữ liệu tổng quan: Tên, Giá, Sao, Review...

**Luồng hoạt động**

Kết nối Database, tạo bảng hotel_scenarios.

Sinh 20 kịch bản tìm kiếm ngẫu nhiên (Random số lượng khách/phòng).

Mở trình duyệt, truy cập lần lượt: TP.HCM, Vũng Tàu, Bình Dương.

Dùng JavaScript Injection để trích xuất dữ liệu nhanh.

Lưu dữ liệu vào bảng hotel_scenarios.

**Module 2: Scrape Chi Tiết (Room Details)**
Dùng để lấy Diện tích (m²) và Tiện ích phòng cụ thể dựa trên link đã cào.

**Cấu hình ID**

Sửa biến ID_RANGES trong code để chạy theo khoảng ID mong muốn (VD: chạy từ ID 2114 đến 8421).

**Luồng hoạt động**

Kết nối Database, tạo bảng room_details (nếu chưa có).

Lấy danh sách link và loại phòng từ bảng nguồn (SOURCE_TABLE) theo khoảng ID_RANGES.

Truy cập link, chặn tải ảnh/media để tăng tốc độ.

Tìm đúng dòng chứa loại phòng, quét diện tích. Nếu thiếu, tự động click mở Modal để lấy dữ liệu ẩn.

Lưu vào DB theo cơ chế Upsert:

Nếu ID đã tồn tại -> Update (Cập nhật).

Nếu ID chưa có -> Insert (Thêm mới).