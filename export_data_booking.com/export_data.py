import pandas as pd
from sqlalchemy import create_engine
import json
import os

# --- CẤU HÌNH DATABASE ---
DB_CONFIG = {
    "dbname": "booking_data",
    "user": "postgres",
    "password": "123456", 
    "host": "localhost",
    "port": "5432"
}
DB_CONNECTION_STR = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

engine = create_engine(DB_CONNECTION_STR)
OUTPUT_FOLDER = "data"

# --- DANH SÁCH CỘT MONG MUỐN XUẤT RA CSV ---
COLS_ORDER_EXPORT = [
    'Scenario', 'Search Location', 'Hotel Name', 'Hotel Link',
    'Stars_Clean', 'District', 'Address',
    'Room_Class', 'Room Type', 'Bed_Class', 'Bed Type', 'Rooms',
    'Final Price', 'Original Price', 'Discount %',
    'Rating_Clean', 'Review Count', 'Location_Clean', 'Distance_KM',
    'Free_Cancel_Bool', 'Breakfast_Bool', 'Badge_Clean',
    'Adults', 'Children', 'Total_Guests', 'Check-in',
    'Area_m2_cleaned', 'Facilities_cleaned' # bảng room_details_cleaned
]

# --- MAPPING: TÊN CỘT DB (snake_case) -> TÊN CỘT CSV (Title Case) ---
COLUMN_MAPPING = {
    'scenario': 'Scenario',
    'search_location': 'Search Location',
    'hotel_name': 'Hotel Name',
    'hotel_link': 'Hotel Link',
    'stars_clean': 'Stars_Clean',
    'district': 'District',
    'address': 'Address',
    'room_class': 'Room_Class',
    'room_type': 'Room Type',
    'bed_class': 'Bed_Class',
    'bed_type': 'Bed Type',
    'rooms': 'Rooms',
    'final_price': 'Final Price',
    'original_price': 'Original Price',
    'discount_percent': 'Discount %',
    'rating_clean': 'Rating_Clean',
    'review_count': 'Review Count',
    'location_clean': 'Location_Clean',
    'distance_km': 'Distance_KM',
    'free_cancel_bool': 'Free_Cancel_Bool',
    'breakfast_bool': 'Breakfast_Bool',
    'badge_clean': 'Badge_Clean',
    'adults': 'Adults',
    'children': 'Children',
    'total_guests': 'Total_Guests',
    'check_in': 'Check-in',
    # Cột từ bảng phụ room_details
    'area_m2_cleaned': 'Area_m2_cleaned',
    'facilities_cleaned': 'Facilities_cleaned'
}

