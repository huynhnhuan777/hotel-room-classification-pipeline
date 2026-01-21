import pandas as pd
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

# --- 2. HÀM BIẾN ĐỔI DỮ LIỆU ---
def transform_hotel_data(df):
    # Chuẩn hóa dữ liệu văn bản
    text_cols = ['room_type', 'bed_type', 'Facilities']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().str.strip()

    # Tạo các cột Boolean cho giường
    bed_keywords = {
        'is_king': r'king',
        'is_queen': r'queen',
        'is_double': r'double|đôi',
        'is_single': r'single|đơn',
        'is_bunk': r'bunk|giường tầng',
        'is_sofa': r'sofa'
    }

    for bed, pattern in bed_keywords.items():
        df[bed] = df.apply(lambda x: 1 if re.search(pattern, str(x.get('room_type', ''))) or 
                                         re.search(pattern, str(x.get('bed_type', ''))) or
                                         re.search(pattern, str(x.get('Facilities', ''))) else 0, axis=1)

    # Trích xuất tiện ích từ Facilities
    facility_keywords = {
        'has_wifi': r'wifi|internet|mạng',
        'has_ac': r'điều hòa|máy lạnh|air conditioning|ac',
        'has_breakfast': r'ăn sáng|breakfast',
        'has_tv': r'tv|tivi|television',
        'has_pool': r'hồ bơi|bể bơi|swimming pool|pool',
        'has_balcony': r'ban công|balcony|view',
        'has_parking': r'đỗ xe|bãi đậu xe|parking',
        'has_kitchen': r'bếp|kitchen|lò vi sóng|microwave',
        'has_fridge': r'tủ lạnh|refrigerator|fridge|minibar'
    }

    for feat, pattern in facility_keywords.items():
        if 'Facilities' in df.columns:
            df[feat] = df['Facilities'].apply(lambda x: 1 if re.search(pattern, str(x)) else 0)

    # Tính toán các chỉ số
    # Thêm fillna(0) để tránh lỗi chia cho 0 hoặc dữ liệu trống
    df['price_per_m2'] = (df['Final Price'] / df['Area_m2']).fillna(0)
    df['m2_per_person'] = (df['Area_m2'] / df['Max People']).fillna(0)
    
    # Đếm số lượng tiện ích
    df['num_facilities'] = df['Facilities'].apply(lambda x: len(str(x).split(',')) if str(x) != 'nan' else 0)

    # Gắn nhãn hạng sang
    luxury_keywords = r'deluxe|superior|suite|premium|luxury|executive'
    df['has_luxury_keyword'] = df['room_type'].apply(lambda x: 1 if re.search(luxury_keywords, str(x)) else 0)

    # Danh sách cột giữ lại
    facility_cols = list(facility_keywords.keys())
    bed_cols = list(bed_keywords.keys())
    cols_to_keep = [
        'Final Price', 'Max People', 'Area_m2', 'price_per_m2', 'm2_per_person',
        'num_facilities', 'has_luxury_keyword', 'room_class'
    ] + bed_cols + facility_cols
    
    final_cols = [c for c in cols_to_keep if c in df.columns]
    return df[final_cols]

# --- 3. QUY TRÌNH THỰC THI ---
try:
    # Khởi tạo kết nối
    engine = create_engine(DB_CONNECTION_STR)
    print("--- Đang kết nối Database... ---")

    # A. Đọc dữ liệu từ merged_data
    query = "SELECT * FROM merged_data"
    df_raw = pd.read_sql(query, engine)
    print(f"Đã lấy {len(df_raw)} dòng dữ liệu từ bảng 'merged_data'.")

    # B. Biến đổi dữ liệu
    print("--- Đang xử lý biến đổi dữ liệu... ---")
    df_transformed = transform_hotel_data(df_raw)

    # C. Lưu vào bảng tranform_data trong Database
    # if_exists='replace' sẽ tạo lại bảng mới mỗi khi chạy, 
    print("--- Đang lưu dữ liệu vào bảng 'tranform_data'... ---")
    df_transformed.to_sql('tranform_data_test', engine, if_exists='replace', index=False)
    print("Lưu vào Database thành công!")

    # D. Xuất ra file CSV
    csv_filename = "../data/hotel_data_transformed.csv"
    df_transformed.to_csv(csv_filename, index=False, encoding='utf-8-sig')
    print(f"Đã xuất file CSV thành công: {csv_filename}")

except Exception as e:
    print(f"Đã xảy ra lỗi: {e}")

finally:
    # Đóng kết nối
    print("--- Hoàn tất quy trình ---")