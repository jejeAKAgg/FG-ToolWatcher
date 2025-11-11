# CORE/Services/logger.py
import logging
import os

from datetime import datetime

from CORE.Services.setup import _IS_FROZEN, LOGS_SUBFOLDER

def setup_logging(log_level=logging.INFO):
    
    """
    Configures the root logger for the entire application.
    This function should only be called ONCE at startup.

    Args:
        log_level (int): The logging level (e.g., logging.DEBUG or logging.INFO).
    """
    
    # Format
    log_format = "[%(asctime)s] [%(levelname)s] (%(name)s) - %(message)s"

    # Logger configuration
    logging.basicConfig(level=log_level, format=log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # Silence External Libraries
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("cloudscraper").setLevel(logging.WARNING)

    if _IS_FROZEN: # .exe mode
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_file = os.path.join(LOGS_SUBFOLDER, f"session_{timestamp}.log")

            # Add a FileHandler
            file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(logging.Formatter(log_format))
            
            logging.getLogger().addHandler(file_handler)
            
            logging.info(f"--- Logging session started (EXE Mode at {logging.getLevelName(log_level)}) ---")
            
        except Exception as e:
            logging.error(f"Failed to create file logger: {e}")
    else: # DEV mode
        logging.info(f"--- Logging session started (DEV Mode at {logging.getLevelName(log_level)}) ---")
        if log_level == logging.INFO:
            logging.info("Run with '--debug' to see full debug logs.")