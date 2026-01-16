import pandas as pd
import re

input_path = r"C:\Users\Nhuan\OneDrive - ut.edu.vn\Desktop\SEMESTER_7\DATA MINING\hotel-room-classification-pipeline\visualize\clean0801\merged_all_data.csv"
output_path = r"C:\Users\Nhuan\OneDrive - ut.edu.vn\Desktop\SEMESTER_7\DATA MINING\hotel-room-classification-pipeline\visualize\clean0801\merged_all_data_roomclass_clean.csv"

df = pd.read_csv(input_path)

# normalize text trước
df["Room_Class_norm"] = (
    df["Room_Class"]
    .astype(str)
    .str.strip()
    .str.replace(r"\s+", " ", regex=True)
)

# thứ tự ưu tiên (cao -> thấp)
priority = [
    "Luxury",
    "Grand",
    "Executive",
    "Suite",
    "Deluxe",
    "Superior",
    "Standard",
    "Classic"
]

def normalize_room_class(val):
    if val.lower() in ["nan", "(blanks)", ""]:
        return "Unknown"

    for p in priority:
        if re.search(rf"\b{p}\b", val, flags=re.IGNORECASE):
            return p

    return "Standard"  # fallback an toàn

df["Room_Class_Clean"] = df["Room_Class_norm"].apply(normalize_room_class)

df.to_csv(output_path, index=False, encoding="utf-8-sig")

print("✅ ĐÃ CHUẨN HOÁ ROOM_CLASS")
print(df[["Room_Class", "Room_Class_Clean"]].head(10))
