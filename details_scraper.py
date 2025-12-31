import asyncio
from playwright.async_api import async_playwright
from sqlalchemy import create_engine, text
import re

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

# --- CẤU HÌNH CÁC KHOẢNG ID MUỐN CHẠY ---
# Định dạng: (Từ ID, Đến ID)
ID_RANGES = [
    (2114, 8421)
]

async def scrape_detail_by_link(page, url, target_room_type):
    print(f"   -> Truy cập: {url[:60]}...")
    try:
        await page.route("**/*.{png,jpg,jpeg,gif,webp,svg}", lambda route: route.abort())
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        
        try:
            await page.wait_for_selector("#hprt-table", timeout=5000)
        except:
            print("      ! Không thấy bảng giá.")
            return None

        # --- BƯỚC 1: TÌM DÒNG CHỨA LOẠI PHÒNG ---
        target_row_selector = await page.evaluate(r"""(targetName) => {
            const rows = Array.from(document.querySelectorAll('#hprt-table tbody tr'));
            const clean = str => str ? str.toLowerCase().trim() : "";
            const tName = clean(targetName);

            for (let i = 0; i < rows.length; i++) {
                const nameEl = rows[i].querySelector('.hprt-table-cell-roomtype .hprt-roomtype-icon-link');
                if (nameEl) {
                    const rowName = clean(nameEl.innerText);
                    if (rowName.includes(tName) || tName.includes(rowName)) {
                        return `#hprt-table tbody tr:nth-child(${i + 1})`;
                    }
                }
            }
            return null;
        }""", target_room_type)

        if not target_row_selector:
            print(f"      ! Không tìm thấy dòng nào khớp với: {target_room_type}")
            return None

        target_row = page.locator(target_row_selector)

        # --- BƯỚC 2: TÌM DIỆN TÍCH Ở NGOÀI TRƯỚC ---
        area = "N/A"
        try:
            size_el = target_row.locator('[data-testid="rp-room-size"]')
            # Chờ nhẹ 0.5s để xem nó có hiện không
            try: await size_el.wait_for(state="attached", timeout=500)
            except: pass

            if await size_el.count() > 0:
                raw_text = await size_el.inner_text()
                match = re.search(r'(\d+)\s*(m²|m2)', raw_text, re.IGNORECASE)
                if match:
                    area = match.group(1) + " m²"
        except:
            pass

        # --- BƯỚC 3: XỬ LÝ CLICK MODAL ---
        facilities = "N/A"

        if area == "N/A": 
            print("      ... Đang click mở chi tiết phòng ...")
            clickable_link = target_row.locator('.hprt-roomtype-icon-link')
            
            try:
                await clickable_link.click()
                
                # 1. Chờ khung Modal hiện ra
                modal_selector = '.rt-lightbox-content, .hprt-lightbox, div[role="dialog"]'
                modal = page.locator(f"{modal_selector} >> visible=true").first
                await modal.wait_for(timeout=5000)
                
                # 2. QUAN TRỌNG: NGỦ 1.5 GIÂY ĐỂ DỮ LIỆU ĐƯỢC ĐIỀN VÀO MODAL
                # (Tránh trường hợp modal vừa hiện lên nhưng chữ chưa load xong)
                await asyncio.sleep(1.5)

                # 3. Cố gắng chờ thẻ diện tích cụ thể trong modal (nếu có)
                try:
                    modal_size_el = modal.locator('[data-testid="rp-room-size"]')
                    await modal_size_el.wait_for(timeout=2000) # Chờ tối đa 2s cho thẻ size hiện
                except:
                    pass

                # 4. TRÍCH XUẤT DỮ LIỆU VÀ LỌC RÁC
                data = await modal.evaluate(r"""(el) => {
                    const fullText = el.innerText;
                    
                    // --- TÌM DIỆN TÍCH ---
                    let areaVal = null;
                    // Ưu tiên tìm trong thẻ định danh
                    const specificSizeEl = el.querySelector('[data-testid="rp-room-size"]');
                    if (specificSizeEl) {
                         const m = specificSizeEl.innerText.match(/(\d+)\s*(m²|m2)/i);
                         if (m) areaVal = m[1] + " m²";
                    }
                    // Nếu không thấy, quét toàn bộ text
                    if (!areaVal) {
                        const mAll = fullText.match(/(\d+)\s*(m²|m2)/i);
                        if (mAll) areaVal = mAll[1] + " m²";
                    }

                    // --- LỌC TIỆN ÍCH ---
                    const lines = fullText.split('\n').map(l => l.trim());
                    const cleanLines = lines.filter(line => {
                        const l = line.toLowerCase();
                        if (l.length < 2) return false; 
                        
                        const badWords = [
                            'đóng', 'close', 
                            'bắt đầu nội dung', 'start of dialog', 
                            'kết thúc nội dung', 'end of dialog',
                            'hộp thoại', 'mô tả', 'description',
                            'diện tích', 'kích thước phòng', 'room size',
                            'trong phòng tắm riêng của bạn',
                            'tầm nhìn', 'hướng nhìn', 'views'
                        ];
                        
                        for (let bad of badWords) {
                            if (l.includes(bad)) return false;
                        }
                        return true;
                    });

                    // Lấy tối đa 500 ký tự tiện ích
                    const facStr = cleanLines.join(', ').substring(0, 500);
                    
                    return { area: areaVal, facilities: facStr };
                }""")
                
                area = data['area'] if data['area'] else "N/A"
                facilities = data['facilities']

                # Đóng modal
                try:
                    close_btn = modal.locator('button[aria-label="Close"], button.modal-close-button')
                    if await close_btn.count() > 0:
                        await close_btn.click()
                    else:
                        await page.keyboard.press('Escape')
                except:
                    pass
                    
            except Exception as e:
                pass
        
        else:
             # Logic lấy tiện ích ngay tại dòng (khi đã có diện tích bên ngoài)
            try:
                facilities = await target_row.evaluate(r"""(row) => {
                    let facs = [];
                    row.querySelectorAll('.hprt-facilities-facility').forEach(el => {
                        const t = el.innerText.trim();
                        if (t && !t.includes('m²') && !t.includes('m2')) facs.push(t);
                    });
                    row.querySelectorAll('.hprt-facilities-others li').forEach(el => {
                        const t = el.innerText.trim();
                        if (t) facs.push(t);
                    });
                    return facs.join(', ');
                }""")
            except:
                pass

        return {
            'area': area,
            'facilities': facilities
        }

    except Exception as e:
        print(f"      ! Lỗi Scraping tổng quát: {e}")
        return None

