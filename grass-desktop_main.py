#!/usr/bin/env python3
import os
import sys
import time
import random
import logging
import subprocess
import re
from typing import List, Optional, Tuple, Any

# --- Constants ---
GRASS_EXECUTABLE_PATH = "/usr/bin/grass"
GRASS_WINDOW_NAME = "Grass"
CONFIGURED_FLAG_FILE = "~/.grass-configured"

# Default values for environment variables
DEFAULT_MAX_RETRY_MULTIPLIER = 3
DEFAULT_TRY_AUTOLOGIN = "true" # Stored as string, like os.getenv

# Timeouts and delays (can be scaled by MAX_RETRY_MULTIPLIER)
INITIAL_X_SERVER_WAIT_FACTOR = 5 # Multiplied by MAX_RETRY_MULTIPLIER
GRASS_LAUNCH_WAIT_FACTOR = 1 # Multiplied by MAX_RETRY_MULTIPLIER (implicit in how it's used)
WINDOW_SEARCH_INITIAL_WAIT_FACTOR = 1 # Multiplied by MAX_RETRY_MULTIPLIER
WINDOW_SEARCH_BACKOFF_MIN_FACTOR = 11 # For random backoff calculation
WINDOW_SEARCH_BACKOFF_MAX_FACTOR = 31 # For random backoff calculation
GRASS_INTERFACE_LOAD_WAIT_FACTOR = 5 # Multiplied by MAX_RETRY_MULTIPLIER
POST_FOCUS_WAIT_FACTOR = 2 # Multiplied by MAX_RETRY_MULTIPLIER
POST_LOGIN_STEP_WAIT_FACTOR = 2 # Multiplied by MAX_RETRY_MULTIPLIER
POST_CREDENTIAL_ENTRY_WAIT_FACTOR = 1 # Multiplied by MAX_RETRY_MULTIPLIER
POST_LOGIN_ATTEMPT_WAIT_FACTOR = 3 # Multiplied by MAX_RETRY_MULTIPLIER
POST_AUTO_UPDATE_TOGGLE_WAIT_FACTOR = 1 # Multiplied by MAX_RETRY_MULTIPLIER
PROCESS_TERMINATE_TIMEOUT = 5 # Seconds to wait for graceful termination

# xdotool command base
XDOTOOL_CMD = ["xdotool"]
XDOTOOL_TYPE_DELAY_MS = "125"


def setup_logging() -> None:
    """
    Set up logging for the script.

    Configures the root logger with an INFO level and a specific log format
    (asctime, levelname, message).
    """
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )


def _run_subprocess(
    cmd: List[str], check: bool = False, **kwargs: Any
) -> subprocess.CompletedProcess[str]:
    """
    Wrapper for subprocess.run with common arguments and error logging.
    kwargs are passed to subprocess.run.
    """
    try:
        return subprocess.run(
            cmd, check=check, universal_newlines=True, **kwargs
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"Command '{' '.join(cmd)}' failed with error: {e}")
        raise
    except FileNotFoundError:
        logging.error(f"Command '{cmd[0]}' not found. Please ensure it is installed and in PATH.")
        raise


