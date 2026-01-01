#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check if Chrome is accessible with remote debugging"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

try:
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    print("Attempting to connect to Chrome...")
    driver = webdriver.Chrome(service=Service(), options=options)
    
    print("[OK] Successfully connected to Chrome!")
    print(f"Current URL: {driver.current_url}")
    print(f"Page title: {driver.title}")
    
    driver.quit()
    print("\nChrome connection is working. You can now run the crawl script.")
    
except Exception as e:
    print(f"\n[ERROR] Error connecting to Chrome: {e}")
    print("\n" + "="*80)
    print("CHROME CHUA MO VOI REMOTE DEBUGGING!")
    print("="*80)
    print("\nVui long:")
    print("1. Dong tat ca cua so Chrome")
    print("2. Chay file: start_chrome_debug.bat")
    print("   Hoac mo Chrome bang lenh:")
    print('   chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\temp\\chrome_debug"')
    print("3. Dang nhap vao Trip.com trong Chrome do")
    print("4. Chay lai: python trip_crawl_hcm_more.py")

