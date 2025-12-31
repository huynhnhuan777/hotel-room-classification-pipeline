# HƯỚNG DẪN CRAWL DỮ LIỆU TỪ HOTELS.COM

## 📋 Tổng quan

Dự án này crawl dữ liệu hotels từ trang web Hotels.com (www.hotels.com) sử dụng Selenium để tự động hóa trình duyệt và capture các API responses.

## 🔧 Yêu cầu

- Python 3.x
- Selenium 4.x
- ChromeDriver (tương thích với Chrome của bạn)
- Chrome browser

## 📦 Cài đặt

```bash
pip install -r requirements.txt
```

**Lưu ý:** Bạn cần cài đặt ChromeDriver phù hợp với phiên bản Chrome của mình. Có thể sử dụng `webdriver-manager` để tự động tải:

```python
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
```

## 📁 Cấu trúc file

### Scripts chính:
1. **hotels_login_and_save_cookie.py** - Đăng nhập và lưu cookies
2. **hotels_crawl_hcm.py** - Script crawl chính
3. **normalize_hotels_data.py** - Chuyển đổi JSONL sang CSV
4. **merge_hcm_data.py** - Merge dữ liệu mới vào file chính

### File dữ liệu:
- `hotels_data_full.jsonl` - File JSONL chính chứa tất cả hotels
- `hotels_data_hcm.jsonl` - File đang crawl thêm
- `hotels_data_complete.csv` - File CSV với đầy đủ các trường
- `hotels_cookies.pkl` - Cookies để authenticate
- `hotels_localstorage.json` - LocalStorage data
- `hotels_sessionstorage.json` - SessionStorage data
- `seen_requests.json` - Track các request đã xử lý

---

## 🚀 QUY TRÌNH CRAWL

### BƯỚC 1: Đăng nhập và lưu cookies

**File:** `hotels_login_and_save_cookie.py`

```bash
python hotels_login_and_save_cookie.py
```

**Cách hoạt động:**
1. Mở trình duyệt Chrome
2. Điều hướng đến https://www.hotels.com
3. **Bạn cần đăng nhập thủ công** (Google/Email)
4. Script tự động detect khi đăng nhập thành công
5. Lưu cookies vào `hotels_cookies.pkl`
6. Lưu localStorage và sessionStorage vào JSON files

**Kết quả:**
- `hotels_cookies.pkl` - Cookies đã lưu
- `hotels_localstorage.json` - LocalStorage
- `hotels_sessionstorage.json` - SessionStorage

---

### BƯỚC 2: Crawl dữ liệu hotels

**File:** `hotels_crawl_hcm.py`

```bash
python hotels_crawl_hcm.py
```

**Cách hoạt động:**

#### 2.1. Khởi tạo
- Load cookies từ `hotels_cookies.pkl`
- Restore localStorage và sessionStorage
- Load danh sách hotel IDs đã có từ `hotels_data_full.jsonl`
- Load seen request IDs từ `seen_requests.json`

#### 2.2. Capture API Responses
Script sử dụng **Selenium Performance Logs** để capture các API calls:

1. **Mở trang listing:**
   - Truy cập URL: `https://www.hotels.com/search.do?destination=Ho%20Chi%20Minh%20City,%20Vietnam&start-date=2025-12-19&end-date=2025-12-20`
   - Script tự động scroll để trigger lazy loading

2. **Capture hotel search API:**
   - Monitor performance logs để tìm các request có URL chứa keywords: `hotels/search`, `hotels/list`, `api/hotels`, etc.
   - Sử dụng Chrome DevTools Protocol (CDP) để lấy response body
   - Parse JSON response

3. **Extract hotels từ response:**
   - Tìm `results`, `hotels`, `hotelList` trong response JSON
   - Extract từng hotel object
   - Filter chỉ lấy hotels từ TP.HCM

#### 2.3. Tránh trùng lặp
- Check `hotelId` với danh sách đã có
- Check `requestId` để tránh xử lý lại cùng một API response
- Lưu ngay vào file để tránh mất dữ liệu

#### 2.4. Lưu dữ liệu
- Mỗi hotel được lưu ngay vào `hotels_data_hcm.jsonl`
- Lưu `seen_request_ids` vào `seen_requests.json` để track

