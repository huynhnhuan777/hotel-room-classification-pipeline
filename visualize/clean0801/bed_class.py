import pandas as pd
import re
from collections import Counter

# Đọc file CSV
input_file = r"C:\Users\Nhuan\OneDrive - ut.edu.vn\Desktop\SEMESTER_7\DATA MINING\hotel-room-classification-pipeline\visualize\clean0801\merged_all_data.csv"
df = pd.read_csv(input_file)

print(f"Tổng số dòng: {len(df)}")
print(f"\nSố giá trị unique của Bed Type: {df['Bed Type'].nunique()}")
print(f"Số giá trị unique của Bed_Class: {df['Bed_Class'].nunique()}")

# ===== CHUẨN HÓA BED_CLASS =====
def standardize_bed_class(bed_class):
    """
    Chuẩn hóa Bed_Class thành các loại cơ bản
    """
    if pd.isna(bed_class) or bed_class == 'Standard':
        return 'Unknown'
    
    bed_class = str(bed_class).strip()
    
    # Đếm số lượng mỗi loại giường
    count_single = bed_class.count('Single')
    count_double = bed_class.count('Double')
    count_king = bed_class.count('King')
    count_queen = bed_class.count('Queen')
    count_bunk = bed_class.count('Bunk')
    count_sofa = bed_class.count('Sofa')
    count_futon = bed_class.count('Futon')
    count_large = bed_class.count('Large')
    count_twin = bed_class.count('Twin')
    
    # Phân loại theo logic ưu tiên
    total_beds = sum([count_single, count_double, count_king, count_queen, 
                      count_bunk, count_sofa, count_futon, count_large, count_twin])
    
    if total_beds == 0:
        return 'Unknown'
    
    # Nếu chỉ có 1 loại giường
    if total_beds == 1:
        if count_king > 0:
            return 'King'
        elif count_queen > 0:
            return 'Queen'
        elif count_double > 0:
            return 'Double'
        elif count_single > 0 or count_twin > 0:
            return 'Single'
        elif count_bunk > 0:
            return 'Bunk'
        elif count_sofa > 0:
            return 'Sofa Bed'
        elif count_futon > 0:
            return 'Futon'
        elif count_large > 0:
            return 'Large Double'
    
    # Nếu có nhiều loại giường -> Mixed
    return 'Mixed'

# ===== CHUẨN HÓA BED TYPE =====
def extract_bed_info(bed_type):
    """
    Trích xuất thông tin giường từ Bed Type phức tạp
    """
    if pd.isna(bed_type):
        return 'Unknown'
    
    bed_type = str(bed_type).strip().lower()
    
    # Đếm số giường từ các pattern
    king_count = len(re.findall(r'(\d+)\s*giường\s*king|(\d+)\s*king\s*bed', bed_type))
    queen_count = len(re.findall(r'(\d+)\s*giường\s*queen|(\d+)\s*queen\s*bed', bed_type))
    double_count = len(re.findall(r'(\d+)\s*giường\s*đôi|(\d+)\s*double\s*bed|(\d+)\s*doublebed', bed_type))
    single_count = len(re.findall(r'(\d+)\s*giường\s*đơn|(\d+)\s*single\s*bed|(\d+)\s*singlebed', bed_type))
    bunk_count = len(re.findall(r'(\d+)\s*giường\s*tầng|(\d+)\s*bunk\s*bed', bed_type))
    sofa_count = len(re.findall(r'(\d+)\s*giường\s*sofa|(\d+)\s*sofa\s*bed', bed_type))
    
    # Kiểm tra các từ khóa
    has_king = 'king' in bed_type or 'giường king' in bed_type
    has_queen = 'queen' in bed_type or 'giường queen' in bed_type
    has_double = 'đôi' in bed_type or 'double' in bed_type or 'giường đôi' in bed_type
    has_single = 'đơn' in bed_type or 'single' in bed_type or 'giường đơn' in bed_type
    has_bunk = 'tầng' in bed_type or 'bunk' in bed_type
    has_sofa = 'sofa' in bed_type
    has_dormitory = 'tập thể' in bed_type or 'dorm' in bed_type
    
    # Logic phân loại
    if has_dormitory:
        return 'Dormitory'
    
    # Đếm tổng số loại giường
    bed_types = []
    if has_king or king_count > 0:
        bed_types.append('King')
    if has_queen or queen_count > 0:
        bed_types.append('Queen')
    if has_double or double_count > 0:
        bed_types.append('Double')
    if has_single or single_count > 0:
        bed_types.append('Single')
    if has_bunk or bunk_count > 0:
        bed_types.append('Bunk')
    if has_sofa or sofa_count > 0:
        bed_types.append('Sofa Bed')
    
    if len(bed_types) == 0:
        return 'Unknown'
    elif len(bed_types) == 1:
        return bed_types[0]
    else:
        return 'Mixed'

