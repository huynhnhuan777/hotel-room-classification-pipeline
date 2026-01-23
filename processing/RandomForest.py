import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from pathlib import Path
import joblib

# =========================
# 1. PATH AN TOÀN (THEO FILE .PY)
# =========================
BASE_DIR = Path(__file__).resolve().parent

TRAIN_PATH = BASE_DIR / "train.csv"
VAL_PATH   = BASE_DIR / "validation.csv"
TEST_PATH  = BASE_DIR / "test.csv"

for p in [TRAIN_PATH, VAL_PATH, TEST_PATH]:
    if not p.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {p}")

# =========================
# 2. LOAD TRAIN DATA
# =========================
df_train = pd.read_csv(TRAIN_PATH)

TARGET = "room_class"

X_train = df_train.drop(columns=[TARGET])
y_train = df_train[TARGET]

# =========================
# 3. TRAIN RANDOM FOREST
# =========================
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

print("✅ Train xong model")

# =========================
# 4. LOAD & EVALUATE VALIDATION
# =========================
df_val = pd.read_csv(VAL_PATH)

X_val = df_val.drop(columns=[TARGET])
y_val = df_val[TARGET]

val_pred = model.predict(X_val)

print("\n===== VALIDATION RESULT =====")
print("Accuracy:", accuracy_score(y_val, val_pred))
print(classification_report(y_val, val_pred))

# =========================
# 5. LOAD TEST DATA
# =========================
df_test = pd.read_csv(TEST_PATH)

# đảm bảo đúng thứ tự feature
X_test = df_test[X_train.columns]

# =========================
# 6. PREDICT TEST
# =========================
test_pred = model.predict(X_test)
df_test["room_class_pred"] = test_pred

# =========================
# 7. SAVE RESULT
# =========================
OUTPUT_PATH = BASE_DIR / "test_with_prediction.csv"
df_test.to_csv(OUTPUT_PATH, index=False)

print(f"\n✅ Đã dự đoán test → {OUTPUT_PATH}")

# =========================
# 8. SAVE MODEL
# =========================
MODEL_PATH = BASE_DIR / "random_forest_room_class.pkl"
joblib.dump(model, MODEL_PATH)

print(f"✅ Đã lưu model → {MODEL_PATH}")
