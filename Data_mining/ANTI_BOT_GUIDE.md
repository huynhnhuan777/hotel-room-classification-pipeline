# HƯỚNG DẪN VƯỢT QUA BOT DETECTION

## 🚨 Vấn đề: Bị Hotels.com chặn

Khi bạn bị chặn, Hotels.com hiển thị thông báo:
- "You have been blocked"
- "We can't tell if you're a human or a bot"

## ✅ Giải pháp đã cải thiện

### 1. Cài đặt dependencies mới

```bash
pip install -r requirements.txt
```

Các package mới:
- `selenium-stealth` - Ẩn dấu hiệu automation
- `undetected-chromedriver` - ChromeDriver không bị detect
- `fake-useragent` - Random user agents
- `requests` + `beautifulsoup4` - Phương án thay thế

### 2. Sử dụng script đã cải thiện

#### Option A: Selenium với Stealth (Khuyến nghị)

```bash
# 1. Đăng nhập và lưu cookies (đã cải thiện)
python hotels_login_and_save_cookie.py

# 2. Crawl với stealth techniques
python hotels_crawl_hcm.py
```

**Cải thiện:**
- ✅ Sử dụng `undetected-chromedriver` để tránh detection
- ✅ Áp dụng `selenium-stealth` để ẩn automation
- ✅ Human-like scrolling (scroll từng phần, có delay)
- ✅ Random mouse movements
- ✅ Random delays giữa các actions
- ✅ User agent mới nhất
- ✅ Kiểm tra và xử lý khi bị block

#### Option B: Requests + BeautifulSoup (Nếu Selenium vẫn bị chặn)

```bash
python hotels_crawl_hcm_alternative.py
```

**Ưu điểm:**
- Không cần browser, nhanh hơn
- Ít bị detect hơn (giống browser thật)
- Có thể dùng với proxy

**Nhược điểm:**
- Không capture được API responses
- Phải parse HTML (phức tạp hơn)
- Có thể thiếu một số dữ liệu

## 🔧 Các kỹ thuật chống bot detection

### 1. Stealth Techniques

```python
# Sử dụng undetected-chromedriver
import undetected_chromedriver as uc
driver = uc.Chrome(options=chrome_options)

# Áp dụng selenium-stealth
from selenium_stealth import stealth
stealth(driver, ...)
```

### 2. Human-like Behavior

- **Random delays:** 1-5 giây giữa các actions
- **Smooth scrolling:** Scroll từng phần nhỏ, không scroll hết một lúc
- **Mouse movements:** Di chuyển chuột ngẫu nhiên
- **Reading pauses:** Dừng lâu hơn ở một số điểm (giống đang đọc)

### 3. Headers và Fingerprinting

- User agent mới nhất
- Accept-Language phù hợp
- Window size thực tế (1920x1080)
- WebGL vendor/renderer giống máy thật

### 4. Cookie Management

- Lưu và load cookies từ session thật
- Giữ cookies còn hiệu lực
- Restore localStorage và sessionStorage

## 🛠️ Troubleshooting

### Vẫn bị chặn sau khi cải thiện?

#### Giải pháp 1: Đợi và thử lại
- Đợi 1-2 giờ để IP được unblock
- Hoặc đổi IP (restart router, dùng VPN)

#### Giải pháp 2: Sử dụng Proxy
```python
# Thêm vào chrome_options
chrome_options.add_argument('--proxy-server=http://proxy-ip:port')
```

#### Giải pháp 3: Giảm tốc độ crawl
```python
# Trong hotels_crawl_hcm.py, tăng delays
human_like_delay(5, 10)  # Thay vì 1-3 giây
```

#### Giải pháp 4: Sử dụng Residential Proxy
- Mua residential proxy service
- Rotate IPs thường xuyên

#### Giải pháp 5: Crawl từ nhiều máy/IP
- Chia nhỏ công việc
- Mỗi máy crawl một phần

### Kiểm tra xem có bị block không

Script tự động kiểm tra:
```python
if "blocked" in page_text or "bot" in page_text:
    print("⚠ PHÁT HIỆN BỊ CHẶN!")
```

### Lưu cookies từ session thật

1. Mở trình duyệt thật (Chrome/Firefox)
2. Đăng nhập vào Hotels.com thủ công
3. Export cookies bằng extension (EditThisCookie, Cookie-Editor)
4. Lưu vào file `hotels_cookies_requests.txt` (format: key=value)

## 📊 So sánh các phương pháp

| Phương pháp | Ưu điểm | Nhược điểm | Tỷ lệ thành công |
|------------|---------|------------|------------------|
| Selenium thông thường | Dễ dùng, capture API | Dễ bị detect | 30-40% |
| Selenium + Stealth | Capture API, stealth | Vẫn có thể bị detect | 70-80% |
| Requests + BeautifulSoup | Khó detect, nhanh | Phải parse HTML | 60-70% |
| Selenium + Proxy | Tránh IP ban | Cần proxy tốt | 80-90% |

## 🎯 Best Practices

1. **Luôn đăng nhập trước:** Cookies từ session thật giúp giảm detection
2. **Crawl chậm:** Đừng quá nhanh, giống người dùng thật
3. **Random hóa:** Delays, scrolling, mouse movements đều random
4. **Monitor:** Kiểm tra thường xuyên xem có bị block không
5. **Backup plan:** Có phương án thay thế (alternative script)

## ⚠️ Lưu ý pháp lý

- Chỉ crawl dữ liệu công khai
- Tuân thủ robots.txt
- Không quá tải server
- Tôn trọng Terms of Service

## 🔄 Workflow khuyến nghị

```bash
# 1. Cài đặt dependencies mới
pip install -r requirements.txt

# 2. Đăng nhập và lưu cookies (với stealth)
python hotels_login_and_save_cookie.py

# 3. Thử crawl với Selenium + Stealth
python hotels_crawl_hcm.py

# 4. Nếu vẫn bị chặn, thử phương án thay thế
python hotels_crawl_hcm_alternative.py

# 5. Merge và normalize
python merge_hcm_data.py
python normalize_hotels_data.py
```

## 📞 Hỗ trợ

Nếu vẫn gặp vấn đề:
1. Kiểm tra logs để xem lỗi cụ thể
2. Thử với IP khác
3. Giảm tốc độ crawl
4. Sử dụng residential proxy






