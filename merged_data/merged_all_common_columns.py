import pandas as pd
import numpy as np
import re
from sqlalchemy import create_engine

# --- CẤU HÌNH DATABASE ---
DB_CONFIG = {
    "dbname": "booking_data",  
    "user": "postgres",         
    "password": "123456",  
    "host": "localhost",          
    "port": "5432"             
}

# --- CÁC HÀM CHUẨN HÓA  ---
def standardize_room_type(room_type):
    if pd.isna(room_type) or str(room_type).strip() == "":
        return 'Unknown'

    text = str(room_type).strip().lower()

    # 1. LUXURY (Ưu tiên cao nhất: Villa, Bungalow, VIP...)
    if any(x in text for x in ['villa', 'bungalow', 'biệt thự', 'luxury', 'vip', 'royal', 'president', 'hoàng gia', 'tổng thống']):
        return 'Luxury'

    # 2. SUITE (Bao gồm cả Apartment, Studio, Penthouse)
    if any(x in text for x in ['suite', 'penthouse', 'apartment', 'căn hộ', 'studio']):
        return 'Suite'

    # 3. EXECUTIVE
    if any(x in text for x in ['executive', 'doanh nhân']):
        return 'Executive'

    # 4. DELUXE
    if any(x in text for x in ['deluxe', 'cao cấp']):
        return 'Deluxe'

    # 5. SUPERIOR
    if 'superior' in text:
        return 'Superior'

    # 6. STANDARD (Nhóm còn lại: Standard, Economy, Dorm, Family...)
    # Mặc định các phòng Dorm, tập thể, family, budget sẽ đưa về Standard
    return 'Standard'

def standardize_bed_type(bed_type):
    if pd.isna(bed_type):
        return 'Unknown'

    text = str(bed_type).lower()
    beds = []

    if 'king' in text:
        beds.append('King')
    if 'queen' in text:
        beds.append('Queen')
    if 'double' in text or 'đôi' in text:
        beds.append('Double')
    if 'single' in text or 'đơn' in text or 'twin' in text:
        beds.append('Single')
    if 'bunk' in text or 'tầng' in text:
        beds.append('Bunk')
    if 'sofa' in text:
        beds.append('Sofa Bed')

    if not beds:
        return 'Unknown'
    if len(set(beds)) == 1:
        return beds[0]
    return 'Mixed Beds'

def clean_col_name(df):
    """Hàm xóa khoảng trắng thừa ở tên cột"""
    df.columns = df.columns.str.strip()
    return df

# =============================================================================
# CHƯƠNG TRÌNH CHÍNH
# =============================================================================

