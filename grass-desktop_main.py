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
            logging.warning(f"{window_name} window not found (attempt {attempt}/{max_attempts}). Retrying...")
            backoff_time = random.randint(11, 31) * attempt * max_retry_multiplier
            logging.info(f"Backing off for {backoff_time} seconds before next attempt...")
            time.sleep(backoff_time)

    logging.error(f"Failed to find the {window_name} window after {max_attempts} attempts.")
    return None


def launch_grass_with_retries(max_attempts, wait_time):
    """
    Attempt to start the Grass application up to max_attempts times.
    Returns a subprocess.Popen object if successful, otherwise None.
    """
    for attempt in range(max_attempts):
        logging.info(f"Launching Grass desktop application... (attempt {attempt+1}/{max_attempts})")
        try:
            proc = subprocess.Popen(["/usr/bin/grass"])
        except FileNotFoundError:
            logging.error("Grass executable not found at /usr/bin/grass.")
            return None

        # Wait a little to see if the process remains active
        time.sleep(wait_time)

        if proc.poll() is not None:
            # If the process ended prematurely, try again
            logging.warning(f"Grass process ended prematurely on attempt {attempt+1}.")
            if attempt < max_attempts - 1:
                logging.info("Retrying Grass launch...")
                continue
            else:
                logging.error(f"Failed to start Grass after {max_attempts} attempts.")
                return None
        else:
            # Grass is still running
            return proc
    return None


def send_xdotool_key(key):
    """
    Send a single key press using xdotool, return True if successful, False if not.
    """
    ret = subprocess.run(["xdotool", "key", key], check=False)
    return (ret.returncode == 0)


def kill_process(proc):
    """
    Gracefully terminate a process, then forcibly kill if it doesn't exit.
    """
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def relaunch_grass(max_attempts, max_retry_multiplier):
    """
    Relaunch Grass and return the new process or None if failed.
    """
    wait_time = max_retry_multiplier
    return launch_grass_with_retries(max_attempts, wait_time)


