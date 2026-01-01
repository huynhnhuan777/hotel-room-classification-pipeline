#!/usr/bin/env python3
"""

"""
import os
import time
import json
import pickle
import random
from typing import List, Dict, Any, Set
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

ROOT = os.path.dirname(__file__)
COOKIES_PKL = os.path.join(ROOT, "trip_cookies.pkl")
LOCAL_JSON = os.path.join(ROOT, "trip_localstorage.json")
SESSION_JSON = os.path.join(ROOT, "trip_sessionstorage.json")

OUT_JSONL = os.path.join(ROOT, "trip_hotels_hcm_more.jsonl")
EXISTING_JSONL = os.path.join(ROOT, "trip_hotels_full.jsonl")
SEEN_REQUESTS_FILE = os.path.join(ROOT, "seen_requests.json")  # File để lưu seen request IDs

# TP.HCM cityId = 301
# Chỉ crawl ngày 19 và 20 tháng 12 năm 2024 (ngày gần hơn để có dữ liệu)
# Tạo nhiều combinations để có đủ dữ liệu
HCM_LISTINGS = []

# Base URLs cho 2 ngày
base_dates = [
    ("2024-12-19", "2024-12-20"),
    ("2024-12-20", "2024-12-21"),
]

# Stars
stars = [2, 3, 4, 5]

# Price ranges
price_ranges = [
    (0, 500000),
    (500000, 1000000),
    (1000000, 2000000),
    (2000000, 5000000),
    (5000000, 10000000),
]

# Districts (thêm nhiều districts hơn)
districts = list(range(1, 11))  # 1-10

# Tạo combinations
for checkin, checkout in base_dates:
    # Base URL không filter
    HCM_LISTINGS.append(f"https://vn.trip.com/hotels/list?city=301&checkin={checkin}&checkout={checkout}")
    
    # Với star filter
    for star in stars:
        HCM_LISTINGS.append(f"https://vn.trip.com/hotels/list?city=301&checkin={checkin}&checkout={checkout}&star={star}")
    
    # Với price filter
    for pmin, pmax in price_ranges:
        HCM_LISTINGS.append(f"https://vn.trip.com/hotels/list?city=301&checkin={checkin}&checkout={checkout}&priceRange={pmin}%2C{pmax}")
    
    # Với district filter
    for district in districts:
        HCM_LISTINGS.append(f"https://vn.trip.com/hotels/list?city=301&checkin={checkin}&checkout={checkout}&districtId={district}")
    
    # Combinations: star + price (thêm nhiều combinations hơn)
    for star in stars:
        for pmin, pmax in price_ranges:  # Lấy tất cả price ranges
            HCM_LISTINGS.append(f"https://vn.trip.com/hotels/list?city=301&checkin={checkin}&checkout={checkout}&star={star}&priceRange={pmin}%2C{pmax}")
    
    # Combinations: star + district (thêm nhiều districts hơn)
    for star in stars:
        for district in districts:  # Lấy tất cả districts
            HCM_LISTINGS.append(f"https://vn.trip.com/hotels/list?city=301&checkin={checkin}&checkout={checkout}&star={star}&districtId={district}")
    
    # Combinations: price + district
    for pmin, pmax in price_ranges[:3]:  # Lấy 3 price ranges đầu
        for district in districts[:5]:  # Lấy 5 districts đầu
            HCM_LISTINGS.append(f"https://vn.trip.com/hotels/list?city=301&checkin={checkin}&checkout={checkout}&priceRange={pmin}%2C{pmax}&districtId={district}")

# Shuffle để crawl ngẫu nhiên và tránh pattern
random.shuffle(HCM_LISTINGS)
print(f"Generated {len(HCM_LISTINGS)} URLs for crawling")

TARGET_NEW_COUNT = 1500  # Số hotels mới cần crawl


