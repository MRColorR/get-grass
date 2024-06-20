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

def get_access_token(email, password):
    logging.info('Authenticating with the API...')
    auth_url = 'https://api.getgrass.io/login'
    payload = {
        'email': email,
        'password': password
    }
    response = requests.post(auth_url, json=payload)
    response.raise_for_status()
    return response.json()['access_token']

def download_extension(access_token):
    logging.info('Fetching the latest release information...')
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get('https://api.getgrass.io/extensionLatestRelease', headers=headers)
    response.raise_for_status()
    data = response.json()['result']['data']
    
    version = data['version']
    download_url = data['links']['linux']
    
    logging.info(f'Downloading the latest release version {version}...')
    response = requests.get(download_url)
    response.raise_for_status()
    
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall()
    
    return version

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

    access_token = get_access_token(email, password)
    version = download_extension(access_token)

    chrome_options = Options()
    chrome_options.add_extension(f'./grass-community-node-linux-{version}.crx')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0")

    # Initialize the WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Navigate to a webpage
        logging.info(f'Navigating to {extension_url} website...')
        driver.get(extension_url)
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
