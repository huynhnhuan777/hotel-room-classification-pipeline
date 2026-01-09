import pandas as pd
import time
import re
from sqlalchemy import create_engine
from playwright.sync_api import sync_playwright

# --- CẤU HÌNH ---
INPUT_FILE = "merged_data_cleaned.csv"  # File đầu vào
OUTPUT_FILE = "merged_data_cleaned_updated.csv" # File đầu ra (nên lưu file mới để backup)
DB_CONFIG = {
    "dbname": "booking_data",
    "user": "postgres",
    "password": "123456", 
    "host": "localhost",
    "port": "5432"
}
DB_CONNECTION_STR = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

# --- HÀM NHẬN DIỆN ĐỊA ĐIỂM TỪ TEXT ---
def detect_location(text):
    if not text: return None
    text = text.lower()
    
    # 1. Hồ Chí Minh
    if any(x in text for x in ['hồ chí minh', 'ho chi minh', 'hcm', 'sai gon', 'quận 1', 'quận 3', 'thành phố hồ chí minh']):
        return 'Hồ Chí Minh'
    
    # 2. Vũng Tàu
    if any(x in text for x in ['vũng tàu', 'vung tau', 'bà rịa', 'ba ria', 'xuyên mộc', 'long hải', 'hồ tràm']):
        return 'Vũng Tàu'
    
    # 3. Bình Dương
    if any(x in text for x in ['bình dương', 'binh duong', 'thủ dầu một', 'dĩ an', 'thuận an']):
        return 'Bình Dương'

    return None

# --- HÀM CRAWL ---
def scrape_unknown_locations():
    # 1. Đọc dữ liệu
    print("-> Đang đọc dữ liệu...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except:
        # Nếu không có file CSV, thử đọc từ DB
        engine = create_engine(DB_CONNECTION_STR)
        df = pd.read_sql("SELECT * FROM merged_data_cleaned", engine)

    # 2. Lọc các dòng Unknown
    # Chuyển về string để tránh lỗi so sánh
    df['location'] = df['location'].fillna('Unknown').astype(str)
    unknown_indices = df[df['location'] == 'Unknown'].index
    
    total_unknown = len(unknown_indices)
    print(f"-> Tìm thấy {total_unknown} dòng có location là 'Unknown'.")

    if total_unknown == 0:
        print("-> Không có gì để xử lý.")
        return

    # 3. Khởi động trình duyệt
    print("-> Đang khởi động trình duyệt để quét lại địa chỉ...")
    
    with sync_playwright() as p:
        # Mở browser (headless=True để chạy ngầm, False để xem nó chạy)
        browser = p.chromium.launch(headless=True) 
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = context.new_page()

        # 4. Duyệt qua từng dòng Unknown
        count = 0
        for idx in unknown_indices:
            count += 1
            url = df.at[idx, 'hotel_link']
            hotel_name = df.at[idx, 'hotel_name']
            
            print(f"[{count}/{total_unknown}] Checking: {hotel_name}...")
            
            if pd.isna(url) or str(url).strip() == "":
                print("   -> Link rỗng, bỏ qua.")
                continue

            try:
                # Truy cập link (timeout 15s)
                page.goto(url, timeout=15000, wait_until="domcontentloaded")
                
                # Logic lấy địa chỉ tùy theo trang web (Booking, Mytour, Ivivu...)
                # Cách an toàn nhất: Lấy toàn bộ text trên trang để tìm từ khóa
                # Tuy nhiên, ưu tiên tìm trong các thẻ địa chỉ phổ biến trước
                
                full_text = ""
                
                # Thử tìm thẻ địa chỉ của Booking.com (.hp_address_subtitle)
                try:
                    address_elem = page.locator(".hp_address_subtitle").first
                    if address_elem.count() > 0:
                        full_text += address_elem.inner_text() + " "
                except: pass

                # Thử tìm thẻ địa chỉ chung chung (nếu là trang khác)
                try:
                    # Lấy text body nếu không tìm thấy thẻ cụ thể
                    full_text += page.locator("body").inner_text()
                except: pass

                # Phân tích địa điểm
                found_loc = detect_location(full_text)
                
                if found_loc:
                    print(f"   -> TÌM THẤY: {found_loc}")
                    df.at[idx, 'location'] = found_loc
                else:
                    print("   -> Vẫn không tìm thấy (giữ nguyên Unknown).")

                # Nghỉ 1 chút để không bị chặn
                time.sleep(1)

            except Exception as e:
                print(f"   -> Lỗi khi truy cập: {e}")

        browser.close()

    # 5. Lưu lại kết quả
    print("-" * 30)
    print("-> Đang lưu file cập nhật...")
    
    # Lưu CSV
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"-> Đã lưu vào file: {OUTPUT_FILE}")

    # Lưu Database 
    try:
        engine = create_engine(DB_CONNECTION_STR)
        df.to_sql("merged_data_cleaned", engine, if_exists='replace', index=False)
        print("-> Đã cập nhật lại Database.")
    except Exception as e:
        print(f"-> Lỗi cập nhật DB: {e}")

if __name__ == "__main__":
    scrape_unknown_locations()