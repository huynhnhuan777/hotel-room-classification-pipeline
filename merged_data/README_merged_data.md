# Tích hợp dữ liệu.
## Tổng quan 
Script này là bước thứ hai trong quy trình xử lý dữ liệu khách sạn (Data Pipeline). Nhiệm vụ chính là thu thập các dữ liệu đã được làm sạch từ nhiều nguồn khác nhau (Booking.com, iVIVU, Mytour) đang lưu trong PostgreSQL, sau đó hợp nhất chúng thành một cơ sở dữ liệu duy nhất và xuất ra file CSV để phục vụ cho việc phân tích (EDA) hoặc huấn luyện mô hình Machine Learning.

## Chức năng chính
Kết nối Database: Tự động kết nối tới PostgreSQL thông qua SQLAlchemy.

Hợp nhất dữ liệu (Data Merging): Đọc 3 bảng dữ liệu riêng biệt (clean_booking, clean_ivivu, clean_mytour) và gộp thành một DataFrame duy nhất.

Xử lý hậu kỳ: Kiểm tra và xử lý các giá trị thiếu (null) còn sót lại ở cột location.

Lưu trữ kép (Dual Storage):

Ghi đè dữ liệu đã gộp vào bảng merged_data trong database.

Xuất file merged_hotel_data.csv với định dạng chuẩn tiếng Việt (UTF-8-SIG).

## Hướng dẫn sử dụng
1. Tiền đề
Đảm bảo bạn đã cài đặt các thư viện cần thiết:

    pip install pandas sqlalchemy psycopg2-binary

2. Cấu hình Database
Mở file script và cập nhật thông tin trong dict DB_CONFIG để khớp với máy cục bộ của bạn:

    DB_CONFIG = {
        "dbname": "your_db_name",
        "user": "your_username",
        "password": "your_password",
        "host": "localhost",
        "port": "5432"
    }

3. Chạy script
Mở terminal và chạy lệnh:

    python merged_data.py

## Kết quả đầu ra
Database: Bảng merged_data được tạo mới hoặc cập nhật trong PostgreSQL.

File: File merged_hotel_data.csv được lưu tại thư mục ../data/.

Log: Console sẽ hiển thị tổng số dòng dữ liệu đã gộp thành công.