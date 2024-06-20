import os
import requests
import zipfile
import io
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import random
import time
import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_extension(access_token):
    logging.info('Fetching the latest release information...')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get('https://api.getgrass.io/extensionLatestRelease', headers=headers, verify=False)
    response.raise_for_status()
    data = response.json()['result']['data']
    
    version = data['version']
    download_url = data['links']['linux']
    
    logging.info(f'Downloading the latest release version {version}...')
    response = requests.get(download_url, headers=headers, verify=False)
    response.raise_for_status()
    
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall()
    
    return version

def login_and_get_cookies(email, password, extension_url):
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(extension_url)
    
    logging.info('Entering credentials...')
    username = driver.find_element(By.NAME, "user")
    username.send_keys(email)
    passwd = driver.find_element(By.NAME, "password")
    passwd.send_keys(password)
    
    logging.info('Clicking the login button...')
    button = driver.find_element(By.XPATH, "//button")
    button.click()
    logging.info('Waiting for response...')
    time.sleep(random.randint(10, 20))
    
    session_cookies = driver.get_cookies()
    driver.quit()
    
    return session_cookies

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

    # Perform initial login and get session cookies
    session_cookies = login_and_get_cookies(email, password, extension_url)
    
    # Use session cookies to get the API token
    access_token = None
    for cookie in session_cookies:
        if cookie['name'] == 'your_cookie_name_for_token':  # Replace with actual cookie name
            access_token = cookie['value']
            break
    
    if not access_token:
        logging.error('Failed to retrieve access token from session cookies.')
        return

    # Download and install the latest extension
    version = download_extension(access_token)

    # Re-initialize the browser with the new extension
    chrome_options = Options()
    chrome_options.add_extension(f'./grass-community-node-linux-{version}.crx')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0")
    
    driver = webdriver.Chrome(options=chrome_options)

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
        button = driver.find_element(By.XPATH, "//button")
        button.click()
        logging.info('Waiting for response...')
        time.sleep(random.randint(10, 50))
        
        logging.info('Accessing extension settings page...')
        driver.get(f'chrome-extension://{extension_id}/index.html')
        time.sleep(random.randint(3, 7))
        
        logging.info('Clicking the extension button...')
        button = driver.find_element(By.XPATH, "//button")
        button.click()
        
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
