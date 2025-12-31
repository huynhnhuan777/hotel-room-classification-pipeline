# HƯỚNG DẪN SỬ DỤNG CHROME REMOTE DEBUGGING

## 🎯 Mục đích

Sử dụng Chrome đã mở sẵn với remote debugging để:
- Tránh bot detection tốt hơn
- Giữ session/cookies đã đăng nhập
- Debug dễ dàng (xem Chrome đang làm gì)
- Không cần mở Chrome mới mỗi lần

## 🚀 Cách sử dụng

### BƯỚC 1: Mở Chrome với Remote Debugging

**Cách 1: Dùng script helper (Khuyến nghị)**
```bash
# Double-click vào file
start_chrome_debug.bat

# Hoặc PowerShell
.\start_chrome_debug.ps1
```

**Cách 2: Chạy thủ công**
```powershell
Start-Process -FilePath "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222", "--user-data-dir=C:\selenium\ChromeProfile"
```

**Cách 3: Command Prompt**
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\selenium\ChromeProfile"
```

### BƯỚC 2: Chạy Crawler

Sau khi Chrome đã mở, chạy:
```bash
python hotels_crawl_hcm.py
```

Script sẽ tự động kết nối với Chrome đang chạy qua port 9222.

## ⚙️ Cấu hình

Script được cấu hình để:
- Kết nối với Chrome tại: `127.0.0.1:9222`
- Sử dụng profile tại: `C:\selenium\ChromeProfile`
- Tự động fallback nếu không kết nối được

## 🔍 Kiểm tra Chrome đã mở chưa

Mở trình duyệt và truy cập:
```
http://localhost:9222/json
```

Nếu thấy JSON response, Chrome đã mở với remote debugging thành công.

## 📝 Lưu ý

1. **Chrome phải mở TRƯỚC khi chạy script**
2. **Không đóng Chrome** khi script đang chạy
3. **Profile được lưu** tại `C:\selenium\ChromeProfile` - có thể đăng nhập và lưu cookies
4. **Nếu Chrome đóng**, chạy lại `start_chrome_debug.bat`

## 🐛 Troubleshooting

### Lỗi: "Không thể kết nối với Chrome remote debugging"

**Giải pháp:**
1. Kiểm tra Chrome đã mở chưa
2. Kiểm tra port 9222 có đang được sử dụng không
3. Chạy lại `start_chrome_debug.bat`
4. Đợi Chrome mở hoàn toàn trước khi chạy script

### Lỗi: "Address already in use"

**Giải pháp:**
- Đóng tất cả Chrome instances
- Hoặc đổi port (sửa trong script và start_chrome_debug.bat)

### Chrome không mở được

**Giải pháp:**
- Kiểm tra đường dẫn Chrome có đúng không
- Thử chạy Chrome thông thường trước
- Kiểm tra quyền admin nếu cần

## ✅ Ưu điểm

- ✅ Tránh bot detection tốt hơn
- ✅ Giữ session/cookies
- ✅ Debug dễ dàng
- ✅ Không cần mở Chrome mới mỗi lần
- ✅ Có thể đăng nhập thủ công và dùng lại


