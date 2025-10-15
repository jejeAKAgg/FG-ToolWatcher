# Watcher.py
import os

from APP.SERVICES.__init__ import *
from APP.SERVICES.MAILservice import *

from APP.UTILS.LOGmaker import *
from APP.UTILS.EXCELutils import *
from APP.UTILS.TOOLSbox import *

from APP.WEBSITES.CIPACwatcher import CIPACwatcher
from APP.WEBSITES.CLABOTSwatcher import CLABOTSwatcher
from APP.WEBSITES.FGwatcher import FGwatcher
from APP.WEBSITES.FIXAMIwatcher import FIXAMIwatcher
from APP.WEBSITES.KLIUMwatcher import KLIUMwatcher
from APP.WEBSITES.LECOTwatcher import LECOTwatcher


class WatcherManager:
    
    """
    Main manager for all watcher modules.

    Responsibilities:
        - Initialize and execute each site-specific watcher.
        - Aggregate and export collected data (CSV/XLSX).
        - Handle progress reporting and optional email delivery.
    
    """

    def __init__(self, user_config: dict, catalog_config:dict, progress_callback=None):

        """
        Initialize the WatcherManager.

        Args:
            user_config (dict): User configuration (selected sites, preferences, etc.).
            catalog_config (dict): Catalog configuration (product data, references, etc.).
            progress_callback (callable, optional): Callback to report progress to the UI.
        
        """

        # === LOGGER SETUP ===
        self.logger = logger("WATCHER")

        # === INPUT VARIABLE(S) ===
        self.user_config = user_config
        self.catalog_config = catalog_config

        # === LOADING SYSTEM ===
        self.progress_callback = progress_callback
        
        # === OTHER VARIABLE(S) ===
        self.selected_sites = []
        self.dfs = []

        self.sites_mapping = {
            "CIPAC": CIPACwatcher,
            "CLABOTS": CLABOTSwatcher,
            "FERNAND GEORGES": FGwatcher,
            "FIXAMI": FIXAMIwatcher,
            "KLIUM": KLIUMwatcher,
            "LECOT": LECOTwatcher,
        }

    def _update_progress(self, step_increment=1, total_steps=None):

        """
        Update progress percentage using the callback function.

        Args:
            step_increment (int): Current progress increment step.
            total_steps (int | None): Total number of steps for the process.
        
        """

        if self.progress_callback and total_steps:
            self.progress_callback(int(step_increment / total_steps * 100))

    def _load_items(self):

        """
        Load product items (references/articles) from Excel.

        Returns:
            pandas.DataFrame: DataFrame containing item references.
        
        """

        self.logger.info("Réception des données [REFs/Articles] et synchronisation...")
        items = EXCELreader("MPNs/Articles")
        return items

    def _run_site_watchers(self, items):

        """
        Run all selected site watchers sequentially.

        Args:
            items (pandas.DataFrame): DataFrame containing items to monitor.
        
        """

        self.selected_sites = [
            site for site in self.user_config.get("websites_to_watch", []) 
            if site in self.sites_mapping
        ]
        self.logger.info(f"Sites sélectionnés : {self.selected_sites}")

        total_sites = len(self.selected_sites)
        for idx, site in enumerate(self.selected_sites, 1):
            self.logger.info(f"Démarrage de {site}watcher...")

            watcher_cls = self.sites_mapping[site]

            try:
                watcher_instance = watcher_cls(
                    items=items,
                    user_config=self.user_config,
                    catalog_config=self.catalog_config
                )
                df = watcher_instance.run()
                if df is not None:
                    self.dfs.append(df)
            except Exception as e:
                self.logger.error(f"Erreur dans {site}watcher : {e}")

            if self.progress_callback:
                self.progress_callback(int(idx / total_sites * 100))

    def _export_results(self):

        """
        Generate and export final results in CSV and XLSX formats.

        Returns:
            tuple[str | None, str | None]: Paths to the generated CSV and XLSX files.
        
        """

        if not self.dfs:
            self.logger.warning("Aucun DataFrame valide, CSV/XLSX non générés")
            return None, None

        self.logger.info("Génération du CSV...")
        FINALcsv = FINALcsvCONVERTER(self.dfs)

        self.logger.info("Génération du XLSX...")
        FINALxlsx = FINALxlsxCONVERTER(self.dfs)

        self.logger.info("Envoi des résultats pour la version WEB...")
        EXCELsender(FINALcsv)

        if self.user_config.get("send_email", False):
            self._send_email(FINALxlsx)

        return FINALcsv, FINALxlsx

    def _send_email(self, xlsx_file):

        """
        Send the final XLSX report via email using the MailService class.
        Configuration is loaded from APP/CONFIGS/EMAILconfig.json.

        Args:
            xlsx_file (str): Path to the generated XLSX file.
        
        """

        self.logger.info("Envoi des résultats par email...")

        # Loading email configuration settings
        MAILconfig = JSONloader(os.path.join(BASE_TEMP_PATH, "APP", "CONFIGS", "EMAILconfig.json"))

        # === Retrieve fields ===
        source = MAILconfig.get("Source")
        password = MAILconfig.get("Password")

        recipients = self.user_config.get("user_mail", [])

        subject = MAILconfig.get("Subject")
        body = "\n".join(MAILconfig.get("BodyLines", []))

        # === Safety checks ===
        if not source or not password or not recipients:
            self.logger.warning("Email config incomplete: missing sender, password, or recipients.")
            
            return
        
        # === Send email ===
        try:
            mail_service = MailService(sender_email=source, password=password)
            mail_service.send_mail(
                recipients=recipients,
                subject=subject,
                body=body,
                attachments=[xlsx_file] if xlsx_file else None,
                html=True
            )

        except Exception as e:
            pass 


    def run(self):

        """
        Execute the complete watcher process:
            - Load items
            - Run site watchers
            - Export results (CSV/XLSX)
            - Optionally send email

        Returns:
            tuple[str | None, str | None]: Paths to the generated CSV and XLSX files.
        
        """

        self.logger.info("Démarrage du WatcherManager...")

        items = self._load_items()
        self._run_site_watchers(items)
        FINALcsv, FINALxlsx = self._export_results()

        self.logger.info("Analyse terminée.")
        
        return FINALcsv, FINALxlsx


# ===================
#    MAIN FUNCTION
# ===================
def main_watcher(user_config, catalog_config, progress_callback=None):

    """
    Entry point to execute the watcher system.

    Args:
        user_config (dict): User-specific configuration.
        catalog_config (dict): Product catalog configuration.
        progress_callback (callable, optional): Callback for progress tracking.

    Returns:
        tuple[str | None, str | None]: Paths to the generated CSV and XLSX files.
    
    """

    manager = WatcherManager(user_config=user_config, catalog_config=catalog_config, progress_callback=progress_callback)
    
    return manager.run()