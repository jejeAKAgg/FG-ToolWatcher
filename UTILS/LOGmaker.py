# UTILS/LOGmaker.py
import logging
import os
from datetime import datetime
import sys  # <--- ajout

_LOGGER = None

def logger(module_name):
    global _LOGGER

    if _LOGGER is not None:
        return _LOGGER.getChild(module_name)

    log_dir = "LOGS"
    os.makedirs(log_dir, exist_ok=True)
    log_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
    log_file = os.path.join(log_dir, log_filename)

    _LOGGER = logging.getLogger("FGToolWatcher")
    _LOGGER.setLevel(logging.INFO)
    _LOGGER.propagate = False

    formatter = logging.Formatter("[%(asctime)s] [%(name)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    _LOGGER.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)  # <--- forcer la sortie vers stdout
    console_handler.setFormatter(formatter)
    _LOGGER.addHandler(console_handler)

    return _LOGGER.getChild(module_name)