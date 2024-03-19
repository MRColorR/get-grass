import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import random
import time
import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run():
    setup_logging()
    logging.info('Starting the script...')

    # Read variables from the OS env
    email = os.getenv('GRASS_USER')
    password = os.getenv('GRASS_PASS')
    extension_id = os.getenv('EXTENSION_ID')

    # Check if credentials are provided
    if not email or not password:
        logging.error('No username or password provided. Please set the GRASS_USER and GRASS_PASS environment variables.')
        return  # Exit the script if credentials are not provided

    chrome_options = Options()
    chrome_options.add_extension(f'./{extension_id}.crx')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0")

    # Initialize the WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Navigate to a webpage
        logging.info('Navigating to the website...')
        driver.get("https://app.getgrass.io/")
        time.sleep(random.randint(3,7))

        logging.info('Entering credentials...')
        username = driver.find_element(By.NAME,"user")
        username.send_keys(email)
        passwd = driver.find_element(By.NAME,"password")
        passwd.send_keys(password)
        
        logging.info('Clicking the login button...')
        button = driver.find_element(By.XPATH, "//button")
        button.click()
        logging.info('Waiting response...')

        time.sleep(random.randint(10,50))
        logging.info('Accessing extension settings page...')
        driver.get(f'chrome-extension://{extension_id}/index.html')
        time.sleep(random.randint(3,7))

        logging.info('Clicking the extension button...')
        button = driver.find_element(By.XPATH, "//button")
        button.click()

        logging.info('Logged in successfully.')
        logging.info('Earning...')
    except Exception as e:
        logging.error(f'An error occurred: {e}')
        driver.quit()

    while True:
        try:
            time.sleep(3600)
        except KeyboardInterrupt:
            logging.info('Stopping the script...')
            driver.quit()
            break

run()
