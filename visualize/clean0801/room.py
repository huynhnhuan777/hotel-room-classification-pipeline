import pandas as pd

# ===================== ĐỌC FILE =====================
input_file = r"C:\Users\Nhuan\OneDrive - ut.edu.vn\Desktop\SEMESTER_7\DATA MINING\hotel-room-classification-pipeline\visualize\clean0801\merged_all_data.csv"
df = pd.read_csv(input_file)

print(f"Tổng số dòng: {len(df)}")

print("\nSố unique ban đầu:")
print(f"  - Room Type: {df['Room Type'].nunique()}")
print(f"  - Bed_Type: {df['Bed_Type'].nunique()}")

# ===================== CHUẨN HÓA ROOM TYPE =====================
def standardize_room_type(room_type):
    if pd.isna(room_type):
        return 'Unknown'

    text = str(room_type).strip().lower()

    # Dormitory
    if any(x in text for x in ['dorm', 'hostel', 'tập thể']):
        return 'Dormitory'

    # Villa / Bungalow
    if any(x in text for x in ['villa', 'bungalow', 'biệt thự']):
        return 'Villa/Bungalow'

    # Apartment
    if 'apartment' in text or 'căn hộ' in text:
        if 'studio' in text:
            return 'Studio'
        if any(x in text for x in ['1 bedroom', '1 phòng ngủ']):
            return 'Apartment 1BR'
        if any(x in text for x in ['2 bedroom', '2 phòng ngủ']):
            return 'Apartment 2BR'
        return 'Apartment'

    # Suite
    if 'suite' in text or 'penthouse' in text:
        return 'Suite'

    # Family
    if 'family' in text or 'gia đình' in text:
        return 'Family Room'

    # Room level
    if 'deluxe' in text:
        return 'Deluxe Room'
    if 'executive' in text:
        return 'Executive Room'
    if 'superior' in text:
        return 'Superior Room'
    if 'standard' in text or 'tiêu chuẩn' in text:
        return 'Standard Room'
    if any(x in text for x in ['economy', 'budget', 'bình dân']):
        return 'Economy Room'
    if any(x in text for x in ['luxury', 'vip', 'royal']):
        return 'Luxury Room'

    if 'room' in text or 'phòng' in text:
        return 'Standard Room'

    return 'Unknown'


# ===================== CHUẨN HÓA BED TYPE =====================
def standardize_bed_type(bed_type):
    if pd.isna(bed_type):
        return 'Unknown'

    text = str(bed_type).lower()
    beds = []

    if 'king' in text:
        beds.append('King')
    if 'queen' in text:
        beds.append('Queen')
    if 'double' in text or 'đôi' in text:
        beds.append('Double')
    if 'single' in text or 'đơn' in text or 'twin' in text:
        beds.append('Single/Twin')
    if 'bunk' in text or 'tầng' in text:
        beds.append('Bunk')
    if 'sofa' in text:
        beds.append('Sofa Bed')

    if not beds:
        return 'Unknown'
    if len(set(beds)) == 1:
        return beds[0]
    return 'Mixed Beds'


# ===================== ÁP DỤNG =====================
df['Room_Type_Standardized'] = df['Room Type'].apply(standardize_room_type)
df['Bed_Configuration'] = df['Bed_Type'].apply(standardize_bed_type)

# ===================== THỐNG KÊ =====================
print("\nROOM TYPE (sau chuẩn hóa):")
print(df['Room_Type_Standardized'].value_counts().to_string())

print("\nBED CONFIGURATION (sau chuẩn hóa):")
print(df['Bed_Configuration'].value_counts().to_string())

# ===================== LƯU FILE =====================
output_file = input_file.replace('.csv', '_standardized.csv')
df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"\n✓ Đã lưu file: {output_file}")
