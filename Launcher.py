# Launcher.py
import sys
import logging

from CORE.Services.logger import setup_logging

from CORE.Services.setup import *
from CORE.Services.user import UserService
from CORE.Services.translator import TranslatorService

from WEB.Viewer import ViewerService

from GUI.Desktop.Client import WatcherGUI

# =====================================================
#                 GUI LAUNCHER (DEFAULT)
# =====================================================
def RUN_GUI():

    """
    Launches the FG-ToolWatcher application.
    Sets up logging, initializes configuration services, and starts the GUI.
    """

    from PySide6.QtWidgets import QApplication

    LOG = logging.getLogger(__name__)

    try:
        LOG.debug("UI starting...")

        # === INITIALIZE SERVICES ===
        # --- User Configuration Service ---
        config_service = UserService(
            user_config_path=USER_CONFIG_PATH,
            catalog_config_path=CATALOG_CONFIG_PATH
        )
        LOG.debug("UserService initialized.")

        # --- Translator Service ---
        translator_service = TranslatorService()
        LOG.debug("TranslatorService initialized.")

        # --- Viewer Service ---
        viewer_service = ViewerService()
        viewer_service.start()

        # === START APPLICATION ===
        app = QApplication(sys.argv)
        app.setStyleSheet("* { outline: 0; }")

        window = WatcherGUI(config_service=config_service, translator_service=translator_service, viewer_service=viewer_service)
        window.show()

        LOG.debug("Window show.")

        # === EXECUTE APPLICATION ===
        APP = app.exec()
        LOG.debug(f"Exiting app with the following code: {APP}")
        sys.exit(APP)

    except Exception as e:
        LOG.exception(f"A critical error occured on GUI mode: {e}")
        sys.exit(1)

# =====================================================
#                   POINT D'ENTRÉE
# =====================================================
if __name__ == "__main__":

    ARGS = sys.argv[1:]

    # --- LOGGING configuration ---
    if "--debug" in ARGS:
        LEVEL = logging.DEBUG
        ARGS.remove("--debug")
    else:
        LEVEL = logging.INFO

    setup_logging(log_level=LEVEL)
    LOG = logging.getLogger(__name__)

    # --- Router ---
    if len(ARGS) == 0:
        RUN_GUI()
        sys.exit(0)

    else:
        print(f"Invalid / Unrecognized arguments: {ARGS}")
        print("---------------------------------------------")
        print("Usage(s):")
        print("1) python Launcher.py [--debug]")
        print("---------------------------------------------")
        sys.exit(1)
