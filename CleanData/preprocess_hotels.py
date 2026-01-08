import pandas as pd
import numpy as np
import re

# =========================
# 1. LOAD DATA
# =========================
df = pd.read_csv("merged_all_data.csv")
print("RAW DATA:", df.shape)

# =========================
# 2. STANDARDIZE COLUMN NAMES
# =========================
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
df = df.loc[:, ~df.columns.duplicated()]

# =========================
# 3. RENAME → SCHEMA CHUẨN
# =========================
rename_map = {
    "room_type": "room_name_original",
    "area_m2_cleaned": "area_m2",
    "total_guests": "max_people",
    "bed_type": "bed_desc"
}
df = df.rename(columns=rename_map)

# =========================
# 4. SOURCE DETECTION
# =========================
def detect_source(url):
    if pd.isna(url):
        return np.nan
    url = str(url).lower()
    if "booking.com" in url:
        return "booking"
    if "mytour.vn" in url:
        return "mytour"
    if "ivivu.com" in url:
        return "ivivu"
    return "other"

df["source"] = df["hotel_link"].apply(detect_source)

# =========================
# 5. LÀM SẠCH DỮ LIỆU SỐ
# =========================
def clean_price(val):
    if pd.isna(val):
        return np.nan
    val = re.sub(r"[^\d]", "", str(val))
    return float(val) if val else np.nan

df["final_price"] = df["final_price"].apply(clean_price)

def clean_area(val):
    if pd.isna(val):
        return np.nan
    val = str(val).replace(",", ".")
    m = re.search(r"(\d+\.?\d*)", val)
    return float(m.group(1)) if m else np.nan

df["area_m2"] = df["area_m2"].apply(clean_area)

df["max_people"] = pd.to_numeric(df["max_people"], errors="coerce")

# =========================
# 6. LÀM SẠCH TIỆN NGHI
# =========================
def clean_facilities(text):
    if pd.isna(text):
        return ""
    text = text.lower()
    text = re.sub(
        r"[^a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ0-9, ]",
        "",
        text
    )
    items = [i.strip() for i in text.split(",") if len(i.strip()) > 2]
    items = sorted(set(items))
    return ", ".join(items)

df["facilities_cleaned"] = df["facilities_cleaned"].apply(clean_facilities)
df = df[df["facilities_cleaned"].str.len() > 0]
df = df.drop_duplicates(
    subset=["hotel_link", "room_name_original"],
    keep="first"
)
# =========================
# 7. LỌC DỮ LIỆU HỢP LỆ
# =========================
before = len(df)

df = df.dropna(subset=[
    "room_name_original",
    "final_price",
    "area_m2",
    "max_people"
])

df = df[df["final_price"] > 0]
df = df.reset_index(drop=True)

print(f"Removed invalid rows: {before - len(df)}")
print("FINAL VALID DATA:", df.shape)

# =========================
# 8. GIỮ ĐÚNG SCHEMA CUỐI
# =========================
final_cols = [
    "source",
    "hotel_link",
    "hotel_name",
    "room_name_original",
    "room_class",
    "bed_desc",
    "bed_class",
    "area_m2",
    "max_people",
    "final_price",
    "facilities_cleaned"
]

for col in final_cols:
    if col not in df.columns:
        df[col] = np.nan

df = df[final_cols]

# =========================
# 9. SAVE
# =========================
df.to_csv("cleaned_rooms.csv", index=False, encoding="utf-8-sig")
print("✅ SAVE SUCCESS: cleaned_rooms.csv")
