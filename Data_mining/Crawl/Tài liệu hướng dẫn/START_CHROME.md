# Hướng dẫn Mở Chrome với Remote Debugging

## Cách 1: Dùng file .bat (Dễ nhất - Khuyến nghị)

Chỉ cần double-click vào file:
```
start_chrome_debug.bat
```

Hoặc chạy trong PowerShell/CMD:
```cmd
start_chrome_debug.bat
```

## Cách 2: Dùng PowerShell script

### Nếu gặp lỗi execution policy:
Chạy lệnh này trong PowerShell (với quyền Administrator nếu cần):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Sau đó chạy script:
```powershell
.\start_chrome_debug.ps1
```

**Lưu ý**: Không có dấu backtick (`) ở cuối!

## Cách 3: Chạy trực tiếp lệnh (Nếu cả hai cách trên không được)

### Trong PowerShell:
```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\selenium\ChromeProfile"
```

### Trong CMD:
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\selenium\ChromeProfile"
```

## Kiểm tra Chrome đã mở đúng chưa

Sau khi mở Chrome, kiểm tra:
1. Chrome đã mở
2. Vào `chrome://version/` trong Chrome
3. Xem dòng "Command Line" có chứa `--remote-debugging-port=9222`

## Sau khi Chrome mở

Chạy script crawl:
```bash
python hotels_crawl_hcm.py
```


