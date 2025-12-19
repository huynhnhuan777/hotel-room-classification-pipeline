import os
import re
import json
import math
import time
import csv
from urllib.parse import urljoin, urlparse, urlunparse

from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

START_URL = "https://www.tripadvisor.com.vn/Hotels-g293925-Ho_Chi_Minh_City-Hotels.html"
OUT_CSV = "tripadvisor_hcm_hotels_list.csv"
STATE_FILE = "tripadvisor_state.json"
DEBUG_DIR = "debug"

BATCH_PAGES = 20                
SCROLL_ROUNDS = 12
SLEEP_BETWEEN_PAGES = 3     

MAX_PAGES_FALLBACK = 252         

BASE = "https://www.tripadvisor.com.vn"

USE_CDP = True
CDP_URL = "http://127.0.0.1:9222"
HEADLESS = False  


RATING_REV_RE = re.compile(
    r"(?<![\d#])([0-5](?:[.,]\d)?)\s*\(\s*([\d\.,]+)\s*(đánh\s*giá|reviews)\b",
    re.IGNORECASE
)


REV_ONLY_RE = re.compile(r"(?<!\d)([\d\.,]+)\s*(đánh\s*giá|reviews)\b", re.IGNORECASE)

PRICE_RE_1 = re.compile(r"(?<!\d)([\d\.,]{4,})\s*đ\b", re.IGNORECASE)
PRICE_RE_2 = re.compile(r"₫\s*([\d\.,]{4,})", re.IGNORECASE)
PRICE_RE_3 = re.compile(r"(?<!\d)([\d\.,]{4,})\s*VND\b", re.IGNORECASE)


def canonicalize_url(url: str) -> str:
    """Bỏ query (?spAttributionToken=...) và fragment"""
    if not url:
        return ""
    if url.startswith("/"):
        url = urljoin(BASE, url)
    u = urlparse(url)
    clean = urlunparse((u.scheme, u.netloc, u.path, "", "", ""))
    m = re.search(r"^(.*?\.html)", clean)
    return m.group(1) if m else clean


def build_list_url_with_offset(base_url: str, offset: int) -> str:
    """
    Hotels-g293925-Ho_Chi_Minh_City-Hotels.html
    -> Hotels-g293925-oa30-Ho_Chi_Minh_City-Hotels.html
    """
    u = urlparse(base_url)
    path = u.path
    if re.search(r"-oa\d+-", path):
        path = re.sub(r"-oa\d+-", f"-oa{offset}-", path)
    else:
        path = re.sub(r"(Hotels-g\d+-)", rf"\1oa{offset}-", path)
    return urlunparse((u.scheme, u.netloc, path, "", "", ""))


def accept_cookies_if_any(page):
    candidates = [
        "#onetrust-accept-btn-handler",
        "button:has-text('Accept')",
        "button:has-text('I accept')",
        "button:has-text('Đồng ý')",
        "button:has-text('Chấp nhận')",
    ]
    for sel in candidates:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible():
                loc.click(timeout=2000)
                page.wait_for_timeout(700)
                return
        except Exception:
            pass


def is_block_or_verify(page) -> bool:
    """
    Chỉ coi là block nếu:
    - Không có (hoặc rất ít) link hotel card trên DOM
    - Và HTML có dấu hiệu challenge/captcha/denied rõ ràng
    """
    hotel_sel = "a[href*='/Hotel_Review-'][href*='-Reviews-']"
    try:
        # Nếu có nhiều hotel link thì KHÔNG block 
        if page.locator(hotel_sel).count() >= 5:
            return False
    except Exception:
        pass

    txt = (page.content() or "").lower()

    hard_signs = [
        "captcha", "hcaptcha", "recaptcha", "arkose", "funcaptcha",
        "challenge-platform", "cf-chl", "cloudflare",
        "verify you are", "unusual traffic", "access denied",
        "temporarily blocked", "suspicious", "robot",
        "xác minh", "không phải robot", "truy cập bị từ chối"
    ]
    return any(s in txt for s in hard_signs)


