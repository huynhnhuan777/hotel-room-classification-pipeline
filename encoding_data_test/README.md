# Categorical Encoding (Mã hóa nhãn dữ liệu)
## Giới thiệu
Hầu hết các thuật toán Machine Learning (như Random Forest, SVM, hay Neural Networks) đều yêu cầu đầu vào là các con số. Module này xử lý cột phân loại duy nhất còn sót lại trong tập dữ liệu là room_class (Ví dụ: "Standard", "Deluxe", "Suite"...) và chuyển đổi chúng thành các số nguyên (0, 1, 2...).

## Phương pháp: Label Encoding
Sử dụng LabelEncoder từ thư viện scikit-learn.
Cơ chế: Mỗi giá trị văn bản duy nhất sẽ được gán cho một số nguyên dựa trên thứ tự bảng chữ cái.
Ví dụ: 
Budget -> 0
Deluxe -> 1
Luxury -> 2
## Các tính năng nổi bật trong Script
Thống kê mẫu (Class Distribution): Trước khi mã hóa, script sẽ in ra số lượng dòng của từng hạng phòng. Điều này giúp kiểm tra xem dữ liệu có bị mất cân bằng
(imbalanced data) hay không.
Bảng tra cứu nhãn (Mapping Dictionary): Script tự động xuất ra bảng tra cứu (ví dụ: {'deluxe': 0, 'standard': 1}) để người dùng biết số nào tương ứng với nhãn nào.
Bảo toàn dữ liệu: Sử dụng phương thức .copy() để đảm bảo không ghi đè trực tiếp lên DataFrame gốc trong quá trình xử lý.
## Hướng dẫn sử dụng
1. Yêu cầu hệ thống
Đảm bảo bạn đã cài đặt các thư viện cần thiết:
   pip install pandas sqlalchemy scikit-learn psycopg2-binary
2. Luồng dữ liệu (Data Flow)
Script này kết nối trực tiếp vào Database để lấy dữ liệu từ bước trước đó:
Input: Bảng normalized_data (Dữ liệu đã chuẩn hóa số).
Process: Mã hóa cột room_class.
Output: 
   Lưu vào Database bảng mới tên là encoding_data.
   Xuất file CSV cuối cùng tại ../data/hotel_data_final.csv.
3. Thực thi
Chạy lệnh sau trong terminal:
   python encoding.py

## Kết quả cuối cùng
Sau khi hoàn thành Module này, tập dữ liệu hoàn toàn là số (All-Numeric Data) phục vụ cho các bước sau.