**Kết quả:**
- `hotels_data_hcm.jsonl` - File chứa hotels mới đã crawl

---

### BƯỚC 3: Merge dữ liệu mới

**File:** `merge_hcm_data.py`

```bash
python merge_hcm_data.py
```

**Cách hoạt động:**
1. Load hotel IDs từ `hotels_data_full.jsonl` (file gốc)
2. Load hotels mới từ `hotels_data_hcm.jsonl`
3. Loại bỏ trùng lặp
4. Append hotels mới vào `hotels_data_full.jsonl`
5. Tự động backup file cũ

**Kết quả:**
- `hotels_data_full.jsonl` - File đã được merge
- `hotels_data_full_backup_YYYYMMDD_HHMMSS.jsonl` - Backup file cũ

---

### BƯỚC 4: Normalize sang CSV

**File:** `normalize_hotels_data.py`

```bash
python normalize_hotels_data.py --input hotels_data_full.jsonl --output hotels_data_complete.csv
```

**Cách hoạt động:**
1. Đọc từng dòng JSON từ file JSONL
2. Extract các trường:
   - **Thông tin cơ bản:** hotelId, hotelName, star, hotelType
   - **Đánh giá:** reviewScore, reviewScoreText, reviewCount
   - **Địa chỉ:** cityId, cityName, districtId, districtName, latitude, longitude, nearbyLandmark
   - **Giá:** minPrice, avgPrice, originalPrice, currency
   - **Phòng:** roomsLeft, lastBookedText, buttonContent, isSoldOut
3. Ghi vào file CSV

**Kết quả:**
- File CSV với đầy đủ 22 trường dữ liệu

---

## 🔍 CHI TIẾT KỸ THUẬT

### 1. Performance Logs Capture

```python
# Enable performance logging
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

# Enable CDP Network domain
driver.execute_cdp_cmd("Network.enable", {})

# Parse performance logs
entries = driver.get_log('performance')
for entry in entries:
    msg = json.loads(entry['message'])['message']
    if msg.get('method') == 'Network.responseReceived':
        url = msg['params']['response']['url']
        if any(keyword in url.lower() for keyword in api_keywords):
            # Get response body via CDP
            body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
```

### 2. Tránh xử lý lại dữ liệu cũ

**Vấn đề:** Performance log buffer có giới hạn và có thể reset

**Giải pháp:**
- Track `last_log_index` để chỉ xử lý log entries mới
- Detect buffer reset khi `len(entries) < last_index`
- Persist `seen_request_ids` vào file JSON
- Reload `seen_ids` từ file thường xuyên

### 3. Cấu trúc dữ liệu

**JSON Response từ API Hotels.com có thể có nhiều format:**
```json
{
  "results": [
    {
      "id": "123",
      "name": "Hotel Name",
      "starRating": 4,
      "reviews": {
        "score": 8.5,
        "total": 100
      },
      "location": {
        "coordinates": {
          "latitude": 10.7,
          "longitude": 106.6
        },
        "address": "..."
      },
      "price": {
        "lead": {
          "amount": 500000,
          "currency": "VND"
        }
      }
    }
  ]
}
```

---

## 📊 CÁC TRƯỜNG DỮ LIỆU ĐƯỢC TRÍCH XUẤT

1. **hotelId** - ID khách sạn
2. **hotelName** - Tên khách sạn
3. **star** - Số sao (0-5)
4. **reviewScore** - Điểm đánh giá
5. **reviewScoreText** - Text đánh giá
6. **reviewCount** - Số lượt đánh giá
7. **cityId** - ID thành phố
8. **cityName** - Tên thành phố
9. **districtId** - ID quận
10. **districtName** - Tên quận
11. **latitude** - Vĩ độ
12. **longitude** - Kinh độ
13. **nearbyLandmark** - Địa danh gần đó
14. **minPrice** - Giá thấp nhất
15. **avgPrice** - Giá trung bình
16. **originalPrice** - Giá gốc
17. **currency** - Đơn vị tiền tệ
18. **roomsLeft** - Số phòng còn lại
19. **lastBookedText** - "Được đặt gần nhất..."
20. **buttonContent** - "Xem phòng trống"
21. **isSoldOut** - Hết phòng hay không
22. **hotelType** - Loại khách sạn
23. **description** - Mô tả khách sạn
24. **amenities** - Tiện ích của khách sạn (danh sách cách nhau bởi dấu phẩy)
25. **roomTypes** - Các loại phòng có sẵn (danh sách cách nhau bởi dấu phẩy)
26. **fullAddress** - Địa chỉ đầy đủ