async def main():
    engine = create_engine(DB_CONNECTION_STR)

    print(f"-> Đang kiểm tra bảng '{TARGET_TABLE}'...")
    try:
        with engine.begin() as conn:
            # Tạo bảng với khóa chính là hotel_id (vì logic insert/update dựa trên ID này)
            create_table_sql = text(f"""
                CREATE TABLE IF NOT EXISTS {TARGET_TABLE} (
                    hotel_id INTEGER PRIMARY KEY,
                    area_m2 TEXT,
                    facilities TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute(create_table_sql)
            print(f"-> Bảng '{TARGET_TABLE}' đã sẵn sàng.")
    except Exception as e:
        print(f"!!! Lỗi khi tạo bảng: {e}")
        return
    
    async with async_playwright() as p:
        print(" KHỞI ĐỘNG BROWSER...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(locale="vi-VN")
        page = await context.new_page()

        print(f"\n>> Đang lấy dữ liệu cho các khoảng: {ID_RANGES} ...")
        
        # --- TẠO CÂU SQL ĐỘNG CHO NHIỀU KHOẢNG ---
        # Logic: WHERE (id BETWEEN x AND y) OR (id BETWEEN a AND b) ...
        where_clauses = []
        params = {}
        
        for i, (start, end) in enumerate(ID_RANGES):
            p_start = f"s{i}"
            p_end = f"e{i}"
            where_clauses.append(f"(id BETWEEN :{p_start} AND :{p_end})")
            params[p_start] = start
            params[p_end] = end
            
        where_sql = " OR ".join(where_clauses)
        
        full_sql = text(f"""
            SELECT id, hotel_link, room_type
            FROM {SOURCE_TABLE}
            WHERE ({where_sql})
              AND hotel_link LIKE 'http%'
            ORDER BY id ASC
        """)
        
        with engine.connect() as conn:
            rows = conn.execute(full_sql, params).fetchall()

        if not rows:
            print("!!! Không tìm thấy dữ liệu nào trong các khoảng ID này.")
            await browser.close()
            return

        print(f"-> Tổng cộng tìm thấy {len(rows)} khách sạn cần xử lý.")

        for row in rows:
            p_id = row[0]
            link = row[1]
            r_type = row[2]

            print(f" [ID: {p_id}] Xử lý chi tiết cho: {r_type}")
            
            # Cào dữ liệu
            details = await scrape_detail_by_link(page, link, r_type)
            
            area = "N/A"
            facilities = "N/A"
            
            if details:
                area = details['area']
                facilities = details['facilities']
                print(f"      + Tìm thấy: {area} | {facilities[:30]}...")
            else:
                print("      ! Không tìm thấy (Lưu N/A).")

            # --- LOGIC KIỂM TRA & UPDATE ---
            try:
                with engine.begin() as trans_conn:
                    # 1. Kiểm tra xem hotel_id này đã có trong bảng room_details chưa
                    check_sql = text(f"SELECT 1 FROM {TARGET_TABLE} WHERE hotel_id = :hid")
                    exists = trans_conn.execute(check_sql, {"hid": p_id}).scalar()

                    if exists:
                        # 2A. NẾU CÓ RỒI -> UPDATE
                        update_sql = text(f"""
                            UPDATE {TARGET_TABLE}
                            SET area_m2 = :area, 
                                facilities = :facs
                            WHERE hotel_id = :hid
                        """)
                        trans_conn.execute(update_sql, {
                            "hid": p_id,
                            "area": area,
                            "facs": facilities
                        })
                        print("      -> [UPDATE] Đã cập nhật dữ liệu cũ.")
                    else:
                        # 2B. NẾU CHƯA CÓ -> INSERT
                        insert_sql = text(f"""
                            INSERT INTO {TARGET_TABLE} (hotel_id, area_m2, facilities)
                            VALUES (:hid, :area, :facs)
                        """)
                        trans_conn.execute(insert_sql, {
                            "hid": p_id,
                            "area": area,
                            "facs": facilities
                        })
                        print("      -> [INSERT] Đã thêm mới.")
                        
            except Exception as e:
                print(f"      ! Lỗi DB Action: {e}")

            await asyncio.sleep(1) 

        print("\n=== HOÀN TẤT ===")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())