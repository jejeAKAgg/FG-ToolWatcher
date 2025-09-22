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


# -------------------------------
#     MAIL SENDER FUNCTION(S)
# -------------------------------
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