def load_existing_hotel_ids() -> Set[str]:
    """Load danh sách hotel IDs đã có từ file JSONL (cả file gốc và file mới)"""
    existing_ids = set()
    
    # Load từ file gốc
    if os.path.exists(EXISTING_JSONL):
        print(f"Loading existing hotel IDs from {EXISTING_JSONL}...")
        with open(EXISTING_JSONL, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    hotel_id = None
                    if 'hotelInfo' in obj:
                        summary = obj['hotelInfo'].get('summary', {})
                        hotel_id = summary.get('hotelId')
                    elif 'hotelId' in obj:
                        hotel_id = obj['hotelId']
                    if hotel_id:
                        existing_ids.add(str(hotel_id))
                except Exception:
                    continue
    
    # Load từ file output mới (nếu có) để tránh trùng lặp khi script restart
    if os.path.exists(OUT_JSONL):
        print(f"Loading hotel IDs from output file {OUT_JSONL}...")
        with open(OUT_JSONL, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    hotel_id = None
                    if 'hotelInfo' in obj:
                        summary = obj['hotelInfo'].get('summary', {})
                        hotel_id = summary.get('hotelId')
                    elif 'hotelId' in obj:
                        hotel_id = obj['hotelId']
                    if hotel_id:
                        existing_ids.add(str(hotel_id))
                except Exception:
                    continue
    
    print(f"Loaded {len(existing_ids)} existing hotel IDs")
    return existing_ids


def setup_driver(headless=False):
    options = webdriver.ChromeOptions()

    # 🚨 QUAN TRỌNG: attach vào Chrome đang mở
    options.add_experimental_option(
        "debuggerAddress", "127.0.0.1:9222"
    )

    # Các option này KHÔNG được xung đột với Chrome đang chạy
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # ❌ TUYỆT ĐỐI KHÔNG dùng headless khi attach
    # if headless:
    #     options.add_argument("--headless=new")

    # Performance log để bắt fetchHotelList
    options.set_capability(
        "goog:loggingPrefs", {"performance": "ALL"}
    )

    driver = webdriver.Chrome(
        service=Service(),
        options=options
    )

    # Enable Network domain (CDP)
    try:
        driver.execute_cdp_cmd("Network.enable", {})
    except Exception:
        pass

    return driver


def load_cookies_and_storage(driver):
    if os.path.exists(COOKIES_PKL):
        with open(COOKIES_PKL, "rb") as f:
            cookies = pickle.load(f)
        driver.get("https://vn.trip.com")
        time.sleep(1)
        for c in cookies:
            try:
                cookie = c.copy()
                cookie.pop("sameSite", None)
                cookie.pop("hostOnly", None)
                if cookie.get("domain") and cookie["domain"].startswith("."):
                    cookie["domain"] = cookie["domain"]
                driver.add_cookie(cookie)
            except Exception as e:
                print("Failed add cookie:", e)
        print(f"Added {len(cookies)} cookies to browser")
    else:
        print("No cookie file found; starting fresh session")

    def _restore_json(path, storage_name):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            driver.get("https://vn.trip.com")
            time.sleep(1)
            for k, v in data.items():
                driver.execute_script(f"window.{storage_name}.setItem(arguments[0], arguments[1]);", k, v)
            print(f"Restored {len(data)} items to {storage_name}")

    _restore_json(LOCAL_JSON, "localStorage")
    _restore_json(SESSION_JSON, "sessionStorage")


def extract_fetch_responses_from_perf_logs(driver, seen_request_ids: Set[str], last_index: int = 0):
    """
    Parse driver.get_log('performance') và chỉ xử lý các log mới từ last_index
    Trả về (results, new_last_index) để tránh xử lý lại
    NOTE: seen_request_ids nên được reload định kỳ ở caller để tối ưu performance
    """
    
    entries = driver.get_log('performance')
    results = []
    new_last_index = last_index
    
    # Detect buffer reset: nếu entries length < last_index, buffer đã reset
    if len(entries) < last_index:
        print(f"  WARNING: Performance log buffer reset detected! (was {last_index}, now {len(entries)})")
        last_index = 0  # Reset về 0 vì buffer đã reset
    
    # Chỉ xử lý các entries mới từ last_index
    if len(entries) > last_index:
        new_entries = entries[last_index:]
        new_last_index = len(entries)
        
        for entry in new_entries:
            try:
                msg = json.loads(entry['message'])['message']
                if msg.get('method') == 'Network.responseReceived':
                    params = msg.get('params', {})
                    response = params.get('response', {})
                    url = response.get('url', '')
                    request_id = params.get('requestId')
                    
                    # QUAN TRỌNG: Check seen_request_ids TRƯỚC khi xử lý
                    if 'fetchHotelList' in url and request_id and request_id not in seen_request_ids:
                        seen_request_ids.add(request_id)
                        # Lưu ngay vào file để tránh mất dữ liệu
                        save_seen_request_ids(seen_request_ids)
                        
                        try:
                            body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                            text = body.get('body', '')
                            try:
                                j = json.loads(text)
                            except Exception:
                                j = {'_raw': text}
                            results.append({'url': url, 'requestId': request_id, 'json': j})
                        except WebDriverException as e:
                            print('Error getting response body for', request_id, e)
                            continue
            except Exception:
                continue
    
    # Nếu log buffer quá lớn (>1500), clear để tránh memory issue
    # Nhưng vẫn giữ seen_request_ids để tránh xử lý lại
    if len(entries) > 1500:
        try:
            driver.get_log('performance')  # Clear log buffer
            new_last_index = 0
            print(f"  Cleared performance log buffer (had {len(entries)} entries, kept {len(seen_request_ids)} seen request IDs)")
        except:
            pass
    
    return results, new_last_index


def extract_hotel_id(item):
    """Extract hotelId from various structures"""
    if not isinstance(item, dict):
        return None
    
    # Try hotelInfo.summary.hotelId
    if 'hotelInfo' in item:
        summary = item['hotelInfo'].get('summary', {})
        if summary and summary.get('hotelId'):
            return str(summary.get('hotelId'))
    
    # Try direct hotelId
    if 'hotelId' in item:
        return str(item['hotelId'])
    
    return None


def load_seen_request_ids() -> Set[str]:
    """Load seen request IDs từ file để tránh xử lý lại"""
    if os.path.exists(SEEN_REQUESTS_FILE):
        try:
            with open(SEEN_REQUESTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('request_ids', []))
        except:
            return set()
    return set()

def extract_amenities_from_detail_page(driver, hotel_id: str) -> List[str]:
    """Crawl amenities từ detail page của hotel"""
    try:
        detail_url = f"https://vn.trip.com/hotels/detail/?hotelId={hotel_id}"
        print(f"    Loading detail page: {detail_url}")
        driver.get(detail_url)
        time.sleep(3)  # Đợi page load
        
        # Scroll để trigger lazy load
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight * 0.3);')
        time.sleep(1.5)
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight * 0.6);')
        time.sleep(1.5)
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(1.5)
        
        # Lấy performance logs
        entries = driver.get_log('performance')
        amenities = []
        api_count = 0
        
        print(f"    Checking {len(entries)} performance log entries...")
        
        for entry in entries:
            try:
                msg = json.loads(entry['message'])['message']
                if msg.get('method') == 'Network.responseReceived':
                    params = msg.get('params', {})
                    response = params.get('response', {})
                    url_api = response.get('url', '')
                    request_id = params.get('requestId')
                    
                    # Tìm API có thể chứa amenities - mở rộng keywords
                    if any(keyword in url_api.lower() for keyword in [
                        'detail', 'hotel', 'amenit', 'facilit', 'service', 'feature', 
                        'property', 'info', 'data', 'fetch', 'get'
                    ]):
                        api_count += 1
                        try:
                            body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                            text = body.get('body', '')
                            try:
                                json_data = json.loads(text)
                                # Tìm amenities trong response
                                found = extract_amenities_from_json(json_data)
                                if found:
                                    amenities.extend(found)
                                    print(f"      Found amenities in API: {url_api[:80]}")
                            except:
                                pass
                        except Exception as e:
                            # Skip nếu không lấy được body
                            pass
            except Exception:
                continue
        
        print(f"    Checked {api_count} APIs, found {len(amenities)} amenities")
        
        # Clear log để tránh memory issue
        try:
            driver.get_log('performance')
        except:
            pass
        
        return list(set(amenities))  # Remove duplicates
    except Exception as e:
        print(f"    Error crawling amenities for {hotel_id}: {e}")
        import traceback
        traceback.print_exc()
        return []

