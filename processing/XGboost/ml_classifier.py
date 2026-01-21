import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import xgboost as xgb

INPUT_CSV = "./processing/val.csv"
OUTPUT_CSV = "data_labeled_xgboost_val.csv"
MISALIGNED_CSV = "suspected_label_errors_val.csv"
CONF_THRESHOLD = 0.9   # ngưỡng tin cậy để coi là lệch nhãn


# TRAIN & DETECT MISALIGNED LABELS
def train_and_predict():
    print("Loading data...")
    df = pd.read_csv(INPUT_CSV)

    # FEATURES
    feature_cols = [
        'Final Price', 'Max People', 'Area_m2', 'price_per_m2', 'm2_per_person',
        'num_facilities', 'has_luxury_keyword',
        'is_king', 'is_queen', 'is_double', 'is_single', 'is_bunk', 'is_sofa',
        'has_wifi', 'has_ac', 'has_breakfast', 'has_tv', 'has_pool',
        'has_balcony', 'has_parking', 'has_kitchen', 'has_fridge'
    ]

    X = df[feature_cols]
    y = df['room_class']

    # SPLIT DATA 
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    # TRAIN MODE 
    print("\nTraining XGBoost model...")
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="mlogloss"
    )

    model.fit(X_train, y_train)

    # EVALUATION 
    print("\n" + "=" * 60)
    print("MODEL EVALUATION (TEST SET)")
    print("=" * 60)

    y_pred = model.predict(X_test)
    accuracy = (y_pred == y_test).mean()
    print(f"Test Accuracy: {accuracy:.2%}")

    class_names = ['Deluxe', 'Executive', 'Luxury', 'Standard', 'Suite', 'Superior']
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=class_names))

    #  FEATURE IMPORTANCE 
    print("\nTop 10 Most Important Features:")
    feature_importance = (
        pd.DataFrame({
            "feature": feature_cols,
            "importance": model.feature_importances_
        })
        .sort_values("importance", ascending=False)
    )
    print(feature_importance.head(10))

    #  PREDICT FULL DATASET 
    print("\n" + "=" * 60)
    print("PREDICTING ON FULL DATASET")
    print("=" * 60)

    df["llm_room_class"] = model.predict(X)
    proba = model.predict_proba(X)
    df["xgb_conf"] = proba.max(axis=1)

    #DETECT MISALIGNED ROWS 
    df["is_misaligned"] = (
        (df["room_class"] != df["llm_room_class"]) &
        (df["xgb_conf"] >= CONF_THRESHOLD)
    )

    misaligned_df = df[df["is_misaligned"]].copy()

    print("\n" + "=" * 60)
    print("MISALIGNED (POTENTIALLY WRONG LABELS)")
    print("=" * 60)
    print(f"Total samples: {len(df)}")
    print(f"Misaligned samples: {len(misaligned_df)}")
    print(f"Ratio: {len(misaligned_df) / len(df):.2%}")

    # PER-CLASS MISALIGNMENT
    print("\nMisaligned samples per class:")
    print(misaligned_df["room_class"].value_counts().sort_index())

    # SAVE FILES 
    df.to_csv(OUTPUT_CSV, index=False)
    misaligned_df.to_csv(MISALIGNED_CSV, index=False)

    print(f"\nSaved full output to: {OUTPUT_CSV}")
    print(f"Saved suspected label errors to: {MISALIGNED_CSV}")

    # SHOW SAMPLE
    print("\nSample suspicious rows:")
    review_cols = feature_cols + ["room_class", "llm_room_class", "xgb_conf"]
    print(misaligned_df[review_cols].head(10))

    return model


if __name__ == "__main__":
    try:
        model = train_and_predict()
        print("\n COMPLETE")
    except ImportError:
        print("\n ERROR: XGBoost not installed")
        print("Install with: pip install xgboost scikit-learn")
