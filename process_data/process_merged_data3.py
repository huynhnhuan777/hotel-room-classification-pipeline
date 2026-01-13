import pandas as pd
import time
import os
from sqlalchemy import create_engine
from playwright.sync_api import sync_playwright

# --- CẤU HÌNH ---
# Danh sách các bảng cần xử lý trong SQL 
TABLE_NAMES = ["clean_booking", "clean_ivivu", "clean_mytour"]

DB_CONFIG = {
    "dbname": "booking_data",
    "user": "postgres",
    "password": "123456", 
    "host": "localhost",
    "port": "5432"
}
DB_CONNECTION_STR = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

# --- HÀM NHẬN DIỆN ĐỊA ĐIỂM (Giữ nguyên) ---
def detect_location(text):
    if not text: return None
    text = text.lower()
    if any(x in text for x in ['hồ chí minh', 'ho chi minh', 'hcm', 'sai gon', 'quận 1', 'quận 3', 'thành phố hồ chí minh']):
        return 'Hồ Chí Minh'
    if any(x in text for x in ['vũng tàu', 'vung tau', 'bà rịa', 'ba ria', 'xuyên mộc', 'long hải', 'hồ tràm']):
        return 'Vũng Tàu'
    if any(x in text for x in ['bình dương', 'binh duong', 'thủ dầu một', 'dĩ an', 'thuận an']):
        return 'Bình Dương'
    return None

# --- HÀM XỬ LÝ TỪNG BẢNG SQL ---
def process_single_table(table_name, page, engine):
    print(f"\n{'='*20} ĐANG XỬ LÝ BẢNG: {table_name} {'='*20}")
    
    # 1. Đọc dữ liệu trực tiếp từ SQL
    try:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, engine)
        print(f"-> Đã tải {len(df)} dòng từ bảng {table_name}.")
    except Exception as e:
        print(f"-> Lỗi khi đọc bảng {table_name}: {e}")
        return

    # Kiểm tra tên cột (Vì bước trước bạn đã chuẩn hóa thành 'Hotel Link' và 'Hotel Name')
    # Code này sẽ tự động thích ứng nếu cột là 'hotel_link' hoặc 'Hotel Link'
    col_link = 'Hotel Link' if 'Hotel Link' in df.columns else 'hotel_link'
    col_name = 'Hotel Name' if 'Hotel Name' in df.columns else 'hotel_name'

    df['location'] = df['location'].fillna('Unknown').astype(str)
    unknown_indices = df[df['location'] == 'Unknown'].index
    total_unknown = len(unknown_indices)

    # 2. Xử lý crawl nếu có 'Unknown'
    if total_unknown > 0:
        print(f"-> Tìm thấy {total_unknown} dòng Unknown. Đang tiến hành quét web...")
        count = 0
        for idx in unknown_indices:
            count += 1
            url = df.at[idx, col_link]
            name = df.at[idx, col_name]
            
            print(f"   [{count}/{total_unknown}] {name}...")
            if pd.isna(url) or str(url).strip() == "": continue

            try:
                page.goto(url, timeout=15000, wait_until="domcontentloaded")
                full_text = ""
                
                # Selector cho Booking
                try:
                    address_elem = page.locator(".hp_address_subtitle").first
                    if address_elem.count() > 0:
                        full_text += address_elem.inner_text() + " "
                except: pass
                
                # Lấy text toàn trang cho các nguồn khác (Ivivu, Mytour)
                try:
                    full_text += page.locator("body").inner_text()
                except: pass

                found_loc = detect_location(full_text)
                if found_loc:
                    print(f"      -> OK: {found_loc}")
                    df.at[idx, 'location'] = found_loc
                
                time.sleep(1) # Nghỉ để tránh bị chặn IP
            except Exception as e:
                print(f"      -> Lỗi crawl: {e}")
    else:
        print("-> Không có dòng Unknown nào cần xử lý.")

    # 3. Lưu dữ liệu mới đè vào bảng cũ
    try:
        # if_exists='replace' sẽ xóa bảng cũ và tạo lại với dữ liệu mới đã điền location
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"-> [THÀNH CÔNG] Đã cập nhật lại bảng: {table_name}")
        
        # Backup ra CSV (tùy chọn)
        # df.to_csv(f"../data/{table_name}_final.csv", index=False, encoding='utf-8-sig')
    except Exception as e:
        print(f"-> [THẤT BẠI] Lỗi khi lưu vào SQL: {e}")

# --- CHƯƠNG TRÌNH CHÍNH ---
def main():
    engine = create_engine(DB_CONNECTION_STR)
    
    with sync_playwright() as p:
        print("-> Đang khởi động trình duyệt...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Duyệt qua danh sách các bảng trong database
        for table in TABLE_NAMES:
            process_single_table(table, page, engine)

        browser.close()
    
    print("\n[HOÀN THÀNH] Tất cả các bảng đã được cập nhật dữ liệu mới.")

if __name__ == "__main__":
    main()