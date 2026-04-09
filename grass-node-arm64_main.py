#!/usr/bin/env python3
"""
Grass Node for arm64 (Raspberry Pi) - Manual Login variant.

Launches Chromium with the Grass extension pre-loaded, then opens the
Grass dashboard. The user completes login manually via the noVNC web UI
on port 6080. Once connected, the script monitors the extension and
restarts the browser if the connection drops.
"""
import os
import logging
import random
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, WebDriverException
)


def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def download_extension(extension_id, extension_dir):
    """Download extension CRX directly from the Chrome Web Store."""
    os.makedirs(extension_dir, exist_ok=True)
    crx_file_path = os.path.join(extension_dir, f"{extension_id}.crx")

    url = (
        "https://clients2.google.com/service/update2/crx"
        f"?response=redirect&prodversion=131.0.0.0&acceptformat=crx2,crx3"
        f"&x=id%3D{extension_id}%26uc"
    )
    logging.info(f'Downloading extension {extension_id} from Chrome Web Store...')
    resp = requests.get(url, allow_redirects=True, timeout=60)
    resp.raise_for_status()

    with open(crx_file_path, 'wb') as f:
        f.write(resp.content)
    logging.info(f'Extension downloaded to {crx_file_path} ({len(resp.content)} bytes)')
    return crx_file_path


def initialize_driver(crx_file_paths=None):
    """Initialize ChromeDriver with Debian's chromium paths."""
    driver_options = Options()
    driver_options.binary_location = '/usr/bin/chromium'
    driver_options.add_argument('--no-sandbox')
    driver_options.add_argument('--disable-dev-shm-usage')
    driver_options.add_argument('--start-maximized')
    driver_options.add_experimental_option('prefs', {'extensions.ui.developer_mode': True})
    driver_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    )

    if crx_file_paths:
        for crx_file_path in crx_file_paths:
            driver_options.add_extension(crx_file_path)

    service = Service(executable_path='/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=driver_options)
    return driver


def wait_for_login(driver, extension_id, timeout=1800):
    """Wait for the user to log in manually. Polls every 30s for up to 30 minutes."""
    logging.info('='*60)
    logging.info('Open noVNC at http://<your-host>:6080 and log in to Grass.')
    logging.info('The script will detect when you are connected.')
    logging.info('='*60)

    start = time.time()
    while time.time() - start < timeout:
        try:
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(f'chrome-extension://{extension_id}/index.html')
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'Grass is Connected')]"))
            )
            logging.info('Grass is Connected!')
            return driver.current_window_handle
        except (TimeoutException, NoSuchElementException, WebDriverException):
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[-1])
            logging.info('Waiting for login... (check noVNC on port 6080)')
            time.sleep(30)

    raise TimeoutException('Timed out waiting for manual login after 30 minutes.')


def refresh_and_check(driver, extension_id, window_handle):
    """Check if the extension is still connected."""
    driver.switch_to.window(window_handle)
    driver.refresh()
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'Grass is Connected')]"))
    )
    logging.info(f'Extension {extension_id} is still connected.')


def safe_quit(driver):
    if driver is not None:
        try:
            driver.quit()
        except Exception:
            pass


def main():
    setup_logging()
    logging.info('Launching Grass node (arm64 - manual login)...')

    extension_id = os.getenv('EXTENSION_ID', 'ilehaonighjijnmpnagapkhpcdbhclfg')
    max_retry_multiplier = int(os.getenv('MAX_RETRY_MULTIPLIER', 3))
    driver = None

    for attempt in range(max_retry_multiplier):
        try:
            # Download extension
            ext_dir = os.path.join('extensions', extension_id)
            crx_path = download_extension(extension_id, ext_dir)

            # Launch browser with extension
            driver = initialize_driver([crx_path])
            driver.get('https://app.grass.io/dashboard')
            logging.info('Browser launched with Grass extension. Waiting for manual login...')

            # Wait for user to log in via VNC
            window_handle = wait_for_login(driver, extension_id)

            # Monitor connection
            while True:
                time.sleep(random.randint(3600, 14400))
                try:
                    refresh_and_check(driver, extension_id, window_handle)
                except Exception as e:
                    logging.error(f'Connection lost: {e}')
                    break

        except Exception as e:
            logging.error(f'Error: {e}')
            if attempt < max_retry_multiplier - 1:
                backoff = random.randint(30, 90) * (attempt + 1)
                logging.info(f'Retrying in {backoff}s... ({attempt + 1}/{max_retry_multiplier})')
                time.sleep(backoff)
        finally:
            safe_quit(driver)
            driver = None


if __name__ == "__main__":
    main()
