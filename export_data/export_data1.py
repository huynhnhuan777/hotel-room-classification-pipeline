import pandas as pd
from sqlalchemy import create_engine
import os

# --- 1. CẤU HÌNH DATABASE ---
DB_CONFIG = {
    "dbname": "booking_data",
    "user": "postgres",
    "password": "123456", 
    "host": "localhost",
    "port": "5432"
}
DB_CONNECTION_STR = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

# --- 2. CẤU HÌNH ---
TABLE_HOTEL = "hotel_scenarios"
TABLE_ROOM = "room_details"
OUTPUT_FILE = "data_booking.com/merged_data_from_sql.csv"

# Danh sách cột mong muốn xuất ra CSV
COLS_ORDER_EXPORT = [
    'Scenario', 'Search Location', 'Hotel Name', 'Hotel Link',
    'Stars_Clean', 'District', 'Address',
    'Room_Class', 'Room Type', 'Bed_Class', 'Bed Type', 'Rooms',
    'Final Price', 'Original Price', 'Discount %',
    'Rating_Clean', 'Review Count', 'Location_Clean', 'Distance_KM',
    'Free_Cancel_Bool', 'Breakfast_Bool', 'Badge_Clean',
    'Adults', 'Children', 'Total_Guests', 'Check-in',
    'Area_m2', 'Facilities'
]

def export_joined_data():
    if not os.path.exists("data"):
        os.makedirs("data")
        
    print(f"=== KẾT NỐI DATABASE & XUẤT CSV ===")
    
    try:
        engine = create_engine(DB_CONNECTION_STR)
        
        # --- [ĐÃ SỬA] CÂU QUERY SQL ---
        # Sửa t2."Area_m2" -> t2.area_m2 (chữ thường, không ngoặc kép)
        # Sửa t2."Facilities" -> t2.facilities
        query = f"""
        SELECT 
            t1.id,
            t1.search_location,
            t1.scenario,
            t1.hotel_name,
            t1.hotel_link,
            t1.stars,
            t1.address, 
            t1.distance,
            t1.rating_score,
            t1.review_count,
            t1.final_price,
            t1.original_price,
            t1.room_type,
            t1.bed_type,
            t1.free_cancellation,
            t1.breakfast_included,
            t1.badge_deal,
            t1.adults,
            t1.children,
            t1.check_in,
            t2.area_m2,     
            t2.facilities   
        FROM {TABLE_HOTEL} t1
        LEFT JOIN {TABLE_ROOM} t2 ON t1.id = t2.hotel_id
        ORDER BY t1.id ASC
        """
        
        print("-> Đang thực thi query SQL...")
        df = pd.read_sql(query, engine)
        
        if df.empty:
            print("⚠️ Không lấy được dữ liệu.")
            return

        print(f"-> Đã tải về {len(df)} dòng. Đang xử lý Python...")

        # --- XỬ LÝ DỮ LIỆU ---
        
        # 1. TẠO CỘT DISTRICT TỪ ADDRESS
        df['District'] = df['address'].apply(lambda x: str(x).split(',')[0] if pd.notna(x) else '')

        # 2. Xử lý giá & Discount
        df['original_price'] = pd.to_numeric(df['original_price'], errors='coerce').fillna(0)
        df['final_price'] = pd.to_numeric(df['final_price'], errors='coerce').fillna(0)
        
        df['Discount %'] = df.apply(
            lambda x: f"{round(((x['original_price'] - x['final_price']) / x['original_price'] * 100), 1)}%" 
            if x['original_price'] > 0 else "0.0%", axis=1
        )

        # 3. Đổi tên cột (Mapping từ tên trong DB -> Tên trong CSV)
        rename_map = {
            'scenario': 'Scenario',
            'search_location': 'Search Location',
            'hotel_name': 'Hotel Name',
            'hotel_link': 'Hotel Link',
            'stars': 'Stars_Clean',
            'address': 'Address',
            'room_type': 'Room Type',
            'bed_type': 'Bed Type',
            'rooms': 'Rooms',
            'final_price': 'Final Price',
            'original_price': 'Original Price',
            'rating_score': 'Rating_Clean',
            'review_count': 'Review Count',
            'distance': 'Distance_KM',
            'badge_deal': 'Badge_Clean',
            'adults': 'Adults',
            'children': 'Children',
            'check_in': 'Check-in',
            'area_m2': 'Area_m2',       # Mapping cột area_m2 (thường) -> Area_m2 (hoa)
            'facilities': 'Facilities'  # Mapping cột facilities (thường) -> Facilities (hoa)
        }
        df.rename(columns=rename_map, inplace=True)

        # 4. Các cột tính toán thêm
        df['Total_Guests'] = df['Adults'].fillna(0) + df['Children'].fillna(0)
        df['Free_Cancel_Bool'] = df['free_cancellation'].map({'Yes': True, 'No': False}).fillna(False)
        df['Breakfast_Bool'] = df['breakfast_included'].map({'Yes': True, 'No': False}).fillna(False)
        
        # Tạo các cột còn thiếu
        for col in COLS_ORDER_EXPORT:
            if col not in df.columns:
                df[col] = None

        # 5. Xuất file
        df = df.reindex(columns=COLS_ORDER_EXPORT)
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"✅ THÀNH CÔNG! File đã lưu tại: {os.path.abspath(OUTPUT_FILE)}")

    except Exception as e:
        print(f"❌ LỖI: {e}")

if __name__ == "__main__":
    export_joined_data()