import pandas as pd
import re
import numpy as np

# Đọc file
df = pd.read_csv("./mergedata/merged_all_data.csv")

#  Chuẩn hoá tên cột
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

#  Đổi tên field
rename_map = {
    "hotel_link": "hotel_link",
    "hotel_name": "hotel_name",
    "room_type": "room_name_original",
    "room_class": "room_class",
    "bed_type": "bed_desc",
    "bed_class": "bed_class",
    "area_m2_cleaned": "area_m2",
    "total_guests": "max_people",
    "final_price": "final_price",
    "facilities_cleaned": "facilities_cleaned"
}
df = df.rename(columns=rename_map)

#  Tạo cột source từ hotel_link
def detect_source(url):
    if pd.isna(url): return None
    url = str(url).lower()
    if "booking.com" in url: return "booking"
    if "mytour.vn" in url: return "mytour"
    if "ivivu.com" in url: return "ivivu"
    return ">>>>"

df["source"] = df["hotel_link"].apply(detect_source)

# Giữ đúng các cột yêu cầu
keep_cols = [
    "source", "hotel_link", "hotel_name",
    "room_name_original", "room_class",
    "bed_desc", "bed_class",
    "area_m2", "max_people",
    "final_price", "facilities_cleaned"
]

# Tạo cột nếu chưa có  nhưng để giá trị NaN
for col in keep_cols:
    if col not in df.columns:
        df[col] = np.nan

df = df[keep_cols]

# Làm sạch dữ liệu
# Xử lý Area 
def clean_area(val):
    if pd.isna(val): return np.nan
    # Thay dấu phẩy thành chấm (cho trường hợp 25,5m2)
    val = str(val).replace(",", ".")
    match = re.search(r"(\d+\.?\d*)", val)
    return float(match.group(1)) if match else np.nan

df["area_m2"] = df["area_m2"].apply(clean_area)

# Xử lý Max People 
df["max_people"] = pd.to_numeric(df["max_people"], errors="coerce")

# Xử lý Final Price 
# Xóa hết ký tự lạ, chỉ giữ số (1.200.000 hay 1,200,000)
def clean_price(val):
    if pd.isna(val): return np.nan
    # Xóa nhứng cái không phải số
    clean_str = re.sub(r'[^\d]', '', str(val))
    try:
        return float(clean_str)
    except ValueError:
        return np.nan

df["final_price"] = df["final_price"].apply(clean_price)

# Xử lý Facilities 
df["facilities_cleaned"] = (
    df["facilities_cleaned"]
    .fillna("") 
    .str.lower()
    .str.replace(r"[^a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ0-9, ]",
                 "", regex=True)
)
# Hàm suy ra bed_class từ bed_desc
def infer_bed_class(desc):
    if pd.isna(desc) or str(desc).strip() == "":
        return "unknown"

    text = str(desc).lower()

    if re.search(r"bunk|family|3 giường|4 giường|nhiều", text):
        return "family"

    if "king" in text:
        return "king"

    if "queen" in text:
        return "queen"

    if re.search(r"2 giường đơn|hai giường đơn|twin", text):
        return "twin"

    if re.search(r"giường đôi|double", text):
        return "double"

    if re.search(r"giường đơn|single", text):
        return "single"

    return "unknown"
# Tạo mask các ô bị thiếu
mask = df["bed_class"].isna() | (df["bed_class"].astype(str).str.strip() == "")
df.loc[mask, "bed_class"] = df.loc[mask, "bed_desc"].apply(infer_bed_class)



# XÓA DÒNG THIẾU 
# Xóa nếu thiếu Tên phòng, Giá, Diện tích hoặc Số người
cols_to_check = ["room_name_original", "final_price", "area_m2", "max_people"]
original_len = len(df)
df = df.dropna(subset=cols_to_check)

# Lọc thêm giá trị dương
df = df[df["final_price"] > 0]
df = df.reset_index(drop=True)

print(f"Đã xóa {original_len - len(df)} dòng thiếu dữ liệu.")
print(f"Số dòng còn lại: {len(df)}")

# Lưu file sạch
df.to_csv("preprocessing/cleaned_rooms.csv", index=False, encoding="utf-8-sig")
print("save success")