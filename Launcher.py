# Launcher.py
import sys
import logging

from CORE.Services.logger import setup_logging

from PySide6.QtWidgets import QApplication

from CORE.Services.setup import *
from CORE.Services.user import UserService
from CORE.Services.translator import TranslatorService

from WEB.Viewer import ViewerService

from GUI.Desktop.Client import WatcherGUI



__version__ = "1.0.0"
__author__ = "LECHAT Jérôme"
__project__ = "FG-ToolWatcher"

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

            from Database.loaders.clabots import CLABOTSloader
            loader_instance = CLABOTSloader()
            loader_instance.run()

        # --- fixami loader ---
        elif loader_name == 'fixami':
            LOG.debug("Initialization of FIXAMIloader & execution...")

            from Database.loaders.fixami import FIXAMIloader
            loader_instance = FIXAMIloader()
            loader_instance.run()

        # --- georges loader ---
        elif loader_name == 'georges':
            return

        # --- klium loader ---
        elif loader_name == 'klium':
            LOG.debug("Initialization of KLIUMloader & execution...")

            from Database.loaders.klium import KLIUMloader
            loader_instance = KLIUMloader()
            loader_instance.run()

        # --- lecot loader ---
        elif loader_name == 'lecot':
            LOG.debug("Initialization of LECOTloader & execution...")

            from Database.loaders.lecot import LECOTloader
            loader_instance = LECOTloader()
            loader_instance.run()

        # --- toolnation loader ---
        elif loader_name == 'toolnation':
            LOG.debug("Initialization of TOOLNATIONloader & execution...")

            from Database.loaders.toolnation import TOOLNATIONloader
            loader_instance = TOOLNATIONloader()
            loader_instance.run()

        elif loader_name == 'all':

            from Database.loaders.clabots import CLABOTSloader
            loader_instance = CLABOTSloader()
            loader_instance.run()

            from Database.loaders.fixami import FIXAMIloader
            loader_instance = FIXAMIloader()
            loader_instance.run()

            from Database.loaders.klium import KLIUMloader
            loader_instance = KLIUMloader()
            loader_instance.run()

            from Database.loaders.lecot import LECOTloader
            loader_instance = LECOTloader()
            loader_instance.run()

            from Database.loaders.toolnation import TOOLNATIONloader
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
#                 LANCEUR DE L'INDEXER
# =====================================================
def RUN_INDEXER():

    """
    Runs the DBIndexer to merge all supplier databases into MASTERproductsDB.csv.
    """

    LOG = logging.getLogger(__name__)

    try:
        LOG.debug("INDEXER starting...")

        from Database.DBindexer import DBIndexer

        indexer = DBIndexer(
            db_paths=[
                os.path.join(DATA_SUBFOLDER_SOURCE, "CLABOTSproductsDB.csv"),
                os.path.join(DATA_SUBFOLDER_SOURCE, "FIXAMIproductsDB.csv"),
                os.path.join(DATA_SUBFOLDER_SOURCE, "KLIUMproductsDB.csv"),
                os.path.join(DATA_SUBFOLDER_SOURCE, "LECOTproductsDB.csv"),
                os.path.join(DATA_SUBFOLDER_SOURCE, "TOOLNATIONproductsDB.csv"),
            ],
            output_dir=DATA_SUBFOLDER
        )

        indexer.run()
        LOG.debug("INDEXER terminated.")

    except ImportError as e:
        LOG.exception(f"An import-error occured: {e}")
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

    # --- Router ---
    # Gestion des commandes à 2 arguments (--loader site, --cleaner site, --train site)
    if len(ARGS) == 1 and ARGS[0] == '--indexer':
        RUN_INDEXER()
        sys.exit(0)

    elif len(ARGS) == 2:
        cmd, site = ARGS[0], ARGS[1]

        if cmd == '--loader':
            RUN_LOADER(site)
        else:
            LOG.error(f"Commande inconnue: {cmd}")
            sys.exit(1)
        sys.exit(0)

    elif len(ARGS) == 0:
        RUN_GUI()
        sys.exit(0)

    else:
        LOG.warning(f"Arguments non reconnus ou format invalide: {ARGS}")
        print("---------------------------------------------")
        print("Usage(s):")
        print("1) python Launcher.py [--debug]")
        print("2) python Launcher.py --loader <website> [--debug]")
        print("3) python Launcher.py --indexer [--debug]")
        print("---------------------------------------------")
        sys.exit(1)
