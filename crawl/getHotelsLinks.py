import asyncio
import csv
from playwright.async_api import async_playwright

OUTPUT_FILE = "ivivu_multi_city.csv"

# ===== CITY URLS =====
CITY_URLS = {
    "Hồ Chí Minh": "https://www.ivivu.com/khach-san-ho-chi-minh",
    "Vũng Tàu": "https://www.ivivu.com/khach-san-vung-tau",
    "Bình Dương": "https://www.ivivu.com/khach-san-binh-duong",
}

# ===== SELECTORS =====
SEL_CARD = ".pdv__content-box"
SEL_NAME = ".pdv__hotel--name"
SEL_STAR = ".ivv-star-full-icon"
SEL_SCORE_NUM = ".rtb__point-number"
SEL_SCORE_TEXT = ".rtb__point-text"
SEL_SCORE_TOTAL = ".rtb__point-total-number"
SEL_ADDRESS = ".pdv__location-name"
SEL_LOAD_MORE = "button.rgc__view-more-btn"


def init_csv():
    with open(OUTPUT_FILE, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerow([
            "ID",
            "City",
            "Hotel Name",
            "Star",
            "Score",
            "Rating Text",
            "Number Rating",
            "Address",
            "Hotel Link"
        ])


async def crawl_city(page, city_name, url, start_id):
    seen_links = set()
    hotel_id = start_id

    print(f"\n🚀 BẮT ĐẦU CÀO: {city_name}")

    await page.goto(url, timeout=60000)
    await page.wait_for_timeout(5000)

    with open(OUTPUT_FILE, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)

        while True:
            cards = await page.locator(SEL_CARD).all()
            new_count = 0

            for card in cards:
                try:
                    link = await card.evaluate(
                        "el => el.closest('a') ? el.closest('a').href : ''"
                    )
                    if not link or link in seen_links:
                        continue

                    seen_links.add(link)

                    name = await card.locator(SEL_NAME).inner_text()
                    star = await card.locator(SEL_STAR).count()

                    score = await card.locator(SEL_SCORE_NUM).inner_text() \
                        if await card.locator(SEL_SCORE_NUM).count() else ""

                    rating_text = await card.locator(SEL_SCORE_TEXT).inner_text() \
                        if await card.locator(SEL_SCORE_TEXT).count() else ""

                    num_rating = 0
                    if await card.locator(SEL_SCORE_TOTAL).count():
                        raw = await card.locator(SEL_SCORE_TOTAL).inner_text()
                        num_rating = int(raw.strip().replace("(", "").replace(")", ""))

                    address = await card.locator(SEL_ADDRESS).get_attribute("title") \
                        if await card.locator(SEL_ADDRESS).count() else ""

                    writer.writerow([
                        f"IVU_{hotel_id:06d}",
                        city_name,
                        name.strip(),
                        star,
                        score.strip(),
                        rating_text.strip(),
                        num_rating,
                        address.strip() if address else "",
                        link
                    ])

                    hotel_id += 1
                    new_count += 1

                except Exception as e:
                    print("⚠️ Lỗi card:", e)
                    continue

            print(f"{city_name}: +{new_count} | Tổng: {len(seen_links)}")

            if new_count == 0:
                print(f">>> Hết khách sạn tại {city_name}")
                break

            if await page.locator(SEL_LOAD_MORE).count() == 0:
                print(">>> Không còn nút Xem thêm")
                break

            await page.locator(SEL_LOAD_MORE).click()
            await page.wait_for_timeout(7000)

    return hotel_id


async def main():
    init_csv()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(
            viewport={"width": 1280, "height": 900}
        )

        hotel_id = 1
        for city, url in CITY_URLS.items():
            hotel_id = await crawl_city(page, city, url, hotel_id)

        await browser.close()
        print("\n✅ CÀO XONG TẤT CẢ CITY")


if __name__ == "__main__":
    asyncio.run(main())