def configure_grass(grass_proc, email_username, password, max_attempts, max_retry_multiplier):
    """
    Attempt to configure Grass (i.e., login and do initial setup) multiple times if the window disappears.
    Returns True if configuration succeeded, False otherwise.
    """
    configured_flag = os.path.expanduser("~/.grass-configured")

    # If already configured, nothing to do
    if os.path.exists(configured_flag):
        logging.info("Grass already configured.")
        return True

    for attempt in range(max_attempts):
        logging.info("Grass not configured yet. Waiting for Grass window to appear...")
        windows = search_windows_by_name("Grass", max_attempts, max_retry_multiplier)
        if windows is None:
            # Window not found even after attempts
            return False

        delay = max_retry_multiplier * 5
        logging.info(f"Waiting {delay} seconds for Grass interface to load...")
        time.sleep(delay)

        # Re-check if window still exists before focusing
        windows = search_windows_by_name("Grass", max_attempts, max_retry_multiplier)
        if windows is None:
            logging.error("Grass window disappeared before focusing. Restarting Grass process.")
            kill_process(grass_proc)
            grass_proc = relaunch_grass(max_attempts, max_retry_multiplier)
            if grass_proc is None:
                return False
            continue

        last_window = windows[-1]
        logging.info("Focusing the Grass main window...")
        if subprocess.run(["xdotool", "windowfocus", "--sync", last_window], check=False).returncode != 0:
            logging.error("Failed to focus Grass window. It might have disappeared. Restarting configuration...")
            kill_process(grass_proc)
            grass_proc = relaunch_grass(max_attempts, max_retry_multiplier)
            if grass_proc is None:
                return False
            continue

        time.sleep(max_retry_multiplier * 2)

        logging.info("Performing Grass login steps...")
        # Press Tab x4, then Enter
        for _ in range(4):
            if not send_xdotool_key("Tab"):
                kill_process(grass_proc)
                grass_proc = relaunch_grass(max_attempts, max_retry_multiplier)
                if grass_proc is None:
                    return False
                continue
        if not send_xdotool_key("Return"):
            kill_process(grass_proc)
            grass_proc = relaunch_grass(max_attempts, max_retry_multiplier)
            if grass_proc is None:
                return False
            continue

        time.sleep(max_retry_multiplier * 2)

        logging.info("Entering credentials...")
        if email_username:
            if subprocess.run(["xdotool", "type", "--delay", "125", email_username], check=False).returncode != 0:
                kill_process(grass_proc)
                grass_proc = relaunch_grass(max_attempts, max_retry_multiplier)
                if grass_proc is None:
                    return False
                continue

        time.sleep(max_retry_multiplier)
        if not send_xdotool_key("Tab"):
            kill_process(grass_proc)
            grass_proc = relaunch_grass(max_attempts, max_retry_multiplier)
            if grass_proc is None:
                return False
            continue

        time.sleep(max_retry_multiplier)
        if password:
            # Use re.sub to escape leading dash if present
            escaped_password = re.sub(r"^-", r"\-", password)
            if subprocess.run(["xdotool", "type", "--delay", "125", escaped_password], check=False).returncode != 0:
                kill_process(grass_proc)
                grass_proc = relaunch_grass(max_attempts, max_retry_multiplier)
                if grass_proc is None:
                    return False
                continue

        time.sleep(max_retry_multiplier)

        logging.info("Sending credentials...")
        if not send_xdotool_key("Return"):
            kill_process(grass_proc)
            grass_proc = relaunch_grass(max_attempts, max_retry_multiplier)
            if grass_proc is None:
                return False
            continue

        logging.info("Credentials sent. Waiting for login to complete...")
        time.sleep(max_retry_multiplier * 3)

        # Enable auto updates (Tab x2, space x2)
        for _ in range(2):
            if not (send_xdotool_key("Tab") and send_xdotool_key("space")):
                kill_process(grass_proc)
                grass_proc = relaunch_grass(max_attempts, max_retry_multiplier)
                if grass_proc is None:
                    return False
                continue

        time.sleep(max_retry_multiplier)

        # Press Escape to leave Grass submenu
        if not send_xdotool_key("Escape"):
            kill_process(grass_proc)
            grass_proc = relaunch_grass(max_attempts, max_retry_multiplier)
            if grass_proc is None:
                return False
            continue

        logging.info("Grass configuration completed successfully. Marking as configured.")
        with open(configured_flag, "w") as f:
            f.write("")
        return True

    return False


def main():
    setup_logging()

    MAX_RETRY_MULTIPLIER = int(os.getenv('MAX_RETRY_MULTIPLIER') or 3)

    # Optional initial wait to help in slow environments
    initial_wait = MAX_RETRY_MULTIPLIER * 5
    logging.info(f"Initial wait of {initial_wait}s to allow the X server to stabilize on slow devices.")
    time.sleep(initial_wait)

    logging.info('Starting Grass Desktop script...')

    # Retrieve credentials from env variables
    email_username = (
        os.getenv('USER_EMAIL') or os.getenv('GRASS_EMAIL')
        or os.getenv('GRASS_USER') or os.getenv('GRASS_USERNAME')
    )
    password = (
        os.getenv('USER_PASSWORD') or os.getenv('GRASS_PASSWORD')
        or os.getenv('GRASS_PASS')
    )

    if not email_username or not password:
        logging.error('No username or password provided. Please set the USER_EMAIL and USER_PASSWORD environment variables.')
        sys.exit(1)

    max_attempts = MAX_RETRY_MULTIPLIER
    wait_time = MAX_RETRY_MULTIPLIER

    # Launch Grass with retries
    grass_proc = launch_grass_with_retries(max_attempts, wait_time)
    if grass_proc is None:
        sys.exit(1)

    # Configure Grass (login etc.) if needed
    if not configure_grass(grass_proc, email_username, password, max_attempts, MAX_RETRY_MULTIPLIER):
        logging.error("Failed to configure Grass after multiple attempts. Exiting.")
        kill_process(grass_proc)
        sys.exit(1)

    logging.info("Keeping the Grass process in the foreground...")
    logging.info("Grass Desktop is earning...")

    # Keep the process running in the foreground until Grass exits
    grass_proc.wait()


if __name__ == "__main__":
    main()
