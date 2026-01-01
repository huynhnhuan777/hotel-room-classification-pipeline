import time
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By

COOKIE_FILE = "trip_cookies.pkl"

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)

# Ẩn webdriver
driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
        """
    }
)

# Mở trang Trip
driver.get("https://vn.trip.com")

print("👉 HÃY ĐĂNG NHẬP BẰNG TAY (Google / QR / Email)")
print("👉 Sau khi login xong, quay lại đây và nhấn ENTER")
input("⏳ Chờ bạn login...")

# Chờ cho đến khi cookie của trip.com xuất hiện hoặc timeout
timeout = 120  # giây
print(f"Waiting up to {timeout}s for trip.com cookies or login confirmation...")
start = time.time()
logged = False
while time.time() - start < timeout:
    try:
        cookies = driver.get_cookies()
    except Exception:
        cookies = []

    # Kiểm tra cookie thuộc domain trip.com
    if any('trip.com' in c.get('domain', '') or c.get('domain', '').endswith('trip.com') for c in cookies):
        print("Detected trip.com cookie(s)")
        logged = True
        break

    # Thử tìm indicator trên trang (avatar, account link)
    try:
        if driver.find_elements(By.CSS_SELECTOR, "[class*=avatar], a[href*='myaccount'], a[href*='account']"):
            print("Detected account element on page")
            logged = True
            break
    except Exception:
        pass

    time.sleep(1)

if not logged:
    print("⚠️ Timeout waiting for login. Saving debug files (screenshot + html)")
    try:
        driver.save_screenshot("login_timeout.png")
    except Exception:
        pass
    try:
        with open("login_timeout.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    except Exception:
        pass

# Lấy cookie cuối cùng và lưu nếu có
try:
    cookies = driver.get_cookies()
except Exception:
    cookies = []

if cookies:
    pickle.dump(cookies, open(COOKIE_FILE, "wb"))
    print(f"✅ Đã lưu {len(cookies)} cookies vào {COOKIE_FILE}")

    # Save localStorage and sessionStorage
    try:
        ls = driver.execute_script("return JSON.stringify(window.localStorage);")
        ss = driver.execute_script("return JSON.stringify(window.sessionStorage);")
        with open("trip_localstorage.json", "w", encoding="utf-8") as f:
            f.write(ls or "{}")
        with open("trip_sessionstorage.json", "w", encoding="utf-8") as f:
            f.write(ss or "{}")
        print("✅ Saved localStorage and sessionStorage to trip_localstorage.json / trip_sessionstorage.json")
    except Exception as e:
        print("Failed to save local/session storage:", e)
else:
    print("⚠️ Không tìm thấy cookie để lưu (login chưa hoàn tất?)")

driver.quit()