# ===== ÁP DỤNG CHUẨN HÓA =====
print("\n" + "="*60)
print("ĐANG CHUẨN HÓA DỮ LIỆU...")
print("="*60)

# Tạo các cột mới đã chuẩn hóa
df['Bed_Class_Standardized'] = df['Bed_Class'].apply(standardize_bed_class)
df['Bed_Type_Standardized'] = df['Bed Type'].apply(extract_bed_info)

# ===== THỐNG KÊ KẾT QUẢ =====
print("\n" + "="*60)
print("KẾT QUẢ CHUẨN HÓA BED_CLASS")
print("="*60)
print(f"Trước: {df['Bed_Class'].nunique()} phân loại")
print(f"Sau:  {df['Bed_Class_Standardized'].nunique()} phân loại\n")
print("Phân bố sau chuẩn hóa:")
print(df['Bed_Class_Standardized'].value_counts())

print("\n" + "="*60)
print("KẾT QUẢ CHUẨN HÓA BED TYPE")
print("="*60)
print(f"Trước: {df['Bed Type'].nunique()} phân loại")
print(f"Sau:  {df['Bed_Type_Standardized'].nunique()} phân loại\n")
print("Phân bố sau chuẩn hóa:")
print(df['Bed_Type_Standardized'].value_counts())

# ===== THỐNG NHẤT 2 CỘT THÀNH 1 =====
print("\n" + "="*60)
print("THỐNG NHẤT THÀNH 1 CỘT DUY NHẤT")
print("="*60)

def merge_bed_info(bed_class_std, bed_type_std):
    """
    Kết hợp thông tin từ 2 cột để tạo phân loại cuối cùng
    Ưu tiên Bed_Class_Standardized nếu có giá trị hợp lệ
    """
    if bed_class_std not in ['Unknown', None] and not pd.isna(bed_class_std):
        return bed_class_std
    elif bed_type_std not in ['Unknown', None] and not pd.isna(bed_type_std):
        return bed_type_std
    else:
        return 'Unknown'

df['Bed_Final'] = df.apply(
    lambda row: merge_bed_info(row['Bed_Class_Standardized'], row['Bed_Type_Standardized']), 
    axis=1
)

print(f"Số phân loại cuối cùng: {df['Bed_Final'].nunique()}\n")
print("Phân bố cuối cùng:")
print(df['Bed_Final'].value_counts())

# ===== LƯU FILE MỚI =====
output_file = input_file.replace('.csv', '_standardized.csv')
df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"\n✓ Đã lưu file mới: {output_file}")

# ===== XUẤT BÁO CÁO =====
print("\n" + "="*60)
print("BÁO CÁO MAPPING")
print("="*60)

# Hiển thị một số ví dụ mapping
print("\nVí dụ mapping từ Bed Type gốc sang Bed_Final:")
sample_mapping = df[['Bed Type', 'Bed_Final']].drop_duplicates().head(20)
for idx, row in sample_mapping.iterrows():
    print(f"  '{row['Bed Type'][:50]}...' -> '{row['Bed_Final']}'")

print("\n" + "="*60)
print("HOÀN THÀNH!")
print("="*60)