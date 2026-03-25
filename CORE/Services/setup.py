# CORE/Services/setup.py
import os
import sys

from typing import Dict, Any, Tuple



# === Internal Variable(s) ===

_OS        = sys.platform.lower()
_IS_FROZEN = getattr(sys, 'frozen', False)


# === Private Function(s) ===

def _get_base_paths() -> Tuple[str, str]:

    """
    Returns (base_system_path, base_temp_path).
    - base_system_path : dossier du .exe (frozen) ou racine du projet (dev)
    - base_temp_path   : dossier temporaire PyInstaller (_MEIPASS) ou "" en dev

    """

    if _IS_FROZEN:
        return os.path.dirname(sys.executable), sys._MEIPASS
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), ""



def _build_paths(sys_path: str, tmp_path: str) -> Dict[str, Any]:

    """
    Constructs the directory path mapping. Ensures consistent logic across Windows, Linux, and macOS.

    """

    return {
        # ── System side ──
        "_RESOURCES_FOLDER":        os.path.join(tmp_path, "CORE", "__RESOURCES"),
        "_SECRETS_FOLDER":          os.path.join(tmp_path, "CORE", "__SECRETS"),

        "_AI_FOLDER":               os.path.join(tmp_path, "CORE", "AI"),
        "_DATABASE_FOLDER":         os.path.join(tmp_path, "CORE", "Database"),
        "_SEARCH_FOLDER":           os.path.join(tmp_path, "CORE", "Search"),
        "_SERVICE_FOLDER":          os.path.join(tmp_path, "CORE", "Service"),

        "_ASSETS_FOLDER":           os.path.join(tmp_path, "GUI",  "__ASSETS"),

        # ── User side (folder(s) & path(s)) ──
        "_USER_FOLDER":             os.path.join(sys_path, "USER"),
        "_CONFIG_SUBFOLDER":        os.path.join(sys_path, "USER", "CONFIG"),
        "_DATA_SUBFOLDER":          os.path.join(sys_path, "USER", "DATA"),
        "_DATA_SUBFOLDER_SOURCE":   os.path.join(sys_path, "USER", "DATA", "SOURCE"),
        "_LOGS_SUBFOLDER":          os.path.join(sys_path, "USER", "LOGS"),
        "_RESULTS_SUBFOLDER":       os.path.join(sys_path, "USER", "RESULTS"),
        "_RESULTS_SUBFOLDER_TEMP":  os.path.join(sys_path, "USER", "RESULTS", "TEMP"),

        "_CATALOG_CONFIG_PATH":     os.path.join(sys_path, "USER", "CONFIG", "catalog.json"),
        "_USER_CONFIG_PATH":        os.path.join(sys_path, "USER", "CONFIG", "settings.json"),
    }


# === Execution ===

_BASE_SYSTEM_PATH, _BASE_TEMP_PATH = _get_base_paths()
_OS_CONFIG = _build_paths(_BASE_SYSTEM_PATH, _BASE_TEMP_PATH)

if not any(_OS.startswith(p) for p in ("win", "linux", "darwin")):
    raise RuntimeError(f"Unsupported system: {_OS}")


# === Path Constant(s) ===

RESOURCES_FOLDER = _OS_CONFIG["_RESOURCES_FOLDER"]              # System
SECRETS_FOLDER = _OS_CONFIG["_SECRETS_FOLDER"]                  # System

AI_FOLDER = _OS_CONFIG["_AI_FOLDER"]                            # System
DATABASE_FOLDER = _OS_CONFIG["_DATABASE_FOLDER"]                # System
SEARCH_FOLDER = _OS_CONFIG["_SEARCH_FOLDER"]                    # System
SERVICE_FOLDER = _OS_CONFIG["_SERVICE_FOLDER"]                  # System

ASSETS_FOLDER = _OS_CONFIG["_ASSETS_FOLDER"]                    # System

USER_FOLDER = _OS_CONFIG["_USER_FOLDER"]                        # User folder
CONFIG_SUBFOLDER = _OS_CONFIG["_CONFIG_SUBFOLDER"]              # User folder
DATA_SUBFOLDER = _OS_CONFIG["_DATA_SUBFOLDER"]                  # User folder
DATA_SUBFOLDER_SOURCE = _OS_CONFIG["_DATA_SUBFOLDER_SOURCE"]    # User folder
LOGS_SUBFOLDER = _OS_CONFIG["_LOGS_SUBFOLDER"]                  # User folder
RESULTS_SUBFOLDER = _OS_CONFIG["_RESULTS_SUBFOLDER"]            # User folder
RESULTS_SUBFOLDER_TEMP = _OS_CONFIG["_RESULTS_SUBFOLDER_TEMP"]  # User folder

CATALOG_CONFIG_PATH = _OS_CONFIG["_CATALOG_CONFIG_PATH"]        # User file path
USER_CONFIG_PATH = _OS_CONFIG["_USER_CONFIG_PATH"]              # User file path


# === Public Function(s) ===

def make_dirs() -> None:

    """
    Creates all required user directories if they do not exist.
    Called during application startup.

    """

    for path in (
        USER_FOLDER,
        CONFIG_SUBFOLDER,
        DATA_SUBFOLDER,
        DATA_SUBFOLDER_SOURCE,
        LOGS_SUBFOLDER,
        RESULTS_SUBFOLDER,
        RESULTS_SUBFOLDER_TEMP,
    ):
        os.makedirs(path, exist_ok=True)
