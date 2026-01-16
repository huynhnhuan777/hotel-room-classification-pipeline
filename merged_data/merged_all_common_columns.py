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

def main():
    print("-> ĐỌC DB, GỘP DỮ LIỆU & XUẤT FILE...")
    
    # 1. Tạo kết nối (Engine)
    conn_str = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    engine = create_engine(conn_str)
    
    try:
        # 2. Đọc các bảng từ Database
        print("-> Đang tải dữ liệu từ Database...")
        df1 = pd.read_sql_table("clean_booking_balanced", engine)
        df2 = pd.read_sql_table("clean_ivivu_balanced", engine)
        df3 = pd.read_sql_table("clean_mytour_balanced", engine)

        # 3. Gộp các DataFrame
        df_final = pd.concat([df1, df2, df3], axis=0, ignore_index=True)

        # 4. Lưu vào Database
        df_final.to_sql('merged_data', engine, if_exists='replace', index=False)
        print("-> [1/2] Đã lưu vào bảng 'merged_data' trong Database.")

        # 5. Xuất ra file CSV
        csv_filename = "../data/merged_hotel_data.csv"
        # encoding='utf-8-sig' giúp hiển thị đúng tiếng Việt khi mở bằng Excel
        df_final.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        print("-" * 30)
        print(f"-> [2/2] [THÀNH CÔNG] Đã xuất file: {os.path.abspath(csv_filename)}")
        print(f"-> Tổng cộng: {len(df_final)} dòng dữ liệu.")
        
    except ValueError as e:
        print(f"Lỗi: Kiểm tra lại tên bảng trong DB. {e}")
    except Exception as e:
        print(f"Lỗi phát sinh: {e}")

if __name__ == "__main__":
    main()