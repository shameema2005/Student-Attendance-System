import os
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

BASE_URL = os.getenv("APP_URL", "http://127.0.0.1:5000")
RUN_SELENIUM = os.getenv("RUN_SELENIUM", "0") == "1"

@pytest.fixture
def driver():
    if not RUN_SELENIUM:
        pytest.skip("Set RUN_SELENIUM=1 and start the Flask app to run browser tests.")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    browser = webdriver.Chrome(options=options)
    yield browser
    browser.quit()

def test_faculty_login_page_loads(driver):
    driver.get(BASE_URL + "/login")
    assert "Faculty Login" in driver.page_source
    assert driver.find_element(By.NAME, "username").is_displayed()

def test_students_page_requires_login(driver):
    driver.get(BASE_URL + "/students")
    WebDriverWait(driver, 5).until(EC.url_contains("/login"))
    assert "/login" in driver.current_url
