# Hotel Room Classification AI - Training Pipeline
Tài liệu này mô tả quy trình huấn luyện mô hình AI dự đoán hạng phòng (room_class). Quy trình được thiết kế theo chuẩn khoa học dữ liệu (Data Science Standard) với chiến lược chia dữ liệu 3 phần để đảm bảo mô hình không bị học vẹt (Overfitting) và chọn được tham số tối ưu nhất.

1. Luồng dữ liệu (Data Pipeline)
Hệ thống hoạt động theo mô hình Database-Centric:

Input: Đọc dữ liệu từ bảng PostgreSQL (encoding_data và tranform_data).

Process: Chia dữ liệu -> Tinh chỉnh tham số (Tuning) -> Huấn luyện -> Đánh giá.

Output:

Lưu mô hình (.pkl).

Ghi kết quả đánh giá ngược lại vào Database (test_evaluation_results).

2. Chiến lược Chia Dữ liệu (Splitting Strategy)
Để đảm bảo tính khách quan, dữ liệu được chia làm 3 tập riêng biệt theo tỷ lệ 70% - 15% - 15% sử dụng kỹ thuật Stratified Sampling (đảm bảo tỷ lệ các loại phòng Standard/Deluxe/Suite cân bằng ở cả 3 tập).
Chi tiết vai trò từng tập:
Tên Tập Dữ liệu     Tỷ lệ     Vai trò (Analogy)         Chức năng trong Code   
  Training Set       70%       Sách Giáo Khoa      Dùng để model.fit(). Máy sẽ học các quy luật từ tập này.
  Validation Set     15%        Đề Thi Thử         Dùng để tinh chỉnh tham số. Máy sẽ thử nghiệm các cấu hình khác nhau trên tập                                              này để tìm ra cấu hình tốt nhất.
  Test Set           15%        Đề Thi Thật        Dữ liệu hoàn toàn bí mật (Unseen Data). Chỉ dùng duy nhất 1 lần cuối cùng để 
                                                   chấm điểm độ chính xác thực tế.
3. Quy trình Huấn luyện & Tinh chỉnh (Training & Tuning Flow)
Thay vì chọn cố định một tham số, hệ thống sử dụng vòng lặp để tìm ra mô hình tốt nhất (Best Model Selection).

Bước 1: Chuẩn bị
Tải dữ liệu và chia thành 3 tập X_train, X_val, X_test.

Bước 2: Hyperparameter Tuning (Vòng lặp tối ưu)
Hệ thống thử nghiệm thuật toán Random Forest với số lượng cây (n_estimators) khác nhau: [50, 100, 200, 300].

Huấn luyện mô hình với n cây trên tập Train.

Chấm điểm mô hình đó trên tập Validation.

So sánh với kết quả cũ, nếu tốt hơn thì tạm thời giữ danh hiệu "Best Model".

Bước 3: Đánh giá cuối cùng (Final Evaluation)
Lấy "Best Model" tìm được ở Bước 2.

Chạy dự đoán trên tập Test (tập chưa bao giờ được dùng để chỉnh sửa hay huấn luyện).

Kết quả Accuracy tại bước này là con số trung thực nhất về hiệu năng của AI.
4. Kết quả đầu ra (Outputs)
Sau khi chạy script, hệ thống sinh ra các tài nguyên sau:

File Model: hotel_ai_model.pkl

Đây là file mô hình đã được huấn luyện với cấu hình tốt nhất (Best Parameter).

Database Table: test_evaluation_results

Bảng chứa kết quả dự đoán chi tiết trên tập Test.

Các cột quan trọng: ai_prediction_name (AI đoán), is_correct (1=Đúng, 0=Sai).

Report File: ../data/final_ai_report.csv

File CSV backup của bảng database trên, phục vụ cho việc phân tích nhanh bằng Excel.
5. Hướng dẫn chạy (How to Run)
Yêu cầu cài đặt
pip install pandas sqlalchemy psycopg2-binary scikit-learn joblib
Lệnh thực thi
python train_ai.py