def search_windows_by_name(
    window_name: str, max_attempts: int, retry_multiplier: int
) -> Optional[List[str]]:
    """
    Search for visible windows matching a name using xdotool, with retry and backoff.

    Attempts to find visible windows matching `window_name`. Retries up to
    `max_attempts` with increasing, randomized backoff times scaled by
    `retry_multiplier`.

    Args:
        window_name: The substring or pattern for window names (used with xdotool --name).
        max_attempts: Maximum number of search attempts.
        retry_multiplier: Factor to scale backoff timings.

    Returns:
        A list of window IDs (strings) if found, otherwise None.
    """
    # Initial small wait, scaled by retry_multiplier
    time.sleep(retry_multiplier * WINDOW_SEARCH_INITIAL_WAIT_FACTOR)

    for attempt in range(max_attempts):
        try:
            cmd = XDOTOOL_CMD + [
                "search", "--sync", "--all", "--onlyvisible",
                "--classname", "--name", window_name,
            ]
            # Use subprocess.check_output directly as it's simpler for this case
            output = subprocess.check_output(cmd, universal_newlines=True).strip()
            windows = output.splitlines()
            if windows:
                logging.info(f"'{window_name}' window detected with IDs: {windows}")
                return windows
        except subprocess.CalledProcessError:
            # xdotool returns non-zero if no windows are found, which is expected.
            pass
        except FileNotFoundError:
            logging.error(f"xdotool command not found. Please ensure it is installed.")
            return None # Cannot proceed without xdotool

        if attempt < max_attempts - 1:
            logging.warning(
                f"'{window_name}' window not found (attempt {attempt + 1}/{max_attempts}). Retrying..."
            )
            backoff_time = (
                random.randint(WINDOW_SEARCH_BACKOFF_MIN_FACTOR, WINDOW_SEARCH_BACKOFF_MAX_FACTOR)
                * (attempt + 1) # Increase backoff with attempts
                * retry_multiplier
            )
            logging.info(f"Backing off for {backoff_time:.2f} seconds before next attempt...")
            time.sleep(backoff_time)

    logging.error(
        f"Failed to find the '{window_name}' window after {max_attempts} attempts."
    )
    return None


def launch_grass_with_retries(
    max_attempts: int, retry_multiplier: int
) -> Optional[subprocess.Popen[Any]]:
    """
    Attempt to start the Grass application, retrying on premature exits.

    Launches Grass using GRASS_EXECUTABLE_PATH. If the process exits prematurely,
    it retries up to `max_attempts` times.

    Args:
        max_attempts: Maximum launch attempts.
        retry_multiplier: Used to determine wait time between launch and poll.

    Returns:
        A subprocess.Popen object if Grass starts successfully, otherwise None.
    """
    wait_time_after_launch = retry_multiplier * GRASS_LAUNCH_WAIT_FACTOR
    for attempt in range(max_attempts):
        logging.info(
            f"Launching Grass desktop application... (Attempt {attempt + 1}/{max_attempts})"
        )
        try:
            proc = subprocess.Popen([GRASS_EXECUTABLE_PATH])
        except FileNotFoundError:
            logging.error(
                f"Grass executable not found at '{GRASS_EXECUTABLE_PATH}'. Cannot start Grass."
            )
            return None

        time.sleep(wait_time_after_launch) # Wait a bit before polling

        if proc.poll() is not None: # Process has terminated
            logging.warning(
                f"Grass process ended prematurely on attempt {attempt + 1} with code {proc.returncode}."
            )
            if attempt < max_attempts - 1:
                logging.info("Retrying Grass launch...")
            else:
                logging.error(
                    f"Failed to start Grass after {max_attempts} attempts."
                )
                return None
        else: # Process is still running
            logging.info("Grass application launched successfully.")
            return proc
    return None # Should be unreachable if logic is correct, but as a fallback


def send_xdotool_key(key_sequence: str, retry_multiplier: int, delay_ms: str = XDOTOOL_TYPE_DELAY_MS) -> bool:
    """
    Send a key sequence using xdotool.

    Args:
        key_sequence: The key(s) to send (e.g., "Tab", "Return", "alt+F4").
        retry_multiplier: Used for a small delay after sending the key.
        delay_ms: Delay between keystrokes when typing a string.

    Returns:
        True if xdotool command returns 0, False otherwise.
    """
    # Differentiate between single keys and typing strings
    if " " in key_sequence or len(key_sequence) > 1 and key_sequence.isalnum(): # Heuristic for typing
        cmd = XDOTOOL_CMD + ["type", "--delay", delay_ms, key_sequence]
    else:
        cmd = XDOTOOL_CMD + ["key", key_sequence]

    logging.info(f"Sending keys: '{key_sequence}'")
    try:
        # Using _run_subprocess for potential FileNotFoundError and logging
        # We don't use check=True here as failure is handled by return code.
        result = _run_subprocess(cmd)
        time.sleep(retry_multiplier * 0.1) # Small delay after key press
        return result.returncode == 0
    except (FileNotFoundError, subprocess.CalledProcessError): # Should be caught by _run_subprocess but as safeguard
        return False


