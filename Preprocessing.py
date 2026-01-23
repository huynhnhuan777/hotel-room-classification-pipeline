import pandas as pd
import os
import re

# =============================
# CONFIG
# =============================
RAW_FILES = [
    "mytour_hotels.xlsx",
    "mytour_hotels01.xlsx",
    "mytour_hotels02.xlsx"
]

MERGED_DIR = "merged_data"
PREPROCESS_DIR = "re-process_data"

MERGED_FILE = f"{MERGED_DIR}/hotels_merged.csv"
CLEAN_FILE = f"{PREPROCESS_DIR}/hotels_clean.csv"


# =============================
# UTILS
# =============================
def normalize_colname(col):
    col = col.strip().lower()
    col = re.sub(r"\s+", "_", col)
    col = re.sub(r"[^\w_]", "", col)
    return col


def clean_text(x):
    if pd.isna(x):
        return ""
    return str(x).strip().lower()


def clean_price(x):
    if pd.isna(x):
        return None
    x = str(x)
    x = re.sub(r"[₫,\.]", "", x)
    try:
        return int(x)
    except:
        return None


# =============================
# MAIN PREPROCESSING
# =============================
def main():
    print("🔹 Step 1: Merge raw files")

    dfs = []
    for file in RAW_FILES:
        if os.path.exists(file):
            print(f"   ✔ Read {file}")
            dfs.append(pd.read_excel(file))
        else:
            print(f"   ❌ Missing file: {file}")

    df = pd.concat(dfs, ignore_index=True)

    # 🔥 NORMALIZE COLUMN NAMES
    df.columns = [normalize_colname(c) for c in df.columns]
    print("   ✔ Normalized column names")

    os.makedirs(MERGED_DIR, exist_ok=True)
    df.to_csv(MERGED_FILE, index=False)

    print("\n🔹 Step 2: Remove duplicates")
    df = df.drop_duplicates()

    print("\n🔹 Step 3: Clean text columns")
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].apply(clean_text)

    print("\n🔹 Step 4: Clean numeric columns")
    num_keywords = ["people", "area", "discount", "pct"]

    for col in df.columns:
        if any(k in col for k in num_keywords):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    print("\n🔹 Step 5: Clean price columns")
    price_keywords = ["price", "cost", "amount"]

    for col in df.columns:
        if any(k in col for k in price_keywords):
            df[col] = df[col].apply(clean_price)

    print("\n🔹 Step 6: Handle missing values")
    if "view" in df.columns:
        df["view"] = df["view"].fillna("unknown")

    if "breakfast" in df.columns:
        df["breakfast"] = df["breakfast"].fillna("unknown")

    # 🔥 SAFE DROPNA
    required_cols = [c for c in ["room_name", "final_price"] if c in df.columns]
    if required_cols:
        df = df.dropna(subset=required_cols)

    print("\n🔹 Step 7: Normalize amenities")
    for col in df.columns:
        if "amenities" in col:
            df[col] = (
                df[col]
                .fillna("")
                .apply(lambda x: ",".join(sorted(set(x.split(",")))))
            )

    print("\n🔹 Step 8: Logical validation")
    if "final_price" in df.columns:
        df = df[df["final_price"] > 0]

    if "list_price" in df.columns:
        df = df[df["final_price"] <= df["list_price"]]

    print("\n🔹 Step 9: Save clean data")
    os.makedirs(PREPROCESS_DIR, exist_ok=True)
    df.to_csv(CLEAN_FILE, index=False)

    print("\n✅ PREPROCESSING DONE")
    print(f"📁 Output: {CLEAN_FILE}")
    print(f"📊 Rows: {len(df)} | Columns: {len(df.columns)}")


# =============================
# RUN
# =============================
if __name__ == "__main__":
    main()
