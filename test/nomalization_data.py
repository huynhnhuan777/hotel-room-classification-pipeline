import pandas as pd
from sqlalchemy import create_engine
from sklearn.preprocessing import MinMaxScaler
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

# --- 2. HÀM CHUẨN HÓA (MIN-MAX SCALING) ---
def normalize_data(df):
    """
    Đưa các giá trị về khoảng [0, 1] để các mô hình ML không bị lệch 
    do sự khác biệt về đơn vị (ví dụ: Giá tiền hàng triệu vs Số người là hàng đơn vị).
    """
    df_norm = df.copy()
    
    # Xác định các cột số (Numeric) cần chuẩn hóa
    # Chúng ta loại bỏ các cột nhị phân (0/1) vì chúng đã nằm trong khoảng [0, 1]
    numeric_cols = [
        'Final Price', 'Max People', 'Area_m2', 
        'price_per_m2', 'm2_per_person', 'num_facilities'
    ]
    
    # Kiểm tra xem các cột này có tồn tại trong dữ liệu thực tế không
    cols_to_scale = [c for c in numeric_cols if c in df_norm.columns]
    
    if not cols_to_scale:
        print("Cảnh báo: Không tìm thấy cột số nào để chuẩn hóa.")
        return df_norm

    # Sử dụng MinMaxScaler
    scaler = MinMaxScaler()
    df_norm[cols_to_scale] = scaler.fit_transform(df_norm[cols_to_scale])
    
    return df_norm

# --- 3. QUY TRÌNH THỰC THI ---
def main():
    try:
        # Khởi tạo kết nối
        engine = create_engine(DB_CONNECTION_STR)
        print("--- Đang kết nối Database... ---")

        # A. Đọc dữ liệu từ bảng tranform_data (kết quả của bước trước)
        query = "SELECT * FROM tranform_data"
        df_transformed = pd.read_sql(query, engine)
        
        if df_transformed.empty:
            print("Lỗi: Bảng 'tranform_data' trống hoặc không tồn tại.")
            return

        print(f"Đã lấy {len(df_transformed)} dòng dữ liệu từ bảng 'tranform_data'.")

        # B. Thực hiện chuẩn hóa
        print("--- Đang chuẩn hóa dữ liệu (Normalization)... ---")
        df_normalized = normalize_data(df_transformed)

        # C. Lưu vào bảng normalized_data trong Database
        print("--- Đang lưu dữ liệu vào bảng 'normalized_data'... ---")
        df_normalized.to_sql('normalized_data_test', engine, if_exists='replace', index=False)
        print("Lưu vào Database thành công!")

        # D. Xuất ra file CSV riêng
        output_dir = "../data"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        csv_filename = f"{output_dir}/hotel_data_normalized.csv"
        df_normalized.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"Đã xuất file CSV chuẩn hóa thành công: {csv_filename}")

    except Exception as e:
        print(f"Đã xảy ra lỗi trong quá trình chuẩn hóa: {e}")

    finally:
        print("--- Hoàn tất quy trình chuẩn hóa ---")

if __name__ == "__main__":
    main()