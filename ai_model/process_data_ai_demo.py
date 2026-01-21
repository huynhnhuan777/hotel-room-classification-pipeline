import pandas as pd
import numpy as np
import joblib
import optuna
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostRegressor

from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import StackingRegressor

# ==============================================================================
# Đặt log về INFO để in ra quá trình chạy (Trial 1, 2, 3...)
# ==============================================================================
optuna.logging.set_verbosity(optuna.logging.INFO)

# ==============================
# 1. ĐỌC DỮ LIỆU & LÀM SẠCH
# ==============================

print(" Đang tải dữ liệu...")
df = pd.read_csv("../data_booking.com/full_data_merged.csv")

# Lọc dữ liệu cơ bản
df = df[df["Final Price"] > 0]
df = df[[
    "Final Price","Area_m2_cleaned","Stars_Clean","Review Count",
    "Rating_Clean","Distance_KM","Adults","Children","Rooms",
    "District","Room_Class","Facilities_cleaned"
]]
df.dropna(inplace=True)
print(f" Số dòng dữ liệu hợp lệ: {len(df)}")

# ==============================
# 2. TẠO ĐẶC TRƯNG (FEATURE ENGINEERING)
# ==============================
print(" Đang tạo đặc trưng AI...")

# --- 1. XỬ LÝ ĐẲNG CẤP PHÒNG (TỪ CỘT ROOM_CLASS CÓ SẴN) ---
ROOM_RANKING = {
    'Presidential': 10, 'Penthouse': 9, 'Villa': 8, 'Resort': 7,
    'Bungalow': 6, 'Suite': 6, 'Luxury': 5, 'Grand': 5, 'Executive': 5,
    'Apartment': 4, 'Studio': 4, 'Apartment & Studio': 4,
    'Deluxe': 4,
    'Superior': 3, 'Classic': 3, 'Family': 3, 'Connecting': 3, 'Triple': 3, 'Quadruple': 3,
    'Standard': 2, 'Economy': 1, 'Dorm': 0, 'Capsule': 0, 'Other': 2
}
df["Room_Score"] = df["Room_Class"].map(ROOM_RANKING).fillna(2)

# --- 2. TẠO TƯƠNG TÁC ĐẶC TRƯNG ---
# Diện tích nhân Số sao (Phòng rộng ở khách sạn xịn giá trị hơn phòng rộng ở nhà nghỉ)
df["Area_x_Stars"] = df["Area_m2_cleaned"] * df["Stars_Clean"]

# Điểm đẳng cấp nhân Diện tích
df["Score_x_Area"] = df["Room_Score"] * df["Area_m2_cleaned"]

# --- 3. CÁC ĐẶC TRƯNG CƠ BẢN ---
df["Total_Guests"] = df["Adults"] + df["Children"]

# Chỉ đếm số lượng tiện ích 
df["Facility_Count"] = df["Facilities_cleaned"].astype(str).apply(lambda x: x.count(",") + 1)

# Biến mục tiêu
df["Log_Price"] = np.log1p(df["Final Price"])
target = "Log_Price"

# ==============================
# CẬP NHẬT DANH SÁCH FEATURES
# ==============================
numeric_features = [
    "Area_m2_cleaned", "Stars_Clean", "Review Count", "Rating_Clean",
    "Distance_KM", "Adults", "Children", "Rooms",
    "Total_Guests", "Facility_Count",
    
    # Các chỉ số đặc biệt
    "Room_Score",       
    "Area_x_Stars",     
    "Score_x_Area"      
]

categorical_features = ["District", "Room_Class"]

X = df[numeric_features + categorical_features]
y = df[target]

print(f" Đã tạo xong đặc trưng!")

# ==============================
# 3. CHIA TRAIN / TEST
# ==============================
print(" Đang chia dữ liệu (80/20)...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ==============================
# 4. THIẾT LẬP PIPELINE XỬ LÝ
# ==============================

# Xử lý số: Điền giá trị thiếu (median) -> Chuẩn hóa (StandardScaler)
num_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

# Preprocessor 1: Dành cho XGBoost
# THÊM: .set_output(transform="pandas") để giữ tên cột
preprocessor_xgb = ColumnTransformer([
    ("num", num_pipeline, numeric_features),
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features)
], verbose_feature_names_out=False).set_output(transform="pandas") 

