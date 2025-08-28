import os
import sys
import time

import json
import pandas as pd
import platform
import psutil
import re
import signal
import smtplib

from difflib import SequenceMatcher
from rapidfuzz import fuzz

from email.message import EmailMessage

from selenium.webdriver.common.by import By

from UTILS.LOGmaker import *



# ====================
#     LOGGER SETUP
# ====================
Logger = logger("TOOLSbox")


# ====================
#    VARIABLE SETUP
# ====================
if sys.platform.startswith("win"):
    BASE_SYSTEM_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    BASE_TEMP_PATH = sys._MEIPASS if getattr(sys, 'frozen', False) else ""
    CHROME_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chrome-win", "chrome.exe")
    CHROMEDRIVER_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chromedriver_win32", "chromedriver.exe")
    PYTHON_EXE = os.path.join(BASE_SYSTEM_PATH, "CORE", "python", "python.exe") if getattr(sys, 'frozen', False) else sys.executable
    
    CORE_FOLDER = os.path.join(BASE_SYSTEM_PATH, "CORE")
    DATA_FOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA")
    LOGS_FOLDER = os.path.join(BASE_SYSTEM_PATH, "LOGS")

if sys.platform.startswith("linux"):
    BASE_SYSTEM_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    BASE_TEMP_PATH = sys._MEIPASS if getattr(sys, 'frozen', False) else ""
    CHROME_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chrome-win", "chrome.exe")
    CHROMEDRIVER_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chromedriver_win32", "chromedriver.exe")
    
    CORE_FOLDER = os.path.join(BASE_SYSTEM_PATH, "CORE")
    DATA_FOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA")
    LOGS_FOLDER = os.path.join(BASE_SYSTEM_PATH, "LOGS")


# ====================
#      FUNCTIONS
# ====================
def JSONloader(path):
    
    """
    Loads a JSON file from the specified path.

    Args:
        path (str): Path to the JSON file.

    Returns:
        dict: Parsed JSON content.
    
    """

    with open(path, 'r', encoding='utf-8') as file:
        cfg = json.load(file)
    return cfg


# =============================
#   SAFE & CHECK CACHE LOADER
# =============================
def load_cache(path):
    
    """
    Loads a cache CSV file safely. If the file does not exist or fails to load,
    returns an empty DataFrame with predefined columns.

    Args:
        path (str): Path to the cache CSV file.

    Returns:
        pd.DataFrame: DataFrame with cache content or empty with default columns.
    
    """

    columns = ['MPN','Société','Article', 'ArticleURL', 'Marque','Prix (HTVA)','Prix (TVA)',
               'Ancien Prix (HTVA)','Evolution du prix','Offres','Stock','Checked on']
    
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, encoding='utf-8-sig')
            # Ensure all necessary columns are present
            missing_cols = set(columns) - set(df.columns)
            for col in missing_cols:
                df[col] = None
            return df[columns]  # reorder columns
        except Exception as e:
            print(f"⚠️ Error loading cache '{path}': {e}")
            return pd.DataFrame(columns=columns)
    else:
        return pd.DataFrame(columns=columns)
    
def check_cache(cache_df, MPN):
    
    """
    Checks if a given MPN exists in the cache DataFrame.

    Args:
        cache_df (pd.DataFrame): Cache DataFrame.
        MPN (str): The MPN code to search for.

    Returns:
        dict | None: Row as a dictionary if found, else None.
    
    """

    key = f"REF-{MPN}"
    if cache_df.empty or 'MPN' not in cache_df.columns:
        return None
    row = cache_df[cache_df['MPN'] == key]
    if not row.empty:
        return row.iloc[0].to_dict()
    return None


