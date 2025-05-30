#!/usr/bin/env python3
import os
import requests
import json
import logging
import random
import time
import subprocess
import zipfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, WebDriverException
)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

class LoginFailedError(Exception):
    pass

class ExtensionConnectionError(Exception):
    pass

class ExtensionDownloadError(Exception):
    pass


def setup_logging():
    """Set up logging for the script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def download_and_extract_extension(driver, extension_id, crx_download_url, extension_urls=None, email_username=None, password=None, max_retry_multiplier=3, require_auth=False):
    """
    Download and extract extension with optional authentication.
    
    Args:
        driver (webdriver): The WebDriver instance
        extension_id (str): The ID of the extension
        crx_download_url (str): The URL to download the extension
        extension_urls (list, optional): List of extension URLs
        email_username (str, optional): User email for authentication
        password (str, optional): User password for authentication
        max_retry_multiplier (int, optional): Max retry attempts multiplier
        require_auth (bool, optional): Whether authentication is required
    """
    auth_data = None
    if require_auth and not crx_download_url.startswith('https://chromewebstore.google.com'):
        if not all([extension_urls, email_username, password]):
            raise ValueError("Missing required authentication data: need extension_urls, email_username, and password")
        auth_data = {
            'email': email_username,
            'password': password,
            'login_url': extension_urls[0],
            'max_retry_multiplier': max_retry_multiplier
        }
    extensions_dir = 'extensions'
    os.makedirs(extensions_dir, exist_ok=True)
    extension_dir = os.path.join(extensions_dir, extension_id)
    os.makedirs(extension_dir, exist_ok=True)
    
    try:
        if crx_download_url.startswith('https://chromewebstore.google.com'):
            logging.info('Downloading extension from Chrome Web Store...')
            crx_file_path = download_from_chrome_webstore(extension_id, extension_dir)
        else:
            logging.info('Downloading extension from provider website...')
            crx_file_path = download_with_auth_check(
                driver, 
                extension_id, 
                crx_download_url, 
                extension_dir,
                require_auth,
                auth_data
            )
        
        logging.info(f"Extension extracted to {crx_file_path}")
        return crx_file_path
    except Exception as e:
        logging.error(f'Error downloading/extracting extension: {e}')
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
    
    try:
        # Get the API response using Selenium (maintains session/auth)
        driver.get(crx_download_url)
        response_text = driver.execute_script("return document.body.textContent")
        response_json = json.loads(response_text)
        
        # Extract download information
        data = response_json['result']['data']
        version = data['version']
        linux_download_url = data['links']['linux']
        
        logging.info(f'Downloading version {version} from {linux_download_url}...')
        
        # Use requests with selenium cookies for download
        cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
        headers = {
            'User-Agent': driver.execute_script("return navigator.userAgent"),
            'Accept': '*/*'
        }
        
        response = requests.get(
            linux_download_url, 
            cookies=cookies,
            headers=headers,
            verify=False
        )
        response.raise_for_status()
        
        # Save the downloaded file
        zip_file_path = os.path.join(extension_dir, f"{extension_id}.zip")
        with open(zip_file_path, 'wb') as zip_file:
            zip_file.write(response.content)
            logging.info(f"Downloaded extension to {zip_file_path}")
        
        # Extract the zip file
        logging.info(f"Extracting the extension from {zip_file_path}")
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extension_dir)
        
        # Look for the CRX file
        for root, dirs, files in os.walk(extension_dir):
            for file in files:
                if file.endswith('.crx'):
                    crx_path = os.path.join(root, file)
                    logging.info(f"Found CRX file: {file}")
                    return crx_path
        
        raise FileNotFoundError('CRX file not found in the extracted folder.')
        
    except json.JSONDecodeError as e:
        logging.error(f'Failed to parse API response: {e}')
        raise
    except requests.exceptions.RequestException as e:
        logging.error(f'Network error during download: {e}')
        raise
    except Exception as e:
        logging.error(f'Error downloading extension: {e}')
        raise


def handle_cookie_banner(driver):
    """
    Handle cookie banner by clicking the accept button if it exists.
    Uses multiple strategies to find and handle the cookie consent button.
    Args:
        driver (webdriver): The WebDriver instance.
    """
    logging.info('Checking for cookie banner...')
    try:
        wait = WebDriverWait(driver, 10)
        
        # List of possible selectors and strategies
        selectors = [
            # CSS Selectors
            (By.CSS_SELECTOR, "button.chakra-button.css-1fjpdqi"),
            (By.CSS_SELECTOR, "button.css-1fjpdqi"),
            (By.CSS_SELECTOR, "div.css-dvf5zo button"),
            
            # XPath for text content variations
            (By.XPATH, "//button[contains(., 'ACCEPT') or contains(., 'Accept')]"),
            (By.XPATH, "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ACCEPT')]"),
            (By.XPATH, "//button[.//span[contains(text(), 'ACCEPT')]]"),
            
            # Contextual XPath
            (By.XPATH, "//div[contains(@class, 'cookie') or contains(@class, 'consent')]//button"),
            (By.XPATH, "//div[contains(@class, 'css-dvf5zo')]//button[contains(@class, 'chakra-button')]")
        ]

        cookie_button = None
        for by, selector in selectors:
            try:
                cookie_button = wait.until(
                    EC.element_to_be_clickable((by, selector))
                )
                break
            except (TimeoutException, NoSuchElementException):
                continue

        if not cookie_button:
            logging.info('No cookie banner found with any known selector')
            return

        # Try multiple click strategies
        click_strategies = [
            # Strategy 1: Regular click
            lambda: cookie_button.click(),
            # Strategy 2: JavaScript click
            lambda: driver.execute_script("arguments[0].click();", cookie_button),
            # Strategy 3: Actions click
            lambda: webdriver.ActionChains(driver).move_to_element(cookie_button).click().perform()
        ]

        for strategy in click_strategies:
            try:
                strategy()
                # Wait for any modal/overlay to disappear
                wait.until(lambda d: len(d.find_elements(By.CLASS_NAME, "css-dvf5zo")) == 0)
                logging.info('Cookie banner handled successfully')
                return
            except Exception as e:
                logging.debug(f'Click strategy failed: {str(e)}. Trying next strategy...')
                continue

        raise Exception("All click strategies failed")

    except Exception as e:
        logging.warning(f'Cookie banner handling failed: {str(e)}. Continuing execution...')

def human_like_typing(element, text):
    """
    Simulate human-like typing with realistic delays and occasional typos.
    
    Args:
        element: The web element to type into
        text: The text to type
    """
    # Clear the field with natural movement
    ActionChains(element._parent).move_to_element(element).click().perform()
    element.clear()
    time.sleep(random.uniform(0.5, 1.0))

    # Type with random delays between keystrokes
    for char in text:
        # Random delay between keystrokes
        time.sleep(random.uniform(0.05, 0.25))
        
        # Occasionally add a typo and correct it (roughly 5% chance)
        if random.random() < 0.05:
            # Make a typo
            typo_chars = "qwertyuiopasdfghjklzxcvbnm"
            typo = random.choice(typo_chars)
            element.send_keys(typo)
            
            # Wait before correcting
            time.sleep(random.uniform(0.1, 0.3))
            
            # Delete the typo
            element.send_keys(Keys.BACKSPACE)
            time.sleep(random.uniform(0.1, 0.2))
        
        # Type the correct character
        element.send_keys(char)
        
        # Occasionally pause like a human thinking
        if random.random() < 0.02:
            time.sleep(random.uniform(0.5, 1.2))

# Modify the login_to_website function to use human_like_typing
def login_to_website(driver, email_username, password, login_url, max_retry_multiplier):
    """
    Log in to the website using the given WebDriver instance.
    Contains delays to reduce captcha and give users time to interact.

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
            # Add initial delay before any login attempt
            if attempt > 0:
                delay = random.randint(67, 127)  # delay between attempts
                logging.info(f'Waiting {delay} seconds before next login attempt...')
                time.sleep(delay)

            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(login_url)
            logging.info(f'Waiting for the login page {login_url} to load...')
            
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'CONTINUE')]"))
            )
            logging.info('Login page loaded successfully!')
            
            handle_cookie_banner(driver)
            
            # Add delay before entering credentials
            time.sleep(random.randint(31, 67))
            logging.info('Entering email...')
            username = driver.find_element(By.NAME, "email")
            human_like_typing(username, email_username)
            logging.info("Email entered")

            # Add delay before clicking continue
            time.sleep(random.randint(17, 31))
            button = driver.find_element(By.XPATH, "//button[contains(text(), 'CONTINUE')]")
            button.click()

            use_password_instead = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//p[translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')='USE PASSWORD INSTEAD']"))
            )
            
            # Add delay before clicking "Use Password Instead"
            time.sleep(random.randint(17, 31))
            use_password_instead.click()
            logging.info("Clicked on Use Password Instead")

            # Add delay before entering password
            time.sleep(random.randint(31, 67))
            passwd = driver.find_element(By.NAME, "password")
            human_like_typing(passwd, password)
            logging.info("Password entered")

            # Add delay before clicking sign in
            time.sleep(random.randint(17, 31))
            logging.info('Clicking the login button...')
            login_button = driver.find_element(By.XPATH, "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'SIGN IN')]")
            login_button.click()
            
            logging.info('Waiting for login to complete...')
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//button[text()='Logout']"))
            )
            logging.info('Login successful!')
            
            # Add final delay after successful login
            time.sleep(random.randint(31, 67))
            handle_cookie_banner(driver)
            return True

        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f'Error during login: {e}')
            if attempt < max_retries - 1:
                logging.info(f'Retrying login... ({attempt + 1}/{max_retries})')
                close_current_tab(driver)
                continue
            else:
                raise LoginFailedError(f"Login failed after {max_retries} attempts for user {email_username}: {e}")
        except Exception as e:
            logging.error(f'An unexpected error occurred during login: {e}')
            if attempt < max_retries - 1:
                logging.info(f'Retrying login... ({attempt + 1}/{max_retries})')
                close_current_tab(driver)
                continue
            else:
                raise LoginFailedError(f"An unexpected error occurred during login after {max_retries} attempts for user {email_username}: {e}")


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
                    continue
                else:
                    raise ExtensionConnectionError(f"Failed to connect extension {extension_id} after {max_retries} attempts. Required elements not found.")
            except Exception as e:
                logging.error(f'An unexpected error occurred while attempting to connect: {e}')
                if attempt < max_retries - 1:
                    logging.info(f'Retrying due to unexpected error... ({attempt + 1}/{max_retries})')
                    close_current_tab(driver)
                    time.sleep(random.randint(3, 11) * (attempt + 1))
                    continue
                else:
                    raise ExtensionConnectionError(f"An unexpected error occurred while attempting to connect extension {extension_id} after {max_retries} attempts: {e}")
    raise ExtensionConnectionError(f"Failed to connect extension {extension_id} after {max_retries} attempts (exhausted retries).")


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
                driver.quit() # Attempt quit again in finally, just in case
            except Exception:
                pass # Ignore errors during final quit attempt
    else:
        logging.info('WebDriver is not active or already closed.')


