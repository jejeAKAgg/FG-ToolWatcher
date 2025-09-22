# WEBSITES/WEBSITEutils.py
import os
import time

import pandas as pd
import re

from selenium.webdriver.common.by import By

from rapidfuzz import fuzz

from APP.UTILS.LOGmaker import *


# ====================
#     LOGGER SETUP
# ====================
Logger = logger("WEBSITEutils")


# ====================
#      FUNCTIONS
# ====================

# -------------------------------
#  COOKIE ACCEPTANCE FUNCTION(S)
# -------------------------------
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


# -------------------------------
#    MATCH TRACKER FUNCTION(S)
# -------------------------------
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


# -----------------------------------------
#   SAFE & CHECK CACHE LOADER FUNCTION(S)
# -----------------------------------------
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