# ===================
#    MATCH TRACKER
# ===================
def potential_match(ref: str, title: str, threshold: float = 0.75, weights: dict = None) -> dict:
    """
    Compute a reliable probability score between a reference and a product title.

    Args:
        ref (str): Reference string (e.g., product code)
        title (str): Product title string
        threshold (float, optional): Minimum score to consider a match. Default = 0.75
        weights (dict, optional): Weights for signals: {"exact":0.5,"fuzzy":0.2,"parts":0.3}

    Returns:
        dict: {
            "match" (bool): True if matched, False otherwise
            "score" (float): final weighted score [0,1]
            "details" (dict): breakdown of metrics used
        }
    """
    if weights is None:
        weights = {"exact": 0.5, "fuzzy": 0.2, "parts": 0.3}

    # -------------------------
    # Normalize strings in-place
    # -------------------------
    def normalize(s: str) -> str:
        s = s.lower()
        s = re.sub(r'[^a-z0-9\s]', '', s)
        s = re.sub(r'\s+', ' ', s).strip()
        # Normalize numbers like "60202.0" -> "60202"
        tokens = []
        for tok in s.split():
            try:
                tokens.append(str(int(float(tok))))
            except:
                tokens.append(tok)
        return ' '.join(tokens)

    ref_norm = normalize(ref)
    title_norm = normalize(title)

    # -------------------------
    # Signals
    # -------------------------
    exact = 1.0 if ref_norm in title_norm else 0.0
    fuzzy_score = fuzz.token_set_ratio(ref_norm, title_norm) / 100
    ref_parts = ref_norm.split()
    parts_score = sum(1 for part in ref_parts if part in title_norm) / len(ref_parts) if ref_parts else 0.0

    # -------------------------
    # Weighted score
    # -------------------------
    final_score = weights["exact"]*exact + weights["fuzzy"]*fuzzy_score + weights["parts"]*parts_score
    final_score = max(0.0, min(1.0, final_score))

    # Adaptive match: accept if exact or all parts present
    match = final_score >= threshold or exact == 1.0 or parts_score == 1.0

    return {
        "match": match,
        "score": final_score,
        "details": {
            "exact": exact,
            "fuzzy_score": fuzzy_score,
            "parts_score": parts_score
        }
    }



# ===============================
#   COOKIE ACCEPTANCE FUNCTIONS
# ===============================
def accept_cookies(driver, site_name):
    
    """
    Automatically clicks the "accept cookies" button for known sites.

    Args:
        driver (selenium.webdriver): Selenium WebDriver instance.
        site_name (str): Name of the website to accept cookies for.

    Notes:
        - Supported sites: fixami, klium, lecot
        - If button is not found or already accepted, logs info.
    
    """

    cookie_buttons = {
        "fixami": "ac",
        "klium": "CybotCookiebotDialogBodyButtonAccept",
        "lecot": "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"
    }

    button_id = cookie_buttons.get(site_name.lower())

    if not button_id:
        Logger.info(f"[{site_name}] No cookie button defined.")
        return

    try:
        accept_button = driver.find_element(By.ID, button_id)
        if accept_button.is_displayed():
            accept_button.click()
            Logger.info(f"Cookies accepted for {site_name}: {driver.current_url}.")
            time.sleep(5)
    except Exception:
        Logger.info(f"No cookies to accept or already accepted for {site_name}: {driver.current_url}.")


# ====================
#    PROCESS KILLER
# ====================
def kill_chromium_processes():
    
    """
    Terminates all Chromium-related processes (chrome, chromium, chromedriver)
    safely depending on the OS.

    Notes:
        - On Windows uses terminate().
        - On Linux/Mac uses SIGTERM signal.
    
    """

    targets = ["chromedriver", "chrome", "chromium"]
    system_os = platform.system().lower()

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pname = proc.info['name']
            if pname and any(t in pname.lower() for t in targets):
                if system_os == "windows":
                    proc.terminate()
                else:
                    proc.send_signal(signal.SIGTERM)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


# =================
#    MAIL SENDER
# =================
def MAILsender(sender_email, password, recipient_email, subject, body, filename):
    
    """
    Sends an email with an attachment via Gmail SMTP SSL.

    Args:
        sender_email (str): Gmail address sending the email.
        password (str): Gmail app password or user password.
        recipient_email (str): Recipient's email address.
        subject (str): Email subject.
        body (str): HTML content of the email.
        filename (str): Path to the file to attach.

    Notes:
        - Uses EmailMessage from standard library.
        - Logs success or warnings if sending fails.
    
    """

    attachment_name = os.path.basename(filename)

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = "FG-ToolWatcher <fgtoolwatcher@gmail.com>"
    msg['To'] = recipient_email
    msg.set_content(body, subtype='html')

    with open(filename, 'rb') as f:
        file_data = f.read()
        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=attachment_name)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, password)
            smtp.send_message(msg)
        Logger.info("Email sent successfully.")
    except Exception as e:
        Logger.warning(f"Error sending email: {e}")