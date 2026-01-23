import pandas as pd

# =========================
# CONFIG
# =========================
CSV_PATH = "val_with_prediction.csv"

LABEL_MAP = {
    0: "Deluxe",
    1: "Executive",
    2: "Luxury",
    3: "Standard",
    4: "Suite",
    5: "Superior"
}

# =========================
# LOAD DATA
# =========================
print("=" * 60)
print("📥 Loading prediction file...")
print("=" * 60)

df = pd.read_csv(CSV_PATH)

required_cols = ["room_class", "room_class_pred"]
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"❌ Missing column: {col}")

print(f"✅ Total samples: {len(df)}")

# =========================
# ADD LABEL NAMES (SIDE BY SIDE)
# =========================
df["room_class_name"] = df["room_class"].map(LABEL_MAP)
df["room_class_pred_name"] = df["room_class_pred"].map(LABEL_MAP)

# =========================
# CHECK MISCLASSIFICATION
# =========================
df["is_correct"] = df["room_class"] == df["room_class_pred"]

total = len(df)
correct = df["is_correct"].sum()
wrong = total - correct

print("\n" + "=" * 60)
print("📊 OVERALL RESULT")
print("=" * 60)
print(f"✅ Correct: {correct}")
print(f"❌ Wrong:   {wrong}")
print(f"🎯 Accuracy: {correct / total:.4f}")

# =========================
# ERROR COUNT PER CLASS (TRUE → PRED)
# =========================
print("\n" + "=" * 60)
print("❌ ERROR ANALYSIS (True → Pred)")
print("=" * 60)

errors = df[~df["is_correct"]]

error_summary = (
    errors
    .groupby(["room_class_name", "room_class_pred_name"])
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)

print(error_summary.head(20))

# =========================
# ERROR RATE PER TRUE CLASS
# =========================
print("\n" + "=" * 60)
print("📉 ERROR RATE PER CLASS")
print("=" * 60)

error_rate = (
    df.groupby("room_class_name")["is_correct"]
    .apply(lambda x: 1 - x.mean())
    .reset_index(name="error_rate")
    .sort_values("error_rate", ascending=False)
)

print(error_rate)

# =========================
# SAVE FILE WITH ANALYSIS
# =========================
OUTPUT = "val_with_error_analysis.csv"
df.to_csv(OUTPUT, index=False)
print(f"\n💾 Saved detailed analysis: {OUTPUT}")