def extract_amenities_from_json(obj, path="") -> List[str]:
    """Recursively tìm amenities trong JSON structure"""
    amenities = []
    
    if isinstance(obj, dict):
        for k, v in obj.items():
            key_lower = k.lower()
            # Nếu key chứa amenities/facilities
            if any(word in key_lower for word in ['amenit', 'facilit', 'service', 'feature', 'equipment']):
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, str):
                            amenities.append(item)
                        elif isinstance(item, dict):
                            # Có thể là object với name/title
                            name = item.get('name') or item.get('title') or item.get('text') or item.get('label')
                            if name:
                                amenities.append(str(name))
                elif isinstance(v, str):
                    amenities.append(v)
            
            # Recursive search
            if isinstance(v, (dict, list)):
                amenities.extend(extract_amenities_from_json(v, f"{path}.{k}" if path else k))
    
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            amenities.extend(extract_amenities_from_json(item, f"{path}[{i}]" if path else f"[{i}]"))
    
    return amenities

def save_seen_request_ids(seen_request_ids: Set[str]):
    """Lưu seen request IDs vào file"""
    try:
        with open(SEEN_REQUESTS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'request_ids': list(seen_request_ids)}, f)
    except:
        pass

def collect_new_hotels(driver, listing_urls: List[str], existing_ids: Set[str], target_count: int):
    # Load lại existing_ids từ file output để đảm bảo không bị reset
    seen_ids: Set[str] = load_existing_hotel_ids()
    new_hotels: List[Dict[str, Any]] = []
    seen_request_ids: Set[str] = load_seen_request_ids()  # Load từ file
    last_log_index = 0  # Track last processed log index

    print(f"Starting crawl. Existing hotels: {len(seen_ids)}, Target new: {target_count}")
    print(f"Loaded {len(seen_request_ids)} seen request IDs from previous session")

    for url_idx, url in enumerate(listing_urls):
        if len(new_hotels) >= target_count:
            print(f"Reached target of {target_count} new hotels!")
            break
        
        print(f'\n[{url_idx+1}/{len(listing_urls)}] Loading listing: {url}')
        driver.get(url)
        time.sleep(3)
        
        # Reset log index khi bắt đầu URL mới
        last_log_index = 0
        # Clear performance log khi bắt đầu URL mới
        try:
            driver.get_log('performance')
            last_log_index = 0
        except:
            pass

        last_len = 0
        idle = 0
        max_scrolls = 800  # Tăng từ 600 lên 800 để scroll nhiều hơn
        reload_counter = 0  # Counter để reload định kỳ
        
        for i in range(max_scrolls):
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            if i % 5 == 0:
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight * 0.7);')
                time.sleep(0.5)
            time.sleep(1 + (i % 3))

            # Reload seen_request_ids từ file định kỳ (mỗi 20 scrolls) để tối ưu performance
            reload_counter += 1
            if reload_counter % 20 == 0:
                seen_request_ids.update(load_seen_request_ids())
                # Reload seen_ids định kỳ để sync
                seen_ids.update(load_existing_hotel_ids())
            
            # Chỉ xử lý các log mới từ last_log_index
            responses, last_log_index = extract_fetch_responses_from_perf_logs(driver, seen_request_ids, last_log_index)
            if responses:
                print(f'  Captured {len(responses)} new fetch responses')
                # Save seen_request_ids ngay sau khi capture responses
                save_seen_request_ids(seen_request_ids)
                
                for r in responses:
                    j = r['json']
                    candidates = []
                    
                    if isinstance(j, dict):
                        if 'hotelList' in j:
                            candidates = j['hotelList'] or []
                        elif 'data' in j and isinstance(j['data'], dict) and 'hotelList' in j['data']:
                            candidates = j['data'].get('hotelList', []) or []
                        elif 'data' in j and isinstance(j['data'], list):
                            for item in j['data']:
                                if isinstance(item, dict) and 'hotelList' in item:
                                    candidates.extend(item.get('hotelList') or [])
                        else:
                            def find_lists(obj):
                                found = []
                                if isinstance(obj, dict):
                                    for v in obj.values():
                                        found.extend(find_lists(v))
                                elif isinstance(obj, list):
                                    if obj and isinstance(obj[0], dict) and 'hotelId' in obj[0]:
                                        found.append(obj)
                                    else:
                                        for e in obj:
                                            found.extend(find_lists(e))
                                return found
                            lists = find_lists(j)
                            if lists:
                                candidates = lists[0]

                    for h in candidates:
                        hid = extract_hotel_id(h)
                        if not hid:
                            continue
                        
                        # Chỉ lấy hotels từ TP.HCM (cityId=301)
                        city_id = None
                        if isinstance(h, dict):
                            if 'hotelInfo' in h:
                                pos_info = h['hotelInfo'].get('positionInfo', {})
                                city_id = pos_info.get('cityId')
                            elif 'cityId' in h:
                                city_id = h['cityId']
                        
                        if city_id != 301:
                            continue
                        
                        # Check duplicate với seen_ids đã load (chỉ reload định kỳ, không phải mỗi lần)
                        if hid in seen_ids:
                            continue
                        
                        seen_ids.add(hid)
                        
                        # Crawl amenities từ detail page
                        print(f"  Crawling amenities for hotel {hid}...")
                        amenities = extract_amenities_from_detail_page(driver, hid)
                        
                        # Thêm amenities vào hotelInfo
                        if 'hotelInfo' in h:
                            h['hotelInfo']['amenities'] = amenities
                        else:
                            h['amenities'] = amenities
                        
                        if amenities:
                            print(f"    ✓ Found {len(amenities)} amenities")
                        else:
                            print(f"    - No amenities found")
                        
                        new_hotels.append(h)
                        
                        # Save immediately to avoid data loss
                        with open(OUT_JSONL, 'a', encoding='utf-8') as f:
                            f.write(json.dumps(h, ensure_ascii=False) + '\n')
                        
                        # Delay để tránh bị block khi crawl detail page
                        time.sleep(1)
                        
                        # Reload và save sau mỗi hotel để đảm bảo không mất dữ liệu
                        if len(new_hotels) % 10 == 0:  # Reload mỗi 10 hotels (giảm từ 5 để tối ưu)
                            print(f"  Collected {len(new_hotels)} new hotels (target: {target_count})")
                            # Reload existing IDs từ file để đảm bảo sync (chỉ định kỳ, không phải mỗi lần)
                            seen_ids.update(load_existing_hotel_ids())
                            # Reload và save seen request IDs để tránh xử lý lại
                            seen_request_ids.update(load_seen_request_ids())
                            save_seen_request_ids(seen_request_ids)

            if len(new_hotels) >= target_count:
                print(f'Reached target hotels count: {len(new_hotels)}')
                break
            
            if len(new_hotels) == last_len:
                idle += 1
            else:
                idle = 0
            last_len = len(new_hotels)

            # Tăng threshold idle để scroll nhiều hơn trước khi dừng
            if idle > 30:  # Tăng từ 15 lên 30 để scroll nhiều hơn
                print(f'  Idle detected after {idle} scrolls; trying next page...')
                try:
                    next_selectors = [
                        "a[aria-label*='Next']",
                        "button[aria-label*='Next']",
                        "a[class*='next']",
                        "button[class*='next']",
                        ".pagination-next",
                        "[data-page='next']",
                        "div[class*='pagination'] a:last-child",
                        "div[class*='pagination'] button:last-child"
                    ]
                    clicked = False
                    for selector in next_selectors:
                        try:
                            next_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                            if next_buttons:
                                for btn in next_buttons:
                                    if btn.is_displayed() and btn.is_enabled():
                                        # Check if it's not the current page button
                                        btn_class = btn.get_attribute('class') or ''
                                        if 'current' not in btn_class.lower() and 'active' not in btn_class.lower():
                                            btn.click()
                                            print(f"    Clicked next button: {selector}")
                                            time.sleep(3)
                                            idle = 0
                                            clicked = True
                                            break
                                if clicked:
                                    break
                        except Exception as e:
                            continue
                    
                    if not clicked:
                        print("    No next button found, continuing scroll...")
                except Exception as e:
                    print(f"    Error clicking next: {e}")
                
                # Tăng threshold break từ 25 lên 50 để scroll nhiều hơn và tiếp tục crawl
                if idle > 50:  # Tăng từ 25 lên 50
                    print(f'  No new hotels after {idle} scrolls, moving to next URL...')
                    # Vẫn tiếp tục với URL tiếp theo thay vì dừng hoàn toàn
                    break

        print(f'  Collected {len(new_hotels)} new hotels so far from this URL')
        # Reload và save sau mỗi URL để đảm bảo không mất dữ liệu
        seen_ids.update(load_existing_hotel_ids())
        save_seen_request_ids(seen_request_ids)

    # Final save
    save_seen_request_ids(seen_request_ids)
    return new_hotels


def main():
    # Load existing hotel IDs
    existing_ids = load_existing_hotel_ids()
    
    # Initialize output file
    if os.path.exists(OUT_JSONL):
        print(f"Appending to existing file: {OUT_JSONL}")
    else:
        print(f"Creating new file: {OUT_JSONL}")
    
    driver = setup_driver(headless=False)
    try:
        load_cookies_and_storage(driver)
        new_hotels = collect_new_hotels(driver, HCM_LISTINGS, existing_ids, TARGET_NEW_COUNT)
        print(f'\nTotal new hotels collected: {len(new_hotels)}')
        print(f'Output saved to: {OUT_JSONL}')
    finally:
        driver.quit()


if __name__ == '__main__':
    main()

