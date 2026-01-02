# Script đơn giản để mở Chrome với Remote Debugging
Write-Host "🚀 Đang mở Chrome với Remote Debugging..." -ForegroundColor Yellow

# Tạo thư mục profile nếu chưa có
$profilePath = "C:\selenium\ChromeProfile"
if (-not (Test-Path $profilePath)) {
    New-Item -ItemType Directory -Path $profilePath -Force | Out-Null
    Write-Host "✓ Đã tạo thư mục ChromeProfile" -ForegroundColor Green
}

# Mở Chrome
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
Start-Process -FilePath $chromePath -ArgumentList "--remote-debugging-port=9222","--user-data-dir=$profilePath"

Write-Host "✓ Chrome đã được mở!" -ForegroundColor Green
Write-Host "  Port: 9222" -ForegroundColor Gray
Write-Host "  Profile: $profilePath" -ForegroundColor Gray
Write-Host ""
Write-Host "Bây giờ bạn có thể chạy: python hotels_crawl_hcm.py" -ForegroundColor Cyan


