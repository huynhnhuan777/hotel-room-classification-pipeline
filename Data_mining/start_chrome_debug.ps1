# Script PowerShell để mở Chrome với Remote Debugging
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Chrome with Remote Debugging" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Tạo thư mục profile nếu chưa có
$profilePath = "C:\selenium\ChromeProfile"
if (-not (Test-Path $profilePath)) {
    New-Item -ItemType Directory -Path $profilePath -Force | Out-Null
    Write-Host "✓ Created ChromeProfile directory" -ForegroundColor Green
}

# Đường dẫn Chrome
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"

# Kiểm tra Chrome có tồn tại không
if (-not (Test-Path $chromePath)) {
    Write-Host "❌ Chrome not found at: $chromePath" -ForegroundColor Red
    Write-Host "Please update the path in this script" -ForegroundColor Yellow
    pause
    exit
}

# Mở Chrome với remote debugging
Write-Host "🚀 Opening Chrome with remote debugging port 9222..." -ForegroundColor Yellow
Start-Process -FilePath $chromePath -ArgumentList "--remote-debugging-port=9222", "--user-data-dir=$profilePath"

Write-Host ""
Write-Host "✓ Chrome đã được mở với remote debugging port 9222" -ForegroundColor Green
Write-Host "  Profile: $profilePath" -ForegroundColor Gray
Write-Host ""
Write-Host "Bây giờ bạn có thể chạy: python hotels_crawl_hcm.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "Nhấn Enter để đóng cửa sổ này (Chrome vẫn sẽ chạy)..." -ForegroundColor Yellow
Read-Host


