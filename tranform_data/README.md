# Data Transformation (Xử lý & Biến đổi dữ liệu)
## Giới thiệu
Sau khi dữ liệu đã được thu thập và gộp lại (merged), module này chịu trách nhiệm biến đổi dữ liệu thành nhiều thông tin mới để chuẩn bị cho các bước sau đó.
## Chức năng chính
Chuẩn hóa văn bản: Chuyển đổi các cột phân loại về dạng viết thường, loại bỏ khoảng trắng dư thừa.

Trích xuất đặc trưng (Regex Extraction):
Giường (Bed Types): Xác định loại giường (King, Queen, Single, Bunk...) từ thông tin phòng.
Tiện ích (Facilities): Tách các tiện ích quan trọng (Wifi, AC, Breakfast, Pool, Kitchen...) từ chuỗi văn bản thô.
Tính toán chỉ số (Calculated Metrics):
   price_per_m2: Giá trên mỗi mét vuông.
   m2_per_person: Diện tích bình quân đầu người.
   num_facilities: Tổng số lượng tiện ích hiện có.
Phân loại hạng phòng: Nhận diện các từ khóa hạng sang (Deluxe, Suite, Premium...) để gắn nhãn has_luxury_keyword.
## Cấu trúc dữ liệu đầu ra
Bảng dữ liệu sau biến đổi bao gồm các nhóm cột:
Nhóm                           Các cột tiêu biểu
Thông tin gốc         "Final Price, Max People, Area_m2, room_class"
Chỉ số tính toán      "price_per_m2, m2_per_person, num_facilities"
Loại giường (Boolean) "is_king, is_double, is_single, is_sofa..."
Tiện ích (Boolean)    "has_wifi, has_ac, has_pool, has_kitchen..."
Gắn nhãn               has_luxury_keyword

## Hướng dẫn sử dụng
1. Yêu cầu hệ thống
Python 3.x
Thư viện: pandas, sqlalchemy, psycopg2-binary
Database: PostgreSQL đã có bảng merged_data.
2. Cấu hình kết nối
Chỉnh sửa thông số trong dict DB_CONFIG tại file transform.py để phù hợp với database của bạn:
PythonDB_CONFIG = {
    "dbname": "booking_data",
    "user": "postgres",
    "password": "YOUR_PASSWORD",
    "host": "localhost",
    "port": "5432"
}
3. Thực thi
Chạy script bằng lệnh:
   python transform.py
## Đầu ra (Output)
Sau khi chạy thành công, hệ thống sẽ sinh ra 2 nguồn dữ liệu:
Database: Bảng tranform_data trong PostgreSQL (tự động ghi đè nếu đã tồn tại).
File vật lý: Lưu tại đường dẫn ../data/hotel_data_transformed.csv.