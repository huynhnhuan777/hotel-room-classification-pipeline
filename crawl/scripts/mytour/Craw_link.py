import re
import time
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, ElementClickInterceptedException

LIST_URL = "https://mytour.vn/khach-san/search?aliasCode=tp33&travellerType=1&childrenAges=&adults=2&rooms=1&children=0&checkIn=21-12-2025&checkOut=22-12-2025"

def is_hotel_detail_link(url: str) -> bool:
    u = urlparse(url)
    if u.scheme not in ("http", "https"):
        return False
    if u.netloc != "mytour.vn":
        return False
    return bool(re.match(r"^/khach-san/\d+-.*\.html$", u.path))

def click_load_more_until_end(driver, max_clicks=200):
    """
    Click nút 'Xem thêm ... khách sạn' đến khi không còn nữa.
    """
    wait = WebDriverWait(driver, 10)
    clicks = 0

    while clicks < max_clicks:
        # scroll xuống gần cuối để nút hiện ra
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        try:
            # Bắt cả button hoặc a có chữ "Xem thêm" và "khách sạn"
            btn = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[self::button or self::a][contains(., 'Xem thêm') and contains(., 'khách sạn')]")
                )
            )
        except TimeoutException:
            # Không còn nút -> hết dữ liệu
            break

        try:
            # scroll vào giữa màn hình rồi click bằng JS để tránh bị che
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", btn)
            clicks += 1
            time.sleep(1.5)  # chờ load thêm
        except (StaleElementReferenceException, ElementClickInterceptedException):
            # DOM thay đổi hoặc bị che -> thử lại vòng sau
            time.sleep(0.8)
            continue

    return clicks

def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1400,900")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(LIST_URL)
        time.sleep(2)

        # Click "Xem thêm..." cho tới khi hết
        clicks = click_load_more_until_end(driver)
        print(f"Clicked 'Xem thêm' {clicks} lần")

        # Scroll vài lần để chắc chắn load hết lazy content
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

        # Lấy link
        links = set()
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href]"):
            href = a.get_attribute("href")
            if not href:
                continue
            full = urljoin("https://mytour.vn", href)
            if is_hotel_detail_link(full):
                links.add(full.split("#")[0])

        links = sorted(links)
        print("Found:", len(links))

        # Lưu txt
        with open("mytour_links.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(links))

        print("Saved -> mytour_links.txt")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
