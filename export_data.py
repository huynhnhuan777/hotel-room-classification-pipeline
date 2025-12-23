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

# Tạo engine toàn cục
engine = create_engine(DB_CONNECTION_STR)
OUTPUT_FOLDER = "exports"

# --- HÀM 1: XỬ LÝ BẢNG SẠCH (CSV + Nested JSON) ---
def export_cleaned_data(table_name="hotel_data_cleaned"):
    print(f"\n=== ĐANG XỬ LÝ BẢNG: {table_name} ===")
    
    # 1. Đọc dữ liệu
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
        if df.empty:
            print("-> Bảng rỗng, bỏ qua.")
            return
        print(f"-> Đã tải {len(df)} dòng.")
        
        # Tạo folder nếu chưa có
        if not os.path.exists(OUTPUT_FOLDER):
            os.makedirs(OUTPUT_FOLDER)

        # 2. XUẤT CSV (Yêu cầu 1)
        csv_filename = f"{OUTPUT_FOLDER}/{table_name}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"-> [OK] Đã xuất CSV: {csv_filename}")

        # 3. XUẤT JSON 1-N (Yêu cầu 2)
        print("-> Đang xử lý cấu trúc JSON lồng nhau (Hotel -> Rooms)...")
        
        # Các cột để gom nhóm khách sạn
        hotel_cols = ['hotel_name', 'address', 'stars_clean', 'district', 'rating_clean']
        valid_hotel_cols = [c for c in hotel_cols if c in df.columns]
        
        grouped = df.groupby(valid_hotel_cols)
        result_json = []

        for i, (key, group_data) in enumerate(grouped):
            first_row = group_data.iloc[0]
            hotel_id = f"HTL_{i+1:04d}" 

            # Object Cha (Hotel)
            hotel_obj = {
                "hotel_id": hotel_id,
                "hotel_name": first_row.get('hotel_name'),
                "star_rating_score": first_row.get('stars_clean'),
                "address": first_row.get('address'),
                "city": first_row.get('district'),
                "rating_score": first_row.get('rating_clean'),
                "link": None,
                "rooms": [] 
            }

            # Mảng Con (Rooms)
            for j, row in group_data.iterrows():
                room_obj = {
                    "room_id": f"{hotel_id}_R{j+1}",
                    "room_name": row.get('room_type'),
                    "area_m2": None,
                    "bed_type": row.get('bed_type'),
                    "max_occupancy": row.get('total_guests'),
                    "view": None,
                    "amenities": row.get('badge_clean'),
                    "price_per_night": row.get('final_price'),
                    "original_price": row.get('original_price'),
                    "discount_percent": row.get('discount_percent')
                }
                hotel_obj["rooms"].append(room_obj)

            result_json.append(hotel_obj)

        json_filename = f"{OUTPUT_FOLDER}/{table_name}_nested.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, ensure_ascii=False, indent=4)
        
        print(f"-> [OK] Đã xuất JSON: {json_filename}")

    except Exception as e:
        print(f"-> LỖI: {e}")

# --- HÀM 2: XỬ LÝ BẢNG SCENARIOS (Chỉ CSV) ---
def export_scenarios_data(table_name="hotel_scenarios"):
    print(f"\n=== ĐANG XỬ LÝ BẢNG: {table_name} ===")
    
    try:
        # 1. Đọc dữ liệu
        df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
        if df.empty:
            print("-> Bảng rỗng.")
            return
        
        print(f"-> Đã tải {len(df)} dòng.")

        # 2. Xuất CSV
        if not os.path.exists(OUTPUT_FOLDER):
            os.makedirs(OUTPUT_FOLDER)
            
        csv_filename = f"{OUTPUT_FOLDER}/{table_name}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"-> [OK] Đã xuất CSV: {csv_filename}")
        print("-> (Không xuất JSON cho bảng này theo yêu cầu)")

    except Exception as e:
        print(f"-> LỖI: {e}")

# --- CHẠY CHƯƠNG TRÌNH ---
if __name__ == "__main__":
    # 1. Xuất bảng dữ liệu sạch (CSV + JSON)
    export_cleaned_data("hotel_data_cleaned")
    
    # 2. Xuất bảng kịch bản thô (Chỉ CSV)
    export_scenarios_data("hotel_scenarios")
    
    print("\n=> HOÀN TẤT TẤT CẢ TÁC VỤ.")