import json
import random
import time
import re
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

INPUT_CSV = "tripadvisor_hcm_hotels_list_link.csv"  
OUT_CSV = "hotels_detail_output.csv"
OUT_JSON = "hotels_detail_output.json"

SLEEP_MIN = 5
SLEEP_MAX = 8

# Cấu hình nghỉ giải lao
BATCH_SIZE = 30       # Cứ sau 30 link thì nghỉ
LONG_SLEEP_TIME = 60  # Thời gian nghỉ (giây)


def canonicalize_url(url: str) -> str:
    if not url: return ""
    try:
        u = urlparse(url)
        return urlunparse((u.scheme, u.netloc, u.path, "", "", ""))
    except:
        return url

def clean_price(price_str):
    if not price_str: return None
    return re.sub(r'\(.*?\)', '', str(price_str)).strip()

def expand_amenities_and_details(driver):
    try:
        buttons = driver.find_elements(By.XPATH, "//div[contains(@id, 'ABOUT_TAB')]//div[contains(text(), 'Hiển thị thêm') or contains(text(), 'Show more')]")
        for btn in buttons:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(1)
            except:
                pass
    except:
        pass

def extract_amenities_from_page(driver, soup):
    amenities = set()
    try:
        amenity_groups = driver.find_elements(By.CSS_SELECTOR, "div[data-test-target='amenity_text']")
        for el in amenity_groups:
            text = el.text.strip()
            if text: amenities.add(text)
    except:
        pass
    
    if len(amenities) < 3:
        about_tab = soup.select_one("#ABOUT_TAB")
        if about_tab:
            candidates = about_tab.find_all("div", string=True)
            keywords = ["Wifi", "Hồ bơi", "Spa", "Gym", "Nhà hàng", "Đỗ xe", "Lễ tân", "Điều hòa", "Giặt ủi"]
            for tag in candidates:
                text = tag.get_text(strip=True)
                if 3 < len(text) < 50 and any(k.lower() in text.lower() for k in keywords):
                    amenities.add(text)

    clean_list = [a for a in amenities if "Hiển thị" not in a and "đánh giá" not in a]
    return ", ".join(sorted(clean_list))

def extract_room_types_safe(soup):
    room_types = set()
    about_section = soup.select_one("#ABOUT_TAB")
    if about_section:
        text_content = about_section.get_text(" | ")
        keywords = [
            "Ngắm cảnh", "Thành phố", "Sông", "Hồ bơi", 
            "Phòng không hút thuốc", "Phòng cách âm", "Phòng gia đình", "Suite", 
            "Ban công", "Bếp nhỏ", "Minibar", 
            "Hạng trung", "Công tác"
        ]
        for k in keywords:
            if k.lower() in text_content.lower():
                pattern = re.compile(re.escape(k), re.IGNORECASE)
                match = pattern.search(text_content)
                if match:
                    room_types.add(match.group(0))
    return ", ".join(sorted(list(room_types)))

def extract_jsonld_hotel(soup):
    for s in soup.select('script[type="application/ld+json"]'):
        try:
            obj = json.loads(s.string or "")
            candidates = obj.get("@graph", [obj]) if isinstance(obj, dict) else obj
            if not isinstance(candidates, list): candidates = [candidates]
            for c in candidates:
                if isinstance(c, dict) and c.get("@type") in ("Hotel", "LodgingBusiness", "Resort"):
                    return c
        except:
            continue
    return None