def kill_process(proc: subprocess.Popen[Any]) -> None:
    """
    Gracefully terminate a process, then forcibly kill if it doesn't exit.

    Args:
        proc: The subprocess.Popen object to terminate.
    """
    if proc.poll() is None: # Process is still running
        logging.info(f"Terminating process {proc.pid}...")
        proc.terminate()
        try:
            proc.wait(timeout=PROCESS_TERMINATE_TIMEOUT)
            logging.info(f"Process {proc.pid} terminated gracefully.")
        except subprocess.TimeoutExpired:
            logging.warning(
                f"Process {proc.pid} did not terminate gracefully. Forcibly killing."
            )
            proc.kill()
            proc.wait() # Ensure kill is processed
            logging.info(f"Process {proc.pid} killed.")


def _get_credentials() -> Tuple[Optional[str], Optional[str]]:
    """
    Retrieve email and password from standard environment variables.
    
    Returns:
        A tuple (email_username, password). Values can be None if not set.
    """
    email_username = (
        os.getenv("USER_EMAIL")
        or os.getenv("GRASS_EMAIL")
        or os.getenv("GRASS_USER")
        or os.getenv("GRASS_USERNAME")
    )
    password = (
        os.getenv("USER_PASSWORD")
        or os.getenv("GRASS_PASSWORD")
        or os.getenv("GRASS_PASS")
    )
    return email_username, password


