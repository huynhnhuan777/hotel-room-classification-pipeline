import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report

# --- 1. CẤU HÌNH DATABASE (Giống code cũ) ---
DB_CONFIG = {
    "dbname": "booking_data",
    "user": "postgres",
    "password": "123456",
    "host": "localhost",
    "port": "5432"
}
DB_CONNECTION_STR = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

def analyze_ai_results():
    try:
        # Kết nối DB
        engine = create_engine(DB_CONNECTION_STR)
        print("--- 1. Đang tải kết quả dự đoán từ bảng 'test_evaluation_results'... ---")
        
        # Đọc dữ liệu kết quả
        df_results = pd.read_sql("SELECT * FROM test_evaluation_results", engine)
        
        if df_results.empty:
            print("Lỗi: Bảng kết quả trống!")
            return

        # --- 2. THỐNG KÊ TỔNG QUAN ---
        total = len(df_results)
        correct = df_results['is_correct'].sum()
        accuracy = (correct / total) * 100
        
        print(f"\n=== TỔNG QUAN ===")
        print(f"- Tổng số mẫu kiểm tra: {total}")
        print(f"- Số mẫu đúng: {correct}")
        print(f"- Số mẫu sai: {total - correct}")
        print(f"- Độ chính xác tổng thể: {accuracy:.2f}%")

        # --- 3. CHI TIẾT THEO TỪNG LOẠI PHÒNG ---
        print(f"\n=== HIỆU SUẤT THEO TỪNG LOẠI PHÒNG (ROOM CLASS) ===")
        # Group by loại phòng thực tế và tính tỷ lệ đúng
        class_perf = df_results.groupby('room_class')['is_correct'].mean().mul(100).sort_values(ascending=False)
        print(class_perf)

        # Hiển thị báo cáo chi tiết (Precision, Recall, F1)
        print("\n=== CLASSIFICATION REPORT ===")
        print(classification_report(df_results['room_class'], df_results['ai_prediction_name']))

        # --- 4. TRỰC QUAN HÓA MA TRẬN NHẦM LẪN (CONFUSION MATRIX) ---
        # Giúp xem model đang nhầm loại nào sang loại nào
        plt.figure(figsize=(10, 8))
        unique_classes = sorted(df_results['room_class'].unique())
        cm = confusion_matrix(df_results['room_class'], df_results['ai_prediction_name'], labels=unique_classes)
        
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=unique_classes, yticklabels=unique_classes)
        plt.xlabel('AI Dự đoán (Predicted)')
        plt.ylabel('Thực tế (Actual)')
        plt.title('Ma trận nhầm lẫn (Confusion Matrix)')
        plt.show()

        # --- 5. PHÂN TÍCH NGUYÊN NHÂN SAI (ERROR ANALYSIS) ---
        print("\n=== PHÂN TÍCH CÁC TRƯỜNG HỢP SAI ===")
        df_wrong = df_results[df_results['is_correct'] == 0]
        
        if not df_wrong.empty:
            print(f"Tìm thấy {len(df_wrong)} trường hợp sai. Dưới đây là 5 mẫu:")
            # Chọn các cột quan trọng để hiển thị
            cols_view = ['Final Price', 'Area_m2', 'num_facili', 'room_class', 'ai_prediction_name']
            # Đảm bảo tên cột khớp với dữ liệu của bạn (trong ảnh là 'Final Price' có space)
            existing_cols = [c for c in cols_view if c in df_wrong.columns]
            print(df_wrong[existing_cols].head(5))
            
        else:
            print("Tuyệt vời! Không có trường hợp nào sai trong tập test này.")

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    analyze_ai_results()