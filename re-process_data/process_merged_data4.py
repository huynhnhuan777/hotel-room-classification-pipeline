import pandas as pd
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

# Danh sách các bảng cần lọc dữ liệu
TABLE_NAMES = ["clean_booking", "clean_ivivu", "clean_mytour"]

def filter_and_update_db():
    engine = create_engine(DB_CONNECTION_STR)
    
    for table_name in TABLE_NAMES:
        print(f"\n{'='*20} ĐANG LỌC BẢNG: {table_name} {'='*20}")
        
        # 1. Đọc dữ liệu từ SQL
        try:
            df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
            if df.empty:
                print(f"Bảng {table_name} trống. Bỏ qua.")
                continue
        except Exception as e:
            print(f"Lỗi khi đọc bảng {table_name}: {e}")
            continue

        # 2. Xử lý chuẩn hóa cột diện tích (Đảm bảo tên cột khớp với Area_m2)
        # Nếu bảng có tên cột là 'area_m2' thì đổi về 'Area_m2' để đồng nhất
        if 'area_m2' in df.columns:
            df = df.rename(columns={'area_m2': 'Area_m2'})
        
        df['Area_m2'] = pd.to_numeric(df['Area_m2'], errors='coerce')

        # 3. Định nghĩa các điều kiện loại bỏ
        # - Điều kiện 1: Location là 'Unknown'
        cond_unknown_loc = (df['location'] == 'Unknown') | (df['location'].isna())
        
        # - Điều kiện 2: Diện tích > 120m2 (loại bỏ các căn quá lớn/không phù hợp)
        cond_large_area = df['Area_m2'] > 120

        # 4. Tách dữ liệu
        df_removed = df[cond_unknown_loc | cond_large_area]
        df_clean = df[~(cond_unknown_loc | cond_large_area)]

        # 5. Thống kê
        print(f"Tổng số dòng ban đầu: {len(df)}")
        print(f"Số dòng bị loại bỏ:   {len(df_removed)}")
        print(f"  - Do Unknown Location: {cond_unknown_loc.sum()}")
        print(f"  - Do Diện tích > 120m2: {cond_large_area.sum()}")
        print(f"Số dòng giữ lại:      {len(df_clean)}")

        # 6. Cập nhật lại vào Database (Lưu đè - replace)
        if not df_clean.empty:
            try:
                df_clean.to_sql(table_name, engine, if_exists='replace', index=False)
                print(f"Đã cập nhật dữ liệu sạch vào bảng: {table_name}")
            except Exception as e:
                print(f"Lỗi khi lưu vào SQL: {e}")
        else:
            print(f"Cảnh báo: Bảng {table_name} không còn dữ liệu sau khi lọc! (Không ghi đè)")

        # 7. Lưu dự phòng các dòng bị loại ra CSV (Tùy chọn)
        if not df_removed.empty:
            removed_filename = f"../data/removed_{table_name}.csv"
            df_removed.to_csv(removed_filename, index=False, encoding='utf-8-sig')
            print(f"Đã lưu các dòng bị loại của {table_name} vào: {removed_filename}")

    print("\n" + "="*50)
    print("HOÀN THÀNH QUY TRÌNH LỌC DỮ LIỆU TRÊN SQL.")

if __name__ == "__main__":
    filter_and_update_db()