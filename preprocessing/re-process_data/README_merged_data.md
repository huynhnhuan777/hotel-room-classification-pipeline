# Pipeline Xử lý & Chuẩn hóa Dữ liệu Booking Khách sạn
Dự án này bao gồm một hệ thống các script Python để thu thập, làm sạch, làm giàu và cân bằng dữ liệu khách sạn từ ba nguồn chính: Booking.com, Ivivu, và Mytour. Dữ liệu sau khi xử lý được lưu trữ tập trung tại cơ sở dữ liệu PostgreSQL.

## Yêu cầu hệ thống
Ngôn ngữ: Python 3.9+

Cơ sở dữ liệu: PostgreSQL

Thư viện cần thiết:

   pip install pandas numpy sqlalchemy psycopg2 playwright sdv matplotlib seaborn openpyxl

   python -m playwright install chromium

## Cấu trúc Pipeline
Quy trình xử lý được thực hiện theo thứ tự từ bước 1 đến bước 5 để đảm bảo tính toàn vẹn của dữ liệu:

Giai đoạn 1: Đổi tên cột và chuẩn hóa thô (data1)

Giai đoạn 2: Làm sạch dữ liệu số, Lọc null, Lọc trùng lặp (data2)

Giai đoạn 3: Bổ sung dữ liệu thiếu (data3)

Giai đoạn 4: Lọc dữ liệu thiếu và dữ liệu không phù hợp (data4)

Giai đoạn 5: Lọc Outliers và cân bằng dữ liệu bằng AI (data5)

## Chi tiết các file xử lý
1. process_merged_data1.py ( Đổi tên cột và chuẩn hóa thô)
Chức năng: Đọc dữ liệu từ các file CSV/Excel gốc.

Nhiệm vụ chính:

Ánh xạ (Mapping) các cột khác nhau từ 3 nguồn về một cấu trúc chuẩn.

Chuẩn hóa room_class (Luxury, Suite, Deluxe, Standard...) dựa trên từ khóa.

Chuẩn hóa bed_type (Single, Double, King...).

Lưu dữ liệu vào 3 bảng: clean_booking, clean_ivivu, clean_mytour.

2. process_merged_data2.py (Làm sạch dữ liệu số, Lọc null, Lọc trùng lặp)
Chức năng: Xử lý các cột dữ liệu định dạng số và loại bỏ rác.

Nhiệm vụ chính:

Sử dụng Regex để trích xuất số từ các chuỗi (ví dụ: "500.000 VND" -> 500000, "35m2" -> 35).

Loại bỏ các dòng có giá trị quan trọng bị thiếu (Price, Area, People).

Khử trùng lặp (Drop duplicates) dựa trên tổ hợp tên khách sạn, loại phòng và giá.

3. process_merged_data3.py (Bổ sung địa điểm bằng Crawling)
Chức năng: Sử dụng Playwright để tự động hóa trình duyệt, tìm kiếm thông tin bị thiếu.

Nhiệm vụ chính:

Truy cập vào Hotel Link của các bản ghi có location là "Unknown".

Quét nội dung trang web để nhận diện địa điểm (Hồ Chí Minh, Vũng Tàu, Bình Dương...).

Cập nhật lại thông tin địa điểm vào Database.

4. process_merged_data4.py (Lọc dữ liệu vi mô)
Chức năng: Loại bỏ các bản ghi không phù hợp với tiêu chí phân tích.

Nhiệm vụ chính:

Loại bỏ các phòng vẫn không xác định được vị trí sau khi crawl.

Loại bỏ các phòng có diện tích quá lớn (> 120m2) để tránh nhiễu dữ liệu căn hộ/biệt thự lớn.

Lưu dự phòng các dòng bị loại ra file CSV để kiểm tra.

5. process_merged_data5.py (Cân bằng dữ liệu bằng AI - CTGAN)
Chức năng: Xử lý mất cân bằng dữ liệu giữa các hạng phòng và loại bỏ outlier triệt để.

Nhiệm vụ chính:

Loại bỏ Outlier theo phương pháp IQR (liên quan đến Giá và Diện tích).

Sử dụng mô hình CTGAN (Synthetic Data Vault) để sinh dữ liệu giả lập cho các nhóm phòng bị thiếu hụt (Upsampling).

Đảm bảo phân bổ dữ liệu đồng đều giữa các room_class.

Lưu kết quả cuối cùng vào các bảng có hậu tố _balanced.

## Hướng dẫn sử dụng
Cấu hình Database: Thay đổi thông tin DB_CONFIG trong các file Python để khớp với tài khoản PostgreSQL của bạn.

Chuẩn bị dữ liệu: Đảm bảo các file nguồn (.csv, .xlsx) nằm đúng đường dẫn trong thư mục ../merged_data/.

Thực thi theo thứ tự:

Bash

python process_merged_data1.py
python process_merged_data2.py
python process_merged_data3.py
python process_merged_data4.py
python process_merged_data5.py
Kiểm tra kết quả: Các bảng dữ liệu sạch nhất sẽ nằm trong Database với tên clean_booking_balanced, clean_ivivu_balanced, v.v.