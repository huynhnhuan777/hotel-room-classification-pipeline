import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata
from sdv.sampling import Condition
import warnings

# Tắt cảnh báo
warnings.filterwarnings('ignore')
sns.set(style="whitegrid")
plt.rcParams['figure.figsize'] = (14, 7)

def remove_outliers_strict(df, col_to_clean, group_col=None, method='iqr', strictness='high'):
    """
    Hàm lọc outlier đa chiến thuật.
    - method='iqr': Dùng IQR. strictness càng cao -> khoảng chấp nhận càng hẹp.
    - method='percentile': Cắt cứng theo % (ví dụ 5% đầu và 5% cuối).
    """
    df_out = df.copy()
    
    # Cấu hình độ gắt
    if method == 'iqr':
        multiplier = 3 if strictness == 'high' else 5
    elif method == 'percentile':
        # Cắt bỏ 5% thấp nhất và 5% cao nhất (giữ lại 5-95)
        lower_p, upper_p = (0.05, 0.95) if strictness == 'high' else (0.01, 0.99)

    if group_col:
        cleaned_groups = []
        for group_name in df_out[group_col].unique():
            group_data = df_out[df_out[group_col] == group_name]
            
            # Nếu ít dữ liệu quá (<5 dòng) thì không lọc
            if len(group_data) < 5:
                cleaned_groups.append(group_data)
                continue
            
            if method == 'iqr':
                Q1 = group_data[col_to_clean].quantile(0.25)
                Q3 = group_data[col_to_clean].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - multiplier * IQR
                upper_bound = Q3 + multiplier * IQR
            else: # method == 'percentile'
                lower_bound = group_data[col_to_clean].quantile(lower_p)
                upper_bound = group_data[col_to_clean].quantile(upper_p)
            
            # Lọc và đảm bảo không lấy giá trị âm cho Giá/Diện tích
            filtered_data = group_data[
                (group_data[col_to_clean] >= max(0, lower_bound)) & 
                (group_data[col_to_clean] <= upper_bound)
            ]
            cleaned_groups.append(filtered_data)
        
        return pd.concat(cleaned_groups).reset_index(drop=True)
    
    else:
        # Xử lý trên toàn bộ cột (Không theo nhóm)
        if method == 'iqr':
            Q1 = df_out[col_to_clean].quantile(0.25)
            Q3 = df_out[col_to_clean].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - multiplier * IQR
            upper_bound = Q3 + multiplier * IQR
        else:
            lower_bound = df_out[col_to_clean].quantile(lower_p)
            upper_bound = df_out[col_to_clean].quantile(upper_p)
            
        return df_out[
            (df_out[col_to_clean] >= max(0, lower_bound)) & 
            (df_out[col_to_clean] <= upper_bound)
        ].reset_index(drop=True)
    
# =========================================
# 2. TẢI VÀ LÀM SẠCH DỮ LIỆU
# =========================================
try:
    df = pd.read_csv('../data/merged_data_cleaned_updated1.csv')
    original_cols = df.columns.tolist()
except FileNotFoundError:
    print("Lỗi: Không tìm thấy file.")
    exit()

# Xử lý thiếu
for col in ['final_price', 'area_m2', 'max_people']:
    if col in df.columns: df[col] = df[col].fillna(df[col].median())
df['room_class'] = df['room_class'].fillna('Unknown')

print("1. Đang làm sạch outlier...")
df_clean = remove_outliers_strict(df, 'area_m2')
df_clean = remove_outliers_strict(df_clean, 'final_price', group_col='room_class')

# =========================================
# 3. TÍNH TOÁN TARGET COUNT
# =========================================
class_counts = df_clean['room_class'].value_counts()
print("\n--- Số lượng mẫu thực tế ban đầu ---")
print(class_counts)

# CHỌN MỐC CÂN BẰNG (Hybrid Strategy)
# Chọn phân vị 60% làm mốc.
target_count = int(class_counts.quantile(0.60)) 

print(f"\n[CHIẾN LƯỢC] Đưa tất cả các lớp về cùng số lượng: {target_count}")

