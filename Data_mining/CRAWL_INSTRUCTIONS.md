# Hướng dẫn Crawl Dữ liệu Hotels

## 🚀 Bắt đầu Crawl

### Bước 1: Mở Chrome với Remote Debugging
Chạy một trong các lệnh sau:
- **Windows**: `start_chrome_debug.bat`
- **PowerShell**: `.\start_chrome_debug.ps1`

Hoặc thủ công:
```powershell
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\selenium\ChromeProfile"
```

### Bước 2: Chạy Script Crawl
```bash
python hotels_crawl_hcm.py
```

## ⚙️ Cấu hình

Script hiện đang ở **TEST MODE**:
- `TEST_MODE = True` - Chỉ crawl 3 khách sạn để kiểm tra
- `TEST_HOTEL_COUNT = 3` - Số khách sạn crawl trong test mode

Sau khi kiểm tra OK, sửa trong file `hotels_crawl_hcm.py`:
```python
TEST_MODE = False  # Tắt test mode để crawl toàn bộ
```

## 📁 File Output

- **File chính**: `hotels_complete_hcm.jsonl` - Mỗi dòng là một JSON object
- **File JSON**: Chạy `python view_hotels_data.py` để tạo file `hotels_complete_hcm.json` (dễ đọc hơn)

## 📊 Cấu trúc Dữ liệu

Mỗi hotel record chứa:
- Thông tin cơ bản: `hotelId`, `hotelName`, `hotelUrl`, `minPrice`, `currency`, etc.
- **`amenities`**: Danh sách tiện ích (đã lọc nhiễu)
- **`roomTypes`**: Danh sách các loại phòng với thông tin chi tiết

## 🔍 Xem Dữ liệu

Sau khi crawl, chạy:
```bash
python view_hotels_data.py
```

Script này sẽ:
- Hiển thị thống kê dữ liệu
- Tạo file JSON dễ đọc
- Hiển thị chi tiết từng khách sạn

## ⚠️ Lưu ý

1. Đảm bảo Chrome đã mở với remote debugging trước khi chạy script
2. Script sẽ tự động lưu cookies nếu có
3. Trong test mode, script sẽ dừng sau khi crawl đủ số lượng hotels
4. Nếu gặp lỗi, kiểm tra console output để debug


