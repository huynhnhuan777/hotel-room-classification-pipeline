import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder
import joblib
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

def train_hotel_ai_database_centric():
    try:
        engine = create_engine(DB_CONNECTION_STR)
        
        # --- BƯỚC 1: TẢI DỮ LIỆU TỪ CÁC BẢNG DATABASE ---
        print("--- 1. Đang tải dữ liệu từ các bảng Database... ---")
        # Lấy dữ liệu đã qua xử lý (Normalization & Encoding) để huấn luyện
        df_encoded = pd.read_sql("SELECT * FROM encoding_data", engine)
        
        # Lấy dữ liệu gốc (trước khi chuẩn hóa) để có giá trị thực (triệu VNĐ, m2...)
        df_original = pd.read_sql("SELECT * FROM tranform_data", engine)
        
        if df_encoded.empty or df_original.empty:
            print("Lỗi: Không tìm thấy dữ liệu trong các bảng Database.")
            return

        # --- BƯỚC 2: THỐNG KÊ & CHUẨN BỊ ---
        print("\n--- 2. Thống kê phân bổ lớp (room_class): ---")
        print(df_encoded['room_class'].value_counts())

        # Tạo bộ giải mã nhãn để chuyển số (0,1,2...) về lại tên phòng (Standard, Deluxe...)
        le = LabelEncoder()
        le.fit(df_original['room_class'].astype(str))
        label_mapping = dict(zip(range(len(le.classes_)), le.classes_))

        # Tách đặc trưng (X) và nhãn (y)
        target_col = 'room_class'
        X = df_encoded.drop(columns=[target_col])
        y = df_encoded[target_col]

        # --- BƯỚC 3: CHIA DỮ LIỆU (70/15/15) ---
        # Chia 70% Train - 30% Còn lại
        X_train, X_rem, y_train, y_rem = train_test_split(
            X, y, train_size=0.7, random_state=42, stratify=y
        )
        # Chia 30% còn lại thành Validation (15%) và Test (15%)
        X_val, X_test, y_val, y_test = train_test_split(
            X_rem, y_rem, test_size=0.5, random_state=42, stratify=y_rem
        )

        # --- BƯỚC 4: HUẤN LUYỆN & LƯU MÔ HÌNH ---
        print("\n--- 3. Đang huấn luyện mô hình Random Forest... ---")
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Lưu file mô hình .pkl
        joblib.dump(model, "hotel_ai_model.pkl")

        # --- BƯỚC 5: ĐÁNH GIÁ MÔ HÌNH ---
        test_preds = model.predict(X_test)
        print(f"\nĐộ chính xác trên tập Test: {accuracy_score(y_test, test_preds) * 100:.2f}%")
        print("\nBáo cáo chi tiết (Classification Report):")
        print(classification_report(y_test, test_preds))

        # --- BƯỚC 6: LIÊN KẾT KẾT QUẢ VÀ LƯU NGƯỢC LẠI DATABASE ---
        print("\n--- 4. Đang lưu kết quả dự đoán tập Test vào Database... ---")
        
        # Lấy dữ liệu nguyên bản tương ứng với tập Test (sử dụng Index)
        test_results = df_original.iloc[X_test.index].copy()
        
        # Gắn kết quả dự đoán vào bảng
        test_results['ai_prediction_id'] = test_preds
        test_results['ai_prediction_name'] = pd.Series(test_preds, index=X_test.index).map(label_mapping)
        test_results['is_correct'] = (test_results['room_class'] == test_results['ai_prediction_name']).astype(int)

        # Ghi kết quả vào bảng mới 'test_evaluation_results' trong Database
        test_results.to_sql('test_evaluation_results', engine, if_exists='replace', index=False)
        
        # Đồng thời xuất file CSV để dự phòng
        output_dir = "../data"
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        test_results.to_csv(f"{output_dir}/final_ai_report.csv", index=False, encoding='utf-8-sig')

        print(f"--- THÀNH CÔNG ---")
        print("- Mô hình đã lưu: hotel_ai_model.pkl")
        print("- Kết quả đã lưu vào bảng DB: 'test_evaluation_results'")
        print("- Kết quả đã xuất file: final_ai_report.csv")

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    train_hotel_ai_database_centric()