def configure_grass(
    grass_proc_ref: subprocess.Popen[Any], # Pass by reference for potential relaunch
    email_username: Optional[str],
    password: Optional[str],
    max_attempts: int,
    retry_multiplier: int,
) -> bool:
    """
    Attempt to configure Grass (login, initial setup) via xdotool automation.

    This function navigates the Grass login and initial setup screens.
    It handles cases where the Grass window might disappear by attempting to
    relaunch Grass and retry configuration.

    Args:
        grass_proc_ref: The running Grass process. This is passed as a list containing
                        the Popen object to allow modification (relaunch) within this function.
                        Not ideal, but works for now.
        email_username: The email/username for login.
        password: The password for login.
        max_attempts: Max attempts for the overall configuration process.
        retry_multiplier: Factor to scale various delays and timeouts.

    Returns:
        True if configuration is successful (or already configured).
        False if configuration fails after all attempts or due to critical errors.
    """
    configured_flag_path = os.path.expanduser(CONFIGURED_FLAG_FILE)
    if os.path.exists(configured_flag_path):
        logging.info(f"Grass already configured (flag found: {configured_flag_path}).")
        return True

    if not email_username or not password:
        logging.error("Credentials not provided to configure_grass. Cannot proceed with autologin.")
        return False # Should be caught earlier, but good safeguard

    current_grass_proc = grass_proc_ref # Assuming grass_proc_ref is the Popen object directly now

    for attempt in range(max_attempts):
        logging.info(f"Attempting Grass configuration (Attempt {attempt + 1}/{max_attempts})...")

        windows = search_windows_by_name(GRASS_WINDOW_NAME, max_attempts, retry_multiplier)
        if windows is None:
            logging.error(f"Grass window '{GRASS_WINDOW_NAME}' not found. Cannot configure.")
            # Try to relaunch Grass if it died
            if current_grass_proc.poll() is not None:
                logging.info("Grass process seems to have died. Attempting relaunch for configuration...")
                new_proc = launch_grass_with_retries(max_attempts, retry_multiplier)
                if new_proc:
                    current_grass_proc = new_proc # Update the process reference
                else:
                    logging.error("Failed to relaunch Grass. Configuration aborted.")
                    return False
            continue # Retry search_windows_by_name or fail after max_attempts

        time.sleep(retry_multiplier * GRASS_INTERFACE_LOAD_WAIT_FACTOR)

        # Re-check if window still exists before focusing (it might crash/close)
        windows = search_windows_by_name(GRASS_WINDOW_NAME, 1, 1) # Quick check
        if not windows:
            logging.warning("Grass window disappeared before focusing. Retrying configuration step.")
            if current_grass_proc.poll() is not None: # If grass died, try relaunch
                 new_proc = launch_grass_with_retries(max_attempts, retry_multiplier)
                 if new_proc: current_grass_proc = new_proc
                 else: return False
            continue

        last_window_id = windows[-1]
        logging.info(f"Focusing the Grass main window (ID: {last_window_id})...")
        if _run_subprocess(XDOTOOL_CMD + ["windowfocus", "--sync", last_window_id]).returncode != 0:
            logging.warning("Failed to focus Grass window. It might have disappeared. Retrying.")
            if current_grass_proc.poll() is not None: # If grass died, try relaunch
                 new_proc = launch_grass_with_retries(max_attempts, retry_multiplier)
                 if new_proc: current_grass_proc = new_proc
                 else: return False
            continue

        time.sleep(retry_multiplier * POST_FOCUS_WAIT_FACTOR)

        # Automation steps (Tab, Enter, Type credentials, etc.)
        # Each step checks for success and continues to next attempt if a step fails
        logging.info("Performing login steps...")
        if not all(send_xdotool_key("Tab", retry_multiplier) for _ in range(4)): continue
        if not send_xdotool_key("Return", retry_multiplier): continue
        time.sleep(retry_multiplier * POST_LOGIN_STEP_WAIT_FACTOR)

        logging.info(f"Entering username: {'*' * len(email_username) if email_username else 'N/A'}")
        if not send_xdotool_key(email_username, retry_multiplier): continue
        time.sleep(retry_multiplier * POST_CREDENTIAL_ENTRY_WAIT_FACTOR)

        if not send_xdotool_key("Tab", retry_multiplier): continue
        time.sleep(retry_multiplier * POST_CREDENTIAL_ENTRY_WAIT_FACTOR)

        logging.info(f"Entering password: {'*' * len(password) if password else 'N/A'}")
        # Escape leading dash for xdotool type if password starts with '-'
        escaped_password = re.sub(r"^-", r"\\-", password) if password else ""
        if not send_xdotool_key(escaped_password, retry_multiplier): continue
        time.sleep(retry_multiplier * POST_CREDENTIAL_ENTRY_WAIT_FACTOR)

        logging.info("Submitting credentials...")
        if not send_xdotool_key("Return", retry_multiplier): continue
        logging.info("Credentials submitted. Waiting for login process...")
        time.sleep(retry_multiplier * POST_LOGIN_ATTEMPT_WAIT_FACTOR)

        # Example: Enable auto updates (Tab x2, space x2)
        logging.info("Attempting to configure auto-updates (example step)...")
        if not all(send_xdotool_key("Tab", retry_multiplier) for _ in range(2)): continue
        if not all(send_xdotool_key("space", retry_multiplier) for _ in range(2)): continue
        time.sleep(retry_multiplier * POST_AUTO_UPDATE_TOGGLE_WAIT_FACTOR)

        logging.info("Pressing Escape to potentially close submenus/dialogs...")
        if not send_xdotool_key("Escape", retry_multiplier): continue

        # Check if configuration seems complete (e.g., main window still there, or a new one appears)
        # This part is crucial and might need adjustment based on Grass behavior after login.
        # For now, assume if all steps passed, it's configured.
        logging.info("Grass configuration steps completed successfully.")
        try:
            with open(configured_flag_path, "w") as f:
                f.write(time.strftime("%Y-%m-%d %H:%M:%S"))
            logging.info(f"Created configuration flag: {configured_flag_path}")
            return True # Configuration successful
        except IOError as e:
            logging.error(f"Failed to write configuration flag file: {e}")
            return False # Critical error, cannot mark as configured

    logging.error(f"Failed to configure Grass after {max_attempts} attempts.")
    return False


