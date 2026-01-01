@echo off
echo Starting Chrome with remote debugging...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome_debug"
echo.
echo Chrome started with remote debugging on port 9222
echo Please login to Trip.com in this Chrome window
echo Then run: python trip_crawl_hcm_more.py
pause


