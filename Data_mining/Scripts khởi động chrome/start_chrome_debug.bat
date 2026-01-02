@echo off
echo ========================================
echo Starting Chrome with Remote Debugging
echo ========================================
echo.

REM Tạo thư mục profile nếu chưa có
if not exist "C:\selenium\ChromeProfile" (
    mkdir "C:\selenium\ChromeProfile"
    echo Created ChromeProfile directory
)

REM Mở Chrome với remote debugging port 9222
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\selenium\ChromeProfile"

echo.
echo Chrome đã được mở với remote debugging port 9222
echo Profile: C:\selenium\ChromeProfile
echo.
echo Bây giờ bạn có thể chạy: python hotels_crawl_hcm.py
echo.
pause


