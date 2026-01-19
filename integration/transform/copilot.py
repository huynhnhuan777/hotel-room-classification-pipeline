import pandas as pd
import os

# Đường dẫn schema
schema_path = r"C:\Users\Nhuan\OneDrive - ut.edu.vn\Desktop\SEMESTER_7\DATA MINING\hotel-room-classification-pipeline\integration\schema.txt"
raw_dir = r"C:\Users\Nhuan\OneDrive - ut.edu.vn\Desktop\SEMESTER_7\DATA MINING\hotel-room-classification-pipeline\integration\raw"
output_file = os.path.join(raw_dir, "hoangvu_hotels.csv")

# Đọc schema
with open(schema_path, "r", encoding="utf-8") as f:
    schema_cols = [line.strip() for line in f.readlines() if line.strip()]

# Hàm chuẩn hóa từng nguồn
def transform_hongnhuan_hotels(path):
    df = pd.read_csv(path)
    df_out = pd.DataFrame(columns=schema_cols)
    df_out["Hotel Name"] = df["hotel_name"]
    df_out["Hotel Link"] = df["hotel_link"]
    df_out["Search Location"] = df["city"]
    # Các cột khác điền giá trị mặc định hoặc NaN
    return df_out

def transform_hongnhuan_rooms(path):
    df = pd.read_csv(path)
    df_out = pd.DataFrame(columns=schema_cols)
    df_out["Room Type"] = df["room_name"]
    df_out["Final Price"] = df["price"]
    df_out["Area_m2_cleaned"] = df["area_m2"]
    df_out["Bed Type"] = df["bed_type"]
    df_out["Total_Guests"] = df["max_occupancy"]
    df_out["Facilities_cleaned"] = df["amenities"]
    return df_out

def transform_trongvu_hotels(path):
    df = pd.read_csv(path)
    df_out = pd.DataFrame(columns=schema_cols)
    df_out["Hotel Name"] = df["hotel_name"]
    df_out["Hotel Link"] = df["hotel_url"]
    df_out["Address"] = df["address"]
    df_out["Rating_Clean"] = df["ratingValue"]
    df_out["Review Count"] = df["reviewCount"]
    df_out["Facilities_cleaned"] = df["amenities"]
    return df_out

def transform_vanduy_hotels(path):
    df = pd.read_csv(path)
    df_out = pd.DataFrame(columns=schema_cols)
    df_out["Hotel Name"] = df["hotelName"]
    df_out["Stars_Clean"] = df["star"]
    df_out["Address"] = df["address"]
    df_out["Search Location"] = df["cityName"]
    df_out["Final Price"] = df["minPrice"]
    df_out["Original Price"] = df["maxPrice"]
    df_out["Rating_Clean"] = df["commentScore"]
    df_out["Review Count"] = df["commenterNumber"]
    return df_out

def transform_vansau_hotels(path):
    df = pd.read_excel(path)
    df_out = pd.DataFrame(columns=schema_cols)
    df_out["Hotel Name"] = df["ten"]
    df_out["Hotel Link"] = df["link"]
    df_out["Address"] = df["dia_chi"]
    df_out["Original Price"] = df["gia_niem_yet"]
    df_out["Final Price"] = df["gia_hien_tai"]
    df_out["Discount %"] = df["discount"]
    df_out["Review Count"] = df["so_luong_danh_gia"]
    df_out["Rating_Clean"] = df["diem_danh_gia"]
    df_out["Facilities_cleaned"] = df["tien_nghi"]
    return df_out

def transform_vansau_rooms(path):
    df = pd.read_excel(path)
    df_out = pd.DataFrame(columns=schema_cols)
    df_out["Hotel Name"] = df["hotel_name"]
    df_out["Hotel Link"] = df["hotel_link"]
    df_out["Room Type"] = df["room_name"]
    df_out["Adults"] = df["people"].str.extract(r'(\d+)').astype(float)
    df_out["Area_m2_cleaned"] = df["area"]
    df_out["Bed Type"] = df["bed"]
    df_out["Facilities_cleaned"] = df["room_amenities"]
    df_out["Final Price"] = df["final_price"]
    df_out["Original Price"] = df["list_price"]
    df_out["Discount %"] = df["discount_pct"]
    df_out["Breakfast_Bool"] = df["breakfast"]
    df_out["Free_Cancel_Bool"] = df["cancel_policy"]
    return df_out

# Gom tất cả lại
dfs = []
dfs.append(transform_hongnhuan_hotels(os.path.join(raw_dir, "hongnhuan_hotels.csv")))
dfs.append(transform_hongnhuan_rooms(os.path.join(raw_dir, "hongnhuan_rooms.csv")))
dfs.append(transform_trongvu_hotels(os.path.join(raw_dir, "trongvu_hotels.csv")))
dfs.append(transform_vanduy_hotels(os.path.join(raw_dir, "vanduy_hotels.csv")))
dfs.append(transform_vansau_hotels(os.path.join(raw_dir, "vansau_hotels_1.xlsx")))
dfs.append(transform_vansau_hotels(os.path.join(raw_dir, "vansau_hotels_2.xlsx")))
dfs.append(transform_vansau_rooms(os.path.join(raw_dir, "vansau_rooms_1.xlsx")))
dfs.append(transform_vansau_rooms(os.path.join(raw_dir, "vansau_rooms_2.xlsx")))

# Hợp nhất
final_df = pd.concat(dfs, ignore_index=True)

# Xuất ra file CSV
final_df.to_csv(output_file, index=False, encoding="utf-8-sig")
print("✅ File đã được chuẩn hóa và lưu tại:", output_file)