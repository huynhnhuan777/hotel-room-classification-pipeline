# Hướng Dẫn Chạy Dự Án

## 📋 Bước 1: Cài đặt môi trường

### Yêu cầu hệ thống
- Python 3.7 trở lên
- pip (package manager)

### Cài đặt thư viện cần thiết

**Cách 1: Sử dụng requirements.txt (Khuyến nghị)**
```bash
pip install -r requirements.txt
```

**Cách 2: Cài đặt thủ công**
```bash
pip install pandas scikit-learn joblib numpy
```

Nếu bạn muốn sử dụng Gemini API:
```bash
pip install google-generativeai
```

## 🚀 Bước 2: Chuẩn bị dữ liệu

Đảm bảo bạn có các file CSV sau trong thư mục dự án:
- `train.csv` - Dữ liệu training (bắt buộc)
- `val.csv` - Dữ liệu validation (bắt buộc cho một số script)

## 📝 Bước 3: Chạy các script

### Workflow cơ bản (Khuyến nghị)

#### **Bước 3.1: Train model và tạo predictions**
```bash
python run_ml_model.py
```

Script này sẽ:
- ✅ Load dữ liệu từ `train.csv`
- ✅ Train Random Forest model
- ✅ Đánh giá trên test set
- ✅ Lưu model vào `room_class_model.pkl`
- ✅ Tạo predictions cho validation set
- ✅ Lưu kết quả vào `val_with_prediction.csv` và `train_with_prediction.csv`

**Thời gian chạy**: ~1-5 phút (tùy vào kích thước dữ liệu)

#### **Bước 3.2: Đánh giá model**
```bash
python evaluate.py
```

Script này sẽ:
- ✅ Đánh giá trên cả training và validation sets
- ✅ Hiển thị accuracy, precision, recall, F1-score
- ✅ Hiển thị confusion matrix
- ✅ Phân tích các lỗi phân loại phổ biến

#### **Bước 3.3: Phân tích lỗi chi tiết**
```bash
python error_analysis.py
```

Script này sẽ:
- ✅ Phân tích chi tiết các lỗi phân loại
- ✅ Tính error rate theo từng class
- ✅ Lưu kết quả phân tích vào `val_with_error_analysis.csv`

---

### Các script khác (Tùy chọn)

#### **Chỉ train model (không tạo predictions)**
```bash
python train_model_only.py
```
Sử dụng khi bạn chỉ muốn train model mà không cần predictions ngay.

#### **Chuẩn bị Gemini model**
```bash
python classify_rooms_gemini.py
```
Tạo file cấu hình cho Gemini API model (nếu bạn muốn sử dụng LLM).

---

## 🎯 Chạy tất cả các bước một lúc

Bạn có thể chạy lần lượt các lệnh sau:

```bash
# 1. Train và predict
python run_ml_model.py

# 2. Đánh giá
python evaluate.py

# 3. Phân tích lỗi
python error_analysis.py
```

Hoặc trên Windows PowerShell:
```powershell
python run_ml_model.py; python evaluate.py; python error_analysis.py
```

---

## ⚠️ Xử lý lỗi thường gặp

### Lỗi: "FileNotFoundError: train.csv"
**Nguyên nhân**: Thiếu file dữ liệu
**Giải pháp**: Đảm bảo file `train.csv` và `val.csv` có trong thư mục dự án

### Lỗi: "ModuleNotFoundError: No module named 'sklearn'"
**Nguyên nhân**: Chưa cài đặt thư viện
**Giải pháp**: Chạy `pip install -r requirements.txt`

### Lỗi: "Missing features: [...]"
**Nguyên nhân**: File CSV thiếu các cột cần thiết
**Giải pháp**: Kiểm tra lại file CSV có đủ các features như trong README.md

### Lỗi khi chạy trên Windows
Nếu gặp lỗi encoding, thử:
```bash
chcp 65001
python run_ml_model.py
```

---

## 📊 Kiểm tra kết quả

Sau khi chạy xong, bạn sẽ có các file output:

1. **`room_class_model.pkl`** - Model đã train (có thể dùng để predict sau)
2. **`train_with_prediction.csv`** - Training data + predictions
3. **`val_with_prediction.csv`** - Validation data + predictions  
4. **`val_with_error_analysis.csv`** - Validation data + phân tích lỗi chi tiết

---

## 💡 Tips

- Chạy `run_ml_model.py` trước vì các script khác cần file predictions
- Kiểm tra output trong terminal để xem accuracy và các metrics
- File `val_with_error_analysis.csv` chứa thông tin chi tiết về các lỗi phân loại

---

## 🔄 Chạy lại từ đầu

Nếu muốn chạy lại từ đầu, bạn có thể xóa các file output:
- `room_class_model.pkl`
- `train_with_prediction.csv`
- `val_with_prediction.csv`
- `val_with_error_analysis.csv`

Sau đó chạy lại các script theo thứ tự.