### Thay đổi số lượng hotels cần crawl:
```python
# Trong hotels_crawl_hcm.py
TARGET_NEW_COUNT = 1000  # Thay đổi số này
```

### Thay đổi ngày check-in/check-out:
```python
# Trong hotels_crawl_hcm.py
HCM_LISTINGS = [
    "https://www.hotels.com/search.do?destination=Ho%20Chi%20Minh%20City,%20Vietnam&start-date=2025-12-19&end-date=2025-12-20",
    # Thêm các URL khác với ngày khác
]
```

### Thay đổi thành phố:
```python
# Thay đổi destination trong URL
# TP.HCM: destination=Ho%20Chi%20Minh%20City,%20Vietnam
# Hà Nội: destination=Hanoi,%20Vietnam
# Đà Nẵng: destination=Da%20Nang,%20Vietnam
```

---

## 🐛 XỬ LÝ LỖI

### Lỗi: "Performance log buffer reset"
- **Nguyên nhân:** Buffer đầy và tự động reset
- **Giải pháp:** Script đã tự động detect và reset `last_log_index`

### Lỗi: "Xử lý lại dữ liệu cũ"
- **Nguyên nhân:** `seen_request_ids` không được persist đúng
- **Giải pháp:** Script tự động reload từ file và lưu ngay sau mỗi request

### Lỗi: "Cookies expired"
- **Giải pháp:** Chạy lại `hotels_login_and_save_cookie.py` để lấy cookies mới

### Lỗi: "ChromeDriver version mismatch"
- **Giải pháp:** Cài đặt ChromeDriver phù hợp hoặc sử dụng webdriver-manager

---

## 📈 TỐI ƯU HÓA

1. **Incremental log reading:** Chỉ đọc log entries mới
2. **Persist tracking:** Lưu seen_request_ids vào file
3. **Reload sync:** Reload existing IDs thường xuyên
4. **Immediate save:** Lưu từng hotel ngay khi crawl được
5. **Buffer management:** Clear buffer khi quá lớn (>1500 entries)

---

## 📝 VÍ DỤ SỬ DỤNG

### Crawl 1000 hotels mới từ TP.HCM:
```bash
# 1. Đăng nhập (nếu chưa có cookies)
python hotels_login_and_save_cookie.py

# 2. Crawl dữ liệu
python hotels_crawl_hcm.py

# 3. Merge vào file chính
python merge_hcm_data.py

# 4. Normalize sang CSV
python normalize_hotels_data.py --input hotels_data_full.jsonl --output hotels_data_complete.csv
```

---

## 🔐 BẢO MẬT

- Cookies được lưu local và không chia sẻ
- Script sử dụng cookies của bạn để authenticate
- Không hardcode credentials

---

## 📌 LƯU Ý

1. **Hotels.com có thể thay đổi API structure:** Script đã được thiết kế để xử lý nhiều format response khác nhau, nhưng nếu Hotels.com thay đổi hoàn toàn, bạn có thể cần điều chỉnh hàm `extract_hotel_data()` và `parse_api_response()`.

2. **Rate limiting:** Hotels.com có thể có rate limiting. Nếu gặp vấn đề, hãy thêm delay giữa các requests.

3. **API keywords:** Script tìm các API calls dựa trên keywords. Nếu Hotels.com thay đổi endpoint, bạn có thể cần cập nhật danh sách `api_keywords` trong `hotels_crawl_hcm.py`.

---

## 🤝 ĐÓNG GÓP

Nếu bạn phát hiện lỗi hoặc có đề xuất cải thiện, vui lòng tạo issue hoặc pull request.

---

## 📄 LICENSE

MIT License






