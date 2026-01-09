import pandas as pd
from sqlalchemy import create_engine
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

def export_cleaned_data():
    print("=== XUẤT DỮ LIỆU ĐÃ XỬ LÝ RA CSV ===")
    
    # Tên bảng cần xuất (bảng kết quả sau khi clean)
    table_name = "merged_data_cleaned"
    output_file = "merged_data_cleaned_test.csv"
    
    try:
        print(f"1. Đang đọc dữ liệu từ bảng '{table_name}'...")
        
        # Đọc toàn bộ bảng
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, engine)
        
        if df.empty:
            print("-> CẢNH BÁO: Bảng rỗng, không có dữ liệu để xuất.")
            return

        print(f"-> Đã tải {len(df)} dòng dữ liệu.")
        
        # Xuất ra CSV
        print(f"2. Đang ghi ra file '{output_file}'...")
        # encoding='utf-8-sig' để mở trên Excel không lỗi font tiếng Việt
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"-> [THÀNH CÔNG] File đã được lưu tại: {os.path.abspath(output_file)}")
        
    except Exception as e:
        print(f"-> [LỖI]: {e}")

if __name__ == "__main__":
    export_cleaned_data()