# Preprocessor 2: Dành cho LightGBM & CatBoost
# THÊM: .set_output(transform="pandas") để giữ tên cột
preprocessor_ordinal = ColumnTransformer([
    ("num", num_pipeline, numeric_features),
    ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical_features)
], verbose_feature_names_out=False).set_output(transform="pandas")

# ==============================
# 5. TỐI ƯU HYPERPARAMETER (OPTUNA)
# ==============================

print("\n Bắt đầu tối ưu hóa tham số (Optuna)...")
print("   (Quá trình này sẽ in ra chi tiết từng lần thử nghiệm)")

# --- 5.1 XGBoost ---
def xgb_objective(trial):
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 500, 1000),
        "max_depth": trial.suggest_int("max_depth", 3, 8),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.1),
        "subsample": trial.suggest_float("subsample", 0.7, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.7, 1.0),
        "random_state": 42,
        "n_jobs": -1
    }
    
    model = Pipeline([
        ('prep', preprocessor_xgb),
        ('model', xgb.XGBRegressor(**params))
    ])
    
    score = -cross_val_score(model, X_train, y_train, cv=3, scoring='neg_mean_absolute_error').mean()
    return score

print("\n--- OPTIMIZING XGBOOST ---")
xgb_study = optuna.create_study(direction="minimize")
xgb_study.optimize(xgb_objective, n_trials=100) 
best_xgb = xgb_study.best_params
print(f" XGBoost BEST: {best_xgb}")

# --- 5.2 LightGBM ---
def lgb_objective(trial):
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 500, 1000),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.1),
        "num_leaves": trial.suggest_int("num_leaves", 20, 50),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "subsample": trial.suggest_float("subsample", 0.7, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.7, 1.0),
        "random_state": 42,
        "n_jobs": -1,
        "verbose": -1
    }
    
    model = Pipeline([
        ('prep', preprocessor_ordinal),
        ('model', lgb.LGBMRegressor(**params))
    ])
    
    score = -cross_val_score(model, X_train, y_train, cv=3, scoring='neg_mean_absolute_error').mean()
    return score

print("\n--- OPTIMIZING LIGHTGBM ---")
lgb_study = optuna.create_study(direction="minimize")
lgb_study.optimize(lgb_objective, n_trials=100)
best_lgb = lgb_study.best_params
best_lgb['verbose'] = -1
print(f" LightGBM BEST: {best_lgb}")

# --- 5.3 CatBoost ---
def cat_objective(trial):
    params = {
        "iterations": trial.suggest_int("iterations", 500, 1000),
        "depth": trial.suggest_int("depth", 4, 8),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.1),
        "verbose": 0,
        "allow_writing_files": False,
        "random_state": 42
    }
    
    model = Pipeline([
        ('prep', preprocessor_ordinal),
        ('model', CatBoostRegressor(**params))
    ])
    
    score = -cross_val_score(model, X_train, y_train, cv=3, scoring='neg_mean_absolute_error').mean()
    return score

print("\n--- OPTIMIZING CATBOOST ---")
cat_study = optuna.create_study(direction="minimize")
cat_study.optimize(cat_objective, n_trials=100)
best_cat = cat_study.best_params
best_cat['verbose'] = 0
best_cat['allow_writing_files'] = False
print(f" CatBoost BEST: {best_cat}")

# ==============================
# 6. XÂY DỰNG FINAL STACKING MODEL
# ==============================

print("\n Đang cấu hình Stacking Ensemble (Kết hợp 3 AI)...")


# Tạo 3 pipeline chính thức với tham số tốt nhất vừa tìm được
estimators = [
    ('xgb', Pipeline([
        ('prep', preprocessor_xgb),
        ('model', xgb.XGBRegressor(**best_xgb))
    ])),
    ('lgb', Pipeline([
        ('prep', preprocessor_ordinal),
        ('model', lgb.LGBMRegressor(**best_lgb))
    ])),
    ('cat', Pipeline([
        ('prep', preprocessor_ordinal),
        ('model', CatBoostRegressor(**best_cat))
    ]))
]

stacking_model = StackingRegressor(
    estimators=estimators,
    final_estimator=LinearRegression(),
    cv=5, 
    n_jobs=-1,
    passthrough=False 
)

