import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

INPUT_CSV = "./processing/LogisticRegression/train.csv"
OUTPUT_CSV = "data_labeled_logreg_train.csv"
MISALIGNED_CSV = "suspected_label_errors_logreg_train.csv"
CONF_THRESHOLD = 0.9


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

    # SPLIT
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    # PIPELINE: SCALE + SOFTMAX REGRESSION
    print("\nTraining Logistic Regression (Softmax)...")
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            solver="lbfgs",
            max_iter=2000,
            class_weight="balanced",
            n_jobs=-1
        ))
    ])

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

    # COEFFICIENT IMPORTANCE
    clf = model.named_steps["clf"]
    coef_df = pd.DataFrame(
        clf.coef_,
        columns=feature_cols,
        index=class_names
    )

    print("\nTop features (absolute coef mean):")
    print(
        coef_df.abs()
        .mean()
        .sort_values(ascending=False)
        .head(10)
    )

    # PREDICT FULL DATASET
    print("\n" + "=" * 60)
    print("PREDICTING ON FULL DATASET")
    print("=" * 60)

    df["lr_room_class"] = model.predict(X)
    proba = model.predict_proba(X)
    df["lr_conf"] = proba.max(axis=1)

    # DETECT MISALIGNED
    df["is_misaligned"] = (
        (df["room_class"] != df["lr_room_class"]) &
        (df["lr_conf"] >= CONF_THRESHOLD)
    )

    misaligned_df = df[df["is_misaligned"]].copy()

    print(f"\nTotal samples: {len(df)}")
    print(f"Misaligned samples: {len(misaligned_df)}")
    print(f"Ratio: {len(misaligned_df) / len(df):.2%}")

    print("\nMisaligned samples per class:")
    print(misaligned_df["room_class"].value_counts().sort_index())

    # SAVE
    df.to_csv(OUTPUT_CSV, index=False)
    misaligned_df.to_csv(MISALIGNED_CSV, index=False)

    print(f"\nSaved full output to: {OUTPUT_CSV}")
    print(f"Saved suspected label errors to: {MISALIGNED_CSV}")

    # SHOW SAMPLE
    review_cols = feature_cols + ["room_class", "lr_room_class", "lr_conf"]
    print("\nSample suspicious rows:")
    print(misaligned_df[review_cols].head(10))

    return model


if __name__ == "__main__":
    model = train_and_predict()
    print("\n COMPLETE")
