# ================================
# 1. IMPORT THƯ VIỆN
# ================================
import os
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, classification_report
import joblib

# ================================
# 2. LẤY ĐƯỜNG DẪN THƯ MỤC FILE .PY
# ================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

train_path = os.path.join(BASE_DIR, "train.csv")
val_path   = os.path.join(BASE_DIR, "validation.csv")
test_path  = os.path.join(BASE_DIR, "test.csv")

# ================================
# 3. LOAD DATA
# ================================
train_df = pd.read_csv(train_path)
val_df   = pd.read_csv(val_path)
test_df  = pd.read_csv(test_path)

TARGET = "room_class"

# ================================
# 4. TÁCH TRAIN
# ================================
X_train = train_df.drop(columns=[TARGET])
y_train = train_df[TARGET]

# LƯU DANH SÁCH FEATURE (CỰC KỲ QUAN TRỌNG)
FEATURE_COLUMNS = X_train.columns.tolist()

# ================================
# 5. TÁCH VALIDATION & TEST (ĐỒNG BỘ FEATURE)
# ================================
X_val = val_df[FEATURE_COLUMNS]
y_val = val_df[TARGET]

X_test = test_df[FEATURE_COLUMNS]   # dù test có room_class cũng không sao

num_classes = y_train.nunique()

# ================================
# 6. KHAI BÁO MÔ HÌNH XGBOOST
# ================================
model = xgb.XGBClassifier(
    objective="multi:softmax",     # phân loại nhiều nhãn
    num_class=num_classes,
    n_estimators=300,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    eval_metric="mlogloss"
)

# ================================
# 7. TRAIN MODEL
# ================================
model.fit(X_train, y_train)

# ================================
# 8. ĐÁNH GIÁ VALIDATION
# ================================
val_pred = model.predict(X_val)

print("===== VALIDATION RESULT =====")
print("Accuracy:", accuracy_score(y_val, val_pred))
print(classification_report(y_val, val_pred))

# ================================
# 9. DỰ ĐOÁN TEST
# ================================
test_df["room_class_pred"] = model.predict(X_test)

output_path = os.path.join(BASE_DIR, "test_with_prediction_xgboost.csv")
test_df.to_csv(output_path, index=False)

# ================================
# 10. LƯU MODEL
# ================================
model_path = os.path.join(BASE_DIR, "xgboost_room_class.pkl")
joblib.dump(model, model_path)

print("✔ XGBoost train & predict hoàn tất")
print("✔ Output:", output_path)
