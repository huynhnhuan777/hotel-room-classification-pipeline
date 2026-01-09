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
DB_CONNECTION_STR = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
engine = create_engine(DB_CONNECTION_STR)

# --- 2. TỪ ĐIỂN MAPPING ĐỊA ĐIỂM ---
LOCATION_MAPPING_DICT = {
    'ho chi minh': 'Hồ Chí Minh', 'hcm': 'Hồ Chí Minh', 'sai gon': 'Hồ Chí Minh',
    'ha noi': 'Hà Nội', 'hanoi': 'Hà Nội',
    'vung tau': 'Vũng Tàu', 'ba ria': 'Vũng Tàu',
    'da nang': 'Đà Nẵng', 'danang': 'Đà Nẵng',
    'da lat': 'Đà Lạt', 'dalat': 'Đà Lạt', 'lam dong': 'Đà Lạt',
    'nha trang': 'Nha Trang', 'khanh hoa': 'Nha Trang',
    'phu quoc': 'Phú Quốc', 'kien giang': 'Phú Quốc',
    'hoi an': 'Hội An', 'quang nam': 'Hội An',
    'phan thiet': 'Phan Thiết', 'mui ne': 'Phan Thiết', 'binh thuan': 'Phan Thiết',
    'hue': 'Huế', 'thua thien hue': 'Huế',
    'quy nhon': 'Quy Nhơn', 'binh dinh': 'Quy Nhơn',
    'sapa': 'Sapa', 'sa pa': 'Sapa', 'lao cai': 'Sapa',
    'ha long': 'Hạ Long', 'quang ninh': 'Hạ Long',
    'hai phong': 'Hải Phòng',
    'can tho': 'Cần Thơ',
    'binh duong': 'Bình Dương',
    'dong nai': 'Đồng Nai', 'bien hoa': 'Đồng Nai',
    'quang binh': 'Quảng Bình', 'dong hoi': 'Quảng Bình',
    'thanh hoa': 'Thanh Hóa',
    'nghe an': 'Nghệ An', 'vinh': 'Nghệ An',
    'ninh binh': 'Ninh Bình',
    'phu yen': 'Phú Yên', 'tuy hoa': 'Phú Yên'
}

def clean_location_general(text):
    if pd.isna(text) or str(text).strip() == "":
        return "Unknown"
    
    raw = str(text).lower().replace('-', ' ').replace('.', ' ').strip()
    
    for key, val in LOCATION_MAPPING_DICT.items():
        if key in raw:
            return val
            
    return str(text).replace('-', ' ').title()

# --- 3. CÁC HÀM XỬ LÝ SỐ LIỆU (Giữ lại để đảm bảo sạch) ---
def clean_price(value):
    if pd.isna(value): return None 
    try: 
        if isinstance(value, (int, float)): return int(value)
        price = int(re.sub(r'[^\d]', '', str(value)))
        return price if price > 0 else None
    except: return None

def clean_area(value):
    if not value or pd.isna(value): return None
    try:
        val_str = str(value).lower().replace('m2', '').replace('m²', '').replace(',', '.').strip()
        match = re.search(r"(\d+(\.\d+)?)", val_str)
        return float(match.group(1)) if match else None
    except: return None

def clean_people(value):
    if pd.isna(value): return None
    try:
        if isinstance(value, (int, float)): return int(value)
        match = re.search(r"(\d+)", str(value))
        return int(match.group(1)) if match else None
    except: return None

def clean_facilities_short(value):
    if pd.isna(value) or str(value).strip() == "": return None
    val_str = str(value).replace("--- hoặc ---", "|")
    items = re.split(r'[;,|\n]', val_str)
    cleaned_items = []
    for item in items:
        item = item.strip().lower()
        if item and len(item) < 60 and 'http' not in item and item not in ['nan', 'null', 'none']:
            item = item.strip('.-_ ')
            cleaned_items.append(item)
    return ", ".join(sorted(list(set(cleaned_items)))) if cleaned_items else None

