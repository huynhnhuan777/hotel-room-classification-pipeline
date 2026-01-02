import os, re, json, time, csv
from urllib.parse import urljoin, urlparse, urlunparse
from playwright.sync_api import sync_playwright

# CẤU HÌNH 

START_URL = "https://www.tripadvisor.com.vn/Hotels-g293925-Ho_Chi_Minh_City-Hotels.html"
OUT_CSV = "tripadvisor_hcm_hotels_list_link.csv"
STATE_FILE = "tripadvisor_state.json"

BASE = "https://www.tripadvisor.com.vn"
CDP_URL = "http://127.0.0.1:9222"

SCROLL_ROUNDS = 10
SLEEP_BETWEEN_PAGES = 3
MAX_PAGES = 250


# Chuẩn hóa URL khách sạn (loại bỏ query)
def canonicalize_url(url):
    if url.startswith("/"):
        url = urljoin(BASE, url)
    u = urlparse(url)
    return urlunparse((u.scheme, u.netloc, u.path, "", "", ""))

# Tạo link trang kế tiếp bằng offset -oa30-
def build_list_url(base, page):
    if page == 1:
        return base
    offset = (page - 1) * 30
    u = urlparse(base)
    path = re.sub(r"(Hotels-g\d+-)", rf"\1oa{offset}-", u.path)
    return urlunparse((u.scheme, u.netloc, path, "", "", ""))

# Click nút chấp nhận cookie nếu có
def accept_cookies(page):
    for sel in ["#onetrust-accept-btn-handler",
                "button:has-text('Accept')",
                "button:has-text('Đồng ý')"]:
        try:
            btn = page.locator(sel).first
            if btn.is_visible():
                btn.click()
                page.wait_for_timeout(1000)
                return
        except:
            pass

# Tự động scroll cho đến khi không load thêm khách sạn
def auto_scroll(page):
    last = 0
    for _ in range(SCROLL_ROUNDS):
        page.mouse.wheel(0, 2500)
        page.wait_for_timeout(800)
        cur = page.locator("a[href*='/Hotel_Review-']").count()
        if cur <= last:
            break
        last = cur

#  CSV + STATE 
def load_seen_urls():
    if not os.path.exists(OUT_CSV):
        return set()
    with open(OUT_CSV, "r", encoding="utf-8-sig") as f:
        return {r["hotel_url"] for r in csv.DictReader(f)}

def append_csv(rows):
    exist = os.path.exists(OUT_CSV)
    with open(OUT_CSV, "a", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["hotel_name", "hotel_url"])
        if not exist:
            w.writeheader()
        w.writerows(rows)

def load_state():
    if not os.path.exists(STATE_FILE):
        return 1
    return json.load(open(STATE_FILE))["next_page"]

def save_state(p):
    json.dump({"next_page": p}, open(STATE_FILE, "w"), indent=2)

# TRÍCH XUẤT 
def extract_hotels(page, seen):
    rows = []
    links = page.locator("a[href*='/Hotel_Review-'][href*='-Reviews-']")
    total = links.count()

    for i in range(total):
        try:
            a = links.nth(i)

            # Lấy text + href bằng JS để tránh lỗi DOM detach
            name = a.evaluate("el => el.innerText || ''").strip()
            href = a.evaluate("el => el.getAttribute('href') || ''")

            url = canonicalize_url(href)

            if len(name) < 3 or not url or url in seen:
                continue

            seen.add(url)
            rows.append({
                "hotel_name": name,
                "hotel_url": url
            })

        except Exception as e:
            print(f"[SKIP] link {i} bị lỗi DOM detach")
            continue

    return rows



def main():
    start_page = load_state()
    seen = load_seen_urls()

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = context.new_page()

        for pnum in range(start_page, MAX_PAGES + 1):
            url = build_list_url(START_URL, pnum)
            print(f"[PAGE {pnum}] {url}")

            page.goto(url, timeout=60000)
            page.wait_for_timeout(2000)
            accept_cookies(page)
            auto_scroll(page)

            rows = extract_hotels(page, seen)
            print("  + New:", len(rows))
            append_csv(rows)
            save_state(pnum + 1)
            time.sleep(SLEEP_BETWEEN_PAGES)

if __name__ == "__main__":
    main()
