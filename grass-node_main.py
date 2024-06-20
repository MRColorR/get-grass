import os
import requests
import zipfile
import io
import json
import logging
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_logging():
    """Set up logging for the script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_and_extract_extension(driver, extension_id):
    """Download and extract the latest version of the extension using the authenticated session."""
    try:
        logging.info('Fetching the latest release information...')
        driver.get('https://api.getgrass.io/extensionLatestRelease')
        response_text = driver.execute_script("return document.body.textContent")
        response_json = json.loads(response_text)
        
        data = response_json['result']['data']
        version = data['version']
        linux_download_url = data['links']['linux']
        
        logging.info(f'Downloading the latest release version {version}...')
        response = requests.get(linux_download_url, verify=False)
        response.raise_for_status()
        
        zip_file_path = f'./{extension_id}.zip'
        with open(zip_file_path, 'wb') as zip_file:
            zip_file.write(response.content)
            logging.info(f"Downloaded extension to {zip_file_path}")
        
        logging.info(f"Extracting the extension from {zip_file_path}")
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall('./')
        
        crx_file_path = None
        for root, dirs, files in os.walk('./'):
            for file in files:
                if file.endswith('.crx'):
                    crx_file_path = os.path.join(root, file)
                    break
        
        if not crx_file_path:
            raise FileNotFoundError('CRX file not found in the extracted folder.')

        logging.info(f"Extension extracted to {crx_file_path}")
        return crx_file_path
    except Exception as e:
        logging.error(f'Error downloading or extracting extension: {e}')
        driver.quit()
        raise

def login_to_website(driver, email, password, extension_url):
    """Log in to the website using the given WebDriver instance."""
    try:
        driver.get(extension_url)
        logging.info('Waiting for the login page to load...')
        
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//button[text()='ACCESS MY ACCOUNT']"))
        )
        logging.info('Login page loaded successfully!')
        
        logging.info('Entering credentials...')
        username = driver.find_element(By.NAME, "user")
        username.send_keys(email)
        passwd = driver.find_element(By.NAME, "password")
        passwd.send_keys(password)
        time.sleep(random.randint(3, 7))
        
        logging.info('Clicking the login button...')
        login_button = driver.find_element(By.XPATH, "//button[text()='ACCESS MY ACCOUNT']")
        login_button.click()
        
        logging.info('Waiting for login to complete...')
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//button[text()='Logout']"))
        )
        logging.info('Login successful!')
        time.sleep(random.randint(3, 7))
    except Exception as e:
        logging.error(f'Error during login: {e}')
        driver.quit()
        raise

def main():
    """Main function to run the script."""
    setup_logging()
    logging.info('Starting the script...')
    
    # Read variables from the OS environment
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
    #driver_options.add_argument('--headless')  # Run Chrome in headless mode
    driver_options.add_argument('--disable-gpu')
    driver_options.add_argument('--remote-debugging-port=9222')
    driver_options.add_argument('--window-size=1280,1024')
    driver_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0")
    
    try:
        # Perform initial login and get WebDriver instance
        driver = webdriver.Chrome(options=driver_options)
        login_to_website(driver, email, password, extension_url)
        
        # Download and install the latest extension
        crx_file_path = download_and_extract_extension(driver, extension_id)

        logging.info('Closing the browser and re-initializing it with the extension installed...')
        driver.quit()
        
        # Add the downloaded extension to the Chrome options
        driver_options.add_extension(crx_file_path)
        
        # Re-initialize the browser with the new extension
        driver = webdriver.Chrome(options=driver_options)
        logging.info('Browser re-initialized with the extension installed.')
        
        # Log in again with the new extension installed
        login_to_website(driver, email, password, extension_url)
        
        logging.info('Accessing extension settings page...')
        driver.get(f'chrome-extension://{extension_id}/index.html')
        time.sleep(random.randint(3, 7))
        
        logging.info('Clicking the extension button...')
        extension_button = driver.find_element(By.XPATH, "//button")
        extension_button.click()
        logging.info('Extension button clicked.')
        time.sleep(random.randint(30, 70))
        logging.info('Logged in successfully.')
        logging.info('Earning...')
    except Exception as e:
        logging.error(f'An error occurred: {e}')
        driver.quit()
        time.sleep(60)
        main()
    
    while True:
        try:
            time.sleep(3600)
        except KeyboardInterrupt:
            logging.info('Stopping the script...')
            driver.quit()
            break

if __name__ == "__main__":
    main()
