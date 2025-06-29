import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

BRAVE_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

@pytest.fixture(scope="module")
def driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.binary_location = BRAVE_PATH
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    yield driver
    driver.quit()

def test_frontend_main_page(driver):
    url = "http://localhost:3000"
    driver.get(url)
    time.sleep(2)  # Ждем загрузки страницы
    assert "relink" in driver.title.lower() or driver.find_element(By.TAG_NAME, "body")
    # Можно добавить дополнительные проверки по элементам:
    # assert driver.find_element(By.CSS_SELECTOR, "header")
    # assert driver.find_element(By.CSS_SELECTOR, "footer") 