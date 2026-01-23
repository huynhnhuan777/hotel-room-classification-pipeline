# 🏨 Hotel Room Classification - Data Processing Pipeline

## 📋 Tổng Quan

Quy trình xử lý dữ liệu cho bài toán **Multi-class Classification** nhằm phân loại phòng khách sạn thành các lớp khác nhau dựa trên các đặc trưng của phòng.

---

## 🎯 Định Nghĩa Bài Toán

### **Loại Bài Toán**
- **Type**: Multi-class Classification (Supervised Learning)
- **Objective**: Dự đoán lớp phòng (room_class) dựa trên các đặc trưng của phòng
- **Method**: Supervised Learning

### **Biến Mục Tiêu (Target Variable)**
```
room_class: Phân loại phòng thành 6 lớp (0, 1, 2, 3, 4, 5)
```

### **Biến Đầu Vào (Features)**
**Tổng cộng: 22 features**

#### 1. **Giá Cả (Price Features)** - 2 features
- `Final Price`: Giá cuối cùng của phòng (đã normalize)
- `price_per_m2`: Giá trên một mét vuông

#### 2. **Kích Thước Phòng (Room Size)** - 3 features
- `Max People`: Số người tối đa có thể ở
- `Area_m2`: Diện tích phòng (m²)
- `m2_per_person`: Diện tích trên một người

#### 3. **Loại Giường (Bed Type)** - 6 features
- `is_king`: Có giường king
- `is_queen`: Có giường queen
- `is_double`: Có giường đôi
- `is_single`: Có giường đơn
- `is_bunk`: Có giường tầng
- `is_sofa`: Có giường sofa

#### 4. **Tiện Ích (Amenities)** - 10 features
- `has_luxury_keyword`: Phòng luxury
- `has_wifi`: WiFi miễn phí
- `has_ac`: Điều hòa không khí
- `has_breakfast`: Bao gồm bữa sáng
- `has_tv`: Tivi
- `has_pool`: Hồ bơi
- `has_balcony`: Ban công/terace
- `has_parking`: Chỗ đỗ xe
- `has_kitchen`: Nhà bếp/kitchenette
- `has_fridge`: Tủ lạnh

#### 5. **Số Lượng Tiện Ích (Facilities Count)** - 1 feature
- `num_facilities`: Tổng số tiện ích trong phòng

---

## 🔄 Quy Trình Xử Lý Dữ Liệu

### **Step 1: Load Train / Val CSV**
```python
# Load training and validation datasets
train_path = './Data/train.csv'
val_path = './Data/val.csv'

df_train = pd.read_csv(train_path)      # 8,497 samples
df_val = pd.read_csv(val_path)          # 1,822 samples
```

**Output:**
- Train set: 8,497 mẫu
- Val set: 1,822 mẫu

---

### **Step 2: Kiểm Tra Dữ Liệu (Data Inspection)**

Kiểm tra:
- ✅ Kích thước dữ liệu (shape)
- ✅ Kiểu dữ liệu (data types)
- ✅ Giá trị thiếu (missing values)
- ✅ Thống kê cơ bản (statistics)
- ✅ Phân bố biến mục tiêu (target distribution)

**Kết quả:**
- ✓ Không có giá trị thiếu
- ✓ Phân bố target cân bằng giữa các lớp

---

### **Step 3: Chọn Features + Target (Feature Selection)**

```python
# Define target and features
target = 'room_class'
X_train = df_train.drop(columns=[target])   # Features
y_train = df_train[target]                  # Target

X_val = df_val.drop(columns=[target])
y_val = df_val[target]
```

**Categorization of Features:**
| Category | Count | Features |
|----------|-------|----------|
| Price | 2 | Final Price, price_per_m2 |
| Room Size | 3 | Max People, Area_m2, m2_per_person |
| Bed Types | 6 | is_king, is_queen, is_double, is_single, is_bunk, is_sofa |
| Amenities | 10 | has_wifi, has_ac, has_breakfast, has_tv, has_pool, has_balcony, has_parking, has_kitchen, has_fridge, has_luxury_keyword |
| Facilities | 1 | num_facilities |
| **Total** | **22** | **All features** |

**Feature-Target Correlation:**
```
Top 3 correlated features with room_class:
1. Final Price        (correlation: highest)
2. Area_m2           (correlation: strong positive)
3. Max People        (correlation: moderate positive)
```

---

### **Step 4: Xử Lý Missing Values**

```python
# Check and handle missing values
missing_count = X_train.isnull().sum().sum()

if missing_count > 0:
    # For numerical: fill with mean
    # For categorical: fill with mode
    print("Missing values handled!")
else:
    print("✓ No missing values!")
```

**Status:** ✅ Không có giá trị thiếu cần xử lý

---

### **Step 5: Encode Categorical Features**

```python
from sklearn.preprocessing import LabelEncoder

if len(categorical_features) > 0:
    for col in categorical_features:
        le = LabelEncoder()
        X_train[col] = le.fit_transform(X_train[col].astype(str))
        X_val[col] = le.transform(X_val[col].astype(str))
else:
    print("✓ No categorical features to encode!")
```

**Status:** ✅ Tất cả features đã là numerical (không cần encode)

---

### **Step 6: Scale Numerical Features**

```python
from sklearn.preprocessing import StandardScaler

# Apply StandardScaler: (x - mean) / std
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train[numerical_features])
X_val_scaled = scaler.transform(X_val[numerical_features])
```

**Scaling Method:** `StandardScaler`
- ✓ Zero mean (μ = 0)
- ✓ Unit variance (σ = 1)
- ✓ Giảm ảnh hưởng của outliers
- ✓ Cải thiện hiệu năng các mô hình ML

