import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata
from sdv.sampling import Condition
import warnings

# --- CẤU HÌNH & THIẾT LẬP ---
warnings.filterwarnings('ignore')
sns.set(style="whitegrid")

DB_CONFIG = {
    "dbname": "booking_data",
    "user": "postgres",
    "password": "123456",
    "host": "localhost",
    "port": "5432"
}
DB_CONNECTION_STR = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
engine = create_engine(DB_CONNECTION_STR)

TABLE_NAMES = ["clean_booking", "clean_ivivu", "clean_mytour"]

# --- 1. HÀM LỌC OUTLIER  ---
def remove_outliers_strict(df, col_to_clean, group_col=None, method='iqr', strictness='high'):
    df_out = df.copy()
    
    if method == 'iqr':
        multiplier = 0.8 if strictness == 'high' else 1.5
    elif method == 'percentile':
        lower_p, upper_p = (0.05, 0.95) if strictness == 'high' else (0.01, 0.99)

    if group_col:
        cleaned_groups = []
        for group_name in df_out[group_col].unique():
            group_data = df_out[df_out[group_col] == group_name]
            if len(group_data) < 5:
                cleaned_groups.append(group_data)
                continue
            
            if method == 'iqr':
                Q1 = group_data[col_to_clean].quantile(0.25)
                Q3 = group_data[col_to_clean].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - multiplier * IQR
                upper_bound = Q3 + multiplier * IQR
            else:
                lower_bound = group_data[col_to_clean].quantile(lower_p)
                upper_bound = group_data[col_to_clean].quantile(upper_p)

            filtered_data = group_data[
                (group_data[col_to_clean] >= max(0, lower_bound)) & 
                (group_data[col_to_clean] <= upper_bound)
            ]
            cleaned_groups.append(filtered_data)
        return pd.concat(cleaned_groups).reset_index(drop=True)
    else:
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

# --- 2. VÒNG LẶP XỬ LÝ ---
for table_name in TABLE_NAMES:
    print(f"\n{'>'*10} ĐANG XỬ LÝ: {table_name.upper()} {'<'*10}")
    
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
        original_cols = df.columns.tolist()
        print(f"  - Tải thành công {len(df)} dòng.")
    except Exception as e:
        print(f"  - Lỗi kết nối: {e}")
        continue

    # Điền giá trị thiếu
    for col in ['Final Price', 'Area_m2', 'Max People']:
        if col in df.columns: 
            df[col] = df[col].fillna(df[col].median())
    df['room_class'] = df['room_class'].fillna('Unknown')

    # Lọc Outlier lần 1
    df_clean = remove_outliers_strict(df, 'Area_m2', strictness='high')
    df_clean = remove_outliers_strict(df_clean, 'Final Price', group_col='room_class', strictness='high')

    # Tính Target Count
    class_counts = df_clean['room_class'].value_counts()
    target_count = int(class_counts.quantile(0.70))
    print(f"  - Mốc cân bằng (Quantile 0.70): {target_count}")

    # Huấn luyện CTGAN
    ai_cols = ['room_class', 'Final Price', 'Area_m2', 'Max People']
    # Chỉ lấy các cột AI cần và tồn tại trong DF
    existing_ai_cols = [c for c in ai_cols if c in df_clean.columns]
    df_train = df_clean[existing_ai_cols]

    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(df_train)
    synthesizer = CTGANSynthesizer(metadata, epochs=300, verbose=False)
    synthesizer.fit(df_train)

    # Cân bằng dữ liệu
    final_dfs = []
    for room_type, real_count in class_counts.items():
        df_real = df_clean[df_clean['room_class'] == room_type].copy()
        
        if real_count >= target_count:
            # Downsampling
            df_resampled = df_real.sample(n=target_count, random_state=42)
            df_resampled['source'] = 'Real'
            final_dfs.append(df_resampled)
        else:
            # Upsampling bằng AI
            num_ai_needed = target_count - real_count
            df_real['source'] = 'Real'
            
            try:
                condition = Condition(num_rows=num_ai_needed, column_values={'room_class': room_type})
                ai_data = synthesizer.sample_from_conditions(conditions=[condition])
                
                # Copy metadata từ bản ghi thật để giữ các cột text khác (Hotel Name, Address...)
                text_samples = df_real.sample(n=num_ai_needed, replace=True).reset_index(drop=True)
                for col in existing_ai_cols:
                    if col != 'room_class':
                        text_samples[col] = ai_data[col].values
                
                text_samples['source'] = 'AI_Generated'
                final_dfs.append(pd.concat([df_real, text_samples]))
            except Exception as e:
                print(f"    ! Lỗi sinh AI lớp {room_type}: {e}")
                final_dfs.append(df_real)

    df_balanced = pd.concat(final_dfs).reset_index(drop=True)

    # Lọc Outlier lần cuối (nới lỏng hệ số thành 'low')
    df_balanced = remove_outliers_strict(df_balanced, 'Final Price', group_col='room_class', strictness='low')
    
    # --- 3. TRỰC QUAN HÓA ---
    plt.figure(figsize=(12, 6))
    sns.countplot(data=df_balanced, y='room_class', hue='source', palette={'Real': '#3498db', 'AI_Generated': '#e74c3c'})
    plt.title(f'Phân bổ Real vs AI - Bảng {table_name}', fontsize=14)
    plt.tight_layout()
    plt.show()

    # --- 4. LƯU VÀO DATABASE ---
    # Đảm bảo source column có trong danh sách cột nếu bạn muốn lưu nó
    if 'source' not in original_cols:
        original_cols.append('source')
        
    final_cols = [c for c in original_cols if c in df_balanced.columns]
    df_save = df_balanced[final_cols]
    
    output_table = f"{table_name}_balanced"
    df_save.to_sql(output_table, engine, if_exists='replace', index=False)
    print(f"--- HOÀN THÀNH {table_name.upper()} -> {len(df_save)} dòng ---")

print("\n[SUCCESS] Đã xử lý và cân bằng tất cả các bảng.")