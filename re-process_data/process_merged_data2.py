import pandas as pd
import numpy as np
import re
from sqlalchemy import create_engine
import warnings

warnings.filterwarnings('ignore')

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

TABLE_NAMES = ["clean_booking", "clean_ivivu", "clean_mytour"]

# --- 2. CÁC HÀM LÀM SẠCH ---
def clean_price(value):
    if pd.isna(value) or value == '': return None
    try:
        if isinstance(value, (int, float, np.number)): return int(value)
        price = int(re.sub(r'[^\d]', '', str(value)))
        return price if price > 0 else None
    except: return None

def clean_area(value):
    if pd.isna(value) or value == '': return None
    try:
        if isinstance(value, (int, float, np.number)): return float(value)
        val_str = str(value).lower().replace('m2', '').replace('m²', '').replace(',', '.').strip()
        match = re.search(r"(\d+(\.\d+)?)", val_str)
        return float(match.group(1)) if match else None
    except: return None

def clean_people(value):
    if pd.isna(value) or value == '': return None
    try:
        if isinstance(value, (int, float, np.number)): return int(value)
        match = re.search(r"(\d+)", str(value))
        return int(match.group(1)) if match else None
    except: return None

# --- 3. LOGIC XỬ LÝ BẢO TOÀN CỘT ---
def process_database_tables():
    for table_name in TABLE_NAMES:
        print(f"\n{'='*20} XỬ LÝ BẢNG: {table_name.upper()} {'='*20}")
        
        try:
            # 1. Đọc toàn bộ dữ liệu
            df = pd.read_sql(f"SELECT * FROM {table_name}", engine) 
            original_columns = df.columns.tolist()
            print(f" -> Đã load {len(df)} dòng với các cột: {original_columns}")

            # 2. Xác định các cột cần làm sạch (mapping linh hoạt)
            col_price = next((c for c in df.columns if c.lower() in ['final_price', 'price', 'final price']), None)
            col_area = next((c for c in df.columns if c.lower() in ['area_m2', 'area', 'area_m2']), None)
            col_people = next((c for c in df.columns if c.lower() in ['max_people', 'max people', 'people', 'total_guests']), None)
            
            # Cột phục vụ lọc trùng
            col_hotel = next((c for c in df.columns if c.lower() in ['hotel_name', 'hotel name', 'hotel']), None)
            col_room = next((c for c in df.columns if c.lower() in ['room_class']), None)

            # 3. Ghi đè dữ liệu đã làm sạch vào các cột tương ứng
            if col_price: 
                df[col_price] = df[col_price].apply(clean_price)
            if col_area: 
                df[col_area] = df[col_area].apply(clean_area)
            if col_people: 
                df[col_people] = df[col_people].apply(clean_people)

            # 4. Loại bỏ giá trị Null dựa trên các cột trọng yếu (dropna)
            critical_cols = [c for c in [col_price, col_area, col_people] if c is not None]
            before_null = len(df)
            df = df.dropna(subset=critical_cols, how='any')
            print(f" -> Loại bỏ dòng thiếu dữ liệu số: {before_null} -> {len(df)}")

            # 5. Lọc trùng (drop_duplicates)
            subset_dedup = [c for c in [col_hotel, col_room, col_price, col_area, col_people] if c is not None]
            before_dedup = len(df)
            df = df.drop_duplicates(subset=subset_dedup, keep='first')
            print(f" -> Lọc trùng (giữ cột gốc): {before_dedup} -> {len(df)}")

            # 6. Lưu lại vào Database
            df.to_sql(f"{table_name}", engine, if_exists='replace', index=False)
            print(f" -> [THÀNH CÔNG] Đã cập nhật bảng {table_name}")

        except Exception as e:
            print(f" -> [LỖI]: {e}")

if __name__ == "__main__":
    process_database_tables()