def parse_detail(driver, url):
    html = driver.page_source
    soup = BeautifulSoup(html, "lxml")

    out = {
        "detail_url": canonicalize_url(url),
        "name_detail": None,
        "phone": None,
        "ratingValue": None,
        "reviewCount": None,
        "priceRange": None,
        "address": None,
        "amenities": None,
        "room_types": None
    }

    ld = extract_jsonld_hotel(soup)
    if ld:
        out["name_detail"] = ld.get("name")
        out["priceRange"] = clean_price(ld.get("priceRange"))
        ar = ld.get("aggregateRating") or {}
        out["ratingValue"] = ar.get("ratingValue")
        out["reviewCount"] = ar.get("reviewCount")
        addr = ld.get("address") or {}
        parts = [
            addr.get("streetAddress"),
            addr.get("addressLocality"),
            addr.get("postalCode"),
            addr.get("addressCountry", {}).get("name") if isinstance(addr.get("addressCountry"), dict) else addr.get("addressCountry")
        ]
        out["address"] = ", ".join([p for p in parts if p])

    tel = soup.select_one('a[href^="tel:"]')
    if tel:
        out["phone"] = tel.get("href").replace("tel:", "").strip()
    
    out["amenities"] = extract_amenities_from_page(driver, soup)
    out["room_types"] = extract_room_types_safe(soup)
    
    if not out["name_detail"]:
        try:
            h1 = soup.select_one("h1#HEADING")
            if h1: out["name_detail"] = h1.get_text(strip=True)
        except:
            pass

    return out
def load_existing_results():
    if Path(OUT_CSV).exists():
        df_old = pd.read_csv(OUT_CSV)

        if "detail_url" not in df_old.columns:
            df_old["detail_url"] = ""

        done_urls = set(
            df_old["detail_url"]
            .dropna()
            .astype(str)
            .apply(canonicalize_url)
            .tolist()
        )

        print(f" Đã tìm thấy file cũ: {len(done_urls)} link đã crawl")
        return done_urls

    return set()


def append_to_csv(row_dict):
    df_row = pd.DataFrame([row_dict])
    file_exists = Path(OUT_CSV).exists()
    df_row.to_csv(
        OUT_CSV,
        mode="a",
        header=not file_exists,
        index=False,
        encoding="utf-8-sig"
    )


def main():
    if not Path(INPUT_CSV).exists():
        print(f" Chưa có file {INPUT_CSV}")
        return

    df = pd.read_csv(INPUT_CSV)
    
    url_col = None
    for col in df.columns:
        if len(df) > 0 and "http" in str(df[col].iloc[0]):
            url_col = col
            break
    
    if not url_col:
        print("Không tìm thấy cột URL")
        return

    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    print("Đang kết nối Chrome...")
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    except Exception as e:
        print(f" Lỗi kết nối Chrome: {e}")
        return

    done_urls = load_existing_results()


    try:
        for i, row in df.iterrows():
            url = str(row[url_col]).strip()
            url_clean = canonicalize_url(url)
            if url_clean in done_urls:
                print(f"[{i+1}/{len(df)}]  Đã có, bỏ qua")
                continue


            try:
                driver.get(url_clean)
                time.sleep(3)
                
                try:
                    about_div = driver.find_element(By.ID, "ABOUT_TAB")
                    driver.execute_script("arguments[0].scrollIntoView();", about_div)
                except:
                    driver.execute_script("window.scrollTo(0, 1000);")
                
                time.sleep(2)
                expand_amenities_and_details(driver)
                detail = parse_detail(driver, url_clean)

                full_data = row.to_dict()
                full_data.update(detail)
                append_to_csv(full_data)
                done_urls.add(url_clean)


                print(f"Tên: {detail.get('name_detail')}")
                print(f"Tiện nghi: {str(detail.get('amenities'))[:60]}...")
                print(f"Loại phòng: {detail.get('room_types')}")

            except Exception as e:
                out = row.to_dict()
                out["detail_url"] = url_clean
                append_to_csv(out)
                done_urls.add(url_clean)


            # Đếm số thứ tự bắt đầu từ 1
            count = i + 1 
            
            # Kiểm tra nếu chia hết cho BATCH_SIZE (30) thì nghỉ dài
            if count % BATCH_SIZE == 0:
                print(f"\nĐã cào được {count} link. Đang nghỉ giải lao {LONG_SLEEP_TIME} giây...")
                time.sleep(LONG_SLEEP_TIME)
                print("Tiếp tục làm việc...\n")
            else:
                # Nghỉ ngắn bình thường
                time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))

    except KeyboardInterrupt:
        print("\n Dừng bởi người dùng...")

    finally:
        print("\n Đã lưu từng dòng trực tiếp trong quá trình crawl.")

if __name__ == "__main__":
    main()