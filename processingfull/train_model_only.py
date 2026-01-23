"""
Model Training Script (Training Only)
Trains a Random Forest model without making predictions on validation data.
This script focuses solely on training and evaluating on a test split.
"""

import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

# =========================
# CONFIGURATION
# =========================
TRAIN_PATH = "train.csv"
MODEL_PATH = "room_class_model.pkl"

FEATURES = [
    "Final Price",
    "Max People",
    "Area_m2",
    "price_per_m2",
    "m2_per_person",
    "num_facilities",
    "has_luxury_keyword",
    "is_king",
    "is_queen",
    "is_double",
    "is_single",
    "is_bunk",
    "is_sofa",
    "has_wifi",
    "has_ac",
    "has_breakfast",
    "has_tv",
    "has_pool",
    "has_balcony",
    "has_parking",
    "has_kitchen",
    "has_fridge"
]

TARGET = "room_class"

# =========================
# LOAD TRAINING DATA
# =========================
print("📥 Loading training data...")
df = pd.read_csv(TRAIN_PATH)

# Validate required columns
missing_features = [f for f in FEATURES if f not in df.columns]
if missing_features:
    raise ValueError(f"❌ Missing features: {missing_features}")

if TARGET not in df.columns:
    raise ValueError(f"❌ Missing target column: {TARGET}")

X = df[FEATURES]
y = df[TARGET]

# =========================
# TRAIN / TEST SPLIT
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print(f"✅ Training samples: {len(X_train)}")
print(f"✅ Test samples: {len(X_test)}")

# =========================
# TRAIN MODEL
# =========================
print("🤖 Training RandomForest model...")
model = RandomForestClassifier(
    n_estimators=300,
    max_depth=None,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

# =========================
# EVALUATION
# =========================
print("\n📊 Evaluating model on test set...")
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
print(f"✅ Accuracy: {accuracy:.4f}")
print("\n📄 Classification Report:")
print(classification_report(y_test, y_pred))

print("\n🧩 Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# =========================
# SAVE MODEL
# =========================
joblib.dump(model, MODEL_PATH)
print(f"\n💾 Model saved: {MODEL_PATH}")
