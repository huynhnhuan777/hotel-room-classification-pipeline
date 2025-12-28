import asyncio
from playwright.async_api import async_playwright
from sqlalchemy import create_engine, text

# --- CẤU HÌNH DATABASE ---
DB_CONFIG = {
    "dbname": "booking_data",  
    "user": "postgres",         
    "password": "123456",  
    "host": "localhost",          
    "port": "5432"             
}
DB_CONNECTION_STR = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

# --- TÊN BẢNG ---
SOURCE_TABLE = "hotel_data_cleaned" 
TARGET_TABLE = "room_details"  
BATCH_SIZE = 10                   # Số lượng xử lý mỗi lần

# --- SQL TẠO BẢNG ---
CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TARGET_TABLE} (
    room_id SERIAL PRIMARY KEY,        -- Khóa chính của bảng này
    hotel_id INTEGER,                  -- Khóa ngoại (FK) trỏ về id của bảng hotel_data_cleaned
    area_m2 VARCHAR(50),               -- Diện tích (VD: 61 m²)
    facilities TEXT,                   -- Tiện ích (VD: TV, Air conditioning...)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Thiết lập liên kết khóa ngoại
    CONSTRAINT fk_{SOURCE_TABLE}
      FOREIGN KEY(hotel_id) 
      REFERENCES {SOURCE_TABLE}(id)
      ON DELETE CASCADE
);
"""

async def scrape_detail_by_link(page, url, target_room_type):
    """
    Truy cập Link -> Tìm dòng chứa target_room_type -> Lấy Area & Facilities
    """
    print(f"   -> Truy cập: {url[:60]}...")
    try:
        # Chặn ảnh để load nhanh
        await page.route("**/*.{png,jpg,jpeg,gif,webp,svg}", lambda route: route.abort())
        
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        
        try:
            await page.wait_for_selector("#hprt-table", timeout=5000)
        except:
            print("      ! Không thấy bảng giá.")
            return None

        # --- LOGIC JS ĐÃ CẬP NHẬT ---
        result = await page.evaluate(r"""(targetName) => {
            const rows = document.querySelectorAll('#hprt-table tbody tr');
            const clean = (str) => str ? str.toLowerCase().trim() : "";
            const tName = clean(targetName);
            
            let bestData = null;

            for (const row of rows) {
                // 1. Lấy tên phòng
                const nameEl = row.querySelector('.hprt-table-cell-roomtype .hprt-roomtype-icon-link');
                if (!nameEl) continue;
                
                const rowName = clean(nameEl.innerText);

                // 2. So khớp tên phòng
                if (rowName.includes(tName) || tName.includes(rowName)) {
                    
                    let size = "N/A";
                    let facs = [];
                    const roomCell = row.querySelector('.hprt-table-cell-roomtype');

                    // --- CÁCH 1: Tìm theo data-testid ---
                    // Tìm thẻ div có data-testid="rp-room-size"
                    const sizeContainer = roomCell.querySelector('[data-testid="rp-room-size"]');
                    if (sizeContainer) {
                        // Lấy text: thường nó sẽ ra "Kích thước phòng 14 m²"
                        // Ta dùng regex để lấy đúng số và m²
                        const text = sizeContainer.innerText;
                        const match = text.match(/(\d+\s*m²)/);
                        if (match) {
                            size = match[1];
                        }
                    }

                    // --- CÁCH 2: Nếu cách 1 thất bại, dùng cách cũ (tìm trong list tiện ích) ---
                    if (size === "N/A") {
                        const divFacs = roomCell.querySelectorAll('.hprt-facilities-facility');
                        divFacs.forEach(div => {
                            const txt = div.innerText.trim();
                            if (txt.includes('m²')) {
                                size = txt;
                            } else {
                                facs.push(txt);
                            }
                        });
                    } else {
                        // Nếu đã tìm thấy size ở cách 1, thì vẫn phải loop qua divFacs để lấy tiện ích 
                        const divFacs = roomCell.querySelectorAll('.hprt-facilities-facility');
                        divFacs.forEach(div => {
                            const txt = div.innerText.trim();
                            if (!txt.includes('m²')) { // Tránh trùng lặp
                                facs.push(txt);
                            }
                        });
                    }

                    // Lấy các tiện ích dạng list (TV, Sofa...)
                    const liFacs = roomCell.querySelectorAll('.hprt-facilities-others li');
                    liFacs.forEach(li => {
                        facs.push(li.innerText.trim());
                    });

                    bestData = {
                        area: size,
                        facilities: facs.join(', ')
                    };
                    break; 
                }
            }
            return bestData;
        }""", target_room_type)
        
        return result

    except Exception as e:
        print(f"      ! Lỗi Scraping: {e}")
        return None
    
async def main():
    # 1. Kết nối Database
    engine = create_engine(DB_CONNECTION_STR)
    
    # --- TẠO BẢNG NẾU CHƯA TỒN TẠI ---
    print(f"--- ĐANG KIỂM TRA/TẠO BẢNG '{TARGET_TABLE}' ---")
    try:
        with engine.begin() as conn:
            conn.execute(text(CREATE_TABLE_SQL))
        print("--- ĐÃ KHỞI TẠO BẢNG THÀNH CÔNG ---")
    except Exception as e:
        print(f"Lỗi tạo bảng (Có thể bảng đã tồn tại constraint): {e}")
        # Không return mà cứ chạy tiếp, vì lỗi có thể do bảng đã có rồi
    
    async with async_playwright() as p:
        print(" KHỞI ĐỘNG BROWSER...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(locale="vi-VN")
        page = await context.new_page()

        while True:
            # --- QUERY THÔNG MINH ---
            # Chỉ lấy ID và Link từ Bảng 1 nếu ID đó chưa tồn tại trong Bảng 2
            sql_fetch = text(f"""
                SELECT t1.id, t1.hotel_link, t1.room_type
                FROM {SOURCE_TABLE} t1
                LEFT JOIN {TARGET_TABLE} t2 ON t1.id = t2.hotel_id
                WHERE t2.hotel_id IS NULL 
                  AND t1.hotel_link LIKE 'http%'
                LIMIT {BATCH_SIZE}
            """)
            
            with engine.connect() as conn:
                rows = conn.execute(sql_fetch).fetchall()

            if not rows:
                print("\n=== ĐÃ HOÀN TẤT: Tất cả dữ liệu đã được xử lý! ===")
                break

            print(f"\n>> Đang xử lý Batch: {len(rows)} dòng...")

            for row in rows:
                p_id = row[0]       # id của bảng 1
                link = row[1]       # link
                r_type = row[2]     # tên loại phòng cần tìm

                print(f" [ID: {p_id}] Tìm chi tiết cho: {r_type}")
                
                # Cào dữ liệu
                details = await scrape_detail_by_link(page, link, r_type)
                
                area = "N/A"
                facilities = "N/A"
                
                if details:
                    area = details['area']
                    facilities = details['facilities']
                    print(f"      + Tìm thấy: {area} | {facilities[:30]}...")
                else:
                    print("      ! Không tìm thấy (Sẽ lưu N/A để không quét lại).")

                # Lưu vào Bảng 2 (room_details)
                try:
                    with engine.begin() as insert_conn:
                        insert_sql = text(f"""
                            INSERT INTO {TARGET_TABLE} (hotel_id, area_m2, facilities)
                            VALUES (:hid, :area, :facs)
                        """)
                        insert_conn.execute(insert_sql, {
                            "hid": p_id,
                            "area": area,
                            "facs": facilities
                        })
                except Exception as e:
                    print(f"      ! Lỗi DB Insert: {e}")

                await asyncio.sleep(2) # Nghỉ nhẹ tránh block

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())