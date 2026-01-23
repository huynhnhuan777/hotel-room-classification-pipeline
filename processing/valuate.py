import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

LABEL_MAP = {
    0: "Deluxe",
    1: "Executive",
    2: "Luxury",
    3: "Standard",
    4: "Suite",
    5: "Superior"
}

FILES = {
    "TRAIN": "train_with_prediction.csv",
    "VAL": "val_with_prediction.csv"
}

def interpret_accuracy(acc):
    if acc >= 0.85:
        return "Mô hình đạt độ chính xác cao, cho thấy khả năng phân loại tốt."
    elif acc >= 0.70:
        return "Mô hình đạt độ chính xác khá, vẫn còn một số nhầm lẫn giữa các lớp tương tự."
    else:
        return "Độ chính xác còn thấp, mô hình cần được cải thiện thêm."

def evaluate_file(path, title):
    print("\n" + "=" * 70)
    print(f"📊 EVALUATING {title}")
    print("=" * 70)

    df = pd.read_csv(path)

    y_true = df["room_class"].astype(int)
    y_pred = df["room_class_pred"].astype(int)

    acc = accuracy_score(y_true, y_pred)

    print(f"✅ Samples: {len(df)}")
    print(f"🎯 Accuracy: {acc:.4f}")
    print("📝 Interpretation:", interpret_accuracy(acc))

    print("\n📄 Classification Report:")
    report = classification_report(
        y_true,
        y_pred,
        target_names=[LABEL_MAP[i] for i in range(6)],
        output_dict=True
    )

    for label, metrics in report.items():
        if label in LABEL_MAP.values():
            print(
                f"- {label}: Precision={metrics['precision']:.2f}, "
                f"Recall={metrics['recall']:.2f}, "
                f"F1={metrics['f1-score']:.2f}"
            )

    print("\n🧩 Confusion Matrix:")
    cm = confusion_matrix(y_true, y_pred)
    print(cm)

    # Phân tích nhầm lẫn
    df_err = df[y_true != y_pred].copy()
    df_err["true_name"] = y_true.map(LABEL_MAP)
    df_err["pred_name"] = y_pred.map(LABEL_MAP)

    print("\n❌ Top misclassifications:")
    top_err = (
        df_err
        .groupby(["true_name", "pred_name"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(5)
    )
    print(top_err)

    if not top_err.empty:
        print("\n📝 Error Analysis:")
        for _, row in top_err.iterrows():
            print(
                f"- Các phòng {row['true_name']} thường bị nhầm thành "
                f"{row['pred_name']} ({row['count']} mẫu), "
                f"nguyên nhân có thể do các đặc trưng giá và tiện nghi tương đồng."
            )

if __name__ == "__main__":
    for name, path in FILES.items():
        evaluate_file(path, name)

    print("\n✅ Evaluation & interpretation completed")
