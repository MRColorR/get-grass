#!/usr/bin/env python3
import os
import sys
import time
import random
import logging
import subprocess
import re


def setup_logging():
    """
    Set up logging for the script.

    This function configures the root logger with an INFO level and a specific log format.
    It does not take any parameters and does not return any value.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def search_windows_by_name(window_name, max_attempts, max_retry_multiplier):
    """
    Search for visible windows matching the given name using xdotool, with retry and backoff logic.
    
    This function attempts to find at least one visible window matching `window_name` using xdotool.
    If no windows are found on the first attempt, it will retry up to `max_attempts` times, waiting
    an increasing amount of time between attempts, as determined by `max_retry_multiplier` and a 
    random backoff factor.

    Args:
        window_name (str): The substring or pattern to look for in window names.
        max_attempts (int): The maximum number of attempts to find the windows.
        max_retry_multiplier (int): The multiplier used to determine backoff timings.

    Returns:
        list: A list of window IDs (strings) if found.

    Raises:
        SystemExit: If after `max_attempts` no windows are found, the script exits.
    """
    # Initial small wait to allow the application to start
    time.sleep(max_retry_multiplier)

    attempt = 0
    while attempt < max_attempts:
        try:
            cmd = [
                "xdotool", "search", "--sync", "--all", "--onlyvisible",
                "--classname", "--name", window_name
            ]
            output = subprocess.check_output(cmd, universal_newlines=True).strip()
            windows = output.splitlines()
            if windows:
                logging.info(f"{window_name} window detected!")
                return windows
        except subprocess.CalledProcessError:
            # xdotool returns non-zero if no windows found
            pass

        attempt += 1
        if attempt < max_attempts:
            logging.warning(f"{window_name} window not found. Retrying... (attempt {attempt + 1}/{max_attempts})")
            # Backoff timing: random wait multiplied by attempt and multiplier
            backoff_time = random.randint(11, 31) * attempt * max_retry_multiplier
            logging.info(f"Backing off for {backoff_time} seconds before attempt {attempt + 1}/{max_attempts}...")
            time.sleep(backoff_time)

    logging.error(f"Failed to find the {window_name} window after {max_attempts} attempts. Exiting with error.")
    sys.exit(1)


def main():
    """
    Main function to run the Grass Desktop script.

    This function:
    - Sets up logging.
    - Reads environment variables for USER_EMAIL and USER_PASSWORD (and their alternatives).
    - Launches the Grass application if not already configured.
    - Uses xdotool to detect and focus the Grass window.
    - Automates login steps using keystrokes sent via xdotool.
    - Waits in the foreground until the Grass process exits.

    Raises:
        SystemExit: If credentials are not provided or if the Grass window cannot be found after the maximum retries.
    """
    setup_logging()
    logging.info('Starting Grass Desktop script...')

    # Read variables from environment for credentials
    email_username = (os.getenv('USER_EMAIL') or os.getenv('GRASS_EMAIL')
                      or os.getenv('GRASS_USER') or os.getenv('GRASS_USERNAME'))
    password = os.getenv('USER_PASSWORD') or os.getenv('GRASS_PASSWORD') or os.getenv('GRASS_PASS')

    # Retrieve retry multiplier
    MAX_RETRY_MULTIPLIER = int(os.getenv('MAX_RETRY_MULTIPLIER', '3'))

    # Check if credentials are provided
    if not email_username or not password:
        logging.error('No username or password provided. Please set the USER_EMAIL and USER_PASSWORD environment variables.')
        sys.exit(1)

    # Start the Grass application
    logging.info("Launching Grass desktop application...")
    grass_proc = subprocess.Popen(["/usr/bin/grass"])

    # Check if Grass was previously configured
    configured_flag = os.path.expanduser("~/.grass-configured")

    if not os.path.exists(configured_flag):
        logging.info("Grass not configured yet. Waiting for Grass window to appear...")

        MAX_ATTEMPTS = MAX_RETRY_MULTIPLIER
        windows = search_windows_by_name("Grass", MAX_ATTEMPTS, MAX_RETRY_MULTIPLIER)

        delay = MAX_RETRY_MULTIPLIER * 5
        logging.info(f"Waiting {delay} seconds for Grass interface to load...")

        # Focus the last found Grass window
        last_window = windows[-1]
        logging.info("Focusing the Grass main window...")
        subprocess.run(["xdotool", "windowfocus", "--sync", last_window], check=True)
        time.sleep(MAX_RETRY_MULTIPLIER *2 )  # Wait increased x2 to help slow devices

        logging.info("Performing Grass login steps...")
        # Press Tab x4, then Enter
        for _ in range(4):
            subprocess.run(["xdotool", "key", "Tab"], check=True)
        subprocess.run(["xdotool", "key", "Return"], check=True)
        time.sleep(MAX_RETRY_MULTIPLIER *2)  # Wait increased x2 to help slow devices

        logging.info("Entering credentials...")
        # Type the username and press Tab (with a x ms delay between keystrokes)
        if email_username:
            subprocess.run(["xdotool", "type", "--delay", "125", email_username], check=True)
        time.sleep(MAX_RETRY_MULTIPLIER)
        subprocess.run(["xdotool", "key", "Tab"], check=True)

        time.sleep(MAX_RETRY_MULTIPLIER)  # Wait added to help slow devices

        # Type the password and press Return (with a x ms delay between keystrokes)
        if password:
            # Escape all special characters in the password, but avoid double escaping 
            escaped_password = re.sub(r'(?<!\\)([\\^$*+?.()|[\]{}-])', r'\\\1'
            subprocess.run(["xdotool", "type", "--delay", "125", escaped_password], check=True)
            # subprocess.run(["xdotool", "type", "--delay", "125", re.sub("^-", "\-", password)], check=True)
        time.sleep(MAX_RETRY_MULTIPLIER)  # Wait added to help slow devices

        logging.info("Sending credentials...")
        # Enter credentials and log in
        subprocess.run(["xdotool", "key", "Return"], check=True)

        logging.info("Credentials sent. Waiting for login to complete...")
        time.sleep(MAX_RETRY_MULTIPLIER*5)

        # Enable auto updates 
        for _ in range(2):
            subprocess.run(["xdotool", "key", "Tab"], check=True)
            subprocess.run(["xdotool", "key", "space"], check=True)

        time.sleep(MAX_RETRY_MULTIPLIER)  # Wait added to help slow devices

        # Press Escape to leave submenu
        subprocess.run(["xdotool", "key", "Escape"], check=True)

        logging.info("Grass configuration completed successfully. Marking as configured.")
        with open(configured_flag, "w") as f:
            f.write("")

    logging.info("Keeping the Grass process in the foreground...")
    logging.info("Grass Desktop is earning...")
    # Keep the process running in the foreground until Grass exits
    grass_proc.wait()


if __name__ == "__main__":
    main()
