"""
Hotel Room Classification Pipeline using Gemini API
Problem Type: Classification (Supervised Learning)
Target Variable: room_class
Input Variables: room_size, price, bed_type, amenities, ...
"""

import pandas as pd
import json
import numpy as np
from typing import Dict, List, Any, Union

# =========================
# CONFIGURATION
# =========================
TRAIN_CSV = "train.csv"
MODEL_SAVE_PATH = "gemini_classification_model.json"
MAX_TRAIN_EXAMPLES = 50

MODEL_NAME = "models/gemini-flash-latest"

LABEL_MAPPING = {
    "Deluxe": 0,
    "Executive": 1,
    "Luxury": 2,
    "Standard": 3,
    "Suite": 4,
    "Superior": 5
}
REVERSE_MAPPING = {v: k for k, v in LABEL_MAPPING.items()}
CLASS_NAMES = list(LABEL_MAPPING.keys())

# =========================
# LOAD DATA
# =========================
print("📥 Loading training data...")
df_train = pd.read_csv(TRAIN_CSV)

feature_cols = [c for c in df_train.columns if c != "room_class"]
unique_classes = sorted(df_train["room_class"].unique())

# =========================
# HELPER FUNCTIONS
# =========================
def to_native(obj: Any) -> Union[int, float, list, dict, Any]:
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_native(v) for v in obj]
    return obj


# =========================
# PREPARE FEW-SHOT EXAMPLES
# =========================
def prepare_examples(df: pd.DataFrame, n_examples: int = 50) -> List[Dict[str, Any]]:
    """Prepare few-shot examples for training, balanced across classes."""
    examples = []
    per_class = n_examples // len(unique_classes)

    for c in unique_classes:
        class_df = df[df["room_class"] == c]
        sample_size = min(per_class, len(class_df))
        sample = class_df.sample(sample_size, random_state=42)
        
        for _, row in sample.iterrows():
            examples.append({
                "features": row[feature_cols].to_dict(),
                "room_class": int(row["room_class"])
            })
    return examples


training_examples = prepare_examples(df_train, MAX_TRAIN_EXAMPLES)

# =========================
# BUILD PROMPT
# =========================
examples_text = ""
for i, ex in enumerate(training_examples[:10], 1):
    name = REVERSE_MAPPING[ex["room_class"]]
    f = ex["features"]
    examples_text += f"""
Example {i}:
- Final Price: {f.get('Final Price')}
- Max People: {f.get('Max People')}
- Area_m2: {f.get('Area_m2')}
- num_facilities: {f.get('num_facilities')}
- has_luxury_keyword: {f.get('has_luxury_keyword')}
→ Room Class: {name}
"""

base_prompt = f"""
You are a hotel room classification model.

Task: Classify rooms into ONE of the following categories:
{", ".join(CLASS_NAMES)}

{examples_text}

Respond with ONLY the CLASS NAME, no explanation.
"""

# =========================
# SAVE MODEL JSON
# =========================
model_info = {
    "model_name": MODEL_NAME,
    "training_examples_count": len(training_examples),
    "features": feature_cols,
    "classes": unique_classes,
    "class_names": CLASS_NAMES,
    "label_mapping": LABEL_MAPPING,
    "base_prompt": base_prompt
}

model_info = to_native(model_info)

with open(MODEL_SAVE_PATH, "w", encoding="utf-8") as f:
    json.dump(model_info, f, indent=2, ensure_ascii=False)

print("✅ Saved Gemini model JSON:")
print(f"   → {MODEL_SAVE_PATH}")
