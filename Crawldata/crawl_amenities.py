#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để crawl amenities từ detail page của các khách sạn đã có
"""
import os
import json
import time
from typing import Dict, List, Set
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

ROOT = os.path.dirname(__file__)
INPUT_JSONL = os.path.join(ROOT, "trip_hotels_full.jsonl")
OUTPUT_JSONL = os.path.join(ROOT, "trip_hotels_with_amenities.jsonl")
AMENITIES_JSON = os.path.join(ROOT, "hotels_amenities.json")  # File riêng lưu amenities

def setup_driver():
    """Setup Chrome driver với remote debugging"""
    options = Options()
    # Attach vào Chrome đang chạy
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    
    driver = webdriver.Chrome(service=Service(), options=options)
    
    try:
        driver.execute_cdp_cmd("Network.enable", {})
    except Exception:
        pass
    
    return driver

def extract_amenities_from_api_responses(driver, hotel_id: str) -> List[str]:
    """Capture API responses và extract amenities"""
    detail_url = f"https://vn.trip.com/hotels/detail/?hotelId={hotel_id}"
    
    print(f"  Loading detail page: {hotel_id}")
    driver.get(detail_url)
    time.sleep(3)  # Đợi page load
    
    # Scroll để trigger lazy load
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight * 0.5);')
    time.sleep(2)
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    time.sleep(2)
    
    # Lấy performance logs
    entries = driver.get_log('performance')
    amenities = []
    
    for entry in entries:
        try:
            msg = json.loads(entry['message'])['message']
            if msg.get('method') == 'Network.responseReceived':
                params = msg.get('params', {})
                response = params.get('response', {})
                url_api = response.get('url', '')
                request_id = params.get('requestId')
                
                # Tìm API có thể chứa amenities
                if any(keyword in url_api.lower() for keyword in [
                    'detail', 'hotel', 'amenit', 'facilit', 'service', 'feature', 'property'
                ]):
                    try:
                        body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                        text = body.get('body', '')
                        try:
                            json_data = json.loads(text)
                            # Tìm amenities trong response
                            found = extract_amenities_from_json(json_data)
                            if found:
                                amenities.extend(found)
                        except:
                            pass
                    except Exception:
                        pass
        except Exception:
            continue
    
    # Clear log để tránh memory issue
    try:
        driver.get_log('performance')
    except:
        pass
    
    return list(set(amenities))  # Remove duplicates

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
                            name = item.get('name') or item.get('title') or item.get('text')
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

def load_hotel_ids() -> List[Dict]:
    """Load danh sách hotels từ file JSONL"""
    hotels = []
    if os.path.exists(INPUT_JSONL):
        with open(INPUT_JSONL, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    hotel_info = obj.get('hotelInfo', {})
                    summary = hotel_info.get('summary', {})
                    hotel_id = summary.get('hotelId')
                    if hotel_id:
                        hotels.append({
                            'hotelId': str(hotel_id),
                            'data': obj
                        })
                except Exception:
                    continue
    return hotels

def load_existing_amenities() -> Dict[str, List[str]]:
    """Load amenities đã crawl từ file"""
    if os.path.exists(AMENITIES_JSON):
        try:
            with open(AMENITIES_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_amenities(amenities_dict: Dict[str, List[str]]):
    """Lưu amenities vào file"""
    with open(AMENITIES_JSON, 'w', encoding='utf-8') as f:
        json.dump(amenities_dict, f, indent=2, ensure_ascii=False)

def crawl_amenities_for_hotels(driver, hotels: List[Dict], start_index: int = 0, max_hotels: int = None):
    """Crawl amenities cho danh sách hotels"""
    existing_amenities = load_existing_amenities()
    total = len(hotels)
    max_hotels = max_hotels or total
    
    print(f"Total hotels: {total}")
    print(f"Starting from index: {start_index}")
    print(f"Will crawl: {min(max_hotels, total - start_index)} hotels")
    print("="*80)
    
    for i in range(start_index, min(start_index + max_hotels, total)):
        hotel = hotels[i]
        hotel_id = hotel['hotelId']
        
        # Skip nếu đã có amenities
        if hotel_id in existing_amenities and existing_amenities[hotel_id]:
            print(f"[{i+1}/{total}] Skipped {hotel_id} (already has amenities)")
            continue
        
        print(f"\n[{i+1}/{total}] Crawling amenities for hotel: {hotel_id}")
        
        try:
            amenities = extract_amenities_from_api_responses(driver, hotel_id)
            
            if amenities:
                existing_amenities[hotel_id] = amenities
                print(f"  ✓ Found {len(amenities)} amenities: {', '.join(amenities[:5])}")
                if len(amenities) > 5:
                    print(f"    ... and {len(amenities) - 5} more")
            else:
                existing_amenities[hotel_id] = []
                print(f"  ✗ No amenities found")
            
            # Save sau mỗi hotel để tránh mất dữ liệu
            save_amenities(existing_amenities)
            
            # Delay để tránh bị block
            time.sleep(2)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            existing_amenities[hotel_id] = []
            save_amenities(existing_amenities)
            continue
    
    print("\n" + "="*80)
    print("CRAWL AMENITIES COMPLETED!")
    print("="*80)
    print(f"Total hotels processed: {len(existing_amenities)}")
    hotels_with_amenities = sum(1 for v in existing_amenities.values() if v)
    print(f"Hotels with amenities: {hotels_with_amenities}")
    print(f"Hotels without amenities: {len(existing_amenities) - hotels_with_amenities}")

def main():
    print("="*80)
    print("CRAWL AMENITIES FROM DETAIL PAGES")
    print("="*80)
    
    # Load hotels
    hotels = load_hotel_ids()
    if not hotels:
        print("No hotels found in input file!")
        return
    
    print(f"Loaded {len(hotels)} hotels from {INPUT_JSONL}")
    
    try:
        driver = setup_driver()
        print("Driver setup successful")
        
        # Crawl amenities
        # Có thể chỉnh start_index và max_hotels để crawl từng batch
        crawl_amenities_for_hotels(driver, hotels, start_index=0, max_hotels=None)
        
        print(f"\nAmenities saved to: {AMENITIES_JSON}")
        print("You can now merge amenities into main data file.")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\n" + "="*80)
        print("CHROME CHUA MO VOI REMOTE DEBUGGING!")
        print("="*80)
        print("\nVui long mo Chrome voi lenh:")
        print('chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\temp\\chrome_debug"')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()


