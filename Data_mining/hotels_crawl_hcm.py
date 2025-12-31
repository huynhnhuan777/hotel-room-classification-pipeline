"""
Script crawl dữ liệu hotels từ hotels.com cho khu vực TP.HCM
Phiên bản tối ưu với UI visible để debug
"""
import json
import time
import pickle
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from datetime import datetime, timedelta
from urllib.parse import quote

try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
except ImportError:
    UC_AVAILABLE = False

# Cấu hình
TARGET_NEW_COUNT = 1000
MAX_RETRIES = 3
TEST_MODE = False  # Chế độ test: chỉ crawl vài khách sạn để kiểm tra
TEST_HOTEL_COUNT = 3  # Số khách sạn crawl trong test mode
OUTPUT_FILE = 'hotels_complete_hcm.jsonl'  # File duy nhất chứa tất cả dữ liệu

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def human_like_delay(min_seconds=1, max_seconds=3):
    """Random delay để giả lập hành vi người dùng"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def setup_visible_driver():
    """Setup driver với Chrome remote debugging - ƯU TIÊN"""
    print("  🔧 Setting up driver với Chrome remote debugging...")
    print("  ℹ Đảm bảo Chrome đã được mở với: start_chrome_debug.bat")
    print("")

    # Cấu hình để kết nối với Chrome đã mở sẵn
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    # Thêm các options khác để đảm bảo hoạt động tốt
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        # Kết nối với Chrome đã mở sẵn
        print("  🔌 Đang kết nối với Chrome (port 9222)...")
        driver = webdriver.Chrome(options=options)
        
        print("  ✓ Đã kết nối với Chrome đang chạy (remote debugging)")
        print("  ℹ Chrome profile: C:\\selenium\\ChromeProfile")
        print("  ℹ Remote debugging port: 9222")
        
        # Test driver - lấy URL hiện tại
        try:
            current_url = driver.current_url
            if current_url:
                print(f"  ✓ Current page: {current_url[:80]}...")
            else:
                print("  ✓ Driver connected successfully")
        except:
            print("  ✓ Driver connected successfully")
        
        return driver

    except Exception as e:
        print(f"\n  ❌ Không thể kết nối với Chrome remote debugging!")
        print(f"  Lỗi: {e}")
        print("\n  📋 HƯỚNG DẪN:")
        print("  1. Mở Chrome với remote debugging bằng một trong các cách:")
        print("     - Chạy: start_chrome_debug.bat")
        print("     - Hoặc PowerShell: .\\start_chrome_debug.ps1")
        print("     - Hoặc thủ công:")
        print('       "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\\selenium\\ChromeProfile"')
        print("  2. Đợi Chrome mở hoàn toàn")
        print("  3. Chạy lại script này\n")
        
        response = input("  Bạn có muốn thử fallback với undetected-chromedriver? (y/n): ")
        if response.lower() != 'y':
            raise Exception("Chrome remote debugging không khả dụng. Vui lòng mở Chrome với remote debugging trước.")
        
        print("  🔄 Thử mở Chrome mới với undetected-chromedriver...")
        
        if not UC_AVAILABLE:
            raise Exception("undetected-chromedriver is required. Cài đặt: pip install undetected-chromedriver")

        # Fallback: Sử dụng undetected-chromedriver
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--lang=en-US')
        
        user_agent = random.choice(USER_AGENTS)
        options.add_argument(f'--user-agent={user_agent}')

        driver = uc.Chrome(options=options, version_main=None)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        driver.get("https://www.google.com")
        human_like_delay(2, 3)
        
        print("  ✓ Driver ready with visible UI (fallback mode)")
        return driver

def generate_many_urls():
    """Generate nhiều URLs với variations"""
    urls = []
    base_url = "https://vi.hotels.com/Hotel-Search"

    # Sort orders
    sorts = ["RECOMMENDED", "PRICE_LOW_TO_HIGH", "PRICE_HIGH_TO_LOW", "DISTANCE", "STAR_RATING"]

    # Price ranges
    prices = ["", "&price=0-2000000", "&price=2000000-5000000", "&price=5000000-10000000"]

    # Stars
    stars = ["", "&stars=5", "&stars=4", "&stars=3"]

    destination = "Thành phố Hồ Chí Minh, Thành phố Hồ Chí Minh, Việt Nam"
    region_id = "3140"
    lat_long = "10.776308,106.702867"
    typeahead_collation_id = "07b5bf58-7906-4276-b4e4-f87f78f99427"

    start = datetime.strptime("2026-01-01", "%Y-%m-%d")

    for i in range(150):  # 150 dates
        checkin = start + timedelta(days=i)
        checkout = checkin + timedelta(days=random.randint(1, 3))

        d1 = checkin.strftime("%Y-%m-%d")
        d2 = checkout.strftime("%Y-%m-%d")

        for sort in sorts[:3]:  # 3 sorts
            for price in prices[:2]:  # 2 price ranges
                url = f"{base_url}?destination={quote(destination)}&regionId={region_id}&latLong={lat_long}&flexibility=0_DAY&d1={d1}&startDate={d1}&d2={d2}&endDate={d2}&adults=2&rooms=1&typeaheadCollationId={typeahead_collation_id}&sort={sort}{price}&theme=&userIntent=&semdtl=&categorySearch=&useRewards=false"
                urls.append(url)

                if len(urls) >= 800:  # Limit to 800 URLs
                    break
            if len(urls) >= 800:
                break
        if len(urls) >= 800:
            break

    random.shuffle(urls)
    print(f"✓ Generated {len(urls)} URLs")
    return urls

def extract_hotels_visible(driver):
    """Extract hotels với UI visible để debug"""
    hotels = []
    try:
        print("  🔍 Extracting hotels...")

        # Scroll 4 lần đầu tiên
        print("  📜 Scrolling 4 times initially...")
        for i in range(4):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print(f"  📜 Initial scroll {i+1}/4")
            human_like_delay(2, 4)

        # Tìm và click nút "xem thêm" (load more)
        load_more_clicked = 0
        max_load_more_clicks = 5  # Click tối đa 5 lần

        while load_more_clicked < max_load_more_clicks:
            try:
                # Tìm nút "xem thêm" - ưu tiên tìm theo text
                load_more_button = None
                
                # Method 1: Tìm tất cả buttons và check text
                try:
                    all_buttons = driver.find_elements(By.TAG_NAME, "button")
                    for btn in all_buttons:
                        try:
                            btn_text = btn.text.strip().lower()
                            if 'xem thêm' in btn_text or 'xem thêm kết quả' in btn_text:
                                if btn.is_displayed() and btn.is_enabled():
                                    load_more_button = btn
                                    print(f"  ✓ Tìm thấy nút 'xem thêm' với text: {btn.text[:50]}")
                                    break
                        except:
                            continue
                except:
                    pass
                
                # Method 2: Tìm bằng CSS selectors
                if not load_more_button:
                    load_more_selectors = [
                        "button[data-stid*='load-more']",
                        "button[data-stid*='show-more']",
                        "button[class*='load-more']",
                        "button[class*='show-more']",
                        "[data-testid*='load-more']",
                        "[aria-label*='xem thêm']",
                        "[aria-label*='load more']",
                        ".uitk-button[aria-label*='xem thêm']",
                    ]
                    
                    for selector in load_more_selectors:
                        try:
                            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                            for btn in buttons:
                                if btn.is_displayed() and btn.is_enabled():
                                    btn_text = btn.text.strip().lower() or btn.get_attribute('aria-label') or ""
                                    if 'xem thêm' in btn_text.lower() or 'load more' in btn_text.lower():
                                        load_more_button = btn
                                        break
                            if load_more_button:
                                break
                        except:
                            continue

                if load_more_button and load_more_button.is_displayed():
                    print(f"  🔘 Found load more button, clicking... (attempt {load_more_clicked + 1})")
                    # Scroll to button
                    driver.execute_script("arguments[0].scrollIntoView();", load_more_button)
                    human_like_delay(1, 2)

                    # Click button
                    load_more_button.click()
                    load_more_clicked += 1

                    # Wait for new hotels to load
                    print("  ⏳ Waiting for more hotels to load...")
                    human_like_delay(3, 5)

                    # Scroll a bit more to trigger loading
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    human_like_delay(2, 3)
                else:
                    print("  ⚠ No load more button found or not visible")
                    break

            except Exception as e:
                print(f"  ⚠ Error clicking load more button: {e}")
                break

        print(f"  ✅ Clicked load more button {load_more_clicked} times")

        # Scroll thêm một chút nữa để đảm bảo tất cả hotels đã load
        print("  📜 Final scroll to ensure all hotels loaded...")
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            human_like_delay(1, 2)

        # Find hotel elements - CHỈ lấy elements có data-stid='lodging-card-responsive'
        # Vì selector .uitk-card lấy cả map, filters, etc.
        hotel_elements = []
        try:
            # Ưu tiên selector chính xác nhất
            elements = driver.find_elements(By.CSS_SELECTOR, "[data-stid='lodging-card-responsive']")
            if elements:
                hotel_elements = elements
                print(f"  🎯 Found {len(elements)} hotel cards with data-stid='lodging-card-responsive'")
            else:
                # Fallback: Tìm các elements có link đến hotel
                print("  ⚠ No elements with data-stid='lodging-card-responsive', trying fallback...")
                all_cards = driver.find_elements(By.CSS_SELECTOR, ".uitk-card")
                for card in all_cards:
                    try:
                        # Kiểm tra xem có link đến hotel không
                        links = card.find_elements(By.CSS_SELECTOR, "a[href*='/hotel/'], a[href*='/ho']")
                        if links:
                            hotel_elements.append(card)
                    except:
                        continue
                print(f"  🎯 Found {len(hotel_elements)} hotel cards with hotel links")
        except Exception as e:
            print(f"  ⚠ Error finding hotel elements: {e}")

        print(f"  📊 Total hotel elements found: {len(hotel_elements)}")
        
        # Filter: Chỉ giữ các elements có link đến hotel
        filtered_elements = []
        for elem in hotel_elements:
            try:
                # Kiểm tra có link đến hotel không
                links = elem.find_elements(By.CSS_SELECTOR, "a[href*='/hotel/'], a[href*='/ho']")
                if links:
                    filtered_elements.append(elem)
            except:
                continue
        
        hotel_elements = filtered_elements
        print(f"  ✅ Filtered to {len(hotel_elements)} valid hotel cards")

        # Debug: Print first element structure
        if hotel_elements:
            print("  🔍 Debug: First element attributes and HTML:")
            first_elem = hotel_elements[0]
            print(f"    Tag: {first_elem.tag_name}")
            print(f"    data-stid: {first_elem.get_attribute('data-stid')}")
            print(f"    data-hotel-id: {first_elem.get_attribute('data-hotel-id')}")
            print(f"    class: {first_elem.get_attribute('class')}")
            print(f"    Inner HTML (first 200 chars): {first_elem.get_attribute('innerHTML')[:200]}...")

        for idx, elem in enumerate(hotel_elements[:100]):  # Process up to 100 hotels now
            try:
                hotel = {}

                # Debug print element info
                if idx < 3:  # Only debug first 3 hotels
                    print(f"  🔍 Processing hotel {idx+1}:")
                    print(f"    Element tag: {elem.tag_name}")
                    print(f"    Element class: {elem.get_attribute('class')}")
                    print(f"    Element data-stid: {elem.get_attribute('data-stid')}")

                # Get ID - try multiple approaches
                hotel_id = None
                hotel_url = None
                
                # KHÔNG dùng data-stid làm hotel ID (vì nó là "lodging-card-responsive")
                # Try data-hotel-id first (nhưng thường không có)
                hotel_id = elem.get_attribute('data-hotel-id') or elem.get_attribute('data-id') or elem.get_attribute('data-property-id')
                
                # Try extracting from URL - thử nhiều cách tìm link
                if not hotel_id:
                    # Tìm tất cả links trong element
                    try:
                        all_links = elem.find_elements(By.TAG_NAME, "a")
                        if not all_links:
                            # Thử tìm với CSS selector
                            all_links = elem.find_elements(By.CSS_SELECTOR, "a[href]")
                    except:
                        all_links = []
                    
                    # Kiểm tra từng link
                    import re
                    patterns = [
                        r'/ho(\d+)/',  # Format: /ho443853/ (Expedia property ID) - QUAN TRỌNG NHẤT
                        r'/hotel/(\d+)',
                        r'/Hotel-(\d+)',
                        r'/en/hotel/(\d+)',
                        r'/property/(\d+)',
                        r'hotel[_-]?(\d+)',
                        r'expediaPropertyId=(\d+)',  # From URL params
                    ]
                    
                    for link in all_links:
                        try:
                            href = link.get_attribute('href') or ""
                            if not href:
                                continue
                            
                            # Normalize URL
                            if not href.startswith('http'):
                                if href.startswith('/'):
                                    href = 'https://vi.hotels.com' + href
                                else:
                                    continue
                            
                            # Extract hotel ID
                            for pattern in patterns:
                                match = re.search(pattern, href, re.IGNORECASE)
                                if match:
                                    hotel_id = match.group(1)
                                    hotel_url = href
                                    break
                            
                            if hotel_id:
                                break
                        except:
                            continue
                    
                    # Nếu vẫn không tìm thấy, thử tìm trong innerHTML
                    if not hotel_id:
                        try:
                            html = elem.get_attribute('innerHTML') or ""
                            # Tìm tất cả URLs trong HTML
                            url_pattern = r'href=["\']([^"\']*(?:/ho\d+|/hotel/|expediaPropertyId=)[^"\']*)["\']'
                            url_matches = re.findall(url_pattern, html, re.IGNORECASE)
                            
                            for url_str in url_matches:
                                # Normalize URL
                                if not url_str.startswith('http'):
                                    if url_str.startswith('/'):
                                        url_str = 'https://vi.hotels.com' + url_str
                                    else:
                                        continue
                                
                                # Extract hotel ID từ URL
                                for pattern in patterns:
                                    match = re.search(pattern, url_str, re.IGNORECASE)
                                    if match:
                                        hotel_id = match.group(1)
                                        hotel_url = url_str
                                        break
                                
                                if hotel_id:
                                    break
                        except Exception as e:
                            if idx < 3:
                                print(f"    ⚠ Error extracting from HTML: {e}")
                            pass

                # Debug: Print what we found
                if idx < 3:
                    print(f"    Found hotel_id: {hotel_id}")
                    print(f"    Found hotel_url: {hotel_url}")

                if not hotel_id:
                    # Skip if no valid ID
                    if idx < 3:
                        print(f"    ⚠ Skipping - no hotel ID found")
                    continue

                hotel['hotelId'] = str(hotel_id)
                if hotel_url:
                    hotel['hotelUrl'] = hotel_url

                # Get name - try multiple selectors với nhiều cách hơn
                hotel_name = None
                name_selectors = [
                    "[data-stid='content-hotel-title']",
                    "[data-testid*='property-name']",
                    "[data-testid*='hotel-name']",
                    "h3", 
                    "h4",
                    "h2",
                    "a[href*='/hotel/']",
                    "a[href*='/Hotel-']",
                    "[class*='hotel-name']",
                    "[class*='property-name']",
                    "[class*='title']",
                    ".uitk-heading",
                ]
                
                for name_sel in name_selectors:
                    try:
                        name_elems = elem.find_elements(By.CSS_SELECTOR, name_sel)
                        for name_elem in name_elems:
                            text = name_elem.text.strip()
                            # Filter out invalid names
                            if text and len(text) > 3 and len(text) < 200:
                                if not any(skip in text.lower() for skip in ['http', 'www', 'click', 'view', 'more']):
                                    hotel_name = text
                                    break
                        if hotel_name:
                            break
                    except:
                        continue
                
                # Fallback: Try to get text from link
                if not hotel_name and hotel_url:
                    try:
                        link = elem.find_element(By.CSS_SELECTOR, f"a[href*='{hotel_id}']")
                        hotel_name = link.text.strip()
                    except:
                        pass

                # Debug
                if idx < 3:
                    print(f"    Found hotel_name: {hotel_name}")

                if not hotel_name:
                    if idx < 3:
                        print(f"    ⚠ Skipping - no hotel name found")
                    continue

                hotel['hotelName'] = hotel_name
                
                # Get star rating from listing page
                try:
                    star_selectors = [
                        "[class*='star']", "[data-testid*='star']", "[aria-label*='star']",
                        ".uitk-rating", "[class*='rating']", "svg[aria-label*='star']"
                    ]
                    for star_sel in star_selectors:
                        try:
                            star_elems = elem.find_elements(By.CSS_SELECTOR, star_sel)
                            for star_elem in star_elems:
                                star_text = star_elem.text.strip() or star_elem.get_attribute('aria-label') or ""
                                import re
                                star_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:star|sao)', star_text, re.IGNORECASE)
                                if star_match:
                                    star_val = float(star_match.group(1))
                                    if 1 <= star_val <= 5:
                                        hotel['star'] = star_val
                                        hotel['starType'] = int(star_val)
                                        break
                                # Also check for filled stars
                                elif 'star' in star_text.lower():
                                    filled_stars = len(star_elem.find_elements(By.CSS_SELECTOR, "[fill*='#'], svg"))
                                    if 1 <= filled_stars <= 5:
                                        hotel['star'] = filled_stars
                                        hotel['starType'] = filled_stars
                                        break
                            if 'star' in hotel:
                                break
                        except:
                            continue
                except:
                    pass

                # Get review score and text from listing page
                try:
                    review_selectors = [
                        "[class*='review']", "[data-testid*='review']", "[class*='rating']",
                        ".uitk-rating", "[aria-label*='review']"
                    ]
                    for review_sel in review_selectors:
                        try:
                            review_elems = elem.find_elements(By.CSS_SELECTOR, review_sel)
                            for review_elem in review_elems:
                                review_text = review_elem.text.strip()
                                import re
                                # Match rating like "8.5" or "4.2/5"
                                score_match = re.search(r'(\d+(?:\.\d+)?)(?:\s*/\s*5)?', review_text)
                                if score_match:
                                    score_val = float(score_match.group(1))
                                    if 0 <= score_val <= 10:  # Allow up to 10 for some rating systems
                                        hotel['reviewScore'] = score_val
                                        hotel['reviewScoreText'] = review_text
                                        break
                            if 'reviewScore' in hotel:
                                break
                        except:
                            continue
                except:
                    pass

                # Get location và cityId - enhanced
                try:
                    loc_selectors = ["[class*='location']", ".location", "[data-testid*='location']", ".uitk-text", "[class*='address']"]
                    for loc_sel in loc_selectors:
                        try:
                            loc_elems = elem.find_elements(By.CSS_SELECTOR, loc_sel)
                            for loc_elem in loc_elems:
                                loc_text = loc_elem.text.strip()
                                if loc_text and len(loc_text) > 2:
                                    if 'Ho Chi Minh' in loc_text or 'Hồ Chí Minh' in loc_text or 'TP.HCM' in loc_text or 'Sài Gòn' in loc_text:
                                        hotel['cityName'] = 'Ho Chi Minh City'
                                        hotel['cityId'] = '94122'
                                        # Extract district if present
                                        import re
                                        district_match = re.search(r'(Quận\s+\d+|District\s+\d+|Phường\s+[^,]+)', loc_text, re.IGNORECASE)
                                        if district_match:
                                            hotel['districtName'] = district_match.group(1).strip()
                                        elif 'Quận' in loc_text or 'District' in loc_text:
                                            hotel['districtName'] = loc_text
                                    elif any(district in loc_text.lower() for district in ['quận', 'district', 'phường', 'ward']):
                                        hotel['districtName'] = loc_text
                                    else:
                                        # Could be nearby landmark
                                        hotel['nearbyLandmark'] = loc_text
                                    break
                        except:
                            continue
                except:
                    pass
                
                # Set default categoryName và categoryId
                hotel['categoryName'] = '1. Khách sạn'
                hotel['categoryId'] = '405'

                # Get price - enhanced to also get avg/original price
                try:
                    price_selectors = ["[class*='price']", "[data-testid*='price']", ".uitk-text", "span", "div"]
                    for price_sel in price_selectors:
                        try:
                            price_elems = elem.find_elements(By.CSS_SELECTOR, price_sel)
                            for price_elem in price_elems:
                                price_text = price_elem.text.strip()
                                if '₫' in price_text or 'VND' in price_text or 'đ' in price_text:
                                    import re
                                    # Match numbers with commas and dots
                                    price_matches = re.findall(r'([\d.,]+)', price_text.replace(' ', ''))
                                    if price_matches:
                                        prices = []
                                        for match in price_matches:
                                            price_str = match.replace(',', '').replace('.', '')
                                            try:
                                                price_val = int(price_str)
                                                if 10000 <= price_val <= 10000000:  # Reasonable price range
                                                    prices.append(price_val)
                                            except:
                                                pass
                                        
                                        if prices:
                                            hotel['minPrice'] = min(prices)
                                            if len(prices) > 1:
                                                hotel['avgPrice'] = sum(prices) // len(prices)
                                                hotel['originalPrice'] = max(prices)
                                            hotel['currency'] = 'VND'
                                            break
                            if 'minPrice' in hotel:
                                break
                        except:
                            continue
                except:
                    pass

                # Get review count - enhanced
                try:
                    review_selectors = ["[class*='review']", "[data-testid*='review']", ".uitk-text", "[class*='rating']"]
                    for review_sel in review_selectors:
                        try:
                            review_elems = elem.find_elements(By.CSS_SELECTOR, review_sel)
                            for review_elem in review_elems:
                                review_text = review_elem.text.strip()
                                import re
                                # Match patterns like "1,234 reviews", "(123)", "123 đánh giá"
                                count_match = re.search(r'(\d+(?:[,.]\d{3})*)', review_text)
                                if count_match:
                                    count_str = count_match.group(1).replace(',', '').replace('.', '')
                                    try:
                                        count_val = int(count_str)
                                        if 1 <= count_val <= 100000:  # Reasonable review count
                                            hotel['reviewCount'] = count_val
                                            break
                                    except:
                                        pass
                            if 'reviewCount' in hotel:
                                break
                        except:
                            continue
                except:
                    pass

                # Get additional info like rooms left, last booked
                try:
                    info_selectors = ["[class*='availability']", "[data-testid*='availability']", ".uitk-text", "small", "span"]
                    for info_sel in info_selectors:
                        try:
                            info_elems = elem.find_elements(By.CSS_SELECTOR, info_sel)
                            for info_elem in info_elems:
                                info_text = info_elem.text.strip().lower()
                                if 'còn' in info_text and 'phòng' in info_text:
                                    import re
                                    room_match = re.search(r'(\d+)\s*phòng', info_text)
                                    if room_match:
                                        hotel['roomsLeft'] = int(room_match.group(1))
                                elif 'đặt' in info_text and ('gần đây' in info_text or 'ago' in info_text):
                                    hotel['lastBookedText'] = info_elem.text.strip()
                                elif 'hết phòng' in info_text or 'sold out' in info_text:
                                    hotel['isSoldOut'] = True
                        except:
                            continue
                except:
                    pass

                # Get button content
                try:
                    button_selectors = ["button", "[role='button']", ".uitk-button"]
                    for btn_sel in button_selectors:
                        try:
                            btn_elems = elem.find_elements(By.CSS_SELECTOR, btn_sel)
                            for btn_elem in btn_elems:
                                btn_text = btn_elem.text.strip()
                                if btn_text and len(btn_text) < 50:
                                    if not any(skip in btn_text.lower() for skip in ['xem', 'view', 'more', 'chi tiết']):
                                        hotel['buttonContent'] = btn_text
                                        break
                            if 'buttonContent' in hotel:
                                break
                        except:
                            continue
                except:
                    pass

                # Get URL (nếu chưa có)
                if 'hotelUrl' not in hotel:
                    try:
                        link_selectors = [
                            f"a[href*='{hotel_id}']",
                            "a[href*='/hotel/']",
                            "a[href*='/Hotel-']",
                        ]
                        for link_sel in link_selectors:
                            try:
                                link = elem.find_element(By.CSS_SELECTOR, link_sel)
                                href = link.get_attribute('href')
                                if href:
                                    if not href.startswith('http'):
                                        href = 'https://vi.hotels.com' + href
                                    hotel['hotelUrl'] = href
                                    break
                            except:
                                continue
                    except:
                        pass

                if hotel.get('hotelId') and hotel.get('hotelName'):
                    hotels.append(hotel)
                    print(f"  ✅ Hotel {idx+1}: {hotel['hotelName'][:50]}... (ID: {hotel['hotelId']})")

            except Exception as e:
                print(f"  ❌ Error processing hotel {idx+1}: {e}")
                continue

    except Exception as e:
        print(f"  ❌ Extraction error: {e}")

    return hotels

def save_complete_hotel(hotel_data):
    """Save hotel với đầy đủ thông tin (amenities, rooms) vào file duy nhất"""
    hotel_id = hotel_data.get('hotelId', 'UNKNOWN')
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Tạo JSON line
            json_line = json.dumps(hotel_data, ensure_ascii=False) + '\n'
            
            # Mở file và ghi với mode append
            f = None
            try:
                f = open(OUTPUT_FILE, 'a', encoding='utf-8', newline='\n')
                f.write(json_line)
                f.flush()  # Đảm bảo ghi vào buffer ngay
                
                # Đảm bảo ghi vào disk
                if hasattr(f, 'fileno'):
                    try:
                        os.fsync(f.fileno())
                    except (OSError, AttributeError):
                        pass  # Một số hệ thống không hỗ trợ fsync
                
                # Đóng file ngay lập tức
                f.close()
                f = None
                
                # Verify: Đọc lại file để kiểm tra dòng cuối cùng
                try:
                    with open(OUTPUT_FILE, 'r', encoding='utf-8') as verify_f:
                        lines = verify_f.readlines()
                        if lines:
                            last_line = lines[-1].strip()
                            if last_line:
                                last_hotel = json.loads(last_line)
                                if str(last_hotel.get('hotelId')) == str(hotel_id):
                                    return True
                                else:
                                    # Dòng cuối không phải hotel này, nhưng có thể đã ghi
                                    # Kiểm tra toàn bộ file
                                    for line in lines:
                                        try:
                                            h = json.loads(line.strip())
                                            if str(h.get('hotelId')) == str(hotel_id):
                                                return True
                                        except:
                                            continue
                except Exception as verify_err:
                    # Nếu verify lỗi nhưng đã ghi được, vẫn return True
                    if attempt == max_retries - 1:
                        print(f"  ⚠ Không thể verify hotel {hotel_id} nhưng đã ghi file: {verify_err}")
                        return True
                
                # Nếu đến đây mà chưa return, thử lại
                if attempt < max_retries - 1:
                    time.sleep(0.1)  # Đợi một chút trước khi retry
                    continue
                
                return True
                
            finally:
                if f is not None:
                    try:
                        f.close()
                    except:
                        pass
                        
        except IOError as e:
            if attempt < max_retries - 1:
                print(f"  ⚠ Lỗi IO khi lưu hotel {hotel_id} (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(0.2)
                continue
            else:
                print(f"  ❌ LỖI LƯU FILE cho hotel {hotel_id} sau {max_retries} lần thử: {e}")
                import traceback
                traceback.print_exc()
                return False
        except Exception as e:
            print(f"  ❌ LỖI LƯU FILE cho hotel {hotel_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return False

def crawl_hotel_detail(driver, hotel_url, hotel_id):
    """Crawl chi tiết từ trang hotel detail: amenities, rooms và các trường khác"""
    hotel_detail = {}
    rooms = []
    
    try:
        print(f"  📄 Đang crawl detail từ: {hotel_url[:80]}...")
        
        # Lưu URL hiện tại
        current_url = driver.current_url
        
        # Navigate đến trang detail
        driver.get(hotel_url)
        human_like_delay(4, 6)
        
        # Đợi trang load
        try:
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except:
            pass
        
        # Extract checkin/checkout dates từ URL
        import re
        from urllib.parse import urlparse, parse_qs
        try:
            parsed_url = urlparse(hotel_url)
            params = parse_qs(parsed_url.query)
            if 'chkin' in params:
                checkin_str = params['chkin'][0]
                # Convert từ YYYY-MM-DD sang YYYYMMDD
                checkin_date = checkin_str.replace('-', '')
                hotel_detail['checkinDat'] = checkin_date
            if 'chkout' in params:
                checkout_str = params['chkout'][0]
                checkout_date = checkout_str.replace('-', '')
                hotel_detail['checkOutDates'] = checkout_date
        except:
            pass
        
        # Extract star rating
        try:
            star_selectors = [
                "[data-stid*='star']",
                "[class*='star-rating']",
                "[class*='star']",
                "[data-testid*='star']"
            ]
            for star_sel in star_selectors:
                try:
                    star_elems = driver.find_elements(By.CSS_SELECTOR, star_sel)
                    for star_elem in star_elems:
                        star_text = star_elem.text.strip()
                        star_match = re.search(r'(\d+)', star_text)
                        if star_match:
                            star_val = int(star_match.group(1))
                            if 1 <= star_val <= 5:
                                hotel_detail['starType'] = star_val
                                break
                    if 'starType' in hotel_detail:
                        break
                except:
                    continue
        except:
            pass
        
        # Extract address và location
        try:
            address_selectors = [
                "[data-stid='content-hotel-location']",
                "[class*='address']",
                "[class*='location']",
                "[data-testid*='address']"
            ]
            for addr_sel in address_selectors:
                try:
                    addr_elems = driver.find_elements(By.CSS_SELECTOR, addr_sel)
                    for addr_elem in addr_elems:
                        addr_text = addr_elem.text.strip()
                        if addr_text and len(addr_text) > 5:
                            hotel_detail['address'] = addr_text
                            break
                    if 'address' in hotel_detail:
                        break
                except:
                    continue
        except:
            pass
        
        # Extract latitude, longitude từ map hoặc data attributes
        try:
            # Tìm trong data attributes
            map_elements = driver.find_elements(By.CSS_SELECTOR, "[data-lat], [data-lng], [data-latitude], [data-longitude]")
            for map_elem in map_elements:
                try:
                    lat = map_elem.get_attribute('data-lat') or map_elem.get_attribute('data-latitude')
                    lng = map_elem.get_attribute('data-lng') or map_elem.get_attribute('data-longitude')
                    if lat and lng:
                        hotel_detail['latitude'] = float(lat)
                        hotel_detail['longitude'] = float(lng)
                        break
                except:
                    continue
            
            # Nếu không tìm thấy, thử tìm trong script tags
            if 'latitude' not in hotel_detail:
                scripts = driver.find_elements(By.TAG_NAME, "script")
                for script in scripts:
                    script_text = script.get_attribute('innerHTML') or ''
                    lat_match = re.search(r'latitude["\']?\s*[:=]\s*([\d.]+)', script_text, re.IGNORECASE)
                    lng_match = re.search(r'longitude["\']?\s*[:=]\s*([\d.]+)', script_text, re.IGNORECASE)
                    if lat_match and lng_match:
                        hotel_detail['latitude'] = float(lat_match.group(1))
                        hotel_detail['longitude'] = float(lng_match.group(1))
                        break
        except:
            pass
        
        # Extract rating
        try:
            rating_selectors = [
                "[data-stid*='rating']",
                "[class*='rating']",
                "[data-testid*='rating']"
            ]
            for rating_sel in rating_selectors:
                try:
                    rating_elems = driver.find_elements(By.CSS_SELECTOR, rating_sel)
                    for rating_elem in rating_elems:
                        rating_text = rating_elem.text.strip()
                        rating_match = re.search(r'([\d.]+)', rating_text)
                        if rating_match:
                            rating_val = float(rating_match.group(1))
                            if 0 <= rating_val <= 10:
                                hotel_detail['fullRating'] = rating_val
                                break
                    if 'fullRating' in hotel_detail:
                        break
                except:
                    continue
        except:
            pass
        
        # 1. Extract Amenities (Tiện ích)
        print("  🔍 Đang extract amenities...")
        amenities = []
        
        # Tìm section "Thông tin về nơi lưu trú này"
        try:
            # Tìm text "Thông tin về nơi lưu trú này"
            info_sections = driver.find_elements(By.XPATH, "//*[contains(text(), 'Thông tin về nơi lưu trú này')]")
            if info_sections:
                # Lấy parent section chứa amenities
                for info_section in info_sections:
                    try:
                        # Tìm parent container
                        parent = info_section.find_element(By.XPATH, "./ancestor::section | ./ancestor::div[@class] | ./ancestor::div[@data-testid]")
                        if parent:
                            # Tìm tất cả amenity items trong section này
                            amenity_items = parent.find_elements(By.CSS_SELECTOR, 
                                "[class*='amenity'], [class*='facility'], [data-testid*='amenity'], li, .uitk-text")
                            
                            for item in amenity_items:
                                text = item.text.strip()
                                if text and len(text) > 2 and len(text) < 100:
                                    # Loại bỏ text không phải amenities
                                    if not any(noise in text.lower() for noise in [
                                        'xem thêm', 'ẩn bớt', 'tất cả', 'chi tiết', 'thông tin',
                                        'đánh giá', 'hình ảnh', 'vị trí', 'liên hệ', 'đặt phòng',
                                        'giá', 'chính sách', 'quy tắc', 'hủy', 'thay đổi'
                                    ]):
                                        if text not in amenities:
                                            amenities.append(text)
                            
                            if amenities:
                                break
                    except:
                        continue
        except:
            pass
        
        # Nếu không tìm thấy, thử cách cũ
        if not amenities:
            amenity_selectors = [
                "[data-stid='content-hotel-amenities']",
                "[class*='amenity']",
                "[class*='facility']",
                "[data-testid*='amenity']",
                "[data-testid*='facility']",
            ]
            
            for selector in amenity_selectors:
                try:
                    amenity_elems = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in amenity_elems:
                        text = elem.text.strip()
                        if text and len(text) > 2:
                            # Split by newlines hoặc commas
                            items = [item.strip() for item in text.replace('\n', ',').split(',') if item.strip()]
                            amenities.extend(items)
                    if amenities:
                        break
                except:
                    continue
        
        # Lọc amenities: loại bỏ các text không phải amenities thực sự
        noise_keywords = [
            'tổng quan', 'khách', 'ngày', 'giá', 'phản hồi', 'người lớn', 'trẻ em',
            'xem', 'tăng', 'giảm', 'phòng', 'thông tin', 'nút', 'chia sẻ',
            'overview', 'guest', 'date', 'price', 'review', 'adult', 'child',
            'view', 'increase', 'decrease', 'room', 'info', 'button', 'share',
            'hotels.com', 'rewards', 'tích lũy', 'đổi thưởng', 'đăng nhập', 'lưu',
            'login', 'save', 'bản đồ', 'map', 'ảnh', 'photo', 'image',
            'đặt chuyến đi', 'điểm đến', 'chính sách', '1/', '2/', '3/', '4/', '5/', '6/',
            'opens in new window', 'hiển thị', 'thẻ trước', 'thẻ tiếp'
        ]
        
        filtered_amenities = []
        for amenity in amenities:
            amenity_lower = amenity.lower().strip()
            # Loại bỏ nếu quá ngắn, quá dài, hoặc chứa noise keywords
            if (len(amenity_lower) < 3 or len(amenity_lower) > 50 or
                any(noise in amenity_lower for noise in noise_keywords) or
                amenity_lower.isdigit() or
                amenity_lower in ['1', '2', '3', '4', '5', '6']):
                continue
            # Chỉ thêm nếu chưa có
            if amenity not in filtered_amenities:
                filtered_amenities.append(amenity)
        
        hotel_detail['amenities'] = filtered_amenities[:30]  # Giới hạn 30 amenities
        print(f"  ✓ Tìm thấy {len(hotel_detail['amenities'])} amenities (sau khi lọc)")
        
        # 2. Extract Rooms (Các loại phòng)
        print("  🔍 Đang extract rooms...")
        
        # Scroll để load rooms
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.5);")
        human_like_delay(2, 3)
        
        room_types = []
        
        # Tìm section "Chọn phòng" hoặc tương tự
        try:
            room_section_selectors = [
                "//*[contains(text(), 'Chọn phòng')]",
                "//*[contains(text(), 'Select room')]",
                "//h2[contains(text(), 'phòng')]",
                "//h3[contains(text(), 'phòng')]",
                "[data-stid*='room']",
                "[class*='room-selection']"
            ]
            
            room_section = None
            for selector in room_section_selectors:
                try:
                    if selector.startswith("//"):
                        elements = driver.find_elements(By.XPATH, selector)
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        room_section = elements[0]
                        break
                except:
                    continue
            
            if room_section:
                # Tìm parent container của room section
                try:
                    container = room_section.find_element(By.XPATH, "./ancestor::section | ./ancestor::div[@class] | ./ancestor::div[@data-testid]")
                    if container:
                        # Tìm các div con chứa room types
                        room_divs = container.find_elements(By.CSS_SELECTOR, "div[class*='room'], div[data-testid*='room'], div[class*='card']")
                        
                        for div in room_divs[:20]:  # Giới hạn 20
                            try:
                                # Lấy title của div - có thể là h3, h4, hoặc text đầu tiên
                                title_selectors = ["h3", "h4", ".uitk-heading", "[class*='title']", "[class*='name']"]
                                room_title = ""
                                
                                for title_sel in title_selectors:
                                    try:
                                        title_elem = div.find_element(By.CSS_SELECTOR, title_sel)
                                        room_title = title_elem.text.strip()
                                        if room_title:
                                            break
                                    except:
                                        continue
                                
                                # Nếu không tìm thấy title, thử lấy text của div
                                if not room_title:
                                    div_text = div.text.strip()
                                    if div_text and len(div_text) < 100:
                                        # Lấy dòng đầu tiên
                                        lines = div_text.split('\n')
                                        room_title = lines[0].strip()
                                
                                if room_title and len(room_title) > 2 and len(room_title) < 100:
                                    # Loại bỏ noise
                                    if not any(noise in room_title.lower() for noise in [
                                        'chọn', 'select', 'xem', 'view', 'đặt', 'book', 'từ', 'from',
                                        'giá', 'price', 'mỗi đêm', 'per night', 'tổng', 'total'
                                    ]):
                                        if room_title not in room_types:
                                            room_types.append(room_title)
                                            
                            except:
                                continue
                except:
                    pass
        except:
            pass
        
        # Nếu không tìm thấy bằng cách mới, thử cách cũ
        if not room_types:
            # Tìm room elements
            room_selectors = [
                "[data-stid='content-room-rate-card']",
                "[data-testid*='room']",
                "[class*='room-card']",
                "[class*='room-rate']",
                "[class*='room-type']",
            ]
            
            room_elements = []
            for selector in room_selectors:
                try:
                    elems = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elems:
                        room_elements = elems
                        print(f"  ✓ Tìm thấy {len(elems)} room elements với selector: {selector}")
                        break
                except:
                    continue
            
            # Extract room names từ cách cũ
            for room_elem in room_elements[:20]:
                try:
                    name_selectors = [
                        "h3", "h4", "[class*='room-name']", "[class*='room-title']",
                        "[data-testid*='room-name']", ".uitk-heading"
                    ]
                    for name_sel in name_selectors:
                        try:
                            name_elem = room_elem.find_element(By.CSS_SELECTOR, name_sel)
                            room_name = name_elem.text.strip()
                            if room_name and len(room_name) > 3:
                                if room_name not in room_types:
                                    room_types.append(room_name)
                                break
                        except:
                            continue
                except:
                    continue
        
        hotel_detail['roomTypes'] = room_types[:20]  # Lưu room types
        print(f"  ✓ Tìm thấy {len(room_types)} room types")
        
        # 3. Extract description
        try:
            desc_selectors = [
                "[data-stid='content-hotel-description']",
                "[class*='description']",
                "[data-testid*='description']",
                "[class*='overview']",
                "[class*='about']"
            ]
            for desc_sel in desc_selectors:
                try:
                    desc_elems = driver.find_elements(By.CSS_SELECTOR, desc_sel)
                    for desc_elem in desc_elems:
                        desc_text = desc_elem.text.strip()
                        if desc_text and len(desc_text) > 20 and len(desc_text) < 2000:
                            # Check if it's actually a description
                            if not any(skip in desc_text.lower() for skip in [
                                'đặt phòng', 'book now', 'xem giá', 'view rates',
                                'chính sách', 'policies', 'điều kiện', 'terms'
                            ]):
                                hotel_detail['description'] = desc_text
                                break
                    if 'description' in hotel_detail:
                        break
                except:
                    continue
        except:
            pass
        
        # 4. Extract hotel type/category
        try:
            type_selectors = [
                "[class*='type']", "[data-testid*='type']", "[class*='category']",
                "[data-stid*='hotel-type']", ".uitk-text"
            ]
            for type_sel in type_selectors:
                try:
                    type_elems = driver.find_elements(By.CSS_SELECTOR, type_sel)
                    for type_elem in type_elems:
                        type_text = type_elem.text.strip()
                        if type_text and len(type_text) < 100:
                            # Look for hotel type indicators
                            if any(hotel_type in type_text.lower() for hotel_type in [
                                'khách sạn', 'hotel', 'resort', 'apartment', 'homestay',
                                'villa', 'motel', 'hostel', 'boutique', 'luxury'
                            ]):
                                hotel_detail['hotelType'] = type_text
                                break
                    if 'hotelType' in hotel_detail:
                        break
                except:
                    continue
        except:
            pass
        
        # 5. Extract full address (more complete than basic address)
        try:
            full_addr_selectors = [
                "[data-stid='content-hotel-address']",
                "[class*='full-address']",
                "[data-testid*='full-address']",
                "[class*='address']"
            ]
            for addr_sel in full_addr_selectors:
                try:
                    addr_elems = driver.find_elements(By.CSS_SELECTOR, addr_sel)
                    for addr_elem in addr_elems:
                        addr_text = addr_elem.text.strip()
                        if addr_text and len(addr_text) > len(hotel_detail.get('address', '')):
                            # More complete address
                            hotel_detail['fullAddress'] = addr_text
                            break
                    if 'fullAddress' in hotel_detail:
                        break
                except:
                    continue
        except:
            pass
        
        # 6. Extract nearby landmarks
        try:
            landmark_selectors = [
                "[class*='landmark']", "[data-testid*='landmark']",
                "[class*='nearby']", "[class*='attraction']"
            ]
            for landmark_sel in landmark_selectors:
                try:
                    landmark_elems = driver.find_elements(By.CSS_SELECTOR, landmark_sel)
                    for landmark_elem in landmark_elems:
                        landmark_text = landmark_elem.text.strip()
                        if landmark_text and len(landmark_text) > 5 and len(landmark_text) < 200:
                            if 'nearby' in landmark_text.lower() or 'gần' in landmark_text.lower():
                                hotel_detail['nearbyLandmark'] = landmark_text
                                break
                    if 'nearbyLandmark' in hotel_detail:
                        break
                except:
                    continue
        except:
            pass
        
        # 7. Extract cleanliness rating if available
        try:
            clean_selectors = [
                "[class*='cleanliness']", "[data-testid*='cleanliness']",
                "[aria-label*='cleanliness']"
            ]
            for clean_sel in clean_selectors:
                try:
                    clean_elems = driver.find_elements(By.CSS_SELECTOR, clean_sel)
                    for clean_elem in clean_elems:
                        clean_text = clean_elem.text.strip()
                        import re
                        clean_match = re.search(r'(\d+(?:\.\d+)?)', clean_text)
                        if clean_match:
                            clean_val = float(clean_match.group(1))
                            if 0 <= clean_val <= 10:
                                hotel_detail['cleanlines'] = clean_val
                                break
                    if 'cleanlines' in hotel_detail:
                        break
                except:
                    continue
        except:
            pass
        
        # 8. Extract district ID if possible
        try:
            # Try to extract district ID from address or location data
            address = hotel_detail.get('address', '') or hotel_detail.get('fullAddress', '')
            if address:
                import re
                # Look for district patterns in Vietnamese
                district_patterns = [
                    r'Quận\s+(\d+)', r'District\s+(\d+)', r'Q\.?\s*(\d+)'
                ]
                for pattern in district_patterns:
                    match = re.search(pattern, address, re.IGNORECASE)
                    if match:
                        district_num = match.group(1)
                        hotel_detail['districtId'] = f"Q{district_num}"
                        break
        except:
            pass
        
        # Quay lại trang listing
        driver.back()
        human_like_delay(2, 3)
        
    except Exception as e:
        print(f"  ⚠ Lỗi crawl detail: {e}")
        import traceback
        traceback.print_exc()
        # Quay lại trang listing nếu có lỗi
        try:
            driver.back()
            human_like_delay(2, 3)
        except:
            pass
    
    return hotel_detail, rooms

def load_existing_hotel_ids():
    """Load existing hotel IDs từ file duy nhất"""
    existing_ids = set()
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    hotel = json.loads(line.strip())
                    hotel_id = hotel.get('hotelId')
                    if hotel_id:
                        existing_ids.add(str(hotel_id))
                except:
                    pass
    except FileNotFoundError:
        pass
    return existing_ids

def is_hotel_crawled(hotel_id, existing_ids=None):
    """
    Kiểm tra xem hotel ID đã được crawl chưa
    
    Args:
        hotel_id: ID của khách sạn (str hoặc int)
        existing_ids: Set các ID đã crawl (nếu None sẽ tự load)
    
    Returns:
        bool: True nếu đã crawl, False nếu chưa
    """
    if existing_ids is None:
        existing_ids = load_existing_hotel_ids()
    
    return str(hotel_id) in existing_ids

def reload_existing_hotel_ids(existing_ids):
    """
    Reload danh sách hotel IDs từ file (dùng khi file được update trong lúc chạy)
    
    Args:
        existing_ids: Set hiện tại cần được update
    
    Returns:
        set: Set mới với tất cả IDs từ file
    """
    return load_existing_hotel_ids()

def filter_crawled_hotels(hotels, existing_ids=None):
    """
    Lọc ra các hotels chưa được crawl
    
    Args:
        hotels: List các hotel dicts
        existing_ids: Set các ID đã crawl (nếu None sẽ tự load)
    
    Returns:
        list: List các hotels chưa được crawl
    """
    if existing_ids is None:
        existing_ids = load_existing_hotel_ids()
    
    new_hotels = []
    for hotel in hotels:
        hotel_id = hotel.get('hotelId')
        if hotel_id and str(hotel_id) not in existing_ids:
            new_hotels.append(hotel)
    
    return new_hotels

def verify_hotel_saved(hotel_id):
    """
    Kiểm tra xem hotel đã được lưu vào file chưa (đọc lại file để verify)
    
    Args:
        hotel_id: ID của hotel cần kiểm tra
    
    Returns:
        bool: True nếu tìm thấy trong file
    """
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    hotel = json.loads(line.strip())
                    if str(hotel.get('hotelId')) == str(hotel_id):
                        return True
                except:
                    continue
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"  ⚠ Lỗi khi verify hotel {hotel_id}: {e}")
    return False

def get_file_line_count():
    """
    Đếm số dòng trong file output
    
    Returns:
        int: Số dòng trong file
    """
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0
    except Exception as e:
        print(f"  ⚠ Lỗi khi đếm dòng: {e}")
        return 0

def main():
    """Main crawler với UI visible"""
    print("=" * 60)
    print("🏨 HOTELS.COM VISIBLE CRAWLER 🏨")
    print("  (UI visible để debug)")
    print("=" * 60)
    
    if TEST_MODE:
        print(f"🧪 TEST MODE: Chỉ crawl {TEST_HOTEL_COUNT} khách sạn để kiểm tra")
        print("   Sau khi kiểm tra OK, đặt TEST_MODE = False để crawl toàn bộ")
    else:
        print(f"🚀 PRODUCTION MODE: Crawl tối đa {TARGET_NEW_COUNT} khách sạn")
    print("=" * 60)

    # Load existing data
    existing_hotel_ids = load_existing_hotel_ids()
    print(f"✓ Loaded {len(existing_hotel_ids)} existing hotels")
    print(f"✓ Output file: {OUTPUT_FILE}")

    # Generate URLs
    HCM_LISTINGS = generate_many_urls()

    driver = None
    new_hotels_count = 0

    try:
        # Setup driver với UI visible
        driver = setup_visible_driver()

        # Load cookies if available
        try:
            if os.path.exists('hotels_cookies.pkl'):
                with open('hotels_cookies.pkl', 'rb') as f:
                    cookies = pickle.load(f)
                    for cookie in cookies[:10]:
                        try:
                            driver.add_cookie(cookie)
                        except:
                            pass
                print("✓ Loaded cookies")
        except:
            pass

        # Crawl URLs
        for url_idx, url in enumerate(HCM_LISTINGS):
            # Check test mode limit
            if TEST_MODE and new_hotels_count >= TEST_HOTEL_COUNT:
                print(f"\n🧪 TEST MODE: Đã crawl {TEST_HOTEL_COUNT} khách sạn!")
                print("   Kiểm tra file output, nếu OK thì đặt TEST_MODE = False để crawl tiếp")
                break
            
            if not TEST_MODE and new_hotels_count >= TARGET_NEW_COUNT:
                print(f"\n🎉 Reached target of {TARGET_NEW_COUNT} new hotels!")
                break

            print(f"\n{'='*50}")
            print(f"🌐 URL {url_idx + 1}/{len(HCM_LISTINGS)}")
            print(f"{'='*50}")

            try:
                # Random delay
                human_like_delay(5, 10)

                print(f"  🔗 Loading: {url[:100]}...")
                driver.get(url)

                # Wait for page load
                print("  ⏳ Waiting for page to load...")
                human_like_delay(8, 12)

                # Check for blocks
                page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                if any(word in page_text for word in ['blocked', 'bot', 'captcha', 'verification']):
                    print("🚫 Detected blocking, skipping...")
                    human_like_delay(15, 25)
                    continue

                # Extract hotels từ listing page
                hotels = extract_hotels_visible(driver)

                # Crawl detail ngay cho từng hotel và lưu luôn
                url_new_hotels = 0
                url_skipped_hotels = 0
                listing_url = driver.current_url  # Lưu URL listing để quay lại
                
                for hotel_idx, hotel in enumerate(hotels, 1):
                    hotel_id = hotel.get('hotelId')
                    
                    # Check limits
                    if TEST_MODE and new_hotels_count >= TEST_HOTEL_COUNT:
                        break
                    if not TEST_MODE and new_hotels_count >= TARGET_NEW_COUNT:
                        break
                    
                    # Reload IDs mỗi 50 hotels để đảm bảo đồng bộ (phòng trường hợp file được update)
                    if new_hotels_count > 0 and new_hotels_count % 50 == 0:
                        print(f"  🔄 Reloading existing hotel IDs...")
                        existing_hotel_ids = reload_existing_hotel_ids(existing_hotel_ids)
                        print(f"  ✓ Total existing hotels: {len(existing_hotel_ids)}")
                    
                    # Check xem hotel đã crawl chưa
                    if not hotel_id:
                        continue
                    
                    if is_hotel_crawled(hotel_id, existing_hotel_ids):
                        url_skipped_hotels += 1
                        if url_skipped_hotels <= 3:  # Chỉ print 3 hotels đầu tiên để không spam
                            print(f"  ⏭️  Skipping hotel {hotel_id} (đã crawl): {hotel.get('hotelName', 'N/A')[:50]}...")
                        continue
                    
                    # Hotel chưa crawl, tiếp tục xử lý
                    existing_hotel_ids.add(str(hotel_id))
                    new_hotels_count += 1
                    url_new_hotels += 1

                    print(f"\n  {'='*50}")
                    print(f"  🏨 Hotel {url_new_hotels}: {hotel.get('hotelName', 'N/A')[:60]}...")
                    print(f"  {'='*50}")
                    
                    # Crawl detail ngay lập tức
                    if hotel.get('hotelUrl'):
                        try:
                            print(f"  📍 Đang crawl detail cho Hotel ID: {hotel_id}")
                            
                            hotel_detail, rooms = crawl_hotel_detail(
                                driver, 
                                hotel.get('hotelUrl'), 
                                hotel_id
                            )
                            
                            # Kết hợp tất cả thông tin vào một record
                            complete_hotel = hotel.copy()
                            complete_hotel['amenities'] = hotel_detail.get('amenities', [])
                            complete_hotel['facilities'] = hotel_detail.get('amenities', [])  # Thêm field facilities
                            complete_hotel['roomTypes'] = rooms
                            
                            # Thêm các trường từ hotel_detail nếu có
                            detail_fields = [
                                'starType', 'categoryName', 'categoryId', 'cityId', 'address',
                                'latitude', 'longitude', 'fullRating', 'cleanlines', 'description',
                                'hotelType', 'fullAddress', 'nearbyLandmark', 'districtId'
                            ]
                            for field in detail_fields:
                                if field in hotel_detail:
                                    complete_hotel[field] = hotel_detail[field]
                            
                            # Lưu vào file duy nhất
                            file_lines_before = get_file_line_count()
                            if save_complete_hotel(complete_hotel):
                                # Đợi một chút để đảm bảo file được ghi vào disk
                                time.sleep(0.1)
                                
                                # Verify đã lưu thành công
                                if verify_hotel_saved(hotel_id):
                                    file_lines_after = get_file_line_count()
                                    if file_lines_after > file_lines_before:
                                        print(f"  ✅ Đã lưu hotel hoàn chỉnh vào file: {hotel_id}")
                                        print(f"     - {len(complete_hotel.get('amenities', []))} amenities, {len(rooms)} loại phòng")
                                        print(f"     - Tổng số hotels trong file: {file_lines_after} (tăng từ {file_lines_before})")
                                    else:
                                        print(f"  ⚠ Hotel {hotel_id} đã có trong file nhưng số dòng không tăng!")
                                        print(f"     - Số dòng trước: {file_lines_before}, sau: {file_lines_after}")
                                else:
                                    print(f"  ❌ Đã gọi save nhưng KHÔNG TÌM THẤY hotel {hotel_id} trong file!")
                                    print(f"     - Đang thử lưu lại...")
                                    # Thử lưu lại một lần nữa
                                    if save_complete_hotel(complete_hotel):
                                        time.sleep(0.2)
                                        if verify_hotel_saved(hotel_id):
                                            print(f"     ✅ Đã lưu lại thành công!")
                                        else:
                                            print(f"     ❌ Vẫn không lưu được sau lần thử thứ 2!")
                            else:
                                print(f"  ❌ KHÔNG THỂ LƯU hotel {hotel_id} vào file!")
                            
                            # Quay lại listing page
                            if driver.current_url != listing_url:
                                driver.get(listing_url)
                                human_like_delay(2, 3)
                            
                            # Delay giữa các hotels
                            human_like_delay(3, 5)
                            
                        except Exception as e:
                            print(f"  ⚠ Lỗi crawl detail cho hotel {hotel_id}: {e}")
                            import traceback
                            traceback.print_exc()
                            
                            # Vẫn lưu hotel cơ bản nếu không crawl được detail
                            try:
                                complete_hotel = hotel.copy()
                                complete_hotel['amenities'] = []
                                complete_hotel['facilities'] = []
                                complete_hotel['roomTypes'] = []
                                file_lines_before = get_file_line_count()
                                if save_complete_hotel(complete_hotel):
                                    time.sleep(0.1)
                                    if verify_hotel_saved(hotel_id):
                                        file_lines_after = get_file_line_count()
                                        print(f"  ✓ Đã lưu hotel cơ bản (không có detail): {hotel_id}")
                                        print(f"     - Tổng số hotels trong file: {file_lines_after}")
                                    else:
                                        print(f"  ⚠ Đã gọi save nhưng không tìm thấy hotel {hotel_id} trong file!")
                                else:
                                    print(f"  ❌ KHÔNG THỂ LƯU hotel cơ bản {hotel_id} vào file!")
                            except Exception as e2:
                                print(f"  ❌ Lỗi khi lưu hotel cơ bản {hotel_id}: {e2}")
                            
                            # Quay lại listing nếu có lỗi
                            try:
                                if driver.current_url != listing_url:
                                    driver.get(listing_url)
                                    human_like_delay(2, 3)
                            except:
                                pass
                    else:
                        # Không có URL, chỉ lưu thông tin cơ bản
                        complete_hotel = hotel.copy()
                        complete_hotel['amenities'] = []
                        complete_hotel['facilities'] = []
                        complete_hotel['roomTypes'] = []
                        file_lines_before = get_file_line_count()
                        if save_complete_hotel(complete_hotel):
                            time.sleep(0.1)
                            if verify_hotel_saved(hotel_id):
                                file_lines_after = get_file_line_count()
                                print(f"  ✓ Đã lưu hotel cơ bản (không có URL): {hotel_id}")
                                print(f"     - Tổng số hotels trong file: {file_lines_after}")
                            else:
                                print(f"  ⚠ Đã gọi save nhưng không tìm thấy hotel {hotel_id} trong file!")
                        else:
                            print(f"  ❌ KHÔNG THỂ LƯU hotel {hotel_id} vào file!")

                print(f"\n  📊 New hotels from this URL: {url_new_hotels}")
                if url_skipped_hotels > 0:
                    print(f"  ⏭️  Skipped hotels (đã crawl): {url_skipped_hotels}")
                print(f"  📈 Total new hotels: {new_hotels_count}")
                file_lines = get_file_line_count()
                print(f"  📄 Tổng số dòng trong file {OUTPUT_FILE}: {file_lines}")

                # Progressive delay
                base_delay = 10 + (new_hotels_count // 100)  # Increase delay every 100 hotels
                print(f"  ⏰ Sleeping {base_delay}-{base_delay+5} seconds...")
                human_like_delay(base_delay, base_delay + 5)

            except Exception as e:
                print(f"  ❌ Error with URL {url_idx + 1}: {e}")
                human_like_delay(10, 15)

        print(f"\n{'='*60}")
        if TEST_MODE:
            print("🧪 TEST MODE COMPLETED!")
            print(f"  🏨 Hotels crawled: {new_hotels_count}")
            print(f"  📁 Output file: {OUTPUT_FILE}")
            print(f"  📋 Kiểm tra file output, nếu OK thì đặt TEST_MODE = False để crawl tiếp")
        else:
            print("🎊 COMPLETED!")
            print(f"  🏨 New hotels crawled: {new_hotels_count}")
        print(f"  📈 Total hotels now: {len(existing_hotel_ids)}")
        print(f"{'='*60}")

    except Exception as e:
        print(f"\n💥 MAIN ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            input("\n🔴 Press Enter to close browser...")
            try:
                driver.quit()
            except:
                pass
        print("\n👋 Browser closed.")

if __name__ == "__main__":
    main()

