import pandas as pd
import numpy as np
import re
from sqlalchemy import create_engine, text

# --- 1. CẤU HÌNH DATABASE ---
DB_CONFIG = {
    "dbname": "booking_data",
    "user": "postgres",
    "password": "123456", 
    "host": "localhost",
    "port": "5432"
}
DB_CONNECTION_STR = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
engine = create_engine(DB_CONNECTION_STR)

# --- 2. CẤU HÌNH TỪ KHÓA (MAPPING) ---

# Cấu hình từ khóa GIƯỜNG
BED_MAPPING = {
    'double': 'Double', 'đôi': 'Double',
    'king': 'King',
    'queen': 'Queen',
    'large': 'Large', 'lớn': 'Large',
    'single': 'Single', 'đơn': 'Single',
    'twin': 'Twin',
    'bunk': 'Bunk', 'tầng': 'Bunk', 'tập thể': 'Bunk',
    'sofa': 'Sofa',
    'futon': 'Futon'
}

# Cấu hình từ khóa PHÒNG
ROOM_MAPPING = {
    'president': 'Presidential', 'tổng thống': 'Presidential',
    'suite': 'Suite',
    'penthouse': 'Penthouse',
    'villa': 'Villa', 'biệt thự': 'Villa',
    'bungalow': 'Bungalow',
    'family': 'Family', 'gia đình': 'Family',
    'connecting': 'Connecting',
    'triple': 'Triple', '3 người': 'Triple',
    'quadruple': 'Quadruple', '4 người': 'Quadruple',
    'luxury': 'Luxury',
    'business': 'Business',
    'executive': 'Executive',
    'deluxe': 'Deluxe', 'grand': 'Grand',
    'apartment': 'Apartment', 'căn hộ': 'Apartment',
    'studio': 'Studio', 'condo': 'Condo',
    'standard': 'Standard', 'tiêu chuẩn': 'Standard',
    'superior': 'Superior',
    'classic': 'Classic',
    'economy': 'Economy', 'budget': 'Budget',
    'dorm': 'Dorm', 'kén': 'Capsule', 'capsule': 'Capsule'
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

# --- HÀM PHÂN LOẠI ĐA NHÃN (MULTI-TAG) ---
def extract_tags(text, mapping_dict):
    """
    Tìm tất cả từ khóa xuất hiện và nối chúng bằng dấu '&'
    """
    if not text or str(text).lower() in ['nan', 'none', '', 'n/a']:
        return "Unknown"
    
    text_lower = str(text).lower()
    found_tags = set() # Dùng set để tránh trùng lặp (VD: Double & Double)

    for keyword, tag_name in mapping_dict.items():
        # Kiểm tra từ khóa có nằm trong text không
        if keyword in text_lower:
            found_tags.add(tag_name)
    
    if not found_tags:
        # Fallback nhẹ
        if 'bed' in mapping_dict.values(): # Đang check giường
             return "Other"
        else: # Đang check phòng
             if 'phòng' in text_lower or 'room' in text_lower:
                 return "Standard"
             return "Other"

    # Sắp xếp và nối bằng dấu &
    return " & ".join(sorted(list(found_tags)))

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
        "hotel_link": "Hotel Link",
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
    str_cols = ['Hotel Name', 'Hotel Link', 'Address', 'Room Type', 'Bed Type', 'Distance', 'Badge Deal', 'Search Location']
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
    
        name_pattern = r'[a-zà-ỹ]+(?:\s+[a-zà-ỹ]+)*'
        
        regex_admin = rf'(quận\s+\d+|quận\s+{name_pattern}|district\s+\d+|tp\.\s+{name_pattern}|thành\s+phố\s+{name_pattern}|thị\s+xã\s+{name_pattern}|huyện\s+{name_pattern}|phường\s+\d+|phường\s+{name_pattern})'
        
        match = re.search(regex_admin, addr)
        if match: return match.group(0).title()
        if 'vũng tàu' in addr or 'vung tau' in addr: return "TP. Vũng Tàu"
        if 'bình dương' in addr or 'binh duong' in addr: return "Bình Dương"
        if 'đà lạt' in addr or 'da lat' in addr: return "TP. Đà Lạt"
        if 'hồ chí minh' in addr or 'tphcm' in addr: return "TP. Hồ Chí Minh"
        search_loc = str(row.get('Search Location', '')).title()
        if search_loc and search_loc not in ['Nan', 'None', '', 'N/A']: return search_loc
        return "Other"
    df['District'] = df.apply(extract_district_custom, axis=1)

    # 3. BED CLASS 
    print("   -> Đang phân loại Giường (dùng dấu &)...")
    df['Bed_Class'] = df['Bed Type'].apply(lambda x: extract_tags(x, BED_MAPPING))

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
        try: return float(str(value).replace(',', '.'))
        except: return np.nan
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

    # 8. ROOM CLASS 
    print("   -> Đang phân loại Phòng (dùng dấu &)...")
    df['Room_Class'] = df['Room Type'].apply(lambda x: extract_tags(x, ROOM_MAPPING))

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
        'Scenario', 'Search Location', 'Hotel Name', 'Hotel Link',
        'Stars_Clean', 'District', 'Address',
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

    # --- BƯỚC G: LƯU VÀO DATABASE ---
    print("   -> Đang xóa trùng lặp nâng cao (2 LỚP)...")
    
    # 1. LỚP LỌC 1:
    ignore_cols = ['Scenario', 'Adults', 'Children', 'Rooms', 'Total_Guests', 'Check-in', 'Hotel Link']
    subset_cols_1 = [c for c in df_clean.columns if c not in ignore_cols]
    
    len_0 = len(df_clean)
    if subset_cols_1:
        df_clean = df_clean.drop_duplicates(subset=subset_cols_1, keep='first')
    len_1 = len(df_clean)
    print(f"      - Lớp 1 (Cơ bản): Đã xóa {len_0 - len_1} dòng.")

    # 2. LỚP LỌC 2:
    strict_subset = ['Hotel Name', 'Room Type', 'Final Price', 'Address']
    valid_strict_subset = [c for c in strict_subset if c in df_clean.columns]
    
    if valid_strict_subset:
        if 'Rating_Clean' in df_clean.columns:
             df_clean = df_clean.sort_values(by=['Hotel Name', 'Final Price', 'Rating_Clean'], ascending=[True, True, False])
        df_clean = df_clean.drop_duplicates(subset=valid_strict_subset, keep='first')
        
    len_2 = len(df_clean)
    print(f"      - Lớp 2 (Mạnh tay): Đã xóa thêm {len_1 - len_2} dòng.")

    print("3. Đang chuẩn bị lưu vào Postgres...")
    
    # 1. Reset index
    df_clean = df_clean.reset_index(drop=True)
    df_clean.index = df_clean.index + 1  
    df_clean['id'] = df_clean.index      
    
    # 2. Chuẩn hóa tên cột
    df_clean.columns = [c.strip().lower().replace(' ', '_').replace('-', '_').replace('%', 'percent') for c in df_clean.columns]
    
    try:
        # === DROP TABLE room_details NẾU CÓ ===
        with engine.connect() as conn:
            print("   -> Đang kiểm tra và xóa bảng 'room_details' cũ (nếu có)...")
            conn.execute(text("DROP TABLE IF EXISTS room_details CASCADE;"))
            conn.commit()
            print("      - Đã thực hiện lệnh: DROP TABLE IF EXISTS room_details")
        # ======================================================

        # 3. Lưu bảng
        df_clean.to_sql(output_table_name, engine, if_exists='replace', index=False)
        
        # 4. SET PRIMARY KEY
        with engine.connect() as conn:
            conn.execute(text(f"ALTER TABLE {output_table_name} ADD PRIMARY KEY (id);"))
            conn.commit()
            
        print(f"HOÀN TẤT! Đã lưu {len(df_clean)} dòng sạch vào bảng '{output_table_name}'.")
        print("      - Đã tạo cột 'id' và thiết lập PRIMARY KEY thành công.")
        
    except Exception as e:
        print(f"Lỗi khi lưu vào Database: {e}")

# --- CHẠY CHƯƠNG TRÌNH ---
if __name__ == "__main__":
    RAW_TABLE = "hotel_scenarios"
    CLEAN_TABLE = "hotel_data_cleaned" 
    
    df_raw = load_data_from_db(RAW_TABLE)
    clean_and_save_data(df_raw, CLEAN_TABLE)