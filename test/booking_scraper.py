import asyncio
import pandas as pd
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
import os
import random
import math
import json
from sqlalchemy import create_engine, text

# --- CẤU HÌNH DATABASE ---
DB_CONFIG = {
    "dbname": "booking_data",  
    "user": "postgres",         
    "password": "123456",  
    "host": "localhost",          
    "port": "5432"             
}

# Tạo chuỗi kết nối
DB_CONNECTION_STR = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

# --- CẤU HÌNH SCRAPING ---
TABLE_NAME = "hotel_scenarios_test" 
BASE_URL = "https://www.booking.com/searchresults.vi.html"
LOCATIONS = {
    "Ho Chi Minh": "Thành+phố+Hồ+Chí+Minh",
    "Vung Tau": "Vũng+Tàu",
    "Binh Duong": "Bình+Dương"
}
# --- CẤU TRÚC BẢNG SQL ---
CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id SERIAL PRIMARY KEY,
    search_location VARCHAR(100),
    scenario VARCHAR(255),
    hotel_name TEXT,
    hotel_link TEXT,
    stars REAL,
    final_price BIGINT,
    original_price BIGINT,
    rating_score REAL,
    review_count REAL,
    location_score REAL,
    address TEXT,
    distance TEXT,
    room_type TEXT,
    bed_type TEXT,
    free_cancellation VARCHAR(50),
    breakfast_included VARCHAR(50),
    badge_deal TEXT,
    check_in DATE,
    adults INTEGER,
    children INTEGER,
    rooms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def generate_random_config():
    # 1. Random số người lớn (1 đến 6 người)
    # Dùng weights để ưu tiên 2 người (cặp đôi) xuất hiện nhiều hơn
    adults = random.choices([1, 2, 3, 4, 5, 6], weights=[20, 40, 10, 10, 10, 10], k=1)[0]

    # 2. Random số trẻ em (0 đến 4 bé)
    # 60% tỉ lệ là không có trẻ em, 40% là có
    has_children = random.choices([True, False], weights=[40, 60], k=1)[0]
    
    children = 0
    ages = []
    
    if has_children:
        children = random.randint(1, 3) # Random 1-3 bé
        # Random tuổi từ 0 (sơ sinh) đến 17 tuổi
        ages = [random.randint(0, 17) for _ in range(children)]

    # 3. Tính toán số phòng hợp lý 
    total_people = adults + children
    
    # Giả sử 1 phòng chứa tối đa 4 người (để tránh book 1 phòng cho 10 người)
    min_rooms_needed = math.ceil(total_people / 4)
    
    # Số phòng tối đa thường không vượt quá số người lớn (để mỗi phòng có 1 người lớn đứng tên)
    max_rooms_allowed = adults
    
    # Đảm bảo min <= max
    if min_rooms_needed > max_rooms_allowed:
        min_rooms_needed = max_rooms_allowed

    # Random số phòng trong khoảng hợp lý
    rooms = random.randint(min_rooms_needed, max_rooms_allowed)

    # 4. Tạo tên gợi nhớ để log
    name_str = f"Random_{adults}A_{children}C_{rooms}R"
    if children > 0:
        ages_str = "_".join(map(str, ages))
        name_str += f"_Ages({ages_str})"

    return {
        "name": name_str,
        "adults": adults,
        "children": children,
        "ages": ages,
        "rooms": rooms
    }

# Tạo danh sách 20 kịch bản ngẫu nhiên
RANDOM_CONFIGS = [generate_random_config() for _ in range(1)]

# In ra kiểm tra
import json
print(json.dumps(RANDOM_CONFIGS, indent=2))

