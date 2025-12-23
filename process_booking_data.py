import pandas as pd
import numpy as np
import re
from sqlalchemy import create_engine

# --- 1. CẤU HÌNH DATABASE ---
DB_CONFIG = {
    "dbname": "booking_data",
    "user": "postgres",
    "password": "123456", 
    "host": "localhost",
    "port": "5432"
}

# Chuỗi kết nối
DB_CONNECTION_STR = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

# Tạo Engine
engine = create_engine(DB_CONNECTION_STR)

# --- 2. CẤU HÌNH TỪ KHÓA ---
ROOM_KEYWORDS = {
    'Presidential/Suite': ['president', 'tổng thống', 'suite', 'penthouse', 'biệt thự', 'villa'],
    'Family/Large': ['family', 'gia đình', '3 phòng', '4 phòng', 'nối liền', 'connecting', 'triple', 'quadruple'],
    'Premium/Luxury': ['premium', 'luxury', 'cao cấp', 'sang trọng', 'business', 'executive'],
    'Deluxe': ['deluxe', 'thượng hạng', 'grand'],
    'Apartment/Studio': ['apartment', 'căn hộ', 'studio', 'condo'],
    'Standard/Superior': ['standard', 'superior', 'tiêu chuẩn', 'phổ thông', 'economy', 'budget', 'classic'],
    'Dormitory': ['dorm', 'tập thể', 'giường tầng', 'bunk', 'capsule', 'kén'],
}

def load_data_from_db(table_name):
    print(f"1. Đang đọc dữ liệu thô từ bảng '{table_name}'...")
    try:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, engine)
        print(f"   -> Đã load thành công {len(df)} dòng.")
        return df
    except Exception as e:
        print(f"   -> Lỗi kết nối Database: {e}")
        return None

