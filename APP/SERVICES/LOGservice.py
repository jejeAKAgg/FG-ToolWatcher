# APP/SERVICES/LOGservice.py
import os
import logging

from datetime import datetime
from typing import Optional


from APP.SERVICES.__init__ import LOGS_SUBFOLDER 

class LogService:
    
    """
    Manages the application's logging system.
    This class uses class methods to ensure the root logger is initialized 
    only once (Singleton pattern via class variables).
    """

    _ROOT_LOGGER: Optional[logging.Logger] = None
    _LOG_FILE_PATH: Optional[str] = None
    _IS_INITIALIZED: bool = False

    @classmethod
    def init_logging(cls) -> bool:
        
        """
        Initializes the root logger, creates the log directory, and sets up file handling.
        """
        
        if cls._IS_INITIALIZED:
            return True

        try:
            os.makedirs(LOGS_SUBFOLDER, exist_ok=True)
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to create log directory {LOGS_SUBFOLDER}. {e}")
            return False

        log_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
        cls._LOG_FILE_PATH = os.path.join(LOGS_SUBFOLDER, log_filename)

        cls._ROOT_LOGGER = logging.getLogger("FGToolWatcher")
        cls._ROOT_LOGGER.setLevel(logging.INFO)
        cls._ROOT_LOGGER.propagate = False

        formatter = logging.Formatter(
            "[%(asctime)s] [%(name)s] %(levelname)s: %(message)s", 
            "%Y-%m-%d %H:%M:%S"
        )

        file_handler = logging.FileHandler(cls._LOG_FILE_PATH, encoding='utf-8')
        file_handler.setFormatter(formatter)
        cls._ROOT_LOGGER.addHandler(file_handler)
        
        cls._IS_INITIALIZED = True
        
        # L'appel interne est maintenant corrigé (il doit aussi être une méthode de classe ou statique)
        cls.logger("LoggingService").info(f"Logging initialized successfully. Log file: {cls._LOG_FILE_PATH}")
        return True

    @classmethod
    def logger(cls, module_name: str) -> logging.Logger:
        
        """
        Returns a specific logger instance for a module.
        If the root logger hasn't been initialized, returns a basic console logger.
        """

        # Remplace self.logger par cls.logger
        if cls._ROOT_LOGGER is None:
            # Retourne un logger non configuré (écrit dans stderr) si l'initialisation n'a pas été faite
            return logging.getLogger(module_name)
            
        return cls._ROOT_LOGGER.getChild(module_name)

    @classmethod
    def get_log_file_path(cls) -> Optional[str]:
        """Returns the path to the current log file."""
        return cls._LOG_FILE_PATH