def save_debug(page, name: str):
    os.makedirs(DEBUG_DIR, exist_ok=True)
    html_path = os.path.join(DEBUG_DIR, f"{name}.html")
    png_path = os.path.join(DEBUG_DIR, f"{name}.png")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(page.content() or "")
    try:
        page.screenshot(path=png_path, full_page=True)
    except Exception:
        pass
    print(f"[DEBUG] saved: {html_path} (+ png nếu được)")


def auto_scroll_until_stable(page, rounds=10):
    selector = "a[href*='/Hotel_Review-'][href*='-Reviews-']"
    last = 0
    for _ in range(rounds):
        page.mouse.wheel(0, 2500)
        page.wait_for_timeout(900)
        cur = page.locator(selector).count()
        if cur <= last:
            page.wait_for_timeout(900)
            cur2 = page.locator(selector).count()
            if cur2 <= last:
                break
            cur = cur2
        last = cur


def parse_total_results_from_text(page):
    """
    Ví dụ: "Hiển thị kết quả 31-60 trong số 7.565" -> 7565
    """
    txt = (page.content() or "")
    m = re.search(r"trong\s+số\s+([\d\.,]+)", txt, flags=re.I)
    if not m:
        return None
    raw = m.group(1)
    num = re.sub(r"[^\d]", "", raw)
    return int(num) if num.isdigit() else None


def _to_float_rating(s: str):
    try:
        return float(s.replace(",", "."))
    except Exception:
        return None


def _to_int_number(s: str):
    num = re.sub(r"[^\d]", "", s or "")
    return int(num) if num.isdigit() else None


def parse_card_metrics(card_text: str):
    """
    Trả về (rating_float, reviews_int, price_vnd_int)
    Fix lỗi dính '#9' + '4,9' -> '94,9' bằng regex có negative lookbehind.
    """
    if not card_text:
        return None, None, None

    t = card_text.replace("\u00a0", " ").strip()

    rating = None
    reviews = None
    price_vnd = None

    # rating + reviews
    m = RATING_REV_RE.search(t)
    if m:
        rating = _to_float_rating(m.group(1))
        reviews = _to_int_number(m.group(2))

    # reviews-only fallback
    if reviews is None:
        m2 = REV_ONLY_RE.search(t)
        if m2:
            reviews = _to_int_number(m2.group(1))

    # price
    pm = PRICE_RE_1.search(t) or PRICE_RE_2.search(t) or PRICE_RE_3.search(t)
    if pm:
        price_vnd = _to_int_number(pm.group(1))

    return rating, reviews, price_vnd


def best_card_for_link(a):
    """
    Leo lên ancestor để bắt đúng card (chứa 'đánh giá' hoặc giá 'đ')
    """
    for level in range(1, 8):
        c = a.locator(f"xpath=ancestor::*[self::div or self::article][{level}]").first
        if c.count() == 0:
            continue
        tx = (c.text_content() or "").lower()
        if ("đánh giá" in tx) or (" reviews" in tx) or (" đ" in tx) or ("₫" in tx) or ("vnd" in tx):
            return c
    return a.locator("xpath=ancestor::*[self::div or self::article][1]").first


def extract_hotels_from_list(page, seen_urls: set):
    rows = []

    links = page.locator("a[href*='/Hotel_Review-'][href*='-Reviews-']")
    n = links.count()

    for i in range(n):
        a = links.nth(i)
        href = a.get_attribute("href") or ""
        if "/Hotel_Review-" not in href:
            continue

        hotel_url = canonicalize_url(href)
        if not hotel_url or hotel_url in seen_urls:
            continue

        name = (a.text_content() or "").strip()
        if len(name) < 3:
            aria = (a.get_attribute("aria-label") or "").strip()
            if len(aria) >= 3:
                name = aria
        if len(name) < 3:
            continue

        card = best_card_for_link(a)
        card_text = (card.text_content() or "").strip()

        rating, reviews, price_vnd = parse_card_metrics(card_text)

        seen_urls.add(hotel_url)
        rows.append({
            "hotel_name": re.sub(r"^\d+\.\s*", "", name).strip(),
            "hotel_url": hotel_url,
            "rating": "" if rating is None else f"{rating:.1f}",
            "reviews": "" if reviews is None else str(reviews),
            "price_vnd": "" if price_vnd is None else str(price_vnd),
        })

    return rows


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"next_page": 1, "max_pages": None}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"next_page": 1, "max_pages": None}