def clean_and_save_data(df, output_table_name):
    if df is None or df.empty:
        print("DataFrame rỗng, dừng xử lý.")
        return

    print("2. Đang xử lý và làm sạch dữ liệu...")

    # --- BƯỚC A: ĐỔI TÊN CỘT ---
    rename_map = {
        "search_location": "Search Location",
        "scenario": "Scenario",   
        "hotel_name": "Hotel Name",
        "stars": "Stars",
        "address": "Address",
        "room_type": "Room Type",
        "bed_type": "Bed Type",
        "final_price": "Final Price",
        "original_price": "Original Price",
        "rating_score": "Rating Score",
        "review_count": "Review Count",
        "location_score": "Location Score",
        "distance": "Distance",
        "free_cancellation": "Free Cancellation",
        "breakfast_included": "Breakfast Included",
        "badge_deal": "Badge Deal",
        "adults": "Adults",
        "children": "Children",
        "rooms": "Rooms",
        "check_in": "Check-in"
    }
    actual_rename_map = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=actual_rename_map)

    # --- BƯỚC B: CHUẨN HÓA TEXT ---
    str_cols = ['Hotel Name', 'Address', 'Room Type', 'Bed Type', 'Distance', 'Badge Deal', 'Search Location']
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
            df[col] = df[col].replace({'nan': '', 'None': '', 'N/A': ''}) 

    # --- BƯỚC C: XỬ LÝ LOGIC ---
    
    # 1. Stars
    df['Stars_Clean'] = pd.to_numeric(df['Stars'], errors='coerce').fillna(0)

    # 2. XỬ LÝ ĐỊA CHỈ
    def extract_district_custom(row):
        addr = str(row.get('Address', '')).lower()
        
        # 1. Kiểm tra đơn vị hành chính chuẩn
        regex_admin = r'(quận\s+\d+|quận\s+[a-zà-ỹ]+|district\s+\d+|tp\.\s+[a-zà-ỹ]+|thành\s+phố\s+[a-zà-ỹ]+|thị\s+xã\s+[a-zà-ỹ]+|huyện\s+[a-zà-ỹ]+|phường\s+\d+|phường\s+[a-zà-ỹ]+)'
        match = re.search(regex_admin, addr)
        
        if match:
            return match.group(0).title()
        
        # 2. Kiểm tra từ khóa địa danh cụ thể
        if 'vũng tàu' in addr or 'vung tau' in addr: return "TP. Vũng Tàu"
        if 'bình dương' in addr or 'binh duong' in addr: return "Bình Dương"
        if 'đà lạt' in addr or 'da lat' in addr: return "TP. Đà Lạt"
        if 'hồ chí minh' in addr or 'tphcm' in addr: return "TP. Hồ Chí Minh"

        # 3. Fallback: Lấy Search Location
        search_loc = str(row.get('Search Location', '')).title()
        if search_loc and search_loc not in ['Nan', 'None', '', 'N/A']:
             return search_loc

        # 4. Fallback cuối cùng
        return "Other"

    df['District'] = df.apply(extract_district_custom, axis=1)

    # 3. Bed Class
    def classify_bed(bed_text):
        if not bed_text: return "Unknown"
        t = str(bed_text).lower()
        if any(x in t for x in ['đôi', 'double', 'king', 'queen', 'lớn', 'large']): return "Double/Large"
        if any(x in t for x in ['đơn', 'single', 'twin']): return "Single/Twin"
        if any(x in t for x in ['tầng', 'bunk']): return "Bunk"
        if any(x in t for x in ['sofa', 'futon']): return "Sofa Bed"
        return "Other"
    df['Bed_Class'] = df['Bed Type'].apply(classify_bed)

    # 4. Booleans
    def to_bool(val):
        s = str(val).lower()
        return 1 if 'yes' in s or 'có' in s or '1' in s else 0
    df['Free_Cancel_Bool'] = df['Free Cancellation'].apply(to_bool)
    df['Breakfast_Bool'] = df['Breakfast Included'].apply(to_bool)
    df['Badge_Clean'] = df['Badge Deal'].replace({'None': 'No Deal', 'N/A': 'No Deal', '': 'No Deal', '0': 'No Deal'})

    # 5. Guests & Rooms
    df['Adults'] = df['Adults'].fillna(0).astype(int)
    df['Children'] = df['Children'].fillna(0).astype(int)
    if 'Rooms' in df.columns:
        df['Rooms'] = df['Rooms'].fillna(1).astype(int)
    else:
        df['Rooms'] = 1
    df['Total_Guests'] = df['Adults'] + df['Children']

    # 6. Scores
    def clean_score(value):
        if pd.isna(value) or str(value).strip() in ['N/A', 'None', '', 'nan']: return np.nan
        try:
            return float(str(value).replace(',', '.'))
        except:
            return np.nan
    df['Rating_Clean'] = df['Rating Score'].apply(clean_score)
    df['Location_Clean'] = df['Location Score'].apply(clean_score)

    # 7. Distance
    def extract_distance_km(value):
        if pd.isna(value) or str(value) in ['N/A', 'nan', '']: return np.nan
        val_str = str(value).lower().replace(',', '.')
        match = re.search(r'(\d+(\.\d+)?)', val_str)
        if match:
            num = float(match.group(1))
            if 'km' in val_str: return num
            elif 'm' in val_str: return num / 1000
            else: return num 
        return np.nan
    df['Distance_KM'] = df['Distance'].apply(extract_distance_km)

    # 8. Room Class
    def classify_room(room_name):
        if not room_name: return 'Unknown'
        name_lower = str(room_name).lower()
        for category, keywords in ROOM_KEYWORDS.items():
            for kw in keywords:
                if kw in name_lower: return category
        if 'phòng' in name_lower or 'room' in name_lower: return 'Standard/Superior'
        return 'Other' 
    df['Room_Class'] = df['Room Type'].apply(classify_room)

    # 9. Prices & Discount
    df['Final Price'] = pd.to_numeric(df['Final Price'], errors='coerce').fillna(0)
    df['Original Price'] = pd.to_numeric(df['Original Price'], errors='coerce').fillna(0)
    
    mask_fix_price = df['Original Price'] < df['Final Price']
    df.loc[mask_fix_price, 'Original Price'] = df.loc[mask_fix_price, 'Final Price']
    
    df['Discount %'] = ((df['Original Price'] - df['Final Price']) / df['Original Price']) * 100
    df['Discount %'] = df['Discount %'].replace([np.inf, -np.inf], 0).fillna(0).clip(0, 100).round(1)

    # 10. Check-in
    if 'Check-in' in df.columns:
        df['Check-in'] = pd.to_datetime(df['Check-in'], errors='coerce').dt.date

    # --- BƯỚC D: LỌC NGOẠI LAI ---
    print("   -> Đang lọc dữ liệu nhiễu...")
    df = df[(df['Final Price'] > 50000) & (df['Final Price'] < 1000000000)]
    df = df[df['Total_Guests'] > 0]
    df = df[df['Hotel Name'].str.len() > 1]

    # --- BƯỚC E: CHỌN CỘT ---
    cols_order = [
        'Scenario', 'Search Location', 'Hotel Name', 'Stars_Clean', 'District', 'Address',
        'Room_Class', 'Room Type', 'Bed_Class', 'Bed Type', 'Rooms',
        'Final Price', 'Original Price', 'Discount %',
        'Rating_Clean', 'Review Count', 'Location_Clean', 'Distance_KM',
        'Free_Cancel_Bool', 'Breakfast_Bool', 'Badge_Clean',
        'Adults', 'Children', 'Total_Guests', 'Check-in'
    ]
    final_cols = [c for c in cols_order if c in df.columns]
    df_clean = df[final_cols]

    # --- BƯỚC F: XÓA DỮ LIỆU 'OTHER' ---
    print("   -> Đang lọc bỏ dòng có dữ liệu 'Other/Unknown'...")
    check_other_cols = ['District', 'Room_Class', 'Bed_Class']
    existing_check_cols = [c for c in check_other_cols if c in df_clean.columns]
    
    if existing_check_cols:
        mask_other = df_clean[existing_check_cols].isin(['Other', 'OTHER', 'other', 'Unknown', 'unknown']).any(axis=1)
        deleted_count = mask_other.sum()
        df_clean = df_clean[~mask_other]
        print(f"      - Đã xóa {deleted_count} dòng có dữ liệu không xác định (Other).")

   # --- BƯỚC G: LƯU VÀO DATABASE (LỌC TRÙNG 2 LỚP) ---
    print("   -> Đang xóa trùng lặp nâng cao (2 LỚP)...")
    
    # 1. LỚP LỌC 1: Loại trừ Scenario, Check-in, Total_Guests...
    ignore_cols = ['Scenario', 'Adults', 'Children', 'Rooms', 'Total_Guests', 'Check-in']
    subset_cols_1 = [c for c in df_clean.columns if c not in ignore_cols]
    
    len_0 = len(df_clean)
    if subset_cols_1:
        df_clean = df_clean.drop_duplicates(subset=subset_cols_1, keep='first')
    len_1 = len(df_clean)
    print(f"      - Lớp 1 (Cơ bản): Đã xóa {len_0 - len_1} dòng.")

    # 2. LỚP LỌC 2 : Logic ép buộc "Cùng Tên + Cùng Giá + Cùng Loại Phòng = Xóa"
    strict_subset = ['Hotel Name', 'Room Type', 'Final Price', 'Address']
    
    # Chỉ check nếu các cột này tồn tại
    valid_strict_subset = [c for c in strict_subset if c in df_clean.columns]
    
    if valid_strict_subset:
        # Sort trước để giữ lại dòng tốt nhất (VD: dòng có Review Count cao nhất hoặc đầy đủ thông tin nhất)
        if 'Rating_Clean' in df_clean.columns:
             df_clean = df_clean.sort_values(by=['Hotel Name', 'Final Price', 'Rating_Clean'], ascending=[True, True, False])
        
        df_clean = df_clean.drop_duplicates(subset=valid_strict_subset, keep='first')
        
    len_2 = len(df_clean)
    print(f"      - Lớp 2 (Mạnh tay): Đã xóa thêm {len_1 - len_2} dòng (Trùng Tên + Loại Phòng + Giá).")

    print("3. Đang chuẩn bị lưu vào Postgres...")
    df_clean.columns = [c.strip().lower().replace(' ', '_').replace('-', '_').replace('%', 'percent') for c in df_clean.columns]
    
    try:
        df_clean.to_sql(output_table_name, engine, if_exists='replace', index=False)
        print(f"HOÀN TẤT! Đã lưu {len(df_clean)} dòng sạch vào bảng '{output_table_name}'.")
    except Exception as e:
        print(f"Lỗi khi lưu vào Database: {e}")

# --- CHẠY CHƯƠNG TRÌNH ---
if __name__ == "__main__":
    RAW_TABLE = "hotel_scenarios"
    CLEAN_TABLE = "hotel_data_cleaned"
    
    df_raw = load_data_from_db(RAW_TABLE)
    clean_and_save_data(df_raw, CLEAN_TABLE)