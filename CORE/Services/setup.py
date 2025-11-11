# CORE/Services/setup.py
import os
import sys

from typing import Dict, Any, Tuple



_OS = sys.platform.lower()
_IS_FROZEN = getattr(sys, 'frozen', False)


# ===============================
#    1. ENVIRONMENT DETECTION
# ===============================
def _get_base_paths() -> Tuple[str, str]:
    
    """
    Calculates the base system path and the temporary path (PyInstaller).

    Returns:
        Tuple[str, str]: (BASE_SYSTEM_PATH, BASE_TEMP_PATH)
    """

    if _IS_FROZEN:
        base_system_path = os.path.dirname(sys.executable)
        base_temp_path = sys._MEIPASS
    else:
        base_system_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        base_temp_path = ""  # Not used when not frozen

    return base_system_path, base_temp_path

_BASE_SYSTEM_PATH, _BASE_TEMP_PATH = _get_base_paths()


# =============================
#        2. OS DETECTION
# =============================

def _configure_windows_paths(base_sys_path: str, base_temp_path: str) -> Dict[str, Any]:
    
    """
    Sets up the main execution paths and download constants for Windows.

    Args:
        base_sys_path (str): The calculated base system path.

    Returns:
        Dict[str, Any]: Dictionary of OS-specific path constants.
    """
    
    return {
        "_SECRETS_FOLDER": os.path.join(base_sys_path, "__UTILS"),
        
        "_USER_FOLDER": os.path.join(base_sys_path, "USER"),
        "_CORE_SUBFOLDER": os.path.join(base_sys_path, "USER", "CORE"),
        "_CONFIG_SUBFOLDER": os.path.join(base_sys_path, "USER", "CONFIG"),
        "_LOGS_SUBFOLDER": os.path.join(base_sys_path, "USER", "LOGS"),
        "_RESULTS_SUBFOLDER": os.path.join(base_sys_path, "USER", "RESULTS"),
        "_RESULTS_SUBFOLDER_TEMP": os.path.join(base_sys_path, "USER", "RESULTS", "TEMP"),

        "_ASSETS_FOLDER": os.path.join(base_temp_path, "GUI", "__ASSETS"),
        "_DATABASE_FOLDER": os.path.join(base_temp_path, "CORE", "__DATABASES"),
        "_UTILS_FOLDER": os.path.join(base_temp_path, "CORE", "__UTILS"),

        "_CATALOG_CONFIG_PATH": os.path.join(base_temp_path, "USER", "CONFIG", "database.json"),
        "_USER_CONFIG_PATH": os.path.join(base_temp_path, "USER", "CONFIG", "settings.json"),
    }

def _configure_linux_paths(base_sys_path: str, base_temp_path: str) -> Dict[str, Any]:
    
    """
    Sets up the main execution paths and download constants for Linux.

    Args:
        base_sys_path (str): The calculated base system path.

    Returns:
        Dict[str, Any]: Dictionary of OS-specific path constants.
    """
    
    return {
        "_SECRETS_FOLDER": os.path.join(base_sys_path, "__UTILS"),
        
        "_USER_FOLDER": os.path.join(base_sys_path, "USER"),
        "_CORE_SUBFOLDER": os.path.join(base_sys_path, "USER", "CORE"),
        "_CONFIG_SUBFOLDER": os.path.join(base_sys_path, "USER", "CONFIG"),
        "_LOGS_SUBFOLDER": os.path.join(base_sys_path, "USER", "LOGS"),
        "_RESULTS_SUBFOLDER": os.path.join(base_sys_path, "USER", "RESULTS"),
        "_RESULTS_SUBFOLDER_TEMP": os.path.join(base_sys_path, "USER", "RESULTS", "TEMP"),

        "_ASSETS_FOLDER": os.path.join(base_temp_path, "GUI", "__ASSETS"),
        "_DATABASE_FOLDER": os.path.join(base_temp_path, "CORE", "__DATABASES"),
        "_UTILS_FOLDER": os.path.join(base_temp_path, "CORE", "__UTILS"),

        "_CATALOG_CONFIG_PATH": os.path.join(base_temp_path, "USER", "CONFIG", "database.json"),
        "_USER_CONFIG_PATH": os.path.join(base_temp_path, "USER", "CONFIG", "settings.json"),
    }

