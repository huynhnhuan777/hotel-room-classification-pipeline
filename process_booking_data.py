import pandas as pd
import numpy as np
import re

# --- CẤU HÌNH TỪ KHÓA PHÂN LOẠI (HỖ TRỢ TIẾNG VIỆT & ANH) ---
ROOM_KEYWORDS = {
    'Presidential/Suite': ['president', 'tổng thống', 'suite', 'penthouse', 'biệt thự', 'villa'],
    'Family/Large': ['family', 'gia đình', '3 phòng', '4 phòng', 'nối liền', 'connecting', 'triple', 'quadruple'],
    'Premium/Luxury': ['premium', 'luxury', 'cao cấp', 'sang trọng', 'business', 'executive'],
    'Deluxe': ['deluxe', 'thượng hạng', 'grand'],
    'Apartment/Studio': ['apartment', 'căn hộ', 'studio', 'condo'],
    'Standard/Superior': ['standard', 'superior', 'tiêu chuẩn', 'phổ thông', 'economy', 'budget', 'classic'],
    'Dormitory': ['dorm', 'tập thể', 'giường tầng', 'bunk', 'capsule', 'kén'],
}

def clean_and_process_data(input_file, output_file):
    print(f"🔄 Đang đọc file: {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(" Không tìm thấy file dữ liệu!")
        return

    # ==============================================================================
    # 1. XỬ LÝ SỐ SAO (STARS) 
    # ==============================================================================
    def clean_stars(val):
        # Chuyển đổi về số, lỗi thì về 0
        if pd.isna(val) or val in ['N/A', 'None']: return 0
        try:
            return float(val)
        except: return 0
    
    print(" Đang xử lý số sao (Stars)...")
    df['Stars_Clean'] = df['Stars'].apply(clean_stars)

    # ==============================================================================
    # 2. XỬ LÝ ĐỊA CHỈ -> LẤY QUẬN (DISTRICT)
    # ==============================================================================
    def extract_district(addr):
        if pd.isna(addr): return "Other"
        # Regex bắt: Quận 1, Quận Bình Thạnh, District 1, TP. Thủ Đức...
        match = re.search(r'(quận\s+\d+|quận\s+[a-zà-ỹ]+|district\s+\d+|tp\.\s+thủ đức|huyện\s+[a-zà-ỹ]+)', str(addr).lower())
        if match:
            return match.group(0).title() # Viết hoa chữ cái đầu (vd: Quận 1)
        return "Other"

    print(" Đang trích xuất Quận/Huyện từ địa chỉ...")
    df['District'] = df['Address'].apply(extract_district)

    # ==============================================================================
    # 3. PHÂN LOẠI GIƯỜNG (BED TYPE)
    # ==============================================================================
    def classify_bed(bed_text):
        if pd.isna(bed_text) or bed_text == 'N/A': return "Unknown"
        t = str(bed_text).lower()
        
        if any(x in t for x in ['đôi', 'double', 'king', 'queen', 'lớn']): return "Double/Large"
        if any(x in t for x in ['đơn', 'single']): return "Single/Twin"
        if any(x in t for x in ['tầng', 'bunk']): return "Bunk"
        if any(x in t for x in ['sofa', 'futon']): return "Sofa/Futon"
        return "Other"

    print(" Đang phân loại giường (Bed Type)...")
    df['Bed_Class'] = df['Bed Type'].apply(classify_bed)

    # ==============================================================================
    # 4. XỬ LÝ BOOLEAN (CANCEL, BREAKFAST) & BADGE 
    # ==============================================================================
    # Chuyển Yes/No thành 1/0 để máy học dễ hiểu hơn
    def to_bool(val):
        s = str(val).lower()
        return 1 if 'yes' in s or 'có' in s else 0

    print(" Đang chuẩn hóa dữ liệu Boolean (Cancel, Breakfast)...")
    df['Free_Cancel_Bool'] = df['Free Cancellation'].apply(to_bool)
    df['Breakfast_Bool'] = df['Breakfast Included'].apply(to_bool)

    # Làm sạch cột Badge Deal
    df['Badge_Clean'] = df['Badge Deal'].fillna('No Deal').replace({'None': 'No Deal', 'N/A': 'No Deal'})

    # ==============================================================================
    # 5. XỬ LÝ NGƯỜI LỚN & TRẺ EM 
    # ==============================================================================
    print(" Đang xử lý thông tin khách (Adults, Children)...")
    # Ép kiểu số nguyên, lỗi về 0
    df['Adults'] = pd.to_numeric(df['Adults'], errors='coerce').fillna(0).astype(int)
    df['Children'] = pd.to_numeric(df['Children'], errors='coerce').fillna(0).astype(int)
    # Tạo cột tổng số người (Feature Engineering)
    df['Total_Guests'] = df['Adults'] + df['Children']

    # ==============================================================================
    # 6.RATING, LOCATION, DISTANCE, ROOM CLASS
    # ==============================================================================
    def clean_score(value):
        if pd.isna(value) or value in ['N/A', 'None']: return np.nan
        if isinstance(value, str): return float(value.replace(',', '.'))
        return float(value)

    print(" Đang làm sạch dữ liệu số (Rating, Location)...")
    df['Rating_Clean'] = df['Rating Score'].apply(clean_score)
    df['Location_Clean'] = df['Location Score'].apply(clean_score)

    def extract_distance_km(value):
        if pd.isna(value) or value == 'N/A': return np.nan
        value = str(value).lower().replace(',', '.')
        match = re.search(r'(\d+(\.\d+)?)', value)
        if match:
            number = float(match.group(1))
            return number if 'km' in value else number / 1000
        return np.nan

    print(" Đang chuẩn hóa khoảng cách (Distance)...")
    df['Distance_KM'] = df['Distance'].apply(extract_distance_km)

    def classify_room(room_name):
        if pd.isna(room_name): return 'Unknown'
        name_lower = str(room_name).lower()
        for category, keywords in ROOM_KEYWORDS.items():
            for kw in keywords:
                if kw in name_lower: return category
        if 'phòng' in name_lower or 'room' in name_lower: return 'Standard/Superior'
        return 'Other'

    print(" Đang phân loại hạng phòng (Room Class)...")
    df['Room_Class'] = df['Room Type'].apply(classify_room)

    # Tính Discount
    df['Final Price'] = pd.to_numeric(df['Final Price'], errors='coerce').fillna(0)
    df['Original Price'] = pd.to_numeric(df['Original Price'], errors='coerce').fillna(0)
    
    # Logic: Nếu Original = 0 hoặc Original < Final thì gán Original = Final (tránh chia cho 0 hoặc discount âm)
    df.loc[df['Original Price'] < df['Final Price'], 'Original Price'] = df['Final Price']
    
    df['Discount %'] = ((df['Original Price'] - df['Final Price']) / df['Original Price']) * 100
    df['Discount %'] = df['Discount %'].fillna(0).round(1)

    # ==============================================================================
    # 7. LƯU FILE VỚI CÁC CỘT MỚI
    # ==============================================================================
    cols_order = [
        'Scenario', 'Hotel Name', 'Stars_Clean', 'District', 'Address',
        'Room_Class', 'Room Type', 'Bed_Class', 'Bed Type',
        'Final Price', 'Original Price', 'Discount %',
        'Rating_Clean', 'Review Count', 'Location_Clean', 'Distance_KM',
        'Free_Cancel_Bool', 'Breakfast_Bool', 'Badge_Clean',
        'Adults', 'Children', 'Total_Guests', 'Check-in'
    ]
    
    # Chỉ lấy các cột thực sự tồn tại trong DataFrame để tránh lỗi
    final_cols = [c for c in cols_order if c in df.columns]
    
    df_clean = df[final_cols]
    df_clean.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f" HOÀN TẤT! File sạch (đầy đủ tính năng) đã lưu tại: {output_file}")
    
    print("\n--- THỐNG KÊ NHANH ---")
    print(f"- Số khách sạn theo quận:\n{df['District'].value_counts().head()}")
    print(f"\n- Phân loại giường:\n{df['Bed_Class'].value_counts()}")

# --- CHẠY PIPELINE ---
if __name__ == "__main__":
    INPUT_CSV = "booking_data_demo.csv"
    OUTPUT_CSV = "booking_data_cleaned.csv"
    
    clean_and_process_data(INPUT_CSV, OUTPUT_CSV)