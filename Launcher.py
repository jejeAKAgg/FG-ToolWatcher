# Launcher.py
import sys
import logging

from CORE.Services.logger import setup_logging

from PySide6.QtWidgets import QApplication

from CORE.Services.setup import *
from CORE.Services.user import UserService
from CORE.Services.translator import TranslatorService

from GUI.Desktop.Client import WatcherGUI



# =====================================================
#                 LANCEUR GUI (DÉFAUT)
# =====================================================
def RUN_GUI():
    
    """
    Launches the FG-ToolWatcher application.
    Sets up logging, initializes configuration services, and starts the GUI.
    """

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

        # === START APPLICATION ===
        app = QApplication(sys.argv)
        window = WatcherGUI(config_service=config_service, translator_service=translator_service)
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
#                 LANCEUR DE SCRIPT (LOADER)
# =====================================================
def RUN_LOADER(loader_name: str):
    
    """
    Imports and runs a specific data loader script based on its name.
    """

    LOG = logging.getLogger(__name__)
    
    try:
        LOG.debug(f"LOADER starting...")

        # === INITIALIZE LOADER(S) ===
        # --- clabots loader ---
        if loader_name == 'clabots':
            LOG.debug("Initialization of CLABOTSloader & execution...")
            
            from CORE.__DATABASES.loader.clabots import CLABOTSloader
            loader_instance = CLABOTSloader()
            loader_instance.run()

        # --- fixami loader ---
        elif loader_name == 'fixami':
            LOG.debug("Initialization of FIXAMIloader & execution...")
            
            from CORE.__DATABASES.loader.fixami import FIXAMIloader
            loader_instance = FIXAMIloader()
            loader_instance.run()
        
        # --- georges loader ---
        elif loader_name == 'georges':
            LOG.debug("Initialization of FGloader & execution...")
            
            from CORE.__DATABASES.loader.georges import FGloader
            loader_instance = FGloader()
            loader_instance.run()

        # --- klium loader ---
        elif loader_name == 'klium':
            LOG.debug("Initialization of KLIUMloader & execution...")
            
            from CORE.__DATABASES.loader.klium import KLIUMloader
            loader_instance = KLIUMloader()
            loader_instance.run()

        # --- lecot loader ---
        elif loader_name == 'lecot':
            LOG.debug("Initialization of LECOTloader & execution...")
            
            #TODO: Finish CORE/__DATABASES/loader/lecot.py
            #from CORE.__DATABASES.loader.lecot import LECOTloader
            #loader_instance = LECOTloader()
            #loader_instance.run()

        # --- toolnation loader ---
        elif loader_name == 'toolnation':
            LOG.debug("Initialization of TOOLNATIONloader & execution...")
            
            from CORE.__DATABASES.loader.toolnation import TOOLNATIONloader
            loader_instance = TOOLNATIONloader()
            loader_instance.run()
            
        else:
            LOG.exception(f"Loader '{loader_name}' not recognized.")
            LOG.exception("Available loader(s) : clabots, fixami, georges, klium, lecot, toolnation.")
            sys.exit(1)
            
        LOG.debug(f"Loader '{loader_name}' termiated.")
        
    except ImportError as e:
        LOG.exception(f"An import-error occured: {e}")
        LOG.exception(f"Please ensure that 'CORE/__DATABASES/loader/{loader_name}.py' exists")
    except Exception as e:
        LOG.exception(f"An error occured: {e}")
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

    LOG.debug(f"Arguments (post-debug): {ARGS}")

    # --- Applying other argument(s) (if any) ---
    if len(ARGS) == 2 and ARGS[0] == '--loader': # 'python Launcher.py --loader <website> [--debug]' case
        LOG.debug(f"LOADER mode detected: {ARGS[1]}")
        RUN_LOADER(ARGS[1])
        
    elif len(ARGS) == 0: # 'python Launcher.py [--debug]' case
        LOG.debug("GUI mode detcted.")
        RUN_GUI()
    
    # --- Bad use case(s) ---
    else:
        LOG.warning(f"Arguments non reconnus: {ARGS}")
        print("---------------------------------------------")
        print("Usage(s):")
        print("1) python Launcher.py")
        print("2) python Launcher.py --debug")
        print("3) python Launcher.py --loader <website> [--debug]")
        print("---------------------------------------------")
        sys.exit(1)