def download_with_auth_check(driver, extension_id, crx_download_url, extension_dir, need_auth=False, auth_data=None):
    """
    Download extension with optional authentication check.
    
    Args:
        driver (webdriver): The WebDriver instance
        extension_id (str): The ID of the extension
        crx_download_url (str): The URL to download the extension
        extension_dir (str): Directory to save the extension
        need_auth (bool): Whether authentication is needed for this download
        auth_data (dict): Dictionary containing auth data {
            'email': str,
            'password': str,
            'login_url': str,
            'max_retry_multiplier': int
        }
    
    Returns:
        str: Path to the downloaded CRX file
    """
    if need_auth and auth_data:
        if not all(k in auth_data for k in ['email', 'password', 'login_url', 'max_retry_multiplier']):
            raise ValueError("Missing required authentication data")
            
        logging.info('Authentication required for download. Logging in...')
        login_to_website(
            driver,
            auth_data['email'],
            auth_data['password'],
            auth_data['login_url'],
            auth_data['max_retry_multiplier']
        )
        
    return download_from_provider_website(driver, extension_id, crx_download_url, extension_dir)

def main():
    """
    Main function to run the script.
    """
    setup_logging()
    try_autologin = os.getenv('TRY_AUTOLOGIN', 'true').lower() == 'true'
    require_auth = os.getenv('REQUIRE_AUTH_FOR_DOWNLOADS', 'false').lower() == 'true'
    logging.info(f"TRY_AUTOLOGIN set to: {try_autologin}")
    logging.info(f"REQUIRE_AUTH_FOR_DOWNLOADS set to: {require_auth}")
    logging.info('Launching Grass node application...')
    
    # Read variables from the OS environment making compatible with both USER_EMAIL and also as fallback GRASS_EMAIL (from lite img)
    email_username = os.getenv('USER_EMAIL') or os.getenv('GRASS_EMAIL') or os.getenv('GRASS_USER') or os.getenv('GRASS_USERNAME')
    password = os.getenv('USER_PASSWORD') or os.getenv('GRASS_PASSWORD') or os.getenv('GRASS_PASS')

    # Check if credentials are provided for autologin, but script can proceed to manual mode if not.
    if not email_username or not password:
        logging.warning('Username or password not provided. Autologin will be skipped if attempted.')

    extension_ids_str = os.getenv('EXTENSION_IDS')
    if not extension_ids_str:
        logging.error("EXTENSION_IDS environment variable is not set. Exiting.")
        return
    extension_ids = extension_ids_str.split(',')

    extension_urls_str = os.getenv('EXTENSION_URLS')
    extension_urls = []
    if extension_urls_str:
        extension_urls = extension_urls_str.split(',')
        if len(extension_urls) != len(extension_ids):
            logging.error("Mismatch between number of EXTENSION_IDS and EXTENSION_URLS. Exiting.")
            return
    else: # Only warn if autologin is attempted with provider downloads that might need it.
        if try_autologin and email_username and password:
             # Check if any crx_download_url is a provider URL
            crx_download_urls_for_check = (os.getenv('CRX_DOWNLOAD_URLS') or "").split(',')
            if any(url and not url.startswith('https://chromewebstore.google.com') for url in crx_download_urls_for_check if url):
                logging.warning("EXTENSION_URLS is not set. This might be an issue if autologin requires login to a website to download extensions from a provider.")


    crx_download_urls_str = os.getenv('CRX_DOWNLOAD_URLS')
    if not crx_download_urls_str:
        logging.error("CRX_DOWNLOAD_URLS environment variable is not set. Exiting.")
        return
    crx_download_urls = crx_download_urls_str.split(',')
    if len(crx_download_urls) != len(extension_ids):
        logging.error("Mismatch between number of EXTENSION_IDS and CRX_DOWNLOAD_URLS. Exiting.")
        return

    max_retry_multiplier = int(os.getenv('MAX_RETRY_MULTIPLIER', 3))
    autologin_successful = False
    driver = None
    manual_mode_activated = False
    extension_window_handles = {}

    if try_autologin and email_username and password:
        logging.info("Attempting autologin...")
        max_retries_main = max_retry_multiplier
        for attempt_main in range(max_retries_main):
            try:
                crx_file_paths = []
                driver = initialize_driver()
                if not extension_urls: # Check before trying to access extension_urls[0]
                    logging.error("EXTENSION_URLS is empty, cannot perform initial login for extension download during autologin.")
                    raise Exception("EXTENSION_URLS is required for autologin sequence if downloads are from provider or if login is needed.")
                
                login_to_website(driver, email_username, password, extension_urls[0], max_retry_multiplier)
                for ext_id, crx_download_url in zip(extension_ids, crx_download_urls):
                    crx_file_path = download_and_extract_extension(
                        driver, 
                        ext_id, 
                        crx_download_url,
                        extension_urls=extension_urls,
                        email_username=email_username,
                        password=password,
                        max_retry_multiplier=max_retry_multiplier,
                        require_auth=require_auth
                    )
                    crx_file_paths.append(crx_file_path)
                logging.info('Closing browser to re-initialize with extensions...')
                safe_quit(driver)
                driver = None
                driver = initialize_driver(crx_file_paths=crx_file_paths)
                logging.info('Browser re-initialized with extensions.')
                login_to_website(driver, email_username, password, extension_urls[0], max_retry_multiplier)
                
                temp_extension_window_handles = {}
                for ext_id in extension_ids:
                    window_handle = check_and_connect(driver, ext_id, max_retry_multiplier)
                    temp_extension_window_handles[ext_id] = window_handle
                extension_window_handles = temp_extension_window_handles
                
                logging.info('All extensions connected successfully. Autologin complete.')
                autologin_successful = True
                break
            except (LoginFailedError, ExtensionConnectionError, ExtensionDownloadError, WebDriverException, TimeoutException, NoSuchElementException, FileNotFoundError) as e:
                logging.error(f'Autologin attempt {attempt_main + 1}/{max_retries_main} failed: {e}')
                if driver:
                    safe_quit(driver)
                    driver = None
                if attempt_main < max_retries_main - 1:
                    time.sleep(random.randint(11, 31) * (attempt_main + 1))
                else:
                    logging.error("Max autologin retries reached. Falling back to manual mode.")
            except Exception as e:
                logging.error(f'Unexpected error during autologin attempt {attempt_main + 1}/{max_retries_main}: {e}')
                if driver:
                    safe_quit(driver)
                    driver = None
                if attempt_main < max_retries_main - 1:
                    time.sleep(random.randint(11, 31) * (attempt_main + 1))
                else:
                    logging.error("Max autologin retries reached after unexpected error. Falling back to manual mode.")
    else:
        if try_autologin and (not email_username or not password):
            logging.warning("TRY_AUTOLOGIN is true, but email or password not provided. Skipping autologin.")
        elif not try_autologin:
            logging.info("TRY_AUTOLOGIN is false. Skipping autologin.")
    
    if not autologin_successful:
        manual_mode_activated = True
        logging.info("Entering manual mode: Attempting to install extension and open its page.")
        try:
            if driver:
                safe_quit(driver)
                driver = None
            
            temp_driver_for_download = None
            crx_file_paths_manual = []
            try:
                needs_temp_driver = any(url and not url.startswith('https://chromewebstore.google.com') for url in crx_download_urls if url)
                if needs_temp_driver:
                    logging.info("Manual mode: Initializing temporary driver for non-CWS extension download.")
                    temp_driver_for_download = initialize_driver()
                
                for ext_id, crx_dl_url in zip(extension_ids, crx_download_urls):
                    logging.info(f"Manual mode: Downloading/extracting extension {ext_id} from {crx_dl_url}")
                    current_driver_for_task = None
                    
                    if not crx_dl_url.startswith('https://chromewebstore.google.com'):
                        current_driver_for_task = temp_driver_for_download
                    
                    crx_path = download_and_extract_extension(
                        current_driver_for_task, 
                        ext_id, 
                        crx_dl_url,
                        extension_urls=extension_urls,
                        email_username=email_username,
                        password=password,
                        max_retry_multiplier=max_retry_multiplier,
                        require_auth=require_auth
                    )
                    crx_file_paths_manual.append(crx_path)
            except ExtensionDownloadError as ede: # Catch specific download error
                 logging.error(f"ExtensionDownloadError in manual mode: {ede}. Will try to open browser.")
            except Exception as e:
                logging.error(f"Failed to download/extract one or more extensions in manual mode: {e}. Will try to open browser.")
            finally:
                if temp_driver_for_download:
                    safe_quit(temp_driver_for_download)

            if crx_file_paths_manual:
                logging.info("Manual mode: Initializing driver with any downloaded extensions.")
                driver = initialize_driver(crx_file_paths=crx_file_paths_manual)
            else:
                logging.warning("Manual mode: No extensions were downloaded/extracted. Proceeding with a basic browser session.")
                driver = initialize_driver()

            if not driver:
                logging.error("Manual mode: Failed to initialize main WebDriver. Exiting.")
                return

            primary_extension_id = extension_ids[0]
            extension_page_url = f'chrome-extension://{primary_extension_id}/index.html'
            logging.info(f"Manual mode: Opening extension page: {extension_page_url}")
            try:
                driver.get(extension_page_url)
            except WebDriverException as e: # Catch error if extension page fails to load
                logging.error(f"Failed to load extension page {extension_page_url} in manual mode: {e}")
                logging.info("Browser will remain open. Please navigate manually or check extension installation.")

            logging.info("Browser is open for manual interaction. Script will now idle.")
            while True: time.sleep(3600)
        except Exception as e:
            logging.error(f"Critical error setting up manual mode: {e}")
            if driver:
                safe_quit(driver)
            logging.info("Exiting due to critical error in manual mode setup.")
            return

    if autologin_successful and driver:
        logging.info("Autologin successful. Starting monitoring loop...")
        try:
            while True:
                time.sleep(random.randint(3600, 14400))
                for ext_id in extension_ids:
                    if ext_id in extension_window_handles: # Check if key exists
                        refresh_and_check(driver, ext_id, extension_window_handles[ext_id])
                    else:
                        logging.warning(f"Window handle for extension ID {ext_id} not found for refresh check.")
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt received. Exiting monitoring loop.")
        except Exception as e:
            logging.error(f"Error in monitoring loop: {e}. Autologin session might be compromised.")
        finally:
            if not manual_mode_activated:
                logging.info("Closing browser from autologin monitoring loop exit.")
                safe_quit(driver)
    elif not manual_mode_activated:
        logging.info("Autologin was not successful and did not enter manual mode. Script will exit.")
        if driver:
            safe_quit(driver)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Script interrupted by user. Exiting.")
    except Exception as e:
        logging.critical(f"Unhandled exception in main: {e}", exc_info=True)
    finally:
        logging.info("Script execution finished.")
