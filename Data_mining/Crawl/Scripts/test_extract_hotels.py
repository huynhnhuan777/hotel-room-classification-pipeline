"""
Script test nhanh để kiểm tra xem có extract được hotels không
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from hotels_crawl_hcm import extract_hotels_visible
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
except ImportError:
    UC_AVAILABLE = False

def test_extract():
    print("="*60)
    print("TEST EXTRACT HOTELS")
    print("="*60)
    
    # Setup driver
    if UC_AVAILABLE:
        options = uc.ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        driver = uc.Chrome(options=options, version_main=None)
    else:
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Load cookies nếu có
        cookies_file = 'hotels_cookies.pkl'
        if os.path.exists(cookies_file):
            import pickle
            driver.get("https://vi.hotels.com/")
            time.sleep(2)
            with open(cookies_file, 'rb') as f:
                cookies = pickle.load(f)
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except:
                    pass
            driver.refresh()
            time.sleep(3)
        
        # Test URL
        test_url = "https://vi.hotels.com/Hotel-Search?destination=Thành%20phố%20Hồ%20Chí%20Minh%2C%20Thành%20phố%20Hồ%20Chí%20Minh%2C%20Việt%20Nam&regionId=3140&latLong=10.776308%2C106.702867&flexibility=0_DAY&d1=2026-01-02&startDate=2026-01-02&d2=2026-01-04&endDate=2026-01-04&adults=2&rooms=1&typeaheadCollationId=07b5bf58-7906-4276-b4e4-f87f78f99427&sort=RECOMMENDED&theme=&userIntent=&semdtl=&categorySearch=&useRewards=false"
        
        print(f"\nĐang mở URL: {test_url[:100]}...")
        driver.get(test_url)
        time.sleep(5)

        # Enable Network domain to capture responses (CDP)
        try:
            driver.execute_cdp_cmd("Network.enable", {})
        except Exception:
            pass

        # Print some performance logs (debug)
        try:
            entries = driver.get_log('performance')
            print(f"\n🔎 Performance log entries: {len(entries)}")
            sample_urls = []
            for entry in entries[:50]:
                try:
                    msg = json.loads(entry['message'])['message']
                    if msg.get('method') == 'Network.responseReceived':
                        resp = msg['params']['response']
                        url = resp.get('url')
                        if url:
                            sample_urls.append(url)
                except Exception:
                    continue
            if sample_urls:
                print("\nSome captured URLs:")
                for u in sample_urls[:20]:
                    print(f"  - {u}")
            else:
                print("\nNo URLs found in performance logs.\nConsider enabling logging capabilities when creating the driver.")
        except Exception as e:
            print(f"\n⚠ Could not read performance logs: {e}")
        
        # Kiểm tra xem có hotels không
        print("\n1. Kiểm tra hotel indicators trên trang...")
        try:
            indicators = driver.find_elements(By.CSS_SELECTOR, 
                "[data-hotel-id], .hotel-result, .property-result, a[href*='/hotel/']")
            print(f"   ✓ Tìm thấy {len(indicators)} hotel indicators")
        except Exception as e:
            print(f"   ⚠ Lỗi: {e}")
        
        # Test extract hotels
        print("\n2. Test extract hotels từ trang listing...")
        hotels = extract_hotels_visible(driver)
        print(f"  📊 Tổng cộng tìm thấy {len(hotels)} hotels")
        
        # Show detailed info for first few hotels
        for i, hotel in enumerate(hotels[:5], 1):
            print(f"   {i}. {hotel.get('hotelName', 'Unknown')} (ID: {hotel.get('hotelId', 'N/A')})")
            if len(hotel) > 2:  # Has additional fields
                extra_fields = {k: v for k, v in hotel.items() if k not in ['hotelId', 'hotelName']}
                print(f"      Extra fields: {extra_fields}")
        
        print(f"   Kết quả: {len(hotels)} hotels")
        
        print("\n" + "="*60)
        print("TỔNG KẾT:")
        print(f"  - Hotels extracted: {len(hotels)} hotels")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nNhấn Enter để đóng trình duyệt...")
        driver.quit()

if __name__ == "__main__":
    test_extract()



