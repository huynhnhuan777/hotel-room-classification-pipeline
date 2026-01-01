#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để kiểm tra API detail page và tìm thông tin amenities
"""
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

def setup_driver():
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

def capture_api_responses(driver, url):
    """Capture tất cả API responses khi load detail page"""
    print(f"Loading: {url}")
    driver.get(url)
    time.sleep(5)  # Đợi page load
    
    # Scroll để trigger lazy load
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    time.sleep(2)
    
    # Lấy tất cả performance logs
    entries = driver.get_log('performance')
    api_responses = []
    
    for entry in entries:
        try:
            msg = json.loads(entry['message'])['message']
            if msg.get('method') == 'Network.responseReceived':
                params = msg.get('params', {})
                response = params.get('response', {})
                url_api = response.get('url', '')
                request_id = params.get('requestId')
                
                # Tìm các API có thể chứa detail info
                if any(keyword in url_api.lower() for keyword in [
                    'detail', 'hotel', 'info', 'amenit', 'facilit', 'service',
                    'feature', 'facility', 'property'
                ]):
                    try:
                        body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                        text = body.get('body', '')
                        try:
                            json_data = json.loads(text)
                            api_responses.append({
                                'url': url_api,
                                'requestId': request_id,
                                'data': json_data
                            })
                        except:
                            api_responses.append({
                                'url': url_api,
                                'requestId': request_id,
                                'data': {'_raw': text[:500]}
                            })
                    except Exception as e:
                        print(f"  Error getting body for {url_api}: {e}")
        except Exception:
            continue
    
    return api_responses

def analyze_for_amenities(api_responses):
    """Phân tích các API responses để tìm amenities"""
    print("\n" + "="*80)
    print("ANALYZING API RESPONSES FOR AMENITIES")
    print("="*80)
    
    for i, resp in enumerate(api_responses, 1):
        print(f"\n{i}. API: {resp['url'][:100]}")
        data = resp['data']
        
        if isinstance(data, dict):
            # Tìm các keys có thể chứa amenities
            def find_amenities_keys(obj, path=""):
                found = []
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        key_lower = k.lower()
                        if any(word in key_lower for word in [
                            'amenit', 'facilit', 'service', 'feature', 
                            'tiện', 'dịch vụ', 'equipment', 'equip'
                        ]):
                            found.append(f"{path}.{k}" if path else k)
                        if isinstance(v, (dict, list)):
                            found.extend(find_amenities_keys(v, f"{path}.{k}" if path else k))
                elif isinstance(obj, list):
                    for idx, item in enumerate(obj):
                        found.extend(find_amenities_keys(item, f"{path}[{idx}]"))
                return found
            
            amenities_keys = find_amenities_keys(data)
            if amenities_keys:
                print(f"  ✓ Found potential amenities fields:")
                for key in amenities_keys[:10]:  # Show first 10
                    print(f"    - {key}")
                
                # Show sample data
                print(f"\n  Sample data structure:")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
            else:
                print(f"  - No amenities fields found")
        else:
            print(f"  - Non-JSON response")

def main():
    # Lấy một hotelId từ file JSONL
    hotel_id = None
    try:
        with open('trip_hotels_full.jsonl', 'r', encoding='utf-8') as f:
            line = f.readline()
            obj = json.loads(line)
            hotel_info = obj.get('hotelInfo', {})
            summary = hotel_info.get('summary', {})
            hotel_id = summary.get('hotelId')
    except:
        print("Error reading hotel ID from file")
        return
    
    if not hotel_id:
        print("No hotel ID found")
        return
    
    # URL detail page
    detail_url = f"https://vn.trip.com/hotels/detail/?hotelId={hotel_id}"
    
    print("="*80)
    print("CHECKING DETAIL PAGE API FOR AMENITIES")
    print("="*80)
    print(f"Hotel ID: {hotel_id}")
    print(f"Detail URL: {detail_url}")
    
    try:
        driver = setup_driver()
        print("\nDriver setup successful")
        
        # Capture API responses
        api_responses = capture_api_responses(driver, detail_url)
        
        print(f"\nCaptured {len(api_responses)} API responses")
        
        # Analyze
        analyze_for_amenities(api_responses)
        
        # Save to file for inspection
        with open('detail_api_responses.json', 'w', encoding='utf-8') as f:
            json.dump(api_responses, f, indent=2, ensure_ascii=False)
        print(f"\nSaved API responses to: detail_api_responses.json")
        
        driver.quit()
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\n" + "="*80)
        print("CHROME CHUA MO VOI REMOTE DEBUGGING!")
        print("="*80)
        print("\nVui long mo Chrome voi lenh sau:")
        print('chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\temp\\chrome_debug"')
        print("\nSau do chay lai script nay.")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