def save_state(next_page: int, max_pages):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"next_page": next_page, "max_pages": max_pages}, f, ensure_ascii=False, indent=2)


def load_seen_urls_from_csv(path: str) -> set:
    if not os.path.exists(path):
        return set()
    seen = set()
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                u = (row.get("hotel_url") or "").strip()
                if u:
                    seen.add(u)
    except Exception:
        pass
    return seen


def append_rows_to_csv(path: str, rows: list[dict]):
    if not rows:
        return
    file_exists = os.path.exists(path)
    with open(path, "a", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["hotel_name", "hotel_url", "rating", "reviews", "price_vnd"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def main():
    state = load_state()
    next_page = int(state.get("next_page", 1))
    max_pages_state = state.get("max_pages", None)

    seen_urls = load_seen_urls_from_csv(OUT_CSV)
    print(f"[STATE] next_page={next_page}, max_pages={max_pages_state}, already_saved={len(seen_urls)}")

    with sync_playwright() as p:
        if USE_CDP:
            browser = p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
        else:
            browser = p.chromium.launch(headless=HEADLESS)
            context = browser.new_context(locale="vi-VN", viewport={"width": 1280, "height": 720})

        page = context.new_page()
        selector = "a[href*='/Hotel_Review-'][href*='-Reviews-']"

        # Lấy max_pages nếu chưa có
        if not max_pages_state:
            print(f"\n[INIT] open page 1: {START_URL}")
            page.goto(START_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(1500)
            accept_cookies_if_any(page)

            if is_block_or_verify(page):
                print("Verify/block/captcha ngay trang 1 -> lưu debug và dừng.")
                save_debug(page, "verify_or_block_page_1")
                browser.close()
                return

            try:
                page.wait_for_selector(selector, timeout=15000)
            except PwTimeout:
                print("Không thấy link hotel -> lưu debug và dừng.")
                save_debug(page, "no_links_page_1")
                browser.close()
                return

            total_results = parse_total_results_from_text(page)
            if total_results:
                max_pages = math.ceil(total_results / 30)
                print(f"[INIT] total_results={total_results} => pages≈{max_pages}")
            else:
                max_pages = MAX_PAGES_FALLBACK
                print(f"[INIT] cannot detect total_results => fallback={max_pages}")

            max_pages_state = max_pages
            save_state(next_page=next_page, max_pages=max_pages_state)

        max_pages = int(max_pages_state)
        end_page = min(max_pages, next_page + BATCH_PAGES - 1)
        print(f"[RUN] crawling pages {next_page} -> {end_page} (of {max_pages})")

        for page_idx in range(next_page, end_page + 1):
            offset = (page_idx - 1) * 30
            url = START_URL if page_idx == 1 else build_list_url_with_offset(START_URL, offset)

            print(f"\n[List {page_idx}/{max_pages}] {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(1500)
            accept_cookies_if_any(page)

            if is_block_or_verify(page):
                print("Verify/block/captcha -> lưu debug và dừng (state giữ để chạy tiếp).")
                save_debug(page, f"verify_or_block_page_{page_idx}")
                save_state(next_page=page_idx, max_pages=max_pages)
                browser.close()
                return

            try:
                page.wait_for_selector(selector, timeout=15000)
            except PwTimeout:
                print("Không thấy link hotel -> lưu debug và dừng (state giữ để chạy tiếp).")
                save_debug(page, f"no_links_page_{page_idx}")
                save_state(next_page=page_idx, max_pages=max_pages)
                browser.close()
                return

            auto_scroll_until_stable(page, rounds=SCROLL_ROUNDS)

            rows = extract_hotels_from_list(page, seen_urls)
            print(f"  -> New hotels saved: {len(rows)}")
            append_rows_to_csv(OUT_CSV, rows)

            save_state(next_page=page_idx + 1, max_pages=max_pages)
            time.sleep(SLEEP_BETWEEN_PAGES)

        browser.close()

    print(f"\n[DONE BATCH] total unique saved so far: {len(seen_urls)}")
    print(f"Saved -> {OUT_CSV}")
    print(f"Next run continues from page {min(end_page + 1, max_pages)} (see {STATE_FILE})")


if __name__ == "__main__":
    main()
