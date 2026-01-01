# HƯỚNG DẪN CRAWL DỮ LIỆU TỪ TRIP.COM

## 📋 Tổng quan

Dự án này crawl dữ liệu hotels từ trang web Trip.com (vn.trip.com) sử dụng Selenium để tự động hóa trình duyệt và capture các API responses.

## 🔧 Yêu cầu

- Python 3.x
- Selenium 4.x
- ChromeDriver (tương thích với Chrome của bạn)
- Chrome browser

## 📁 Cấu trúc file

### Scripts chính:
1. **trip_login_and_save_cookie.py** - Đăng nhập và lưu cookies
2. **trip_crawl_hcm_more.py** - Script crawl chính
3. **normalize_trip_hotels.py** - Chuyển đổi JSONL sang CSV
4. **merge_hcm_data.py** - Merge dữ liệu mới vào file chính

### File dữ liệu:
- `trip_hotels_full.jsonl` - File JSONL chính chứa tất cả hotels
- `trip_hotels_hcm_more.jsonl` - File đang crawl thêm
- `trip_hotels_hcm_complete.csv` - File CSV với đầy đủ các trường
- `trip_cookies.pkl` - Cookies để authenticate
- `seen_requests.json` - Track các request đã xử lý

---

## 🚀 QUY TRÌNH CRAWL

### BƯỚC 1: Đăng nhập và lưu cookies

**File:** `trip_login_and_save_cookie.py`

```bash
python trip_login_and_save_cookie.py
```

**Cách hoạt động:**
1. Mở trình duyệt Chrome
2. Điều hướng đến https://vn.trip.com
3. **Bạn cần đăng nhập thủ công** (Google/QR/Email)
4. Script tự động detect khi đăng nhập thành công
5. Lưu cookies vào `trip_cookies.pkl`
6. Lưu localStorage và sessionStorage vào JSON files

**Kết quả:**
- `trip_cookies.pkl` - Cookies đã lưu
- `trip_localstorage.json` - LocalStorage
- `trip_sessionstorage.json` - SessionStorage

---

### BƯỚC 2: Crawl dữ liệu hotels

**File:** `trip_crawl_hcm_more.py`

```bash
python trip_crawl_hcm_more.py
```

**Cách hoạt động:**

#### 2.1. Khởi tạo
- Load cookies từ `trip_cookies.pkl`
- Restore localStorage và sessionStorage
- Load danh sách hotel IDs đã có từ `trip_hotels_full.jsonl`
- Load seen request IDs từ `seen_requests.json`

#### 2.2. Capture API Responses
Script sử dụng **Selenium Performance Logs** để capture các API calls:

1. **Mở trang listing:**
   - Truy cập URL: `https://vn.trip.com/hotels/list?city=301&checkin=2025-12-19&checkout=2025-12-20`
   - Script tự động scroll để trigger lazy loading

2. **Capture fetchHotelList API:**
   - Monitor performance logs để tìm các request có URL chứa `fetchHotelList`
   - Sử dụng Chrome DevTools Protocol (CDP) để lấy response body
   - Parse JSON response

3. **Extract hotels từ response:**
   - Tìm `hotelList` trong response JSON
   - Extract từng hotel object
   - Filter chỉ lấy hotels từ TP.HCM (cityId=301)

#### 2.3. Tránh trùng lặp
- Check `hotelId` với danh sách đã có
- Check `requestId` để tránh xử lý lại cùng một API response
- Lưu ngay vào file để tránh mất dữ liệu

#### 2.4. Lưu dữ liệu
- Mỗi hotel được lưu ngay vào `trip_hotels_hcm_more.jsonl`
- Lưu `seen_request_ids` vào `seen_requests.json` để track

**Kết quả:**
- `trip_hotels_hcm_more.jsonl` - File chứa hotels mới đã crawl

---

### BƯỚC 3: Merge dữ liệu mới

**File:** `merge_hcm_data.py`

```bash
python merge_hcm_data.py
```

**Cách hoạt động:**
1. Load hotel IDs từ `trip_hotels_full.jsonl` (file gốc)
2. Load hotels mới từ `trip_hotels_hcm_more.jsonl`
3. Loại bỏ trùng lặp
4. Append hotels mới vào `trip_hotels_full.jsonl`
5. Tự động backup file cũ

**Kết quả:**
- `trip_hotels_full.jsonl` - File đã được merge
- `trip_hotels_full_backup.jsonl` - Backup file cũ

---

### BƯỚC 4: Normalize sang CSV

**File:** `normalize_trip_hotels.py`

```bash
python normalize_trip_hotels.py --input trip_hotels_full.jsonl --output trip_hotels_complete.csv
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
        if 'fetchHotelList' in url:
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

**JSON Response từ API:**
```json
{
  "hotelList": [
    {
      "hotelInfo": {
        "summary": {"hotelId": "123", "hotelType": "NORMAL"},
        "nameInfo": {"name": "Hotel Name"},
        "hotelStar": {"star": 3},
        "commentInfo": {
          "commentScore": "8.5",
          "commentDescription": "Rất Tốt",
          "commenterNumber": "100 đánh giá"
        },
        "positionInfo": {
          "cityId": 301,
          "cityName": "TP. Hồ Chí Minh",
          "mapCoordinate": [{"latitude": "10.7", "longitude": "106.6"}]
        },
        "roomInfo": [
          {
            "priceInfo": {"price": 500000, "currency": "VND"},
            "roomTags": {
              "encourageTags": [{"tagTitle": "Chỉ còn 3 phòng"}]
            }
          }
        ]
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
4. **reviewScore** - Điểm đánh giá (8.3, 9.1...)
5. **reviewScoreText** - Text đánh giá ("Rất tốt", "Tuyệt vời")
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
17. **currency** - Đơn vị tiền tệ (VND)
18. **roomsLeft** - Số phòng còn lại
19. **lastBookedText** - "Được đặt gần nhất..."
20. **buttonContent** - "Xem phòng trống"
21. **isSoldOut** - Hết phòng hay không
22. **hotelType** - Loại khách sạn

---

## ⚙️ CẤU HÌNH

### Thay đổi số lượng hotels cần crawl:
```python
# Trong trip_crawl_hcm_more.py
TARGET_NEW_COUNT = 1000  # Thay đổi số này
```

### Thay đổi ngày check-in/check-out:
```python
# Trong trip_crawl_hcm_more.py
HCM_LISTINGS = [
    "https://vn.trip.com/hotels/list?city=301&checkin=2025-12-19&checkout=2025-12-20",
    # Thêm các URL khác với ngày khác
]
```

### Thay đổi thành phố:
```python
# TP.HCM: city=301
# Hà Nội: city=1
# Đà Nẵng: city=2
# Thay đổi trong URL và filter cityId trong code
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
- **Giải pháp:** Chạy lại `trip_login_and_save_cookie.py` để lấy cookies mới

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
python trip_login_and_save_cookie.py

# 2. Crawl dữ liệu
python trip_crawl_hcm_more.py

# 3. Merge vào file chính
python merge_hcm_data.py

# 4. Normalize sang CSV
python normalize_trip_hotels.py --input trip_hotels_full.jsonl --output trip_hotels_complete.csv
```

---

## 🔐 BẢO MẬT

- Cookies được lưu local và không chia sẻ
- Script sử dụng cookies của bạn để authenticate
- Không hardcode credentials

---





