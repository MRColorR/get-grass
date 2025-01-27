#!/usr/bin/env python3
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
    """
    Download and extract the latest version of the extension using the authenticated session.

    Args:
        driver (webdriver): The WebDriver instance.
        extension_id (str): The ID of the extension.
        crx_download_url (str): The URL to download the extension.

    Returns:
        str: The path to the extracted CRX file.

    Raises:
        Exception: If there is an error during the download or extraction process.
    """
    extensions_dir = 'extensions'
    os.makedirs(extensions_dir, exist_ok=True)
    extension_dir = os.path.join(extensions_dir, extension_id)
    os.makedirs(extension_dir, exist_ok=True)
    
    try:
        if crx_download_url.startswith('https://chromewebstore.google.com'):
            logging.info('Downloading the extension from the Chrome Web Store...')
            crx_file_path = download_from_chrome_webstore(extension_id, extension_dir)
        else:
            logging.info('Downloading the extension from the provider website...')
            crx_file_path = download_from_provider_website(driver, extension_id, crx_download_url, extension_dir)
        
        logging.info(f"Extension extracted to {crx_file_path}")
        return crx_file_path
    except Exception as e:
        logging.error(f'Error downloading or extracting extension: {e}')
        safe_quit(driver)
        raise


def download_from_chrome_webstore(extension_id, extension_dir):
    """
    Download extension from the Chrome Web Store.

    Args:
        extension_id (str): The ID of the extension.
        extension_dir (str): The directory to save the downloaded extension.

    Returns:
        str: The path to the downloaded CRX file.

    Raises:
        subprocess.CalledProcessError: If there is an error during the download process.
    """
    GIT_USERNAME = 'sryze'
    GIT_REPO = 'crx-dl'
    # Remove the crx-dl repository if it already exists to avoid conflicts
    if os.path.exists(GIT_REPO):
        logging.info(f'Removing existing {GIT_REPO} directory...')
        subprocess.run(["rm", "-rf", GIT_REPO], check=True)
    
    # Clone the crx-dl repository then download the extension
    logging.info(f'Cloning the {GIT_USERNAME}/{GIT_REPO} repository...')
    subprocess.run(["git", "clone", f"https://github.com/{GIT_USERNAME}/{GIT_REPO}.git"], check=True)
    logging.info(f'Using {GIT_USERNAME}/{GIT_REPO} to download the extension CRX file from the Chrome Web Store...')
    subprocess.run(["chmod", "+x", f"./{GIT_REPO}/crx-dl.py"], check=True)
    crx_file_path = os.path.join(extension_dir, f"{extension_id}.crx")
    os.makedirs(extension_dir, exist_ok=True)
    subprocess.run(["python3", f"./{GIT_REPO}/crx-dl.py", f"-o={crx_file_path}", extension_id], check=True)
    return crx_file_path


def download_from_provider_website(driver, extension_id, crx_download_url, extension_dir):
    """
    Download extension from the provider website.

    Args:
        driver (webdriver): The WebDriver instance.
        extension_id (str): The ID of the extension.
        crx_download_url (str): The URL to download the extension.
        extension_dir (str): The directory to save the downloaded extension.

    Returns:
        str: The path to the downloaded CRX file.

    Raises:
        FileNotFoundError: If the CRX file is not found after extraction.
        requests.RequestException: If there is an error during the download process.
    """
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
    
    zip_file_path = os.path.join(extension_dir, f"{extension_id}.zip")
    with open(zip_file_path, 'wb') as zip_file:
        zip_file.write(response.content)
        logging.info(f"Downloaded extension to {zip_file_path}")
    
    logging.info(f"Extracting the extension from {zip_file_path}")
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extension_dir)
    
    for root, dirs, files in os.walk(extension_dir):
        for file in files:
            if file.endswith('.crx'):
                logging.info(f"Found CRX file: {file}")
                return os.path.join(root, file)
    
    raise FileNotFoundError('CRX file not found in the extracted folder.')

# function to handle cookie banner: If a cookie banner is present press the button containing the accept text
def handle_cookie_banner(driver):
    """
    Handle the cookie banner by clicking the "Accept" button if it's present.

    Args:
        driver (webdriver): The WebDriver instance.
    """
    try:
        cookie_banner = driver.find_element(By.XPATH, "//button[contains(text(), 'ACCEPT')]")
        if cookie_banner:
            logging.info('Cookie banner found. Accepting cookies...')
            cookie_banner.click()
            time.sleep(random.randint(3, 11))
            logging.info('Cookies accepted.')
    except Exception:
        pass

