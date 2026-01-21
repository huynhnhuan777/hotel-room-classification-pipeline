# Data Normalization (Chuẩn hóa dữ liệu)
## Giới thiệu
Sau bước biến đổi dữ liệu (Transformation), các đặc trưng (features) thường có đơn vị và khoảng giá trị (scale) rất khác nhau. Module này sử dụng kỹ thuật Min-Max Scaling để đưa tất cả các biến số về cùng một khoảng giá trị từ 0 đến 1.
## Tại sao cần bước này?
Trong dữ liệu khách sạn của chúng ta:
   Giá tiền (Final Price): Có thể lên đến hàng chục triệu.
   Số người (Max People): Thường chỉ từ 1 đến 10.
   Diện tích (Area_m2): Thường từ 15 đến 200.
Nếu đưa trực tiếp vào các thuật toán Machine Learning (như K-Means, KNN, hay Neural Networks), thuật toán sẽ bị "đánh lừa" rằng cột Giá tiền quan trọng hơn vì nó có trị số lớn hơn. Chuẩn hóa giúp các cột có giá trị ngang nhau trong mô hình.
## Phương pháp: 
Min-Max Scaling
Công thức áp dụng cho từng giá trị x trong một cột:
   xnormalized = (x - xmin)/(xmax - xmin)
Kết quả:
   Giá trị nhỏ nhất xmin sẽ trở thành 0.
   Giá trị lớn nhất xmax sẽ trở thành 1.
   Các giá trị khác nằm trong khoảng (0, 1).
## Các cột được thực hiện chuẩn hóa
Chúng ta chỉ chuẩn hóa các cột có kiểu dữ liệu số liên tục (Continuous Numeric):
   Final Price
   Max People
   Area_m2
   price_per_m2
   m2_per_person
   num_facilities
Các cột Boolean/Binary (như has_wifi, is_king) không cần chuẩn hóa vì chúng vốn đã là 0 và 1.
## Hướng dẫn sử dụng
1. Yêu cầu cài đặt
Ngoài các thư viện ở các bước trước, bạn cần cài đặt thêm thư viện học máy scikit-learn:
   pip install scikit-learn
2. Cấu hình
Đảm bảo thông tin kết nối trong DB_CONFIG khớp với Database PostgreSQL của bạn. 
Script sẽ tìm bảng đầu vào là tranform_data.
3. Thực thiChạy script normalization:
   python normalization.py
## Đầu ra (Output)
Database: Tạo hoặc ghi đè bảng normalized_data trong PostgreSQL.
File vật lý: Xuất file sạch tại ../data/hotel_data_normalized.csv.