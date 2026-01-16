import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

input_path = BASE_DIR / "merged_all_data.csv"
output_path = BASE_DIR / "column_unique_list.csv"

print("📂 Reading:", input_path)

# ❗ KHÔNG set sep
df = pd.read_csv(input_path)

print("📊 Columns detected:")
print(list(df.columns))

TARGET_COLUMNS = [
    "Search Location",
    "Hotel Name",
    "Hotel Link",
    "Address",
    "Room_Class",
    "Room Type",
    "Bed_Class",
    "Bed Type",
    "Rooms",
    "Original Price",
    "Rating_Clean",
    "Breakfast_Bool",
    "Adults",
    "Children",
    "Total_Guests",
    "Area_m2_cleaned",
    "Facilities_cleaned"
]

rows = []

for col in TARGET_COLUMNS:
    if col not in df.columns:
        print(f"⚠️ Missing column: {col}")
        continue

    values = (
        df[col]
        .dropna()
        .astype(str)
        .unique()
    )

    rows.append({
        "column_name": col,
        "unique_count": len(values),
        "unique_values": " | ".join(sorted(values))
    })

if not rows:
    raise ValueError("❌ Không lấy được cột nào – kiểm tra delimiter hoặc header")

result_df = pd.DataFrame(rows).sort_values("column_name")

result_df.to_csv(output_path, index=False, encoding="utf-8-sig")

print("✅ DONE")
print("📁 Output:", output_path)
print(result_df)
