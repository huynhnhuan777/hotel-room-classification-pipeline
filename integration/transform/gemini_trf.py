import pandas as pd
import os
import re

# ==========================================
# CẤU HÌNH ĐƯỜNG DẪN (ĐÃ SỬA)
# ==========================================
# Đường dẫn thư mục chứa file raw (Đã cập nhật thêm /integration)
RAW_FOLDER = r"C:\Users\Nhuan\OneDrive - ut.edu.vn\Desktop\SEMESTER_7\DATA MINING\hotel-room-classification-pipeline\integration\raw"

# Đường dẫn thư mục lưu file kết quả
OUTPUT_FOLDER = r"C:\Users\Nhuan\OneDrive - ut.edu.vn\Desktop\SEMESTER_7\DATA MINING\hotel-room-classification-pipeline\integration\unified"

# Tạo thư mục output nếu chưa tồn tại
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Schema chung mong muốn
TARGET_COLUMNS = [
    'source', 'hotel_name', 'hotel_link', 'address', 
    'rating', 'room_type', 'bed_type', 'area_m2', 
    'facilities', 'price'
]

# ==========================================
# HÀM HỖ TRỢ LÀM SẠCH DỮ LIỆU
# ==========================================
def clean_price(price_raw):
    """Chuyển đổi giá tiền từ string (có đ, dấu phẩy) sang float"""
    if pd.isna(price_raw):
        return None
    if isinstance(price_raw, (int, float)):
        return float(price_raw)
    
    # Lấy số đầu tiên tìm thấy (xử lý trường hợp range giá: "1.000 - 2.000")
    # Xóa ký tự không phải số hoặc dấu phân cách
    clean_str = str(price_raw).replace(',', '').replace('.', '').replace('₫', '').strip()
    # Tìm chuỗi số
    match = re.search(r'(\d+)', clean_str)
    if match:
        return float(match.group(1))
    return None

def clean_area(area_raw):
    """Lấy số m2 từ chuỗi"""
    if pd.isna(area_raw):
        return None
    clean_str = str(area_raw).lower().replace('m2', '').replace('m²', '').strip()
    try:
        return float(clean_str)
    except:
        return None

# ==========================================
# XỬ LÝ TỪNG NGUỒN DỮ LIỆU
# ==========================================

# 1. Xử lý HoangVu (Booking.com format)
def process_hoangvu():
    file_path = os.path.join(RAW_FOLDER, 'hoangvu_hotels.csv')
    if not os.path.exists(file_path):
        print(f"Không tìm thấy file: {file_path}")
        return pd.DataFrame(columns=TARGET_COLUMNS)
        
    try:
        df = pd.read_csv(file_path)
        df['source'] = 'hoangvu'
        
        # Mapping
        df_mapped = pd.DataFrame()
        df_mapped['source'] = df['source']
        df_mapped['hotel_name'] = df['Hotel Name']
        df_mapped['hotel_link'] = df['Hotel Link']
        df_mapped['address'] = df['Address']
        df_mapped['rating'] = df['Rating_Clean']
        df_mapped['room_type'] = df['Room Type']
        df_mapped['bed_type'] = df['Bed Type']
        df_mapped['area_m2'] = df['Area_m2_cleaned'] # Đã clean sẵn
        df_mapped['facilities'] = df['Facilities_cleaned']
        df_mapped['price'] = df['Final Price']
        
        return df_mapped
    except Exception as e:
        print(f"Lỗi xử lý HoangVu: {e}")
        return pd.DataFrame(columns=TARGET_COLUMNS)

# 2. Xử lý VanDuy (Trip.com format)
def process_vanduy():
    file_path = os.path.join(RAW_FOLDER, 'vanduy_hotels.xlsx')
    if not os.path.exists(file_path):
        print(f"Không tìm thấy file: {file_path}")
        return pd.DataFrame(columns=TARGET_COLUMNS)

    try:
        df = pd.read_excel(file_path)
        df['source'] = 'vanduy'
        
        df_mapped = pd.DataFrame()
        df_mapped['source'] = df['source']
        df_mapped['hotel_name'] = df['hotelName']
        df_mapped['hotel_link'] = df['imageUrl'] 
        df_mapped['address'] = df['address']
        df_mapped['rating'] = df['commentScore']
        df_mapped['room_type'] = df['roomNames'] 
        df_mapped['bed_type'] = None
        df_mapped['area_m2'] = None
        df_mapped['facilities'] = df['categoryName'] 
        df_mapped['price'] = df['minPrice']
        
        return df_mapped
    except Exception as e:
        print(f"Lỗi xử lý VanDuy: {e}")
        return pd.DataFrame(columns=TARGET_COLUMNS)

# 3. Xử lý HongNhuan (IVIVU format - Cần ghép 2 file)
def process_hongnhuan():
    path_hotel = os.path.join(RAW_FOLDER, 'hongnhuan_hotels.csv')
    path_room = os.path.join(RAW_FOLDER, 'hongnhuan_rooms.csv')
    
    if not os.path.exists(path_hotel) or not os.path.exists(path_room):
        print("Không tìm thấy file HongNhuan")
        return pd.DataFrame(columns=TARGET_COLUMNS)

    try:
        df_hotel = pd.read_csv(path_hotel)
        df_room = pd.read_csv(path_room)
        
        # Join Hotel và Room
        merged = pd.merge(df_room, df_hotel, on='hotel_id', how='left')
        merged['source'] = 'hongnhuan'
        
        df_mapped = pd.DataFrame()
        df_mapped['source'] = merged['source']
        df_mapped['hotel_name'] = merged['hotel_name']
        df_mapped['hotel_link'] = merged['hotel_link']
        df_mapped['address'] = merged['city'] 
        df_mapped['rating'] = None
        df_mapped['room_type'] = merged['room_name']
        df_mapped['bed_type'] = merged['bed_type']
        df_mapped['area_m2'] = merged['area_m2'].apply(clean_area)
        df_mapped['facilities'] = merged['amenities']
        df_mapped['price'] = merged['price']
        
        return df_mapped
    except Exception as e:
        print(f"Lỗi xử lý HongNhuan: {e}")
        return pd.DataFrame(columns=TARGET_COLUMNS)

