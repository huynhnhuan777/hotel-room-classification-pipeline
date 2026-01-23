Hotel Room Classification – Logistic Regression Pipeline
📌 Mô tả

Dự án này sử dụng Logistic Regression (Softmax Regression) để phân loại hạng phòng khách sạn dựa trên các đặc trưng về giá, diện tích, tiện nghi và loại giường.
Ngoài ra, mô hình còn được dùng để phát hiện các mẫu dữ liệu có khả năng bị gán nhãn sai (misaligned labels) dựa trên độ tin cậy dự đoán.

🎯 Mục tiêu

Huấn luyện mô hình Softmax Regression cho bài toán phân loại đa lớp

Đánh giá hiệu năng mô hình trên tập test

Phát hiện các bản ghi có:

Nhãn gốc ≠ nhãn dự đoán

Độ tin cậy (confidence) cao

Xuất danh sách các mẫu nghi ngờ sai nhãn để rà soát thủ công

🧠 Mô hình sử dụng

Logistic Regression (Multiclass – Softmax)

Solver: lbfgs

Chuẩn hóa dữ liệu: StandardScaler

Xử lý mất cân bằng lớp: class_weight="balanced"

Khi sử dụng solver lbfgs, Logistic Regression tự động mở rộng cho bài toán đa lớp theo cơ chế Softmax Regression.

🧾 Dữ liệu đầu vào

File CSV:

./processing/LogisticRegression/train.csv

🎯 Nhãn

room_class (đa lớp)

🔢 Đặc trưng sử dụng

Giá & diện tích:

Final Price

Area_m2

price_per_m2

m2_per_person

Sức chứa & tiện nghi:

Max People

num_facilities

Từ khóa cao cấp:

has_luxury_keyword

Loại giường:

is_king, is_queen, is_double, is_single, is_bunk, is_sofa

Tiện ích:

has_wifi, has_ac, has_breakfast, has_tv

has_pool, has_balcony, has_parking

has_kitchen, has_fridge

⚙️ Quy trình xử lý

Load dữ liệu từ CSV

Chia tập:

80% train

20% test (stratified)

Chuẩn hóa dữ liệu bằng StandardScaler

Huấn luyện Logistic Regression (Softmax)

Đánh giá mô hình (Accuracy, Precision, Recall, F1-score)

Dự đoán toàn bộ dataset

Phát hiện nhãn lệch dựa trên:

nhãn*gốc ≠ nhãn_dự*đoán AND confidence ≥ 0.9

Xuất file kết quả

📤 File đầu ra

data_labeled_logreg_train.csv

Toàn bộ dữ liệu + nhãn dự đoán + độ tin cậy

suspected_label_errors_logreg_train.csv

Các mẫu nghi ngờ bị gán nhãn sai

🚀 Cách chạy
py processing/LogisticRegression/LogisticRegression.py

📊 Đánh giá mô hình

Accuracy trên tập test

Classification Report cho từng lớp phòng

Top đặc trưng quan trọng (dựa trên hệ số Logistic Regression)

🧪 Phát hiện nhãn sai (Misaligned Labels)

Một bản ghi được xem là nghi ngờ sai nhãn nếu:

Nhãn gốc khác nhãn dự đoán

Xác suất Softmax lớn hơn hoặc bằng 0.9

Các bản ghi này nên được:

Kiểm tra thủ công

Hoặc dùng để làm sạch dữ liệu trước khi huấn luyện model nâng cao (XGBoost, RandomForest…)