# =========================================
# 4. HUẤN LUYỆN AI
# =========================================
print("\n2. Đang huấn luyện AI (CTGAN)...")
ai_cols = ['room_class', 'final_price', 'area_m2', 'max_people']
df_train = df_clean[ai_cols]

metadata = SingleTableMetadata()
metadata.detect_from_dataframe(df_train)
synthesizer = CTGANSynthesizer(metadata, epochs=300, verbose=False)
synthesizer.fit(df_train)

# =========================================
# 5. CÂN BẰNG DỮ LIỆU
# =========================================
print("3. Đang thực hiện cân bằng dữ liệu...")
final_dfs = []

for room_type, real_count in class_counts.items():
    df_real = df_clean[df_clean['room_class'] == room_type]
    
    if real_count >= target_count:
        # Downsample hoặc giữ nguyên
        df_resampled = df_real.sample(n=target_count, random_state=42)
        if 'source' in df_resampled.columns:
            df_resampled['source'] = 'Real'
        final_dfs.append(df_resampled)
        print(f" -> {room_type}: Cắt giảm/Giữ nguyên từ {real_count} về {target_count} (100% Real)")
        
    else:
        # Upsample (Sinh thêm)
        num_ai_needed = target_count - real_count
        
        # Kiểm tra an toàn
        if num_ai_needed <= 0:
            final_dfs.append(df_real)
            continue
            
        print(f" -> {room_type}: Sinh thêm {num_ai_needed} dòng AI.")
        
        # 1. Giữ nguyên dữ liệu thật
        df_real_part = df_real.copy()
        if 'source' in df_real_part.columns: df_real_part['source'] = 'Real'
        
        try:
            # 2. Sinh dữ liệu AI
            condition = Condition(num_rows=num_ai_needed, column_values={'room_class': room_type})
            ai_data = synthesizer.sample_from_conditions(conditions=[condition])
            
            # 3. Ghép thông tin text
            text_samples = df_real.sample(n=num_ai_needed, replace=True).reset_index(drop=True)
            text_samples['final_price'] = ai_data['final_price'].values
            text_samples['area_m2'] = ai_data['area_m2'].values
            text_samples['max_people'] = ai_data['max_people'].values
            
            if 'source' in text_samples.columns: text_samples['source'] = 'AI_Generated'
            
            # Gộp
            df_merged = pd.concat([df_real_part, text_samples])
            final_dfs.append(df_merged)
            
        except Exception as e:
            print(f"Lỗi khi sinh dữ liệu cho {room_type}: {e}")
            final_dfs.append(df_real_part)

# Gộp danh sách thành DataFrame final
if final_dfs:
    df_balanced = pd.concat(final_dfs).reset_index(drop=True)
else:
    df_balanced = df_clean.copy()

# =========================================
# 6. LỌC LẠI & LƯU
# =========================================
# Lọc lại outlier lần cuối
df_balanced = remove_outliers_strict(df_balanced, 'final_price', group_col='room_class')
df_balanced = remove_outliers_strict(df_balanced, 'area_m2')

# Sắp xếp cột
final_cols = [c for c in original_cols if c in df_balanced.columns]
df_balanced = df_balanced[final_cols]

print("\n" + "="*30)
print(f"TỔNG SỐ DÒNG CUỐI CÙNG: {len(df_balanced)}")
print("PHÂN BỐ CÁC LỚP:")
print(df_balanced['room_class'].value_counts())

# Vẽ biểu đồ
plt.figure(figsize=(12, 6))
df_plot = df_balanced.copy()
# Tạo cột giả nếu source không tồn tại để tránh lỗi vẽ
if 'source' not in df_plot.columns:
    df_plot['source'] = 'Unknown'
    
df_plot['Source_Label'] = df_plot['source'].apply(lambda x: 'AI' if 'AI' in str(x) else 'Real')

sns.countplot(data=df_plot, y='room_class', hue='Source_Label', palette={'Real': '#3498db', 'AI': '#e74c3c'})
plt.title('Tỉ lệ Dữ liệu Thật vs AI sau khi cân bằng (Hybrid Strategy)', fontsize=15)
plt.tight_layout()
plt.show()

# Lưu file
df_balanced.to_csv('../data/balanced_data.csv', index=False, encoding='utf-8-sig')
print("Đã lưu file: balanced_data.csv")