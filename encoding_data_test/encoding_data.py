import pandas as pd
from sqlalchemy import create_engine
from sklearn.preprocessing import LabelEncoder

# --- 1. CẤU HÌNH DATABASE ---
DB_CONFIG = {
    "dbname": "booking_data",
    "user": "postgres",
    "password": "123456",
    "host": "localhost",
    "port": "5432"
}
DB_CONNECTION_STR = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

def encode_room_class(df):
    df_encoded = df.copy()
    target_col = 'room_class'
    
    if target_col in df_encoded.columns:
        # --- BƯỚC BỔ SUNG: IN SỐ LƯỢNG TRƯỚC KHI ENCODING ---
        print("\n--- THỐNG KÊ SỐ LƯỢNG MẪU TRƯỚC KHI MÃ HÓA ---")
        class_counts = df_encoded[target_col].value_counts()
        print(class_counts)
        print(f"Tổng cộng: {class_counts.sum()} dòng.")
        print("-" * 45)

        print(f"--- Đang mã hóa cột: {target_col} ---")
        le = LabelEncoder()
        
        # Chuyển đổi chữ thành số
        df_encoded[target_col] = le.fit_transform(df_encoded[target_col].astype(str))
        
        # Hiển thị bảng tra cứu nhãn
        mapping = dict(zip(le.classes_, le.transform(le.classes_)))
        print(f"Bảng tra cứu nhãn: {mapping}")
    else:
        print("Không tìm thấy cột room_class để mã hóa!")
        
    return df_encoded

# --- 2. THỰC THI ---
try:
    engine = create_engine(DB_CONNECTION_STR)
    
    # Đọc dữ liệu từ bảng đã chuẩn hóa (normalized_data)
    df = pd.read_sql("SELECT * FROM normalized_data", engine)

    if df.empty:
        print("Cảnh báo: Bảng 'normalized_data' không có dữ liệu!")
    else:
        # Thực hiện encoding
        df_final = encode_room_class(df)

        # Lưu vào database bảng encoding_data
        df_final.to_sql('encoding_data', engine, if_exists='replace', index=False)

        # Xuất ra CSV để kiểm tra
        output_path = "../data/hotel_data_final.csv"
        df_final.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print("\n--- HOÀN TẤT ---")
        print(f"Dữ liệu đã được lưu và xuất ra file: {output_path}")

except Exception as e:
    print(f"Lỗi: {e}")