async def scrape_detailed_data(page, checkin, checkout, config, location_name, location_query):
    # 1. Tạo URL
    url = f"{BASE_URL}?ss={location_query}&checkin={checkin}&checkout={checkout}"
    url += f"&group_adults={config['adults']}&no_rooms={config['rooms']}&group_children={config['children']}"
    for age in config['ages']:
        url += f"&age={age}"

    print(f"\n >> [Scenario: {config['name']}] Truy cập Booking...")
    
    try:
        await page.goto(url, timeout=60000)
        
        # --- XỬ LÝ POPUP ---
        await asyncio.sleep(15)
        try: await page.keyboard.press("Escape")
        except: pass
        try:
            close_btn = page.locator('button[aria-label="Bỏ qua thông tin đăng nhập"], button[aria-label="Đóng"]')
            if await close_btn.count() > 0: await close_btn.first.click()
        except: pass

        # --- GIAI ĐOẠN 1: SCROLL & LOAD MORE ---
        print("    -> Bắt đầu quy trình mở rộng danh sách...")
        click_count = 0
        max_clicks = 3
        
        while click_count < max_clicks:
            last_height = await page.evaluate("document.body.scrollHeight")
            scroll_retries = 0
            
            while True:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                
                load_more_btn = page.locator('button:has-text("Load more results"), button:has-text("Hiển thị thêm kết quả"), button:has-text("Tải thêm kết quả")').first
                if await load_more_btn.count() > 0 and await load_more_btn.is_visible():
                    break
                
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    scroll_retries += 1
                    if scroll_retries >= 3: break
                else:
                    scroll_retries = 0
                    last_height = new_height

            load_more_btn = page.locator('button:has-text("Load more results"), button:has-text("Hiển thị thêm kết quả"), button:has-text("Tải thêm kết quả")').first
            
            if await load_more_btn.count() > 0 and await load_more_btn.is_visible():
                try:
                    await load_more_btn.scroll_into_view_if_needed()
                    await load_more_btn.click()
                    click_count += 1
                    print(f"       + [Click {click_count}] Đã bấm nút. Đang chờ 10s...")
                    await asyncio.sleep(10) 
                except Exception as e:
                    print(f"       ! Lỗi bấm nút: {e}")
                    await asyncio.sleep(2)
            else:
                print("    -> Không còn nút 'Hiển thị thêm'. Đã tải hết danh sách.")
                break
        
        # --- GIAI ĐOẠN 2: TRÍCH XUẤT SIÊU TỐC BẰNG JAVASCRIPT ---
        print("    -> Bắt đầu trích xuất dữ liệu (Chế độ JS Fast Mode)...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(3)

        # SỬ DỤNG r""" ĐỂ TRÁNH LỖI CÚ PHÁP REGEX VÀ STRING
        raw_data = await page.evaluate(r"""() => {
            const items = [];
            const cards = document.querySelectorAll('div[data-testid="property-card"]');
            
            cards.forEach(card => {
                let info = {};
                
                // 1. Name
                const titleEl = card.querySelector('div[data-testid="title"]');
                info['Hotel Name'] = titleEl ? titleEl.innerText : "N/A";
                
                // === LẤY LINK KHÁCH SẠN ===
                const linkEl = card.querySelector('a[data-testid="title-link"]');
                // Lấy href absolute (đầy đủ)
                info['Hotel Link'] = linkEl ? linkEl.href : "N/A";
                
               // 2. Stars 
                let stars = 0;
                // Gom chung container lại để xử lý gọn hơn
                const starContainer = card.querySelector('div[data-testid="rating-stars"]') || 
                                      card.querySelector('div[data-testid="rating-squares"]');

                if (starContainer) {
                    // --- CÁCH 1: Ưu tiên tuyệt đối lấy từ aria-label (Chính xác 100%) ---
                    // Ví dụ aria-label="5 out of 5 stars" hoặc "5 sao"
                    const label = starContainer.getAttribute('aria-label');
                    if (label) {
                        const match = label.match(/^(\d+)/); // Lấy số đầu tiên tìm thấy
                        if (match) stars = parseInt(match[1]);
                    }

                    // --- CÁCH 2: Nếu không có aria-label thì mới đếm SVG ---
                    if (stars === 0) {
                        const svgCount = starContainer.querySelectorAll('svg').length;
                            stars = svgCount / 2; 
                    }
                }

                // --- CÁCH 3: Quét text div ảo ---
                if (stars === 0) {
                    const ratingDiv = card.querySelector('div[aria-label*="sao"], div[aria-label*="star"]');
                    if (ratingDiv) {
                        const label = ratingDiv.getAttribute('aria-label');
                        const match = label.match(/(\d+)/);
                        if (match) stars = parseInt(match[1]);
                    }
                }

                info['Stars'] = stars > 0 ? stars : "N/A";

                // === 3. Price Processing ===
                let finalPriceStr = "0";
                let originalPriceStr = "0";

                const getNumber = (str) => {
                    if (!str) return 0;
                    // Chỉ giữ lại số, loại bỏ chữ và ký tự đặc biệt
                    const numStr = str.replace(/\D/g, ''); 
                    return numStr ? parseInt(numStr) : 0;
                };

                // --- CÁCH 1: Quét Text ẩn ---
                //  Dùng 'textContent' để đọc được cả text bị ẩn
                const invisibleTextEl = Array.from(card.querySelectorAll('div')).find(el => 
                    el.textContent.includes('Original price') && el.textContent.includes('Current price')
                );

                if (invisibleTextEl) {
                    const text = invisibleTextEl.textContent;
                    const matches = text.match(/[\d,.]+/g); // Tìm các cụm số
                    if (matches && matches.length >= 2) {
                        const nums = matches.map(m => getNumber(m));
                        originalPriceStr = Math.max(...nums).toString(); // Số lớn nhất là giá gốc
                        finalPriceStr = Math.min(...nums).toString();    // Số nhỏ nhất là giá cuối
                    }
                }

                // --- CÁCH 2: Fallback dựa vào vị trí DOM ---
                // Chỉ chạy nếu chưa lấy được giá gốc hoặc giá gốc đang bằng 0
                if (originalPriceStr === "0" || originalPriceStr === finalPriceStr) {
                    
                    // A. Xác định giá cuối trước
                    const finalPriceEl = card.querySelector('[data-testid="price-and-discounted-price"]');
                    
                    if (finalPriceEl) {
                        const currentVal = getNumber(finalPriceEl.innerText);
                        finalPriceStr = currentVal.toString();

                        // B. Tìm giá gốc dựa vào vị trí tương đối trong ảnh DOM
                        // Bước 1: Tìm lên thẻ cha <div> chứa giá cuối
                        const parentDiv = finalPriceEl.closest('div');
                        
                        // Bước 2: Tìm thẻ <span> nằm ngay trước thẻ cha đó
                        if (parentDiv && parentDiv.previousElementSibling) {
                            const sibling = parentDiv.previousElementSibling;
                            if (sibling.tagName === 'SPAN') {
                                const siblingVal = getNumber(sibling.innerText);
                                // Chỉ nhận nếu nó lớn hơn giá cuối
                                if (siblingVal > currentVal) {
                                    originalPriceStr = siblingVal.toString();
                                }
                            }
                        }
                        
                        // Bước 3: Quét tất cả thẻ span có aria-hidden="true"
                        if (originalPriceStr === "0") {
                            const potentialSpans = card.querySelectorAll('span[aria-hidden="true"]');
                            for (const span of potentialSpans) {
                                const val = getNumber(span.innerText);
                                // Nếu tìm thấy số nào lớn hơn giá cuối thì khả năng cao là giá gốc
                                if (val > currentVal) {
                                    originalPriceStr = val.toString();
                                    break; 
                                }
                            }
                        }
                    }
                }

                // --- C. Safety Check & Finalize ---
                let fVal = parseInt(finalPriceStr);
                let oVal = parseInt(originalPriceStr);

                // Nếu vẫn không tìm được giá gốc thì chấp nhận nó bằng giá cuối
                if (oVal === 0) oVal = fVal;
                // Đảm bảo logic: Giá gốc không được nhỏ hơn giá bán
                if (oVal < fVal) oVal = fVal;

                info['Final Price'] = fVal.toString();
                info['Original Price'] = oVal.toString();
                
                // === 4. Rating ===
                let ratingScore = "N/A";
                const scoreCard = card.querySelector('[data-testid="review-score"] div[aria-hidden="true"]') || 
                                  card.querySelector('[data-testid="review-score"] div:first-child') ||
                                  card.querySelector('.ac4a7896c7');

                if (scoreCard) {
                    let rawScore = scoreCard.innerText.trim();
                    rawScore = rawScore.replace(',', '.'); // Xử lý dấu phẩy
                    const match = rawScore.match(/(\d+(\.\d+)?)/);
                    if (match) ratingScore = match[0];
                }
                info['Rating Score'] = ratingScore;
                
                // === Review Count (Xử lý dấu chấm hàng nghìn) ===
                let reviewCount = "N/A";
                const reviewTextEl = card.querySelector('[data-testid="review-score"] div:last-child') ||
                                     card.querySelector('[data-testid="review-score"]');
                if (reviewTextEl) {
                    const rText = reviewTextEl.innerText.replace(/\./g, ''); // Bỏ dấu chấm (1.200 -> 1200)
                    const match = rText.match(/(\d+)\s*(reviews|đánh giá)/i);
                    if (match) reviewCount = match[1];
                }
                info['Review Count'] = reviewCount;

                // === 5. LOCATION SCORE ===
                let locScore = "N/A";
                const secondaryScore = card.querySelector('[data-testid="secondary-review-score-link"]');
                
                // Tìm text theo từ khóa nếu không có selector ID
                const locationTextElement = Array.from(card.querySelectorAll('span, div')).find(el => 
                    (el.innerText.includes('Location') || el.innerText.includes('Địa điểm')) && 
                    /\d+[.,]\d+/.test(el.innerText)
                );

                let locRaw = "";
                if (secondaryScore) {
                    locRaw = secondaryScore.innerText;
                } else if (locationTextElement) {
                    locRaw = locationTextElement.innerText;
                }

                if (locRaw) {
                    locRaw = locRaw.replace(',', '.'); // Xử lý dấu phẩy
                    const match = locRaw.match(/(\d+(\.\d+)?)/); 
                    if (match && parseFloat(match[0]) <= 10) {
                        locScore = match[0];
                    }
                }
                info['Location Score'] = locScore;

                const addrEl = card.querySelector('span[data-testid="address"]');
                info['Address'] = addrEl ? addrEl.innerText : "N/A";
                const distEl = card.querySelector('span[data-testid="distance"]');
                info['Distance'] = distEl ? distEl.innerText : "N/A";

                // Tìm h4 có role="link" (theo ảnh) hoặc h4 bất kỳ trong phần thông tin
                const roomEl = card.querySelector('h4[role="link"]') || card.querySelector('h4');
                info['Room Type'] = roomEl ? roomEl.innerText : "N/A";
                
                const unitEl = card.querySelector('div[data-testid="recommended-units"]');
                let bedTxt = "N/A";
                if (unitEl) {
                    // Dùng regex split để an toàn hơn với Raw String
                    const lines = unitEl.innerText.split(/\n/);
                    for (let line of lines) {
                        if (line.toLowerCase().includes('bed') || line.toLowerCase().includes('giường')) {
                            bedTxt = line;
                            break;
                        }
                    }
                }
                info['Bed Type'] = bedTxt;

                const cardText = (card.innerText || "").toLowerCase();
                
                const hasCancel = cardText.includes('free cancellation') || 
                                  cardText.includes('miễn phí hủy') || 
                                  cardText.includes('hủy miễn phí');
                info['Free Cancellation'] = hasCancel ? "Yes" : "No";

                let hasBreakfast = false;
                const bfCandidates = card.querySelectorAll('span, li, div');
                for (let el of bfCandidates) {
                    const t = (el.textContent || "").toLowerCase().trim();
                    if (t.includes('breakfast included') || t.includes('bao gồm bữa sáng') ||
                        t.includes('bữa sáng miễn phí') || t.includes('ăn sáng miễn phí')) {
                        hasBreakfast = true;
                        break;
                    }
                }

                if (!hasBreakfast) {
                    const unitInfo = card.querySelector('[data-testid="recommended-units"]');
                    if (unitInfo) {
                        const uText = unitInfo.innerText.toLowerCase();
                        if (uText.includes('breakfast') || uText.includes('bữa sáng')) {
                            hasBreakfast = true;
                        }
                    }
                }
                info['Breakfast Included'] = hasBreakfast ? "Yes" : "No";
                
                let badgeText = "None";
                const dealBadge = card.querySelector('[data-testid="property-card-deal"]');
                if (dealBadge) {
                    badgeText = dealBadge.innerText.trim();
                } else {
                    const normalBadge = card.querySelector('[data-testid="badge"]');
                    if (normalBadge) {
                        badgeText = normalBadge.innerText.trim();
                    }
                }
                info['Badge Deal'] = badgeText;

                items.push(info);
            });
            return items;
        }""")

        print(f"       Đã trích xuất xong {len(raw_data)} dòng dữ liệu từ JS.")

        # Xử lý lại dữ liệu 
        all_hotels_data = []
        for item in raw_data:
            try: f_price = int(item['Final Price'])
            except: f_price = 0
            try: o_price = int(item['Original Price'])
            except: o_price = f_price
            
            if o_price < f_price and o_price > 0:
                o_price, f_price = f_price, o_price
            elif o_price == 0:
                o_price = f_price

            final_item = {
                "Scenario": config['name'],
                "search_location": location_name,
                "Check-in": checkin,
                "Check-out": checkout,
                "Adults": config['adults'],
                "Children": config['children'],
                "Rooms": config['rooms'],
                "Source": "Booking.com",
                **item,
                "Final Price": f_price,
                "Original Price": o_price
            }
            all_hotels_data.append(final_item)

        return all_hotels_data

    except Exception as e:
        print(f"    Lỗi hệ thống: {e}")
        import traceback
        traceback.print_exc()
        return []
    
async def main():
    # 1. Khởi tạo Engine Database
    print(" Đang kết nối Database Postgres...")
    try:
        engine = create_engine(DB_CONNECTION_STR)
        
        with engine.connect() as conn:
            # DROP table cũ
            print(f"   Đang xóa bảng cũ '{TABLE_NAME}' (nếu có) để cập nhật cấu trúc mới...")
            conn.execute(text(f"DROP TABLE IF EXISTS {TABLE_NAME};"))
            
            print("   Đang tạo bảng mới...")
            conn.execute(text(CREATE_TABLE_SQL))
            conn.commit()
            print("   Đã chuẩn bị Database xong!")

    except Exception as e:
        print(f" Lỗi kết nối/xóa Database: {e}")
        return

    async with async_playwright() as p:
        print(" KHỞI ĐỘNG TRÌNH DUYỆT...")
        
        tomorrow = datetime.now() + timedelta(days=5)
        next_day = tomorrow + timedelta(days=5)
        c_in = tomorrow.strftime("%Y-%m-%d")
        c_out = next_day.strftime("%Y-%m-%d")
        
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1366, 'height': 768}, locale="vi-VN")
        page = await context.new_page()

        for loc_name, loc_query in LOCATIONS.items():
            print(f"\n==========================================")
            print(f" BẮT ĐẦU CÀO DỮ LIỆU TẠI: {loc_name.upper()}")
            print(f"==========================================")
            
            for config in RANDOM_CONFIGS:
                # Truyền thêm tham số location vào hàm cào
                data = await scrape_detailed_data(page, c_in, c_out, config, loc_name, loc_query)
                
                if data:
                    df = pd.DataFrame(data)
                    
                    # Danh sách cột
                    cols = ["search_location", "Scenario", "Hotel Name", "Hotel Link", "Stars", "Final Price", "Original Price", 
                            "Rating Score", "Review Count", "Location Score", 
                            "Address", "Distance", "Room Type", "Bed Type", 
                            "Free Cancellation", "Breakfast Included", "Badge Deal",
                            "Check-in", "Adults", "Children", "Rooms"]
                    
                    existing_cols = [c for c in cols if c in df.columns]
                    df = df[existing_cols]

                    numeric_cols = ["Stars", "Rating Score", "Review Count", "Location Score"]
                    for col in numeric_cols:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')

                    rename_map = {
                        "search_location": "search_location",
                        "Scenario": "scenario",
                        "Hotel Name": "hotel_name",
                        "Hotel Link": "hotel_link",
                        "Stars": "stars",
                        "Final Price": "final_price",
                        "Original Price": "original_price",
                        "Rating Score": "rating_score",
                        "Review Count": "review_count",
                        "Location Score": "location_score",
                        "Address": "address",
                        "Distance": "distance",
                        "Room Type": "room_type",
                        "Bed Type": "bed_type",
                        "Free Cancellation": "free_cancellation",
                        "Breakfast Included": "breakfast_included",
                        "Badge Deal": "badge_deal",
                        "Check-in": "check_in",
                        "Adults": "adults",
                        "Children": "children",
                        "Rooms": "rooms"
                    }
                    df = df.rename(columns=rename_map)

                    try:
                        df.to_sql(TABLE_NAME, engine, if_exists='append', index=False)
                        print(f"    ->  Đã lưu {len(data)} dòng của {loc_name} vào Database.")
                    except Exception as e:
                        print(f"    ->  Lỗi lưu Database: {e}")
                
                await asyncio.sleep(2) 

        await browser.close()
        print(f"\n HOÀN TẤT TOÀN BỘ QUÁ TRÌNH CÀO DỮ LIỆU!")

if __name__ == "__main__":
    asyncio.run(main())