import os

import json
import platform
import psutil

import signal
import smtplib

from email.message import EmailMessage

from APP.UTILS.LOGmaker import *



# ====================
#     LOGGER SETUP
# ====================
Logger = logger("TOOLSbox")


# ====================
#      FUNCTIONS
# ====================

# -------------------------------
#     JSON LOADER FUNCTION(S)
# -------------------------------
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


# --------------------------------
#  PROCESS(ES) KILLER FUNCTION(S)
# --------------------------------
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