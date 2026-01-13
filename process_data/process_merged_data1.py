import pandas as pd
import numpy as np
from sqlalchemy import create_engine

# --- CẤU HÌNH DATABASE ---
DB_CONFIG = {
    "dbname": "booking_data",
    "user": "postgres",
    "password": "123456",
    "host": "localhost",
    "port": "5432"
}
DB_CONNECTION_STR = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

# --- CẤU HÌNH LOGIC ---
TARGET_COLUMNS = [
    'Source', 'location', 'Hotel Name', 'Hotel Link', 
    'room_type', 'room_class', 'bed_type', 
    'Final Price', 'Max People', 'Area_m2', 'Facilities'
]

def standardize_room_type(room_type):
    if pd.isna(room_type) or str(room_type).strip() == "": return 'Unknown'
    text = str(room_type).strip().lower()
    if any(x in text for x in ['villa', 'bungalow', 'biệt thự', 'luxury', 'vip', 'royal', 'president']): return 'Luxury'
    if any(x in text for x in ['suite', 'penthouse', 'apartment', 'căn hộ', 'studio']): return 'Suite'
    if any(x in text for x in ['executive', 'doanh nhân']): return 'Executive'
    if any(x in text for x in ['deluxe', 'cao cấp']): return 'Deluxe'
    if 'superior' in text: return 'Superior'
    if any(x in text for x in ['standard', 'tiêu chuẩn', 'dorm', 'tập thể', 'family', 'economy', 'budget']): return 'Standard'
    return 'Unknown'

def standardize_bed_type(bed_type):
    if pd.isna(bed_type): return 'Unknown'
    text = str(bed_type).lower()
    beds = []
    if 'king' in text: beds.append('King')
    if 'queen' in text: beds.append('Queen')
    if 'double' in text or 'đôi' in text: beds.append('Double')
    if 'single' in text or 'đơn' in text or 'twin' in text: beds.append('Single')
    if 'bunk' in text or 'tầng' in text: beds.append('Bunk')
    if 'sofa' in text: beds.append('Sofa Bed')
    return beds[0] if len(set(beds)) == 1 else ('Mixed Beds' if beds else 'Unknown')

def clean_and_save_to_db(df, mapping, source_name, table_name, engine):
    """Hàm xử lý sạch và lưu TRỰC TIẾP vào Database"""
    print(f"-> Đang xử lý nguồn: {source_name}...")
    
    # 1. Đổi tên cột và gán nguồn
    df = df.rename(columns=mapping)
    df['Source'] = source_name
    
    # 2. Chuẩn hóa dữ liệu logic
    df['room_class'] = df['room_type'].apply(standardize_room_type)
    df['bed_type'] = df['bed_type'].apply(standardize_bed_type)
    
    # 3. Bổ sung cột thiếu và lọc đúng danh sách cột mục tiêu
    for col in TARGET_COLUMNS:
        if col not in df.columns: 
            df[col] = np.nan
            
    clean_df = df[TARGET_COLUMNS]
    
    # 4. Lưu vào Database (if_exists='replace' để làm mới bảng)
    try:
        clean_df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"   [Thành công] Đã cập nhật Table: {table_name}")
    except Exception as e:
        print(f"   [Lỗi SQL] {e}")
    print("-" * 30)

def main():
    print("-> ĐANG KẾT NỐI DATABASE...")
    try:
        engine = create_engine(DB_CONNECTION_STR)
    except Exception as e:
        print(f"Lỗi kết nối: {e}")
        return

    # 1. Xử lý Booking
    try:
        df_b = pd.read_csv("../merged_data/merged_data_from_sql.csv")
        map_b = {'Search Location': 'location', 'Hotel Name': 'Hotel Name', 'Hotel Link': 'Hotel Link', 'Room Type': 'room_type', 'Bed Type': 'bed_type', 'Total_Guests': 'Max People'}
        clean_and_save_to_db(df_b, map_b, 'Booking', 'clean_booking', engine)
    except Exception as e: print(f"Lỗi đọc file Booking: {e}")

    # 2. Xử lý Ivivu
    try:
        df_i = pd.read_csv("../merged_data/merged_hotel_rooms.csv")
        map_i = {'city': 'location', 'hotel_name': 'Hotel Name', 'hotel_link': 'Hotel Link', 'room_name': 'room_type', 'price': 'Final Price', 'area_m2': 'Area_m2', 'amenities': 'Facilities', 'max_occupancy': 'Max People'}
        clean_and_save_to_db(df_i, map_i, 'Ivivu', 'clean_ivivu', engine)
    except Exception as e: print(f"Lỗi đọc file Ivivu: {e}")

    # 3. Xử lý Mytour
    try:
        df_m = pd.read_excel("../merged_data/mytour_rooms_full02.xlsx")
        map_m = {'hotel_name': 'Hotel Name', 'hotel_link': 'Hotel Link', 'room_name': 'room_type', 'final_price': 'Final Price', 'area': 'Area_m2', 'bed': 'bed_type', 'room_amenities': 'Facilities', 'people': 'Max People'}
        clean_and_save_to_db(df_m, map_m, 'Mytour', 'clean_mytour', engine)
    except Exception as e: print(f"Lỗi đọc file Mytour: {e}")

if __name__ == "__main__":
    main()