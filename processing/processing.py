import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.utils import resample

def process_hotel_data(input_file, output_file):
    # 1. Đọc dữ liệu
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {input_file}")
        return

    # Danh sách các cột đặc trưng (features) dùng để phân cụm
    features = [
        'Final Price', 'Max Peopl', 'Area_m2', 'price_per_', 'm2_per_p', 
        'num_facili', 'has_luxury', 'is_king', 'is_queen', 'is_double', 
        'is_single', 'is_bunk', 'is_sofa', 'has_wifi', 'has_ac', 
        'has_break', 'has_tv', 'has_pool', 'has_balco', 'has_parkir', 
        'has_kitche', 'has_fridge'
    ]

    available_features = [col for col in features if col in df.columns]

    # 2. Quy tắc tính điểm để định hướng thứ hạng (Weighted Scoring)
    weights = {
        'Final Price': 3.0,    
        'Area_m2': 2.0,        
        'has_luxury': 2.0,     
        'is_king': 1.5,        
        'has_pool': 1.5,
        'num_facili': 1.0
    }

    df['Temp_Score'] = 0
    for col in available_features:
        weight = weights.get(col, 0.5)
        df['Temp_Score'] += df[col] * weight

    # 3. Chạy K-Means Clustering (K=6)
    kmeans = KMeans(n_clusters=6, init='k-means++', random_state=42, n_init=10)
    df['Cluster_ID'] = kmeans.fit_predict(df[available_features])

    # 4. Ánh xạ nhãn chuẩn: Standard(3), Superior(5), Deluxe(0), Executive(1), Suite(4), Luxury(2)
    ordered_labels = [3, 5, 0, 1, 4, 2]
    avg_scores = df.groupby('Cluster_ID')['Temp_Score'].mean().sort_values().index
    mapping = {avg_scores[i]: ordered_labels[i] for i in range(6)}
    
    df['room_class_relabelled'] = df['Cluster_ID'].map(mapping)

    # 5. Thống kê số nhãn trùng giữa 'room_class' (gốc) và 'room_class_relabelled' (mới)
    if 'room_class' in df.columns:
        matches = (df['room_class'] == df['room_class_relabelled']).sum()
        print(f"--- THỐNG KÊ ĐỘ KHỚP ---")
        print(f"Số lượng nhãn trùng khớp: {matches}/{len(df)}")
        print(f"Tỷ lệ tương đồng: {(matches/len(df))*100:.2f}%")

    # 6. Undersampling để cân bằng số lượng giữa các hạng phòng
    print(f"\n--- THỰC HIỆN UNDERSAMPLING ---")
    min_samples = df['room_class_relabelled'].value_counts().min()
    print(f"Mục tiêu cân bằng: {min_samples} mẫu mỗi hạng phòng.")

    list_balanced = []
    for label in ordered_labels:
        df_group = df[df['room_class_relabelled'] == label]
        df_resampled = resample(
            df_group, 
            replace=False, 
            n_samples=min_samples, 
            random_state=42
        )
        list_balanced.append(df_resampled)

    df_final = pd.concat(list_balanced)

    # 7. Lưu file và dọn dẹp cột phụ
    cols_to_drop = ['Temp_Score', 'Cluster_ID']
    df_save = df_final.drop(columns=[c for c in cols_to_drop if c in df_final.columns])
    
    df_save.to_csv(output_file, index=False)
    
    print(f"\nHoàn tất! File đã lưu tại: {output_file}")
    print("Thống kê sau khi cân bằng:")
    print(df_save['room_class_relabelled'].value_counts().sort_index())

# --- Chạy chương trình ---
input_path = '../data/hotel_data_final.csv' 
output_path = '../data/hotel_data_balanced.csv'

process_hotel_data(input_path, output_path)