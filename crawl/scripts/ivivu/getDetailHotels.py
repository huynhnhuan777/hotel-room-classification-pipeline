import asyncio
import csv
from statistics import mean
from playwright.async_api import async_playwright, TimeoutError

# ================= CONFIG =================
CITY_URL = "https://www.ivivu.com/khach-san-ho-chi-minh"
HOTEL_CSV = "ivivu_hotels.csv"
ROOM_CSV = "ivivu_rooms.csv"

SEL_CARD = ".pdv__content-box"
SEL_LOAD_MORE = "button.rgc__view-more-btn"
NO_ROOM_TEXT = "Rất tiếc, iVIVU không còn phòng"

# Số tab xử lý song song (QUAN TRỌNG NHẤT)
MAX_CONCURRENT_TABS = 4

# ================= INIT CSV =================
def init_csv():
    with open(HOTEL_CSV, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerow([
            "hotel_id", "hotel_name", "hotel_link"
        ])
    with open(ROOM_CSV, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerow([
            "room_id", "hotel_id", "room_name", "price",
            "area_m2", "bed_type", "max_occupancy",
            "view", "amenities"
        ])

# ================= UTILS =================
def clean_price(p):
    p = p.replace(".", "").strip()
    return int(p) if p.isdigit() else None

# ================= SCRAPE ROOMS (TỐI ƯU) =================
async def scrape_rooms(context, hotel_id, hotel_name, hotel_link, start_room_id):
    rows = []
    room_id = start_room_id
    page = await context.new_page()

    print(f"      → Mở trang phòng: {hotel_name}")

    try:
        await page.goto(hotel_link, timeout=60000)
        await page.wait_for_timeout(3000)

        # Scroll để load hết - GIỮ NGUYÊN
        for _ in range(6):
            await page.mouse.wheel(0, 1200)
            await page.wait_for_timeout(600)

        if NO_ROOM_TEXT in await page.content():
            print("      ⚠️ Không có phòng → đóng tab")
            await page.close()
            return rows, room_id

        room_blocks = page.locator("div[id^='room-class-']")
        total_rooms = await room_blocks.count()
        
        if total_rooms == 0:
            await page.close()
            return rows, room_id
            
        print(f"      🔍 {total_rooms} phòng")

        # ===== TỐI ƯU: Lấy tất cả giá trong 1 lần evaluate =====
        all_prices = await page.evaluate("""
            () => {
                const blocks = document.querySelectorAll("div[id^='room-class-']");
                const result = [];
                
                blocks.forEach(block => {
                    const prices = [];
                    
                    // Thử OTA trước
                    const otaPrices = block.querySelectorAll('.rcct__price--ota-text');
                    if (otaPrices.length > 0) {
                        otaPrices.forEach(p => {
                            const text = p.innerText.replace(/\\./g, '').trim();
                            if (/^\\d+$/.test(text)) {
                                prices.push(parseInt(text));
                            }
                        });
                    } else {
                        // Không có OTA thì lấy TA
                        const taPrices = block.querySelectorAll('.rcct__price--ta-text');
                        taPrices.forEach(p => {
                            const text = p.innerText.replace(/\\./g, '').trim();
                            if (/^\\d+$/.test(text)) {
                                prices.push(parseInt(text));
                            }
                        });
                    }
                    
                    if (prices.length > 0) {
                        const avgPrice = Math.floor(prices.reduce((a,b) => a+b, 0) / prices.length);
                        result.push(avgPrice);
                    } else {
                        result.push(null);
                    }
                });
                
                return result;
            }
        """)

        # Xử lý từng phòng
        for i in range(total_rooms):
            price = all_prices[i]
            if price is None:
                continue

            block = room_blocks.nth(i)

            # ===== CLICK XEM CHI TIẾT =====
            try:
                btn = block.locator("span:has-text('Xem chi tiết')").first
                await btn.scroll_into_view_if_needed()
                await btn.click()
            except:
                continue

            # ===== MODAL =====
            try:
                modal = page.locator(".rtod__container")
                await modal.wait_for(timeout=15000)

                # TỐI ƯU: Lấy tất cả data modal trong 1 lần
                data = await modal.evaluate("""
                    () => {
                        const name = document.querySelector(
                          '.rcid__right--text__room-name'
                        )?.innerText || '';

                        let area='', view='', bed='';
                        const amenities=[];

                        document.querySelectorAll('.fal__facilities--item').forEach(i=>{
                            const t=i.innerText.toLowerCase();
                            amenities.push(i.innerText);
                            if(t.includes('m²')) area=i.innerText;
                            if(t.includes('hướng')) view=i.innerText;
                            if(t.includes('giường')) bed=i.innerText;
                        });

                        let maxOcc='';
                        const pax=document.querySelector('.pxn__col-1--title-html');
                        if(pax){
                            const m=pax.innerText.match(/(\\d+)/);
                            if(m) maxOcc=m[1];
                        }

                        return {name, area, bed, view, maxOcc, amenities: amenities.join('; ')};
                    }
                """)

                rows.append([
                    f"ROOM_{room_id:06d}",
                    hotel_id,
                    data["name"],
                    price,
                    data["area"],
                    data["bed"],
                    data["maxOcc"],
                    data["view"],
                    data["amenities"]
                ])
                room_id += 1

                await page.locator(".rtod__header--close-icon").click()
                await page.wait_for_timeout(400)

            except TimeoutError:
                print("      ❌ Modal lỗi → skip phòng")
                try:
                    await page.keyboard.press("Escape")
                except:
                    pass

        print(f"      ✅ Lấy {len(rows)} phòng")

    except Exception as e:
        print(f"      ❌ Lỗi: {e}")

    await page.close()
    return rows, room_id

# ================= XỬ LÝ SONG SONG =================
async def process_hotels_parallel(context, hotels_info, start_hotel_id, start_room_id):
    """Xử lý nhiều hotel đồng thời"""
    
    # Write tất cả hotel info trước
    with open(HOTEL_CSV, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        for idx, (name, link) in enumerate(hotels_info):
            hid = f"IVU_{start_hotel_id + idx:06d}"
            writer.writerow([hid, name, link])
    
    # Tạo tasks song song
    tasks = []
    for idx, (name, link) in enumerate(hotels_info):
        hid = f"IVU_{start_hotel_id + idx:06d}"
        # Mỗi hotel có room_id riêng để tránh conflict
        task_room_id = start_room_id + (idx * 1000)  # Reserve 1000 IDs per hotel
        tasks.append(scrape_rooms(context, hid, name, link, task_room_id))
    
    # Chạy song song
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Ghi rooms và tính room_id cuối cùng
    max_room_id = start_room_id
    for result in results:
        if isinstance(result, Exception):
            print(f"      ⚠️ Lỗi khi xử lý: {result}")
            continue
        rows, last_room_id = result
        if rows:
            with open(ROOM_CSV, "a", encoding="utf-8-sig", newline="") as f:
                csv.writer(f).writerows(rows)
            max_room_id = max(max_room_id, last_room_id)
    
    return start_hotel_id + len(hotels_info), max_room_id

# ================= MAIN =================
async def main():
    init_csv()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage"
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"
        )

        # Block images để tải nhanh hơn
        await context.route("**/*.{png,jpg,jpeg,webp,svg,gif}", lambda r: r.abort())

        page = await context.new_page()
        await page.goto(CITY_URL, timeout=60000)
        await page.wait_for_selector(SEL_CARD)

        hotel_id = 1
        room_id = 1
        processed = 0

        while True:
            cards = page.locator(SEL_CARD)
            total = await cards.count()

            # Thu thập thông tin hotels trong batch
            hotels_batch = []
            for i in range(processed, total):
                card = cards.nth(i)
                await card.scroll_into_view_if_needed()
                await asyncio.sleep(0.4)

                name = await card.locator(".pdv__hotel--name").inner_text()
                link = await card.evaluate("el => el.closest('a')?.href || ''")
                
                if link:
                    hotels_batch.append((name, link))
                    print(f"\n🏨 [{hotel_id + len(hotels_batch) - 1}] {name}")

            # Xử lý theo batch song song
            if hotels_batch:
                for i in range(0, len(hotels_batch), MAX_CONCURRENT_TABS):
                    batch = hotels_batch[i:i + MAX_CONCURRENT_TABS]
                    print(f"\n⚡ Xử lý {len(batch)} hotels song song...")
                    hotel_id, room_id = await process_hotels_parallel(
                        context, batch, hotel_id, room_id
                    )

            processed = total

            # Check load more
            if await page.locator(SEL_LOAD_MORE).count() == 0:
                break

            await page.locator(SEL_LOAD_MORE).click()
            await page.wait_for_timeout(1500)

        await browser.close()
        print("\n🎉 HOÀN THÀNH – GIÁ BẮT BUỘC, OTA → TA → TRUNG BÌNH")

if __name__ == "__main__":
    asyncio.run(main())