**Features Scaled:** Tất cả 22 numerical features

---

### **Step 7: Lưu Processed Dataset**

```python
# Save processed datasets
train_processed.to_csv('./Data/train_processed.csv', index=False)
val_processed.to_csv('./Data/val_processed.csv', index=False)

# Save processing objects
with open('./Data/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

with open('./Data/processing_metadata.json', 'w') as f:
    json.dump(metadata, f)
```

---

## 📁 Output Files

```
Processing/Data/
├── train_processed.csv          # 8,497 × 23 (22 features + 1 target)
├── val_processed.csv            # 1,822 × 23
├── scaler.pkl                   # StandardScaler object for test set
└── processing_metadata.json     # Processing metadata
```

### **Processing Metadata:**
```json
{
  "scaling": {
    "scaler_type": "StandardScaler",
    "numerical_features": [...all 22 features...],
    "mean": [...mean values...],
    "scale": [...scale values...]
  },
  "encoding": {
    "categorical_features": [],
    "encoders": {}
  },
  "data_info": {
    "train_samples": 8497,
    "val_samples": 1822,
    "total_features": 22,
    "target": "room_class",
    "target_classes": 6
  }
}
```

---

## 🚀 Cách Sử Dụng

### **1. Chạy Notebook**
```bash
# Mở Processed.ipynb trong Jupyter
jupyter notebook Processed.ipynb

# Hoặc sử dụng VS Code
# Ctrl + Shift + D để chạy tất cả cells
```

### **2. Load Processed Data**
```python
import pandas as pd
import pickle

# Load processed data
train_processed = pd.read_csv('./Data/train_processed.csv')
val_processed = pd.read_csv('./Data/val_processed.csv')

# Load scaler for future test set
with open('./Data/scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

# For future predictions
X_test_scaled = scaler.transform(X_test)
```

### **3. Chuẩn Bị cho Model Training**
```python
from sklearn.model_selection import train_test_split

# Separate features and target
X_train = train_processed.drop('room_class', axis=1)
y_train = train_processed['room_class']

X_val = val_processed.drop('room_class', axis=1)
y_val = val_processed['room_class']

# Ready for model training!
```

---

## 📊 Thống Kê Dữ Liệu

### **Data Split**
| Dataset | Samples | Features + Target | Percentage |
|---------|---------|------------------|-----------|
| Train | 8,497 | 23 | 82.3% |
| Val | 1,822 | 23 | 17.7% |
| **Total** | **10,319** | **23** | **100%** |

### **Target Distribution**
```
room_class 0: ~17%
room_class 1: ~17%
room_class 2: ~17%
room_class 3: ~17%
room_class 4: ~17%
room_class 5: ~15%
```
*(Phân bố cân bằng - Good for classification)*

### **Feature Statistics (After Scaling)**
- Mean (μ): 0 for all features
- Std Dev (σ): 1 for all features
- Range: Typically [-3, 3] (Gaussian distribution)

---

## ⚙️ Điều Kiện Tiên Quyết

### **Thư Viện Cần Thiết**
```python
pandas >= 1.3.0
numpy >= 1.21.0
scikit-learn >= 0.24.0
matplotlib >= 3.4.0
seaborn >= 0.11.0
```

### **Cài Đặt**
```bash
pip install -r requirements.txt
```

---

## 📝 Ghi Chú Quan Trọng

### **Scaling Considerations**
- ✅ StandardScaler được áp dụng cho TẤT CẢ numerical features
- ✅ Fitted trên training data
- ✅ Applied trên validation data sử dụng training parameters
- ⚠️ **Important**: Khi predict trên test set, phải dùng cùng scaler này

### **Train-Val Split**
- ✅ Dữ liệu được split trước khi xử lý
- ✅ Scaler được fit trên train set
- ✅ Validation set được transform sử dụng train parameters
- ✅ Tránh data leakage

### **Missing Values**
- ✅ Dataset gốc không có missing values
- ✅ Logic xử lý sẵn có trong code (mean cho numerical, mode cho categorical)

### **Categorical Features**
- ✅ Tất cả features đã là numerical
- ✅ Không cần LabelEncoder hoặc OneHotEncoder
- ✅ Các binary features (is_king, has_wifi...) là 0/1

---

## 🔗 Liên Kết Tài Liệu

- **Processed Notebook**: [Processed.ipynb](./Processed.ipynb)
- **Raw Data**: [train.csv](./Data/train.csv), [val.csv](./Data/val.csv)
- **Processed Data**: [train_processed.csv](./Data/train_processed.csv), [val_processed.csv](./Data/val_processed.csv)

---

## ✅ Checklist - Sẵn Sàng cho Model Training

- [x] Load và kiểm tra dữ liệu
- [x] Chọn features và target
- [x] Xử lý missing values
- [x] Encode categorical features
- [x] Scale numerical features
- [x] Lưu processed datasets
- [ ] **Next Step**: Train classification models (Random Forest, Logistic Regression, SVM, etc.)

---

## 📚 Các Bước Tiếp Theo

1. **Model Training** (`Random_Forest.ipynb`)
   - Train Random Forest Classifier
   - Hyperparameter tuning
   - Cross-validation

2. **Model Evaluation**
   - Accuracy, Precision, Recall, F1-score
   - Confusion Matrix
   - ROC-AUC curves

3. **Visualization** (`visualize_data_hotel.ipynb`)
   - Feature importance
   - Model performance visualization

---

## 👤 Thông Tin Tác Giả

**Project**: Hotel Room Classification Pipeline
**Purpose**: Multi-class classification for hotel room categorization
**Date**: 2026

---

*Last Updated: January 23, 2026* ✨
