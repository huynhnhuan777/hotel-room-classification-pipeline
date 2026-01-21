XGBoost Room Classification & Label Quality Detection
Tổng quan

Script Python sử dụng XGBoost để:

Huấn luyện mô hình phân loại hạng phòng khách sạn

Phát hiện nhãn bị gán sai (label errors) dựa trên độ tin cậy dự đoán

Xuất danh sách các mẫu nghi ngờ để review và làm sạch dữ liệu

🎯 Mục đích

Trong quá trình gán nhãn (thủ công hoặc bằng LLM), dữ liệu có thể bị sai nhãn.
Script này giúp:

Phát hiện các mẫu không phù hợp giữa đặc trưng và nhãn
Cải thiện chất lượng dataset
Đánh giá hiệu quả mô hình phân loại
📊 Dữ liệu đầu vào

File: train.csv, val.csv

Target: room_class
(Deluxe, Executive, Luxury, Standard, Suite, Superior)

Features (22): giá, diện tích, số người, tiện nghi, loại giường, từ khóa luxury,…

⚙️ Cấu hình chính
CONF_THRESHOLD = 0.9

0.9 (mặc định): cân bằng tốt

> 0.95: rất chắc chắn, ít false positive
> < 0.8: phát hiện nhiều hơn nhưng dễ nhiễu

🔄 Quy trình hoạt động

Load & chuẩn bị dữ liệu

Train/Test split (80/20, stratified)

Huấn luyện XGBoost

XGBClassifier(
n_estimators=200, # 200 decision trees
max_depth=6, # Độ sâu tối đa mỗi cây
learning_rate=0.1, # Tốc độ học
subsample=0.8, # 80% mẫu cho mỗi cây
colsample_bytree=0.8 # 80% features cho mỗi cây
)

Đánh giá: Accuracy, Classification Report, Feature Importance

Phát hiện lệch nhãn

Một dòng được coi là misaligned khi:

(predicted_label ≠ room_class) AND (confidence ≥ CONF_THRESHOLD)

Output
1️⃣ data*labeled_xgboost*\*.csv

Dataset đầy đủ kèm:

llm_room_class: nhãn dự đoán

xgb_conf: độ tin cậy

is_misaligned: True / False

2️⃣ suspected*label_errors*\*.csv

Chỉ chứa các dòng nghi ngờ gán nhãn sai (để review)

Cách sử dụng kết quả

Bước 1: Review file suspected*label_errors*\*.csv
Bước 2: So sánh nhãn gốc và nhãn dự đoán
Bước 3: Quyết định:

✅ Sửa nhãn

Giữ nguyên (edge case)

Bước 4: Cập nhật dataset & train lại