# 4. Xử lý TrongVu (TripAdvisor format)
def process_trongvu():
    file_path = os.path.join(RAW_FOLDER, 'trongvu_hotels.csv')
    if not os.path.exists(file_path):
        print(f"Không tìm thấy file: {file_path}")
        return pd.DataFrame(columns=TARGET_COLUMNS)

    try:
        df = pd.read_csv(file_path)
        df['source'] = 'trongvu'
        
        df_mapped = pd.DataFrame()
        df_mapped['source'] = df['source']
        df_mapped['hotel_name'] = df['hotel_name']
        df_mapped['hotel_link'] = df['hotel_url']
        df_mapped['address'] = df['address']
        df_mapped['rating'] = df['ratingValue']
        df_mapped['room_type'] = df['room_types'] 
        df_mapped['bed_type'] = None
        df_mapped['area_m2'] = None
        df_mapped['facilities'] = df['amenities']
        df_mapped['price'] = df['priceRange'].apply(clean_price) 
        
        return df_mapped
    except Exception as e:
        print(f"Lỗi xử lý TrongVu: {e}")
        return pd.DataFrame(columns=TARGET_COLUMNS)

# 5. Xử lý VanSau (Mytour format - Ghép nhiều file và join)
def process_vansau():
    p_h1 = os.path.join(RAW_FOLDER, 'vansau_hotels_1.xlsx')
    p_h2 = os.path.join(RAW_FOLDER, 'vansau_hotels_2.xlsx')
    p_r1 = os.path.join(RAW_FOLDER, 'vansau_rooms_1.xlsx')
    p_r2 = os.path.join(RAW_FOLDER, 'vansau_rooms_2.xlsx')

    if not all(os.path.exists(p) for p in [p_h1, p_h2, p_r1, p_r2]):
        print("Thiếu file VanSau")
        return pd.DataFrame(columns=TARGET_COLUMNS)

    try:
        # Đọc và gộp các file Hotel
        h1 = pd.read_excel(p_h1)
        h2 = pd.read_excel(p_h2)
        df_hotel = pd.concat([h1, h2], ignore_index=True)
        
        # Đọc và gộp các file Room
        r1 = pd.read_excel(p_r1)
        r2 = pd.read_excel(p_r2)
        df_room = pd.concat([r1, r2], ignore_index=True)
        
        # Join: Bên Hotel dùng 'link', Bên Room dùng 'hotel_link'
        merged = pd.merge(df_room, df_hotel, left_on='hotel_link', right_on='link', how='left')
        merged['source'] = 'vansau'
        
        df_mapped = pd.DataFrame()
        df_mapped['source'] = merged['source']
        df_mapped['hotel_name'] = merged['ten'] 
        df_mapped['hotel_link'] = merged['hotel_link']
        df_mapped['address'] = merged['dia_chi']
        df_mapped['rating'] = merged['diem_danh_gia']
        df_mapped['room_type'] = merged['room_name']
        df_mapped['bed_type'] = merged['bed']
        df_mapped['area_m2'] = merged['area'].apply(clean_area)
        # Gộp tiện nghi
        df_mapped['facilities'] = merged['room_amenities'].fillna('') + ' | ' + merged['tien_nghi'].fillna('')
        df_mapped['price'] = merged['final_price'].apply(clean_price)
        
        return df_mapped
    except Exception as e:
        print(f"Lỗi xử lý VanSau: {e}")
        return pd.DataFrame(columns=TARGET_COLUMNS)

# ==========================================
# MAIN PROCESS
# ==========================================
def main():
    print(f"Đang đọc dữ liệu từ: {RAW_FOLDER}")
    print("Bắt đầu transform dữ liệu...")
    
    # 1. Transform từng nguồn
    df1 = process_hoangvu()
    df2 = process_vanduy()
    df3 = process_hongnhuan()
    df4 = process_trongvu()
    df5 = process_vansau()
    
    print(f"- HoangVu: {len(df1)} dòng")
    print(f"- VanDuy: {len(df2)} dòng")
    print(f"- HongNhuan: {len(df3)} dòng")
    print(f"- TrongVu: {len(df4)} dòng")
    print(f"- VanSau: {len(df5)} dòng")

    # 2. Ghép tất cả (Union)
    final_df = pd.concat([df1, df2, df3, df4, df5], ignore_index=True)
    
    # 3. Clean lại lần cuối (nếu cần)
    final_df = final_df.dropna(subset=['hotel_name'])
    
    # 4. Lưu file
    output_path = os.path.join(OUTPUT_FOLDER, 'unified_hotel_data.csv')
    try:
        final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print("------------------------------------------------")
        print(f"Đã hoàn thành! File được lưu tại:\n{output_path}")
        print(f"Tổng số dòng dữ liệu: {len(final_df)}")
    except Exception as e:
        print(f"Lỗi khi lưu file: {e}")

if __name__ == "__main__":
    main()