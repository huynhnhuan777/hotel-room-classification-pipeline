# =============================
# MODEL COMPARISON & EVALUATION
# Random Forest vs XGBoost
# =============================

import os
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

# =============================
# 1. LOAD DATA
# =============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

XGB_FILE = os.path.join(BASE_DIR, "test_with_prediction_xgboost.csv")
RF_FILE  = os.path.join(BASE_DIR, "test_with_prediction_randomforest.csv")

print("Loading prediction files...")

df_xgb = pd.read_csv(XGB_FILE)
df_rf  = pd.read_csv(RF_FILE)

print("Files loaded successfully!\n")

# =============================
# 2. BASIC CHECK
# =============================
assert len(df_xgb) == len(df_rf), "❌ Two files must have the same number of samples"

print("========== BASIC INFO ==========")
print(f"Total samples: {len(df_xgb)}\n")

# =============================
# 3. EXTRACT LABELS
# =============================
y_true = df_xgb["room_class"]
y_pred_xgb = df_xgb["room_class_pred"]
y_pred_rf  = df_rf["room_class_pred"]

classes = sorted(y_true.unique())

# =============================
# 4. ACCURACY
# =============================
acc_xgb = accuracy_score(y_true, y_pred_xgb)
acc_rf  = accuracy_score(y_true, y_pred_rf)

print("========== ACCURACY ==========")
print(f"XGBoost Accuracy       : {acc_xgb:.4f}")
print(f"Random Forest Accuracy : {acc_rf:.4f}\n")

# =============================
# 5. CLASSIFICATION REPORT
# =============================
print("========== CLASSIFICATION REPORT (XGBoost) ==========")
print(classification_report(y_true, y_pred_xgb))

print("========== CLASSIFICATION REPORT (Random Forest) ==========")
print(classification_report(y_true, y_pred_rf))

# =============================
# 6. CONFUSION MATRIX
# =============================
cm_xgb = confusion_matrix(y_true, y_pred_xgb, labels=classes)
cm_rf  = confusion_matrix(y_true, y_pred_rf, labels=classes)

# =============================
# 7. TP / FP / TN / FN (ONE-VS-REST)
# =============================
def compute_metrics(cm, idx):
    TP = cm[idx, idx]
    FP = cm[:, idx].sum() - TP
    FN = cm[idx, :].sum() - TP
    TN = cm.sum() - (TP + FP + FN)
    return TP, FP, TN, FN

rows = []

for i, cls in enumerate(classes):
    tp_xgb, fp_xgb, tn_xgb, fn_xgb = compute_metrics(cm_xgb, i)
    tp_rf,  fp_rf,  tn_rf,  fn_rf  = compute_metrics(cm_rf, i)

    rows.append({
        "class": cls,

        "XGB_TP": tp_xgb,
        "XGB_FP": fp_xgb,
        "XGB_TN": tn_xgb,
        "XGB_FN": fn_xgb,
        "XGB_Positive": tp_xgb + fp_xgb,
        "XGB_Negative": tn_xgb + fn_xgb,

        "RF_TP": tp_rf,
        "RF_FP": fp_rf,
        "RF_TN": tn_rf,
        "RF_FN": fn_rf,
        "RF_Positive": tp_rf + fp_rf,
        "RF_Negative": tn_rf + fn_rf,
    })

metrics_df = pd.DataFrame(rows)

# =============================
# 8. PRECISION / RECALL (MANUAL)
# =============================
def safe_div(a, b):
    return a / b if b != 0 else 0

metrics_df["XGB_Precision"] = metrics_df.apply(
    lambda r: safe_div(r.XGB_TP, r.XGB_TP + r.XGB_FP), axis=1
)
metrics_df["XGB_Recall"] = metrics_df.apply(
    lambda r: safe_div(r.XGB_TP, r.XGB_TP + r.XGB_FN), axis=1
)

metrics_df["RF_Precision"] = metrics_df.apply(
    lambda r: safe_div(r.RF_TP, r.RF_TP + r.RF_FP), axis=1
)
metrics_df["RF_Recall"] = metrics_df.apply(
    lambda r: safe_div(r.RF_TP, r.RF_TP + r.RF_FN), axis=1
)

print("========== TP / FP / TN / FN PER CLASS ==========")
print(metrics_df)

# =============================
# 9. SAVE RESULTS
# =============================
OUTPUT_FILE = os.path.join(BASE_DIR, "tp_fp_tn_fn_comparison.csv")
metrics_df.to_csv(OUTPUT_FILE, index=False)

print(f"\nDetailed TP/FP/TN/FN saved to: {OUTPUT_FILE}\n")

# =============================
# 10. FINAL CONCLUSION
# =============================
print("========== FINAL CONCLUSION ==========")

if acc_xgb > acc_rf:
    print(
        f"✅ XGBoost performs BETTER than Random Forest\n"
        f"- Accuracy gain: {(acc_xgb - acc_rf)*100:.2f}%"
    )
elif acc_rf > acc_xgb:
    print(
        f"✅ Random Forest performs BETTER than XGBoost\n"
        f"- Accuracy gain: {(acc_rf - acc_xgb)*100:.2f}%"
    )
else:
    print("⚖️ Both models have EQUAL accuracy")