def login_to_website(driver, email_username, password, login_url, max_retry_multiplier):
    """
    Log in to the website using the given WebDriver instance.

    Args:
        driver (webdriver): The WebDriver instance.
        email_username (str): The user email or username.
        password (str): The user password.
        login_url (str): The login URL.
        max_retry_multiplier (int): The maximum number of retry attempts.

    Returns:
        bool: True if login is successful, otherwise raises an exception.

    Raises:
        Exception: If login fails after maximum retries.
    """
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
            handle_cookie_banner(driver)
            logging.info('Entering credentials...')
            username = driver.find_element(By.NAME, "user")
            username.clear()
            username.send_keys(email_username)
            passwd = driver.find_element(By.NAME, "password")
            passwd.clear()
            passwd.send_keys(password)
            time.sleep(random.randint(3, 11))
            
            logging.info('Clicking the login button...')
            login_button = driver.find_element(By.XPATH, "//button[text()='ACCESS MY ACCOUNT']")
            login_button.click()
            
            logging.info('Waiting for login to complete...')
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//button[text()='Logout']"))
            )
            logging.info('Login successful!')
            handle_cookie_banner(driver)
            time.sleep(random.randint(3, 11))
            return True
        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f'Error during login: {e}')
            if attempt < max_retries - 1:
                logging.info(f'Retrying login... ({attempt + 1}/{max_retries})')
                close_current_tab(driver)
                time.sleep(random.randint(3, 11) * (attempt + 1))
                continue  # Move to the next iteration (retry)
            else:
                safe_quit(driver)
                raise
        except Exception as e:
            logging.error(f'An unexpected error occurred during login: {e}')
            if attempt < max_retries - 1:
                logging.info(f'Retrying login... ({attempt + 1}/{max_retries})')
                close_current_tab(driver)
                time.sleep(random.randint(3, 11) * (attempt + 1))
                continue  # Move to the next iteration (retry)
            else:
                safe_quit(driver)
                raise


def initialize_driver(crx_file_paths=None):
    """
    Initialize the WebDriver with specified options and extensions.

    Args:
        crx_file_paths (list, optional): List of CRX file paths to load as extensions. Defaults to None.

    Returns:
        webdriver: The initialized WebDriver instance.

    Raises:
        Exception: If there is an error during WebDriver initialization.
    """
    driver_options = Options()
    driver_options.add_argument('--no-sandbox')  # Disables the sandbox security feature for compatibility in containerized environments
    driver_options.add_argument('--disable-dev-shm-usage')  # Prevents Chrome from using /dev/shm to avoid limited shared memory issues in Docker
    driver_options.add_argument('--start-maximized')  # Starts the browser maximized to ensure all elements are visible and interactable
    driver_options.add_experimental_option('prefs', {'extensions.ui.developer_mode': True})  # Enables developer mode for extensions

    # Check for headless mode
    headless_mode = os.getenv('HEADLESS', 'false').lower() == 'true'
    if headless_mode:
        driver_options.add_argument('--headless')

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
    """
    Check if the extension is connected and if not, attempt to connect it.

    Args:
        driver (webdriver): The WebDriver instance.
        extension_id (str): The ID of the extension.
        max_retry_multiplier (int): The maximum number of retry attempts.

    Returns:
        str: The handle of the current window.

    Raises:
        Exception: If the extension connection fails after maximum retries.
    """
    max_retries = max_retry_multiplier
    for attempt in range(max_retries):
        try:
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(f'chrome-extension://{extension_id}/index.html')
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'Grass is Connected')]"))
            )
            logging.info('Grass is Connected message found.')
            return driver.current_window_handle  # Return the handle of the current window
        except TimeoutException:
            try:
                connect_button = driver.find_element(By.XPATH, "//button[contains(text(), 'CONNECT GRASS')]")
                logging.info('Connect Grass button found. Clicking the button...')
                connect_button.click()
                time.sleep(random.randint(3, 11))
            except NoSuchElementException:
                logging.error('Neither "Grass is Connected" message nor "CONNECT GRASS" button found.')
                if attempt < max_retries - 1:
                    logging.info(f'Retrying... ({attempt + 1}/{max_retries})')
                    close_current_tab(driver)
                    time.sleep(random.randint(3, 11) * (attempt + 1))
                    continue  # Move to the next iteration (retry)
                else:
                    raise Exception('Failed to find the required elements on the page after several attempts.')
            except Exception as e:
                logging.error(f'An unexpected error occurred while attempting to connect: {e}')
                close_current_tab(driver)
                raise
    return False


def refresh_and_check(driver, extension_id, window_handle):
    """
    Refresh the extension page and check if it remains connected.

    Args:
        driver (webdriver): The WebDriver instance.
        extension_id (str): The ID of the extension.
        window_handle (str): The handle of the window to switch to.

    Raises:
        Exception: If the extension is not connected after refresh.
    """
    try:
        driver.switch_to.window(window_handle)
        logging.info(f'Refreshing extension {extension_id} page...')
        driver.refresh()
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'Grass is Connected')]"))
        )
        logging.info(f'Extension {extension_id} is still connected.')
    except Exception as e:
        logging.error(f'Extension {extension_id} lost connection. Restarting...')
        raise Exception(f'Extension {extension_id} lost connection: {e}')


