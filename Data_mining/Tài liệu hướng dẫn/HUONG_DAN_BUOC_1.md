# 📋 HƯỚNG DẪN BƯỚC 1: Mở Chrome với Remote Debugging

## ✅ Cách đơn giản nhất (Đã chạy thành công):

Trong PowerShell, chạy lệnh này:

```powershell
Start-Process -FilePath "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222","--user-data-dir=C:\selenium\ChromeProfile"
```

## 🔄 Hoặc dùng script mới (đơn giản hơn):

```powershell
.\start_chrome.ps1
```

## 📝 Hoặc copy-paste lệnh này vào PowerShell:

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\selenium\ChromeProfile"
```

## ✅ Kiểm tra Chrome đã mở đúng:

1. Chrome sẽ tự động mở
2. Vào Chrome, gõ: `chrome://version/`
3. Kiểm tra dòng "Command Line" có chứa `--remote-debugging-port=9222`

## 🚀 Sau khi Chrome mở xong:

Chuyển sang **Bước 2**: Chạy script crawl
```bash
python hotels_crawl_hcm.py
```

---

## ⚠️ Lưu ý:

- **KHÔNG** đóng Chrome sau khi mở
- Chrome phải chạy trong khi script crawl đang chạy
- Nếu Chrome đã mở sẵn, đóng tất cả cửa sổ Chrome trước khi chạy lệnh trên