def main() -> None:
    """
    Main function to launch and optionally configure Grass Desktop.

    Handles:
    - Initial setup (logging, environment variables).
    - Launching Grass application with retries.
    - Reading TRY_AUTOLOGIN environment variable.
    - Retrieving credentials.
    - Conditionally attempting autologin (Grass configuration).
    - Gracefully falling back to manual mode if autologin is disabled,
      credentials are missing, or autologin process fails.
    - Keeping the Grass process running.
    """
    setup_logging()

    max_retry_multiplier_str = os.getenv("MAX_RETRY_MULTIPLIER", str(DEFAULT_MAX_RETRY_MULTIPLIER))
    try:
        max_retry_multiplier = int(max_retry_multiplier_str)
    except ValueError:
        logging.warning(
            f"Invalid MAX_RETRY_MULTIPLIER: '{max_retry_multiplier_str}'. Using default: {DEFAULT_MAX_RETRY_MULTIPLIER}"
        )
        max_retry_multiplier = DEFAULT_MAX_RETRY_MULTIPLIER

    initial_wait = max_retry_multiplier * INITIAL_X_SERVER_WAIT_FACTOR
    logging.info(
        f"Initial wait of {initial_wait}s to allow X server to stabilize."
    )
    time.sleep(initial_wait)

    logging.info("Starting Grass Desktop script...")

    email_username, password = _get_credentials()

    try_autologin_env_str: str = os.getenv("TRY_AUTOLOGIN", DEFAULT_TRY_AUTOLOGIN)
    # Autologin is true if TRY_AUTOLOGIN is 'true' (case-insensitive)
    should_try_autologin: bool = try_autologin_env_str.lower() == "true"
    
    autologin_status_message: str = ""

    if should_try_autologin:
        if not email_username or not password:
            logging.warning(
                "Autologin enabled by TRY_AUTOLOGIN, but credentials (e.g., USER_EMAIL, USER_PASSWORD) missing. "
                "Switching to manual login mode."
            )
            should_try_autologin = False
            autologin_status_message = "Autologin disabled: Credentials not provided."
        else:
            autologin_status_message = "Autologin enabled: TRY_AUTOLOGIN is true and credentials provided."
    else:
        autologin_status_message = f"Autologin disabled: TRY_AUTOLOGIN set to '{try_autologin_env_str}'."
        if not email_username or not password:
             logging.info("Credentials also not provided (this is informational as autologin is disabled).")


    logging.info(f"Effective autologin status: {autologin_status_message}")

    # max_attempts for launch and configure can be the same as retry_multiplier or different
    # For simplicity, using max_retry_multiplier as the number of attempts too.
    launch_configure_max_attempts = max_retry_multiplier

    grass_proc = launch_grass_with_retries(
        launch_configure_max_attempts, max_retry_multiplier
    )

    if grass_proc is None:
        logging.error("Grass application failed to launch. Exiting script.")
        sys.exit(1) # Critical failure if Grass itself doesn't start

    if should_try_autologin:
        logging.info("Proceeding with automated Grass configuration (autologin)...")
        # Pass grass_proc directly, configure_grass no longer modifies it by list reference
        if configure_grass(
            grass_proc, email_username, password, launch_configure_max_attempts, max_retry_multiplier
        ):
            logging.info("Grass configuration (autologin) reported success.")
            autologin_status_message = "Autologin successful."
        else:
            # Resilience Enhancement: If configure_grass fails, do NOT exit or kill.
            logging.error(
                "Automated Grass configuration (autologin) failed. Switching to manual login mode. "
                "Grass will remain running. Please check logs for details of the failure."
            )
            autologin_status_message = "Autologin attempted but failed. Running in manual mode."
            # ensure should_try_autologin is false so we don't think we are in autologin mode
            should_try_autologin = False 
    else:
        # This branch is hit if autologin was initially disabled OR
        # it was enabled but credentials were missing (should_try_autologin became false).
        logging.info(f"{autologin_status_message} Waiting for manual Grass interaction.")


    logging.info(f"Final status: {autologin_status_message} Keeping Grass process ({grass_proc.pid}) in foreground.")
    logging.info("Grass Desktop is now running. Interact with the VNC window for manual login if needed.")

    try:
        grass_proc.wait() # Wait for Grass process to exit
        logging.info(f"Grass process {grass_proc.pid} has exited with code {grass_proc.returncode}.")
    except KeyboardInterrupt:
        logging.info("Script interrupted by user (Ctrl+C). Terminating Grass...")
        kill_process(grass_proc)
        logging.info("Grass terminated due to script interruption.")
    sys.exit(grass_proc.returncode if grass_proc.returncode is not None else 0)


if __name__ == "__main__":
    main()