def close_current_tab(driver):
    """
    Close the current tab and switch to the previous tab.

    Args:
        driver (webdriver): The WebDriver instance.
    """
    if len(driver.window_handles) > 1:
        driver.close()
        driver.switch_to.window(driver.window_handles[-1])


def is_driver_active(driver):
    """
    Check if the WebDriver is still active.

    Args:
        driver (webdriver): The WebDriver instance.

    Returns:
        bool: True if the driver is active, False otherwise.
    """
    try:
        driver.title
        return True
    except WebDriverException:
        return False


def safe_quit(driver):
    """
    Safely quit the WebDriver if it is still running.

    Args:
        driver (webdriver): The WebDriver instance.
    """
    if driver is not None and is_driver_active(driver):
        try:
            logging.info('Closing the browser...')
            driver.quit()
        except WebDriverException as e:
            logging.warning(f'WebDriverException occurred while quitting: {e}')
        except Exception as e:
            logging.error(f'Unexpected error occurred while quitting the browser: {e}')
        finally:
            try:
                driver.quit()
            except Exception:
                pass
    else:
        logging.info('WebDriver is not active or already closed.')


def main():
    """
    Main function to run the script.
    """
    setup_logging()
    logging.info('Launching Grass node application...')
    
    # Read variables from the OS environment making compatible with both USER_EMAIL and also as fallback GRASS_EMAIL (from lite img)
    email_username = os.getenv('USER_EMAIL') or os.getenv('GRASS_EMAIL') or os.getenv('GRASS_USER') or os.getenv('GRASS_USERNAME')
    password = os.getenv('USER_PASSWORD') or os.getenv('GRASS_PASSWORD') or os.getenv('GRASS_PASS')
    extension_ids = os.getenv('EXTENSION_IDS').split(',')
    extension_urls = os.getenv('EXTENSION_URLS').split(',')
    crx_download_urls = os.getenv('CRX_DOWNLOAD_URLS').split(',')
    max_retry_multiplier = int(os.getenv('MAX_RETRY_MULTIPLIER', 3))  # Default to 3 if not set
    
    # Check if credentials are provided
    if not email_username or not password:
        logging.error('No username or password provided. Please set the USER_EMAIL and USER_PASSWORD environment variables.')
        return

    driver = None  # Initialize driver to None

    max_retries = max_retry_multiplier
    for attempt in range(max_retries):
        try:
            crx_file_paths = []
            driver = initialize_driver()
            extension_window_handles = {}

            for extension_id, extension_url, crx_download_url in zip(extension_ids, extension_urls, crx_download_urls):
                # Perform initial login
                login_to_website(driver, email_username, password, extension_url, max_retry_multiplier)
                
                # Download and install the latest extension
                crx_file_path = download_and_extract_extension(driver, extension_id, crx_download_url)
                crx_file_paths.append(crx_file_path)
            
            logging.info('Closing the browser and re-initializing it with the extensions installed...')
            safe_quit(driver)
            driver = None  # Reset driver to None after quitting
            
            # Re-initialize the browser with the new extensions
            driver = initialize_driver(crx_file_paths)
            logging.info('Browser re-initialized with the extensions installed.')
            # Log in again and check the connection status for each extension
            for extension_id, extension_url in zip(extension_ids, extension_urls):
                login_to_website(driver, email_username, password, extension_url, max_retry_multiplier)
                window_handle = check_and_connect(driver, extension_id, max_retry_multiplier)
                extension_window_handles[extension_id] = window_handle
            
            logging.info('All extensions are connected successfully.')

            while True:
                try:
                    time.sleep(random.randint(3600, 14400))  # Wait for 1-4 hours before the next check
                    for extension_id in extension_ids:
                        refresh_and_check(driver, extension_id, extension_window_handles[extension_id])
                except Exception as e:
                    logging.error(f'An error occurred during the refresh cycle: {e}')
                    # safequit driver moved to finally block
                    break  # Exit the while loop to re-initialize
            continue  # Try to re-initialize everything until max attempts
        except Exception as e:
            logging.error(f'An error occurred: {e}')
            # safequit driver moved to finally block
            if attempt < max_retries - 1:
                # Backoff timing: random wait multiplied by attempt and multiplier
                backoff_time = random.randint(11, 31) * (attempt+1) * max_retry_multiplier
                logging.info(f'Backing off for {backoff_time} seconds before attempt {attempt + 1}/{max_retries}...')
                time.sleep(backoff_time)
                continue
            else:
                raise
        finally:
            if driver is not None:
                safe_quit(driver)
                driver = None  # Reset driver to None after quitting


if __name__ == "__main__":
    main()
