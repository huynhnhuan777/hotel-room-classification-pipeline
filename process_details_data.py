import pandas as pd
from sqlalchemy import create_engine
import re

# --- 1. CẤU HÌNH KẾT NỐI DATABASE ---
DB_CONFIG = {
    "dbname": "booking_data",
    "user": "postgres",
    "password": "123456",
    "host": "localhost",
    "port": "5432"
}
DB_CONNECTION_STR = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

# --- 2. CÁC HÀM XỬ LÝ (CLEANING FUNCTIONS) ---

def clean_area(value):
    """
    Chuyển đổi '25 m²', '25m2' -> 25.0 (Float)
    Nếu là 'N/A' hoặc lỗi -> None
    """
    if not value or pd.isna(value) or str(value).strip() == "N/A":
        return None
    
    # Dùng Regex tìm số đầu tiên trong chuỗi (ví dụ: "Khoảng 20 m2" -> lấy 20)
    match = re.search(r"(\d+(\.\d+)?)", str(value))
    if match:
        return float(match.group(1))
    return None

def clean_facilities(value):
    """
    - Chuyển về chữ thường (lowercase)
    - Loại bỏ khoảng trắng thừa
    - Loại bỏ 'N/A'
    - Sắp xếp lại cho gọn
    """
    if not value or pd.isna(value) or str(value).strip() == "N/A":
        return None # Hoặc trả về "" tùy nhu cầu
    
    # Tách chuỗi bằng dấu phẩy
    items = str(value).split(',')
    
    # Làm sạch từng tiện ích: xóa khoảng trắng 2 đầu, chuyển thường
    cleaned_items = [item.strip().lower() for item in items if item.strip()]

    # Nối lại thành chuỗi chuẩn
    return ", ".join(cleaned_items)

def main():
    # Kết nối DB
    engine = create_engine(DB_CONNECTION_STR)
    print("-> Đang kết nối Database và tải dữ liệu thô...")

    # --- 3. ĐỌC DỮ LIỆU TỪ BẢNG CŨ ---
    query = "SELECT * FROM room_details"
    df = pd.read_sql(query, engine)
    
    print(f"-> Đã tải {len(df)} dòng dữ liệu. Bắt đầu làm sạch...")

    # --- 4. ÁP DỤNG CLEANING ---
    
    # a. Xử lý cột Area (Diện tích)
    # Tạo cột mới 'area_number' dạng số để tính toán được
    df['area_m2_cleaned'] = df['area_m2'].apply(clean_area)

    # b. Xử lý cột Facilities (Tiện ích)
    df['facilities_cleaned'] = df['facilities'].apply(clean_facilities)

    # c. Xử lý thời gian (Đảm bảo định dạng datetime)
    df['updated_at'] = pd.to_datetime(df['updated_at'])

    # d. Thống kê sơ bộ
    print("\n--- THỐNG KÊ SAU KHI CLEAN ---")
    print(f"- Số lượng khách sạn có diện tích hợp lệ: {df['area_m2_cleaned'].notna().sum()}")
    print(f"- Diện tích trung bình: {df['area_m2_cleaned'].mean():.2f} m2")
    
    # Hiển thị mẫu 5 dòng
    print("\n--- MẪU DỮ LIỆU ---")
    print(df[['hotel_id', 'area_m2', 'area_m2_cleaned', 'facilities_cleaned']].head())

    # --- 5. LƯU VÀO BẢNG MỚI ---
    target_table = "room_details_cleaned"
    print(f"\n-> Đang lưu dữ liệu sạch vào bảng '{target_table}'...")
    
    try:
        df.to_sql(target_table, engine, if_exists='replace', index=False)
        
        # Đặt khóa chính cho bảng mới (PostgreSQL mặc định to_sql không tạo PK)
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {target_table} ADD PRIMARY KEY (hotel_id);"))
            
        print("-> [THÀNH CÔNG] Dữ liệu đã được làm sạch và lưu.")
        
    except Exception as e:
        print(f"-> [LỖI] Không thể lưu vào Database: {e}")

from sqlalchemy import text # Import thêm text để chạy lệnh ALTER TABLE

if __name__ == "__main__":
    main()