import os

import logging

from datetime import datetime

_LOGGER = None
_log_file_path = None

def logger(module_name):
    global _LOGGER, _log_file_path

    if _LOGGER is not None:
        return _LOGGER.getChild(module_name)

    log_dir = "DATA/LOGS"
    os.makedirs(log_dir, exist_ok=True)
    log_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
    _log_file_path = os.path.join(log_dir, log_filename)

    _LOGGER = logging.getLogger("FGToolWatcher")
    _LOGGER.setLevel(logging.INFO)
    _LOGGER.propagate = False

    formatter = logging.Formatter("[%(asctime)s] [%(name)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")

    file_handler = logging.FileHandler(_log_file_path, encoding='utf-8')
    file_handler.setFormatter(formatter)
    _LOGGER.addHandler(file_handler)

    return _LOGGER.getChild(module_name)

def get_log_file_path():
    return _log_file_path