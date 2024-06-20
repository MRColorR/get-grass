import os
import requests
import zipfile
import io
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import time
import logging
import json

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_extension(driver, extension_id):
    logging.info('Fetching the latest release information...')
    
    driver.get('https://api.getgrass.io/extensionLatestRelease')
    
    # Execute JavaScript to get the JSON response from the page body
    response_text = driver.execute_script("return document.body.textContent")
    response_json = json.loads(response_text)
    
    data = response_json['result']['data']
    version = data['version']
    linux_download_url = data['links']['linux']
    
    logging.info(f'Downloading the latest release version {version}...')
    response = requests.get(linux_download_url, verify=False)
    response.raise_for_status()
    
    crx_file_path = f'./{extension_id}.crx'
    with open(crx_file_path, 'wb') as crx_file:
        crx_file.write(response.content)
    
    # close the browser window
    logging.info(f"Extension downloaded to {crx_file_path}")
    logging.info('Closing the browser...')
    driver.quit()
    
    return crx_file_path

def login_and_get_driver(email, password, extension_url, driver_options):
    driver = webdriver.Chrome(options=driver_options)
    driver.get(extension_url)
    
    logging.info('Entering credentials...')
    username = driver.find_element(By.NAME, "user")
    username.send_keys(email)
    passwd = driver.find_element(By.NAME, "password")
    passwd.send_keys(password)
    
    logging.info('Clicking the login button...')
    login_button = driver.find_element(By.XPATH, "//button")
    login_button.click()
    
    logging.info('Waiting for login to complete...')
    logout_button = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//button[text()='Logout']")))
    logging.info('Login successful!')
    
    return driver

def run():
    setup_logging()
    logging.info('Starting the script...')
    
    # Read variables from the OS env
    email = os.getenv('GRASS_USER')
    password = os.getenv('GRASS_PASS')
    extension_id = os.getenv('EXTENSION_ID')
    extension_url = os.getenv('EXTENSION_URL')
    
    # Check if credentials are provided
    if not email or not password:
        logging.error('No username or password provided. Please set the GRASS_USER and GRASS_PASS environment variables.')
        return  # Exit the script if credentials are not provided

    # Define Chrome options
    driver_options = Options()
    driver_options.add_argument('--no-sandbox')
    driver_options.add_argument('--disable-dev-shm-usage')
    driver_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0")
    
    # Perform initial login and get WebDriver instance
    driver = login_and_get_driver(email, password, extension_url, driver_options)
    
    # Download and install the latest extension
    crx_file_path = download_extension(driver, extension_id)

    # Add the downloaded extension to the Chrome options
    driver_options.add_extension(crx_file_path)
    
    # Re-initialize the browser with the new extension
    driver = webdriver.Chrome(options=driver_options)

    try:
        logging.info(f'Navigating to {extension_url} website...')
        driver.get(extension_url)
        time.sleep(random.randint(3, 7))

        logging.info('Entering credentials...')
        username = driver.find_element(By.NAME, "user")
        username.send_keys(email)
        passwd = driver.find_element(By.NAME, "password")
        passwd.send_keys(password)
        
        logging.info('Clicking the login button...')
        login_button = driver.find_element(By.XPATH, "//button")
        login_button.click()
        logging.info('Waiting for response...')
        time.sleep(random.randint(10, 50))
        
        logging.info('Accessing extension settings page...')
        driver.get(f'chrome-extension://{extension_id}/index.html')
        time.sleep(random.randint(3, 7))
        
        logging.info('Clicking the extension button...')
        extension_button = driver.find_element(By.XPATH, "//button")
        extension_button.click()
        
        logging.info('Logged in successfully.')
        logging.info('Earning...')
    except Exception as e:
        logging.error(f'An error occurred: {e}')
        driver.quit()
        time.sleep(60)
        run()

    while True:
        try:
            time.sleep(3600)
        except KeyboardInterrupt:
            logging.info('Stopping the script...')
            driver.quit()
            break

run()