def main():
    # 1. ĐỌC DỮ LIỆU TỪ 3 FILE
    print("-> Đang đọc dữ liệu...")
    try:
        # Booking
        df_booking = pd.read_csv("merged_data_from_sql.csv") 
        df_booking = clean_col_name(df_booking)
        
        # Ivivu
        df_ivivu = pd.read_csv("merged_hotel_rooms.csv")
        df_ivivu = clean_col_name(df_ivivu)
        
        # Mytour
        df_mytour = pd.read_excel("mytour_rooms_full02.xlsx")
        df_mytour = clean_col_name(df_mytour)
        
    except FileNotFoundError as e:
        print(f"Lỗi: Không tìm thấy file. {e}")
        return

    # 2. ĐỊNH NGHĨA MAPPING

    # Mapping Booking -> Chuẩn
    map_booking = {
        'Scenario': 'Scenario',
        'Search Location': 'location',
        'Hotel Name': 'Hotel Name',
        'Hotel Link': 'Hotel Link',
        'Room Type': 'room_type',  
        'Final Price': 'Final Price',
        'Bed Type': 'bed_type',  
        'Area_m2': 'Area_m2',           
        'Facilities': 'Facilities',     
        'Total_Guests': 'Max People'    
    }

    # Mapping Ivivu -> Chuẩn
    map_ivivu = {
        'city': 'location',  
        'hotel_name': 'Hotel Name',
        'hotel_link': 'Hotel Link',
        'room_name': 'room_type', 
        'price': 'Final Price',
        'area_m2': 'Area_m2',
        'bed_type': 'bed_type', 
        'amenities': 'Facilities',
        'max_occupancy': 'Max People'
    }

    # Mapping Mytour -> Chuẩn
    map_mytour = {
        'hotel_name': 'Hotel Name',
        'hotel_link': 'Hotel Link',
        'room_name': 'room_type',
        'final_price': 'Final Price',
        'area': 'Area_m2',
        'bed': 'bed_type',
        'room_amenities': 'Facilities',
        'people': 'Max People'
    }

    # 3. ĐỔI TÊN CỘT
    df_booking = df_booking.rename(columns=map_booking)
    df_ivivu = df_ivivu.rename(columns=map_ivivu)
    df_mytour = df_mytour.rename(columns=map_mytour)

    # 4. THÊM CỘT SOURCE
    df_booking['Source'] = 'Booking'
    df_ivivu['Source'] = 'Ivivu'
    df_mytour['Source'] = 'Mytour'

    # 5. GỘP DỮ LIỆU

    target_columns = [
        'Source', 'location', 'Hotel Name', 'Hotel Link', 
        'room_type', 'Final Price', 'Max People', 
        'Area_m2', 'bed_type', 'Facilities'
    ]

    # Kiểm tra xem các dataframe có đủ cột không, nếu thiếu thì thêm vào với giá trị NaN
    for df in [df_booking, df_ivivu, df_mytour]:
        for col in target_columns:
            if col not in df.columns:
                df[col] = np.nan 

    df_final = pd.concat([
        df_booking[target_columns],
        df_ivivu[target_columns],
        df_mytour[target_columns]
    ], axis=0, ignore_index=True)

    print(f"-> Tổng số dòng dữ liệu gộp được: {len(df_final)}")

    # 6. XỬ LÝ DỮ LIỆU SAU KHI GỘP (FEATURE ENGINEERING)

    print("-> Đang xử lý Location và chuẩn hóa Room/Bed...")

    # 6.1 Xử lý Location: Điền chuỗi rỗng nếu thiếu
    df_final['location'] = df_final['location'].fillna("").astype(str).str.strip()

    # 6.2 Tạo cột room_class từ room_type
    print("-> Đang phân loại Room Class về 7 nhóm: Standard, Deluxe, Superior, Suite, Executive, Luxury, Unknown...")
    df_final['room_class'] = df_final['room_type'].apply(standardize_room_type)

    # 6.3 Chuẩn hóa lại cột bed_type
    df_final['bed_type'] = df_final['bed_type'].apply(standardize_bed_type)

    # Sắp xếp lại cột
    final_cols_order = [
        'Source', 'location', 'Hotel Name', 'Hotel Link', 
        'room_type', 'room_class', 'bed_type', 
        'Final Price', 'Max People', 'Area_m2', 'Facilities'
    ]
    final_cols_order = [c for c in final_cols_order if c in df_final.columns]
    df_final = df_final[final_cols_order]

    # 7. LƯU VÀO DATABASE
    print("-" * 30)
    print("-> Đang lưu vào Postgres...")
    try:
        connection_str = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
        engine = create_engine(connection_str)
        
        df_final.to_sql('merged_data', engine, if_exists='replace', index=False)
        print("-> [THÀNH CÔNG] Đã lưu vào bảng 'merged_data'.")
        
        # In mẫu dữ liệu để kiểm tra
        print("\nMẫu dữ liệu sau khi xử lý:")
        print(df_final[['Source', 'location', 'room_type', 'room_class', 'bed_type']].head(10))
        
        # Thống kê nhanh
        print("\nThống kê Room Class:")
        print(df_final['room_class'].value_counts())
        
    except Exception as e:
        print(f"-> [LỖI] Không thể lưu vào DB: {e}")

if __name__ == "__main__":
    main()