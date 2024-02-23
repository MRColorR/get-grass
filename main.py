import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By



import time

def run():
    email = os.environ['USER']
    password = os.environ['PASS']
    # Create Chrome options and add the extension
    # Start the virtual display

    chrome_options = Options()
    chrome_options.add_extension('./3.3.0_1.crx')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0")

    #chrome_options.add_experimental_option("detach", True)

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
    time.sleep(3)
    button = driver.find_element(By.XPATH, "//button")

    button.click()

    print('logged in')
    while True:
        try:
            
            time.sleep(3600)
        except KeyboardInterrupt:
            driver.close()
            break

run()