# --- 4. CHƯƠNG TRÌNH CHÍNH ---
def main():
    print("1. Đang đọc dữ liệu từ Database...")
    try:
        query = "SELECT * FROM merged_data"
        df = pd.read_sql(query, engine)
        print(f" -> Đã load {len(df)} dòng dữ liệu.")
        # print("Cột hiện có:", list(df.columns)) # Bỏ comment nếu muốn kiểm tra tên cột
    except Exception as e:
        print(f"Lỗi: {e}")
        return

    print("2. Đang xử lý và chuẩn hóa...")

    # CẤU HÌNH TÊN CỘT TRONG DATABASE (merged_data)
    # Lưu ý: 'room_class' và 'bed_type' đã được xử lý ở bước trước
    col_room_raw = 'room_type'      # Tên gốc
    col_room_class = 'room_class'   # Đã xử lý (Standard, Deluxe...)
    col_bed_final = 'bed_type'      # Đã xử lý (Double, King...)
    
    col_price = 'Final Price'       # Có thể là 'final_price' tùy DB
    col_area = 'Area_m2'            # Có thể là 'area_m2'
    col_max_people = 'Max People'   # Có thể là 'max_people'
    col_facilities = 'Facilities'   # Có thể là 'facilities'
    
    col_location = 'location'       
    col_source = 'Source'           # Có thể là 'source'
    col_link = 'Hotel Link'         # Có thể là 'hotel_link'
    col_hotel_name = 'Hotel Name'   # Có thể là 'hotel_name'

    # Fallback tên cột (đề phòng DB lưu chữ thường snake_case)
    if col_price not in df.columns and 'final_price' in df.columns: col_price = 'final_price'
    if col_area not in df.columns and 'area_m2' in df.columns: col_area = 'area_m2'
    if col_max_people not in df.columns and 'max_people' in df.columns: col_max_people = 'max_people'
    if col_facilities not in df.columns and 'facilities' in df.columns: col_facilities = 'facilities'
    if col_source not in df.columns and 'source' in df.columns: col_source = 'source'
    if col_link not in df.columns and 'hotel_link' in df.columns: col_link = 'hotel_link'
    if col_hotel_name not in df.columns and 'hotel_name' in df.columns: col_hotel_name = 'hotel_name'

    # --- XỬ LÝ LOCATION (CHUẨN HÓA) ---
    print(" -> Đang chuẩn hóa cột Location...")
    if col_location in df.columns:
        df['location_clean'] = df[col_location].apply(clean_location_general)
    else:
        df['location_clean'] = "Unknown"

    # --- LÀM SẠCH SỐ LIỆU (Safety check) ---
    if col_price in df.columns: df['final_price'] = df[col_price].apply(clean_price)
    else: return
    
    if col_area in df.columns: df['area_m2_clean'] = df[col_area].apply(clean_area)
    else: df['area_m2_clean'] = None
    
    if col_max_people in df.columns: df['max_people_clean'] = df[col_max_people].apply(clean_people)
    else: df['max_people_clean'] = None
    
    if col_facilities in df.columns: df['facilities_clean'] = df[col_facilities].apply(clean_facilities_short)
    else: df['facilities_clean'] = None

    # --- KHÔNG XỬ LÝ LẠI ROOM/BED -> CHỈ MAPPING ---
    print(" -> Mapping dữ liệu Room/Bed đã có sẵn...")
    
    # 1. Room Name Gốc
    if col_room_raw in df.columns:
        df['room_name_original'] = df[col_room_raw]
    else:
        df['room_name_original'] = None

    # 2. Room Class (Đã có sẵn)
    if col_room_class in df.columns:
        df['room_class_final'] = df[col_room_class]
    else:
        print(f"CẢNH BÁO: Không tìm thấy cột '{col_room_class}' trong DB.")
        df['room_class_final'] = 'Standard'

    # 3. Bed Type (Đã có sẵn)
    if col_bed_final in df.columns:
        df['bed_type_final'] = df[col_bed_final]
    else:
        print(f"CẢNH BÁO: Không tìm thấy cột '{col_bed_final}' trong DB.")
        df['bed_type_final'] = 'Unknown'
    
    # Chuẩn hóa tên khách sạn
    df['hotel_name_clean'] = df[col_hotel_name].str.strip().str.title() if col_hotel_name in df.columns else ""

    # --- MAPPING OUTPUT ---
    final_mapping = {
        col_source: 'source',
        'location_clean': 'location',   
        col_link: 'hotel_link',
        'hotel_name_clean': 'hotel_name',
        'room_name_original': 'room_type',    # Tên gốc
        'room_class_final': 'room_class',     # Lấy trực tiếp từ DB
        'bed_type_final': 'bed_type',         # Lấy trực tiếp từ DB
        'area_m2_clean': 'area_m2',
        'max_people_clean': 'max_people',
        'final_price': 'final_price',
        'facilities_clean': 'facilities_cleaned'
    }

    df_out = pd.DataFrame()
    for src_col, dest_col in final_mapping.items():
        if src_col in df.columns:
            df_out[dest_col] = df[src_col]
        else:
            df_out[dest_col] = None 

    # --- LỌC DỮ LIỆU ---
    print("-" * 30)
    print(f" -> Số lượng trước khi lọc: {len(df_out)}")
    
    # Lọc nếu thiếu dữ liệu quan trọng (Giá, Diện tích, Số người)
    # Không lọc Location, không lọc Room/Bed (vì đã có sẵn)
    cols_to_check = [c for c in df_out.columns if c not in ['facilities_cleaned', 'location']]
    df_filtered = df_out.dropna(subset=cols_to_check, how='any')

    print(f" -> Số lượng sau khi lọc dữ liệu lỗi: {len(df_filtered)}")
    
    # Khử trùng lặp
    dedup_subset = ['hotel_name', 'room_type', 'final_price', 'max_people', 'area_m2']
    valid_dedup = [c for c in dedup_subset if c in df_filtered.columns]
    
    if len(df_filtered) > 0:
        df_filtered = df_filtered.drop_duplicates(subset=valid_dedup, keep='first')
    
    print(f" -> TỔNG CỘNG CÒN LẠI: {len(df_filtered)} dòng.")

    # --- LƯU FILE ---
    output_table = "merged_data_cleaned"
    output_csv = "merged_data_cleaned.csv"
    
    if len(df_filtered) > 0:
        try:
            df_filtered.to_sql(output_table, engine, if_exists='replace', index=False)
            df_filtered.to_csv(output_csv, index=False, encoding='utf-8-sig')
            print(f" -> [OK] Đã xuất file CSV và lưu DB.")
            print("\nTop 5 địa điểm:")
            print(df_filtered['location'].value_counts().head(5))
            print("\nTop 5 loại phòng (Room Class):")
            print(df_filtered['room_class'].value_counts().head(5))
        except Exception as e:
            print(f"Lỗi lưu: {e}")
    else:
        print("CẢNH BÁO: Dữ liệu trống!")

if __name__ == "__main__":
    main()