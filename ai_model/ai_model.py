import pandas as pd
import numpy as np
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

# --- HÀM MỚI: PHÂN TÍCH ĐẶC ĐIỂM TỪNG LOẠI PHÒNG ---
def print_room_insights(df_original):
    """
    Hàm này thống kê và in ra luật (Rule) cho từng loại phòng
    Dựa trên Giá (khoảng phổ biến) và Tiện ích (xuất hiện nhiều).
    """
    print("\n" + "="*60)
    print("=== TỔNG HỢP KIẾN THỨC: ĐẶC ĐIỂM NHẬN DẠNG TỪNG LOẠI PHÒNG ===")
    print("="*60)

    # Lấy danh sách các loại phòng
    room_classes = df_original['room_class'].unique()
    
    # Xác định các cột tiện ích (bắt đầu bằng 'has_' hoặc 'is_')
    facility_cols = [col for col in df_original.columns if col.startswith('has_') or col.startswith('is_')]

    for r_class in sorted(room_classes):
        # Lấy dữ liệu của riêng loại phòng này
        subset = df_original[df_original['room_class'] == r_class]
        
        if subset.empty: continue

        # 1. Thống kê GIÁ (Dùng phân vị 10% - 90% để loại bỏ giá ảo/nhiễu)
        price_min = subset['Final Price'].quantile(0.1)
        price_max = subset['Final Price'].quantile(0.9)
        avg_price = subset['Final Price'].mean()
        
        # 2. Thống kê DIỆN TÍCH
        area_min = subset['Area_m2'].quantile(0.1)
        area_max = subset['Area_m2'].quantile(0.9)

        # 3. Thống kê TIỆN ÍCH PHỔ BIẾN (Xuất hiện trên 70% số phòng loại này)
        common_facilities = []
        for col in facility_cols:
            # Tính tỷ lệ xuất hiện (Mean của cột 0/1 chính là tỷ lệ %)
            if subset[col].mean() >= 0.7: 
                # Làm đẹp tên tiện ích (bỏ tiền tố, viết hoa)
                clean_name = col.replace('has_', '').replace('is_', '').replace('_', ' ').capitalize()
                common_facilities.append(clean_name)
        
        # IN RA MÀN HÌNH
        print(f"\n  LOẠI PHÒNG: {r_class.upper()}")
        print(f"   ------------------------------------------------")
        print(f"    Khoảng giá phổ biến: {price_min:,.0f} - {price_max:,.0f} VNĐ (TB: {avg_price:,.0f})")
        print(f"    Diện tích phổ biến:  {area_min:.1f}m² - {area_max:.1f}m²")
        
        if common_facilities:
            print(f"   Tiện ích đặc trưng:  {', '.join(common_facilities)}")
        else:
            print(f"   Tiện ích đặc trưng:  Không có tiện ích nào quá nổi bật (>70%)")

def train_hotel_ai_database_centric():
    try:
        engine = create_engine(DB_CONNECTION_STR)
        
        # --- BƯỚC 1: TẢI DỮ LIỆU ---
        print("--- 1. Đang tải dữ liệu từ các bảng Database... ---")
        df_encoded = pd.read_sql("SELECT * FROM encoding_data", engine)
        df_original = pd.read_sql("SELECT * FROM tranform_data", engine)
        
        if df_encoded.empty or df_original.empty:
            print("Lỗi: Không tìm thấy dữ liệu.")
            return

        # --- BƯỚC 2: CHUẨN BỊ DỮ LIỆU ---
        print(f"\n--- 2. Tổng số dữ liệu: {len(df_encoded)} dòng ---")

        le = LabelEncoder()
        le.fit(df_original['room_class'].astype(str))
        label_mapping = dict(zip(range(len(le.classes_)), le.classes_))

        target_col = 'room_class'
        X = df_encoded.drop(columns=[target_col])
        y = df_encoded[target_col]

        # --- BƯỚC 3: CHIA DỮ LIỆU ---
        X_train, X_rem, y_train, y_rem = train_test_split(X, y, train_size=0.7, random_state=42, stratify=y)
        X_val, X_test, y_val, y_test = train_test_split(X_rem, y_rem, test_size=0.5, random_state=42, stratify=y_rem)
        
        # --- BƯỚC 4: HUẤN LUYỆN & TUNING ---
        print("\n--- 3. Bắt đầu huấn luyện và tìm tham số tối ưu... ---")
        
        n_estimators_options = [50, 100, 200]
        best_score = 0
        best_model = None
        best_n = 0

        for n in n_estimators_options:
            model = RandomForestClassifier(n_estimators=n, random_state=42)
            model.fit(X_train, y_train)
            val_score = model.score(X_val, y_val)
            print(f"   > Thử với {n} cây: Val Acc = {val_score * 100:.2f}%")
            if val_score > best_score:
                best_score = val_score
                best_model = model
                best_n = n

        print(f"\n-> Chọn model tốt nhất: {best_n} cây")
        joblib.dump(best_model, "hotel_ai_model.pkl")

        # --- BƯỚC 5: ĐÁNH GIÁ ---
        print("\n--- 4. Đánh giá trên tập Test ---")
        test_preds = best_model.predict(X_test)
        print(f"Độ chính xác Test: {accuracy_score(y_test, test_preds) * 100:.2f}%")
        
        # --- BƯỚC 6: LƯU KẾT QUẢ ---
        print("\n--- 5. Lưu kết quả... ---")
        test_results = df_original.iloc[X_test.index].copy()
        test_results['ai_prediction_name'] = pd.Series(test_preds, index=X_test.index).map(label_mapping)
        test_results['is_correct'] = (test_results['room_class'] == test_results['ai_prediction_name']).astype(int)
        
        test_results.to_sql('test_evaluation_results', engine, if_exists='replace', index=False)
        
        output_dir = "../data"
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        test_results.to_csv(f"{output_dir}/final_ai_report.csv", index=False, encoding='utf-8-sig')

        # --- BƯỚC 7: IN RA LUẬT/INSIGHT ---
        print_room_insights(df_original)

        print(f"\n--- THÀNH CÔNG ---")

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    train_hotel_ai_database_centric()