def export_all_data():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        
    print(f"\n=== BẮT ĐẦU QUÁ TRÌNH EXPORT DỮ LIỆU ===")

    # ---------------------------------------------------------
    # PHẦN 1: EXPORT FILE GỘP (CSV)
    # ---------------------------------------------------------
    print("\n[1/2] Đang xử lý file CSV gộp (Clean Data + Room Details)...")
    
    # Query lấy đúng tên cột snake_case trong DB
    query_merged = """
    SELECT 
        T1.id,
        T1.scenario,
        T1.search_location,
        T1.hotel_name,
        T1.hotel_link,
        T1.stars_clean,
        T1.district,
        T1.address,
        T1.room_class,
        T1.room_type,
        T1.bed_class,
        T1.bed_type,
        T1.rooms,
        T1.final_price,
        T1.original_price,
        T1.discount_percent,
        T1.rating_clean,
        T1.review_count,
        T1.location_clean,
        T1.distance_km,
        T1.free_cancel_bool,
        T1.breakfast_bool,
        T1.badge_clean,
        T1.adults,
        T1.children,
        T1.total_guests,
        T1.check_in,
        T2.area_m2_cleaned,            
        T2.facilities_cleaned          
    FROM hotel_data_cleaned T1
    LEFT JOIN room_details_cleaned T2 ON T1.id = T2.hotel_id
    ORDER BY T1.id ASC
    """
    
    try:
        df_merged = pd.read_sql(query_merged, engine)
        
        if df_merged.empty:
            print("-> Không có dữ liệu để gộp.")
            return

        print(f"-> Đã tải {len(df_merged)} dòng dữ liệu từ DB.")

        # ========================================================
        # XỬ LÝ NULL/NAN -> 0
        # ========================================================
        # 1. Rating: Điền 0 nếu null
        df_merged['rating_clean'] = df_merged['rating_clean'].fillna(0)
        
        # 2. Review Count: Điền 0 nếu null, và ép kiểu về số nguyên (int)
        df_merged['review_count'] = df_merged['review_count'].fillna(0).astype(int)
        # ========================================================

        # --- XỬ LÝ CSV ---
        df_csv = df_merged.copy()
        
        # Đổi tên cột từ snake_case sang Title Case đẹp
        df_csv.rename(columns=COLUMN_MAPPING, inplace=True)
        
        # Sắp xếp cột đúng thứ tự mong muốn
        df_csv = df_csv.reindex(columns=COLS_ORDER_EXPORT)

        csv_merged = f"../{OUTPUT_FOLDER}/full_data_merged.csv"
        df_csv.to_csv(csv_merged, index=False, encoding='utf-8-sig')
        print(f"-> [OK] Đã xuất CSV: {csv_merged}")

    except Exception as e:
        print(f"-> Lỗi khi export CSV: {e}")
        import traceback
        traceback.print_exc()
        return 

    # ---------------------------------------------------------
    # PHẦN 2: XUẤT JSON NESTED (Cấu trúc phân cấp)
    # ---------------------------------------------------------
    print("\n[2/2] Đang tạo cấu trúc JSON (Hotel -> Rooms)...")
    
    try:
        # Nhóm theo khách sạn
        grouped = df_merged.groupby(['hotel_name', 'hotel_link', 'address'])
        result_json = []

        for i, (key, group_data) in enumerate(grouped):
            first_row = group_data.iloc[0]
            
            # Lấy ID dạng chuỗi (HTL_00001)
            hotel_id_raw = first_row.get('id')
            hotel_id_str = f"HTL_{hotel_id_raw:05d}" if pd.notna(hotel_id_raw) else f"HTL_UNKNOWN_{i}"

            hotel_obj = {
                "hotel_id": hotel_id_str,
                "info": {
                    "name": first_row.get('hotel_name'),
                    "link": first_row.get('hotel_link'),
                    "address": first_row.get('address'),
                    "district": first_row.get('district'),
                    "city": first_row.get('search_location'),
                },
                "stats": {
                    "stars": first_row.get('stars_clean'),
                    # Đã xử lý fillna(0) ở trên, nên ở đây an toàn
                    "rating": first_row.get('rating_clean'),
                    "review_count": int(first_row.get('review_count')), # Đảm bảo là int trong JSON
                    "distance_km": first_row.get('distance_km')
                },
                "rooms": [] 
            }

            for j, row in group_data.iterrows():
                # Xử lý tiện ích (lấy từ facilities)
                amenities_final = row.get('facilities_cleaned') if pd.notna(row.get('facilities_cleaned')) else row.get('badge_clean')
                
                # Xử lý hiển thị phần trăm giảm giá
                disc_val = row.get('discount_percent')
                disc_str = f"{disc_val}%" if pd.notna(disc_val) else "0%"

                room_obj = {
                    "room_id": f"{hotel_id_str}_R{j+1}",
                    "details": {
                        "type": row.get('room_type'),
                        "class": row.get('room_class'),
                        "bed": row.get('bed_type'),
                        "area_m2_cleaned": row.get('area_m2_cleaned'),
                        "amenities": amenities_final
                    },
                    "occupancy": {
                        "adults": row.get('adults'),
                        "children": row.get('children'),
                        "total": row.get('total_guests')
                    },
                    "pricing": {
                        "final": int(row.get('final_price')) if pd.notna(row.get('final_price')) else 0,
                        "original": int(row.get('original_price')) if pd.notna(row.get('original_price')) else 0,
                        "discount": disc_str,
                        "free_cancel": bool(row.get('free_cancel_bool')),
                        "breakfast": bool(row.get('breakfast_bool'))
                    }
                }
                hotel_obj["rooms"].append(room_obj)

            result_json.append(hotel_obj)

        json_filename = f"../{OUTPUT_FOLDER}/final_hotel_data.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, ensure_ascii=False, indent=4)
        
        print(f"-> [OK] Đã xuất JSON: {json_filename}")
        print(f"-> Tổng số khách sạn: {len(result_json)}")

    except Exception as e:
        print(f"-> Lỗi khi tạo JSON: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    export_all_data()