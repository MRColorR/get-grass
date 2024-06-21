import os
import requests
import zipfile
import json
import logging
import random
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, WebDriverException
)

def setup_logging():
    """Set up logging for the script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_and_extract_extension(driver, extension_id, crx_download_url):
    """Download and extract the latest version of the extension using the authenticated session."""
    try:
        if crx_download_url.startswith('https://chromewebstore.google.com'):
            # Clone the CRX downloader repository and use it to download the extension
            GIT_USERNAME = 'warren-bank'
            GIT_REPO = 'chrome-extension-downloader'
            logging.info(f'Using {GIT_USERNAME}/{GIT_REPO} to download the extension CRX file from the Chrome Web Store...')
            subprocess.run(["git", "clone", f"https://github.com/{GIT_USERNAME}/{GIT_REPO}.git"], check=True)
            subprocess.run(["chmod", "+x", f"./{GIT_REPO}/bin/*"], check=True)
            subprocess.run([f"./{GIT_REPO}/bin/crxdl", extension_id], check=True)
            crx_file_path = f"./{extension_id}.crx"
        else:
            logging.info('Using the defined URL to download the extension CRX file from the provider website...')
            logging.info('Fetching the latest release information...')
            driver.get(crx_download_url)
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
            for root, _, files in os.walk('./'):
                for file in files:
                    if file.endswith('.crx'):
                        crx_file_path = os.path.join(root, file)
                        break
            
            if not crx_file_path:
                raise FileNotFoundError('CRX file not found in the extracted folder.')

        logging.info(f"Extension extracted to {crx_file_path}")
        return crx_file_path
    except (requests.RequestException, zipfile.BadZipFile, FileNotFoundError, json.JSONDecodeError, subprocess.CalledProcessError) as e:
        logging.error(f'Error downloading or extracting extension: {e}')
        driver.quit()
        raise
    except Exception as e:
        logging.error(f'An unexpected error occurred during download and extraction: {e}')
        driver.quit()
        raise

def login_to_website(driver, email, password, login_url, max_retry_multiplier):
    """Log in to the website using the given WebDriver instance."""
    max_retries = max_retry_multiplier
    for attempt in range(max_retries):
        try:
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(login_url)
            logging.info(f'Waiting for the login page {login_url} to load...')
            
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//button[text()='ACCESS MY ACCOUNT']"))
            )
            logging.info('Login page loaded successfully!')
            
            logging.info('Entering credentials...')
            username = driver.find_element(By.NAME, "user")
            username.clear()
            username.send_keys(email)
            passwd = driver.find_element(By.NAME, "password")
            passwd.clear()
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
            return True
        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f'Error during login: {e}')
            if attempt < max_retries - 1:
                logging.info(f'Retrying login... ({attempt + 1}/{max_retries})')
                time.sleep(random.randint(5, 10) * max_retry_multiplier)
                continue
            else:
                driver.quit()
                raise
        except Exception as e:
            logging.error(f'An unexpected error occurred during login: {e}')
            if attempt < max_retries - 1:
                logging.info(f'Retrying login... ({attempt + 1}/{max_retries})')
                time.sleep(random.randint(5, 10) * max_retry_multiplier)
                continue
            else:
                driver.quit()
                raise

def initialize_driver(crx_file_paths=None):
    """Initialize the WebDriver with specified options and extensions."""
    driver_options = Options()
    driver_options.add_argument('--no-sandbox')
    driver_options.add_argument('--disable-dev-shm-usage')
    driver_options.add_experimental_option('prefs', {'extensions.ui.developer_mode': True})
    # driver_options.add_argument('--headless')  # Uncomment if you want to run Chrome in headless mode
    driver_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    )
    
    if crx_file_paths:
        for crx_file_path in crx_file_paths:
            driver_options.add_extension(crx_file_path)
    
    try:
        driver = webdriver.Chrome(options=driver_options)
        return driver
    except WebDriverException as e:
        logging.error(f'Error initializing WebDriver: {e}')
        raise
    except Exception as e:
        logging.error(f'An unexpected error occurred during WebDriver initialization: {e}')
        raise

def check_and_connect(driver, extension_id, max_retry_multiplier):
    """Check if the extension is connected and if not, attempt to connect it."""
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(f'chrome-extension://{extension_id}/index.html')
    max_retries = max_retry_multiplier
    for attempt in range(max_retries):
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'Grass is Connected')]"))
            )
            logging.info('Grass is Connected message found.')
            return True
        except TimeoutException:
            try:
                connect_button = driver.find_element(By.XPATH, "//button[contains(text(), 'CONNECT GRASS')]")
                logging.info('Connect Grass button found. Clicking the button...')
                connect_button.click()
                time.sleep(random.randint(5, 10))  # wait for the connection process
            except NoSuchElementException:
                logging.error('Neither "Grass is Connected" message nor "CONNECT GRASS" button found.')
                if attempt < max_retries - 1:
                    logging.info(f'Retrying... ({attempt + 1}/{max_retries})')
                    time.sleep(random.randint(5, 10) * max_retry_multiplier)
                    continue
                else:
                    raise Exception('Failed to find the required elements on the page after several attempts.')
            except Exception as e:
                logging.error(f'An unexpected error occurred while attempting to connect: {e}')
                raise
    return False

def main():
    """Main function to run the script."""
    setup_logging()
    logging.info('Starting the script...')
    
    # Read variables from the OS environment
    email = os.getenv('USER_EMAIL')
    password = os.getenv('USER_PASSWORD')
    extension_ids = os.getenv('EXTENSION_IDS').split(',')
    extension_urls = os.getenv('EXTENSION_URLS').split(',')
    crx_download_urls = os.getenv('CRX_DOWNLOAD_URLS').split(',')
    max_retry_multiplier = int(os.getenv('MAX_RETRY_MULTIPLIER', 3))  # Default to 3 if not set
    
    # Check if credentials are provided
    if not email or not password:
        logging.error('No username or password provided. Please set the USER_EMAIL and USER_PASSWORD environment variables.')
        return  # Exit the script if credentials are not provided

    try:
        crx_file_paths = []
        driver = initialize_driver()  # Initialize WebDriver once for login and downloads

        for extension_id, extension_url, crx_download_url in zip(extension_ids, extension_urls, crx_download_urls):
            # Perform initial login
            login_to_website(driver, email, password, extension_url, max_retry_multiplier)
            
            # Download and install the latest extension
            crx_file_path = download_and_extract_extension(driver, extension_id, crx_download_url)
            crx_file_paths.append(crx_file_path)
        
        logging.info('Closing the browser and re-initializing it with the extensions installed...')
        driver.quit()
        
        # Re-initialize the browser with the new extensions
        driver = initialize_driver(crx_file_paths)
        logging.info('Browser re-initialized with the extensions installed.')
        
        # Log in again and check the connection status for each extension
        for extension_id, extension_url in zip(extension_ids, extension_urls):
            login_to_website(driver, email, password, extension_url, max_retry_multiplier)
            check_and_connect(driver, extension_id, max_retry_multiplier)
        
        logging.info('All extensions are connected successfully.')
    except Exception as e:
        logging.error(f'An error occurred: {e}')
        if 'driver' in locals():
            driver.quit()
        time.sleep(60 * max_retry_multiplier)
        main()

    while True:
        try:
            time.sleep(3600)
        except KeyboardInterrupt:
            logging.info('Stopping the script...')
            if 'driver' in locals():
                driver.quit()
            break

if __name__ == "__main__":
    main()
