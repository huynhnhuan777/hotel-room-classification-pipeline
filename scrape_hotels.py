import re
import time
import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ================== CẤU HÌNH ==================
INPUT_LINKS_TXT = "mytour_links.txt"   # mỗi dòng 1 link khách sạn
OUT_CSV = "mytour_hotels.csv"

WAIT_AFTER_OPEN = 5      # vào trang chờ 5s rồi mới lấy dữ liệu
WAIT_BEFORE_NEXT = 5     # lấy xong chờ 5s rồi mới sang trang khác
# ==============================================


PRICE_RE = re.compile(r"(\d{1,3}(?:[.,]\d{3})+)\s*₫")
PERCENT_RE = re.compile(r"-\s*\d+\s*%")
RATING_RE = re.compile(r"^\d{1,2}(?:\.\d{1,2})?$")  # 9.4, 8.0, 10


def clean(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def all_matches(pattern: re.Pattern, text: str):
    if not text:
        return []
    return [m.group(0) for m in pattern.finditer(text)]


def extract_hotel_name(soup: BeautifulSoup) -> str:
    h1 = soup.select_one("h1.MuiBox-root") or soup.select_one("h1")
    return clean(h1.get_text(" ", strip=True)) if h1 else ""


def extract_rating_score(soup: BeautifulSoup) -> str:
    best = ""
    for sp in soup.find_all("span"):
        t = clean(sp.get_text(" ", strip=True))
        if not t or not RATING_RE.match(t):
            continue
        try:
            val = float(t.replace(",", "."))
        except Exception:
            continue
        if not (0 <= val <= 10):
            continue

        has_svg = sp.find("svg") is not None or (sp.parent and sp.parent.find("svg") is not None)
        if has_svg:
            return t
        if not best:
            best = t
    return best


def extract_review_count(soup: BeautifulSoup) -> str:
    text = clean(soup.get_text(" ", strip=True)).lower()
    m = re.search(r"(\d[\d.,]*)\s*đánh\s*giá", text)
    if m:
        return m.group(1).replace(".", "").replace(",", "")
    m = re.search(r"(\d[\d.,]*)\s*reviews?", text)
    if m:
        return m.group(1).replace(".", "").replace(",", "")
    return ""


def extract_address(soup: BeautifulSoup) -> str:
    btn = soup.find(
        lambda tag: tag.name in ("button", "span", "div")
        and clean(tag.get_text()).lower() == "xem bản đồ"
    )
    if btn:
        container = btn.find_parent("div")
        if container:
            candidates = []
            for sp in container.find_all("span"):
                t = clean(sp.get_text(" ", strip=True))
                if len(t) < 8:
                    continue
                score = 0
                if "," in t:
                    score += 2
                if "việt nam" in t.lower():
                    score += 2
                if "hồ chí minh" in t.lower() or "ho chi minh" in t.lower():
                    score += 2
                score += min(len(t) / 50, 2)
                candidates.append((score, t))
            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                return candidates[0][1]

    full = clean(soup.get_text(" ", strip=True))
    m = re.search(r"([^\n]{10,200}việt nam[^\n]{0,50})", full, flags=re.IGNORECASE)
    if m:
        return clean(m.group(1))
    return ""


def extract_discount(soup: BeautifulSoup) -> str:
    for sp in soup.find_all(["span", "div"]):
        t = clean(sp.get_text(" ", strip=True))
        m = PERCENT_RE.search(t)
        if m:
            return m.group(0)
    return ""


def extract_amenities(soup: BeautifulSoup) -> str:
    """
    Tiện nghi: theo layout bạn đưa (div.jss369 -> div.jss373 là tên tiện nghi)
    Nối bằng " | "
    """
    amenities = []
    for block in soup.select("div.jss369"):
        name_div = block.select_one("div.jss373")
        if name_div:
            text = clean(name_div.get_text(" ", strip=True))
            if text:
                amenities.append(text)

    # loại trùng nhưng giữ thứ tự
    return " | ".join(dict.fromkeys(amenities))


def extract_prices(soup: BeautifulSoup):
    """
    Trả về: (giá_niêm_yết, discount, giá_hiện_tại)
    Giá hiện tại = giá niêm yết - giá niêm yết * discount(%)
    """

    list_price_text = ""
    discount_text = ""
    current_price_text = ""

    # --- 1. Tìm discount ---
    for sp in soup.find_all(["span", "div"]):
        t = clean(sp.get_text(" ", strip=True))
        m = PERCENT_RE.search(t)
        if m:
            discount_text = m.group(0)  # ví dụ "-18%"
            break

    # --- 2. Tìm giá niêm yết ---
    prices = all_matches(PRICE_RE, clean(soup.get_text(" ", strip=True)))
    if prices:
        list_price_text = prices[0]   # lấy giá đầu tiên làm giá niêm yết

    # --- 3. Tính giá hiện tại ---
    if list_price_text:
        # chuyển "2.894.667 ₫" -> 2894667
        list_price_num = int(
            list_price_text.replace("₫", "")
            .replace(".", "")
            .replace(",", "")
            .strip()
        )

        if discount_text:
            discount_value = int(discount_text.replace("-", "").replace("%", ""))
            current_price_num = int(list_price_num * (100 - discount_value) / 100)
        else:
            current_price_num = list_price_num

        # format lại tiền VNĐ
        current_price_text = f"{current_price_num:,}".replace(",", ".") + " ₫"

    return list_price_text, discount_text, current_price_text

def load_links_from_txt(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def main():
    urls = load_links_from_txt(INPUT_LINKS_TXT)

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 25)

    rows = []

    try:
        for i, url in enumerate(urls, start=1):
            try:
                driver.get(url)

                # chờ h1 xuất hiện để chắc chắn trang load DOM chính
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))

                # ✅ (1) vào trang chờ 5s rồi mới lấy dữ liệu
                time.sleep(WAIT_AFTER_OPEN)

                # scroll nhẹ để load các block động (nếu có)
                for _ in range(2):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)

                soup = BeautifulSoup(driver.page_source, "lxml")

                hotel_name = extract_hotel_name(soup)
                rating_score = extract_rating_score(soup)
                review_count = extract_review_count(soup)
                address = extract_address(soup)
                list_price, discount, current_price = extract_prices(soup)
                amenities = extract_amenities(soup)

                rows.append({
                    "link": url,
                    "ten": hotel_name,
                    "gia_niem_yet": list_price,
                    "discount": discount,
                    "gia_hien_tai": current_price,
                    "dia_chi": address,
                    "so_luong_danh_gia": review_count,
                    "diem_danh_gia": rating_score,
                    "tien_nghi": amenities,
                })

                print(
                    f"[{i}/{len(urls)}] OK | {hotel_name} | "
                    f"list={list_price} | disc={discount} | now={current_price} | "
                    f"rating={rating_score} | reviews={review_count}"
                )

                # ✅ (2) lấy xong chờ 5s rồi mới sang trang khác
                time.sleep(WAIT_BEFORE_NEXT)

            except Exception as e:
                print(f"[{i}/{len(urls)}] FAIL | {url} | {e}")
                time.sleep(WAIT_BEFORE_NEXT)

    finally:
        if rows:
            pd.DataFrame(rows).to_csv(
                OUT_CSV,
                index=False,
                sep=";",
                encoding="utf-8-sig"
            )
        driver.quit()

    print("🎉 DONE ->", OUT_CSV)


if __name__ == "__main__":
    main()