# ==============================
# 7. HUẤN LUYỆN VÀ ĐÁNH GIÁ
# ==============================

print(" Đang huấn luyện mô hình tổng hợp (có thể mất 1-2 phút)...")
stacking_model.fit(X_train, y_train)

print(" Đang dự đoán trên tập Test...")
y_pred_log = stacking_model.predict(X_test)

# Chuyển ngược từ Log về giá tiền thực tế
y_pred_real = np.expm1(y_pred_log)
y_test_real = np.expm1(y_test)

mae = mean_absolute_error(y_test_real, y_pred_real)
r2 = r2_score(y_test_real, y_pred_real)

print("\n==============================")
print(" KẾT QUẢ ĐÁNH GIÁ CUỐI CÙNG")
print(f"Sai số trung bình (MAE): {mae:,.0f} VNĐ")
print(f"Độ chính xác (R²): {r2 * 100:.2f} %")
print("==============================\n")

# ==============================
# 8. LƯU MÔ HÌNH
# ==============================

print(" Đang lưu mô hình...")
joblib.dump(stacking_model, "../data_booking.com/final_stacking_model.pkl")

print(" Đã lưu thành công: data_booking.com/final_stacking_model.pkl")
print(" Hoàn tất!")

# ==============================
# 9. DỰ ĐOÁN THỬ TRÊN 10 DÒNG ĐẦU
# ==============================
print("\n Đang tải lại model để dự đoán thử...")
loaded_model = joblib.load("../data_booking.com/final_stacking_model.pkl")

# 1. Đọc dữ liệu mẫu
print(" Đọc dữ liệu mẫu...")
df_sample = pd.read_csv("../data_booking.com/full_data_merged.csv").head(10)

# 2. TÁI TẠO ĐẶC TRƯNG (Khớp với cấu trúc mới)
# --- Đẳng cấp phòng ---
ROOM_RANKING = {
    'Presidential': 10, 'Penthouse': 9, 'Villa': 8, 'Resort': 7,
    'Bungalow': 6, 'Suite': 6, 'Luxury': 5, 'Grand': 5, 'Executive': 5,
    'Apartment': 4, 'Studio': 4, 'Apartment & Studio': 4,
    'Deluxe': 4,
    'Superior': 3, 'Classic': 3, 'Family': 3, 'Connecting': 3, 'Triple': 3, 'Quadruple': 3,
    'Standard': 2, 'Economy': 1, 'Dorm': 0, 'Capsule': 0, 'Other': 2
}
df_sample["Room_Score"] = df_sample["Room_Class"].map(ROOM_RANKING).fillna(2)

# --- Tương tác đặc trưng ---
df_sample["Area_x_Stars"] = df_sample["Area_m2_cleaned"] * df_sample["Stars_Clean"]
df_sample["Score_x_Area"] = df_sample["Room_Score"] * df_sample["Area_m2_cleaned"]

# --- Cơ bản ---
df_sample["Total_Guests"] = df_sample["Adults"] + df_sample["Children"]
df_sample["Facility_Count"] = df_sample["Facilities_cleaned"].astype(str).apply(lambda x: x.count(",") + 1)

# 3. Chọn cột input (Bỏ các cột Has_Pool, Has_AC...)
numeric_features = [
    "Area_m2_cleaned", "Stars_Clean", "Review Count", "Rating_Clean",
    "Distance_KM", "Adults", "Children", "Rooms",
    "Total_Guests", "Facility_Count",
    "Room_Score", "Area_x_Stars", "Score_x_Area"
]
categorical_features = ["District", "Room_Class"]

X_sample = df_sample[numeric_features + categorical_features]

# 4. Dự đoán
pred_log = loaded_model.predict(X_sample)
pred_real = np.expm1(pred_log)

print("\n=======================================================")
print(f"{'GIÁ THỰC TẾ':<15} | {'AI DỰ ĐOÁN':<15} | {'CHÊNH LỆCH':<15}")
print("=======================================================")
for real, pred in zip(df_sample["Final Price"], pred_real):
    diff = abs(real - pred)
    print(f"{real:,.0f} VNĐ".ljust(15) + " | " + f"{pred:,.0f} VNĐ".ljust(15) + " | " + f"{diff:,.0f} VNĐ")
print("=======================================================")