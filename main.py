import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import time

def run():
    email = os.environ['USER']
    password = os.environ['PASS']
    # Create Chrome options and add the extension
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_extension('./3.3.0_1.crx')
    chrome_options.add_experimental_option("detach", True)

    # Initialize the WebDriver
    driver = webdriver.Chrome( options=chrome_options)

    # Navigate to a webpage
    driver.get("https://app.getgrass.io/")

    time.sleep(3)
    username = driver.find_element(By.NAME,"user")
    username.send_keys(email)

    passwd = driver.find_element(By.NAME,"password")
    passwd.send_keys(password)
    
    button = driver.find_element(By.XPATH, "//button")

    button.click()
    time.sleep(10)
    driver.get('chrome-extension://ilehaonighjijnmpnagapkhpcdbhclfg/index.html')
    button = driver.find_element(By.XPATH, "//button")

    button.click()

run()