def _configure_darwin_paths(base_sys_path: str, base_temp_path: str) -> Dict[str, Any]:
    
    """
    Sets up the main execution paths for macOS (Darwin).
    
    Args:
        base_sys_path (str): The calculated base system path.
        
    Returns:
        Dict[str, Any]: Dictionary of OS-specific path constants (using empty strings where executables are not pre-bundled).
    """
    
    return {
        "_SECRETS_FOLDER": os.path.join(base_sys_path, "__UTILS"),
        
        "_USER_FOLDER": os.path.join(base_sys_path, "USER"),
        "_CORE_SUBFOLDER": os.path.join(base_sys_path, "USER", "CORE"),
        "_CONFIG_SUBFOLDER": os.path.join(base_sys_path, "USER", "CONFIG"),
        "_LOGS_SUBFOLDER": os.path.join(base_sys_path, "USER", "LOGS"),
        "_RESULTS_SUBFOLDER": os.path.join(base_sys_path, "USER", "RESULTS"),
        "_RESULTS_SUBFOLDER_TEMP": os.path.join(base_sys_path, "USER", "RESULTS", "TEMP"),

        "_ASSETS_FOLDER": os.path.join(base_temp_path, "GUI", "__ASSETS"),
        "_DATABASE_FOLDER": os.path.join(base_temp_path, "CORE", "__DATABASES"),
        "_UTILS_FOLDER": os.path.join(base_temp_path, "CORE", "__UTILS"),

        "_CATALOG_CONFIG_PATH": os.path.join(base_temp_path, "USER", "CONFIG", "database.json"),
        "_USER_CONFIG_PATH": os.path.join(base_temp_path, "USER", "CONFIG", "settings.json"),
    }


# =============================
#        3. OS MAPPING
# =============================

_OS_CONFIG: Dict[str, Any] = {}

if _OS.startswith("win"):
    _OS_CONFIG = _configure_windows_paths(base_sys_path=_BASE_SYSTEM_PATH, base_temp_path=_BASE_TEMP_PATH)
elif _OS.startswith("linux"):
    _OS_CONFIG = _configure_linux_paths(base_sys_path=_BASE_SYSTEM_PATH, base_temp_path=_BASE_TEMP_PATH)
elif _OS.startswith("darwin"):
    _OS_CONFIG = _configure_darwin_paths(base_sys_path=_BASE_SYSTEM_PATH, base_temp_path=_BASE_TEMP_PATH)
else:
    raise RuntimeError(f"Non-supported OS: {_OS}")


# =============================
#       4. PATH CONSTANTS
# =============================
SECRETS_FOLDER = _OS_CONFIG["_SECRETS_FOLDER"]

USER_FOLDER = _OS_CONFIG["_USER_FOLDER"]
CORE_SUBFOLDER = _OS_CONFIG["_CORE_SUBFOLDER"]
CONFIG_SUBFOLDER = _OS_CONFIG["_CONFIG_SUBFOLDER"]
LOGS_SUBFOLDER = _OS_CONFIG["_LOGS_SUBFOLDER"]
RESULTS_SUBFOLDER = _OS_CONFIG["_RESULTS_SUBFOLDER"]
RESULTS_SUBFOLDER_TEMP = _OS_CONFIG["_RESULTS_SUBFOLDER_TEMP"]

ASSETS_FOLDER = _OS_CONFIG["_ASSETS_FOLDER"]
DATABASE_FOLDER = _OS_CONFIG["_DATABASE_FOLDER"]
UTILS_FOLDER = _OS_CONFIG["_UTILS_FOLDER"]

USER_CONFIG_PATH = _OS_CONFIG["_USER_CONFIG_PATH"]
CATALOG_CONFIG_PATH = _OS_CONFIG["_CATALOG_CONFIG_PATH"]


# =============================
#       5. CREATE FOLDERS
# =============================

def make_dirs():
    os.makedirs(USER_FOLDER, exist_ok=True)
    os.makedirs(CONFIG_SUBFOLDER, exist_ok=True)
    os.makedirs(CORE_SUBFOLDER, exist_ok=True)
    os.makedirs(LOGS_SUBFOLDER, exist_ok=True)
    os.makedirs(RESULTS_SUBFOLDER, exist_ok=True)
    os.makedirs(RESULTS_SUBFOLDER_TEMP, exist_ok=True)