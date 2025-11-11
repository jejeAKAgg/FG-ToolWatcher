# CORE/Manager.py
import os
import requests

import logging

import pandas as pd 

from CORE.Services.setup import *
from CORE.Services.user import UserService

from CORE.Watchers.clabots import CLABOTSwatcher
from CORE.Watchers.georges import FGwatcher
from CORE.Watchers.fixami import FIXAMIwatcher



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

class WatcherManager:
    
    """
    Main manager for all watcher modules.

    Responsibilities:
        - Initialize and execute each site-specific watcher.
        - Aggregate and export collected data (CSV/XLSX).
        - Handle progress reporting and optional email delivery.
    
    """

    def __init__(self, config: UserService, progress_callback=None, interruption_check=None):

        """
        Initialize the WatcherManager.

        Args:
            user_config (dict): User configuration (selected sites, preferences, etc.).
            catalog_config (dict): Catalog configuration (product data, references, etc.).
            progress_callback (callable, optional): Callback to report progress to the UI.
        
        """

        # === INPUT VARIABLE(S) ===
        self.config_service = config

        # === LOADING SYSTEM ===
        self.progress_callback = progress_callback

        # === THREAD SYSTEM ===
        self.interruption_check = interruption_check
        
        # === INTERNAL PARAMETER(S) ===
        self.selected_sites = []
        self.dfs = []

        self.sites_mapping = {
            'CIPAC': 'CIPACwatcher',
            'CLABOTS': CLABOTSwatcher,
            'GEORGES': FGwatcher,
            'FIXAMI': FIXAMIwatcher,
            'KLIUM': 'KLIUMwatcher',
            'LECOT': 'LECOTwatcher',
        }

    def _update_progress(self, percentage: int):
        
        """
        Update progress percentage using the callback function.

        Args:
            percentage (int): The new progress percentage (0-100).
        """
        
        if self.progress_callback:
            self.progress_callback(percentage)

    def _load_items(self):

        """
        Load product items (articles) from the UserService catalog config.

        Returns:
            List[str] | None: A list of item names, or None if empty.
        """
        
        items = self.config_service.get_catalog_items() 
        if not items:
            LOG.debug("Aucun article trouvé dans le catalogue (MPNs.json).")
            return None
        
        LOG.debug(f"[Manager] {len(items)} articles chargés depuis le catalogue.")
        return items
    
    def _check_internet_connection(self, timeout: int = 5) -> bool:
        
        """
        Checks for a live internet connection by pinging a reliable DNS server.
        
        Args:
            timeout (int): Seconds to wait for a response.

        Returns:
            bool: True if connection is successful, False otherwise.
            
        Raises:
            requests.exceptions.ConnectionError: If the connection attempt fails.
        """
        
        try:
            response = requests.head("https://8.8.8.8", timeout=timeout)     # Simple request to check status

            if response.status_code >= 200:
                LOG.info(f"Internet connection check successful.")
                return True
            
        except (requests.ConnectionError, requests.Timeout) as e:
            LOG.exception(f"Internet connection check failed: {e}")
            
        return False

    def _run_site_watchers(self, items):

        """
        Run all selected site watchers sequentially.

        Args:
            items (pandas.DataFrame): DataFrame containing items to monitor.
        
        """

        self.selected_sites = [
            site for site in self.config_service.get("websites_to_watch", []) 
            if site in self.sites_mapping
        ]

        total_sites = len(self.selected_sites)
        if total_sites == 0:
            LOG.warning("No website(s) selected. Skipping...")
            return
        
        for idx, site in enumerate(self.selected_sites, 1):
            if self.interruption_check and self.interruption_check():
                LOG.debug("Interruption requested. Stopping...")
                break

            LOG.info(f"Starting watcher: {site} ({idx}/{total_sites})")

            watcher_cls = self.sites_mapping[site]

            try:
                watcher_instance = watcher_cls(
                    items=items,
                    config=self.config_service
                )
                df = watcher_instance.run()
                if df is not None:
                    self.dfs.append(df)

            except Exception as e:
                LOG.exception(f"[Manager] Erreur lors de l'exécution de {watcher_cls}: {e}")
                continue

    def _export_results(self):

        """
        Generate and export final results in CSV and XLSX formats.

        Returns:
            tuple[str | None, str | None]: Paths to the generated CSV and XLSX files.
        
        """
        
        if not self.dfs:
            LOG.info("No result(s) to export.")
            return None, None
        
        try:
            # Concaténer tous les dataframes collectés
            final_df = pd.concat(self.dfs, ignore_index=True)
            
            # Définir les chemins de sauvegarde
            csv_path = os.path.join(RESULTS_SUBFOLDER, "FG-ToolWatcher_RESULTS.csv")
            xlsx_path = os.path.join(RESULTS_SUBFOLDER, "FG-ToolWatcher_RESULTS.xlsx")
            
            # Sauvegarder les fichiers
            final_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            final_df.to_excel(xlsx_path, index=False)
            
            LOG.info(f"Results exported to {xlsx_path}")
            return csv_path, xlsx_path

        except Exception as e:
            LOG.exception(f"An error occured during the exportation of the results: {e}")
            return None, None

    def _send_email(self, xlsx_file):

        """
        Send the final XLSX report via email using the MailService class.
        Configuration is loaded from APP/CONFIGS/EMAILconfig.json.

        Args:
            xlsx_file (str): Path to the generated XLSX file.
        
        """

        return

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
        
        try:
            # === LOADING (0% -> 5%) ===
            self._update_progress(0)
            items = self._load_items()
            
            if not items:
                LOG.info("No article to watch. Process stopping...")
                self._update_progress(100)
                return None, None
            
            self._update_progress(5) # 5%

            # Interruption checking
            if self.interruption_check and self.interruption_check():
                 LOG.debug("Interruption requested. Loading items stopping...")
                 return None, None

            # === WATCHER(S) (5% -> 95%) ===
            if self._check_internet_connection() == False: 
                return None, None

            self._run_site_watchers(items)

            # Interruption checking
            if self.interruption_check and self.interruption_check():
                 LOG.debug("Interruption requested. Watcher(s) stopping...")
                 return None, None
            
            self._update_progress(95) # 95%
            
            # === EXPORTATION (95% -> 100%) ===
            if self.interruption_check and self.interruption_check():
                LOG.debug("Interruption requested. Exportation stopping...")
                return None, None
            
            csv_path, xlsx_path = self._export_results() # Exporting results

            # TODO: Send email if user asked to.

            self._update_progress(100) # Finished
            return csv_path, xlsx_path

        except Exception as e:
            LOG.exception(f"An error occured: {e}")
            self._update_progress(100)
            return None, None


# ===================
#    MAIN FUNCTION
# ===================
def main_watcher(config: UserService, progress_callback=None, interruption_check=None):

    """
    Entry point to execute the watcher system.

    Args:
        user_config (dict): User-specific configuration.
        catalog_config (dict): Product catalog configuration.
        progress_callback (callable, optional): Callback for progress tracking.

    Returns:
        tuple[str | None, str | None]: Paths to the generated CSV and XLSX files.
    
    """

    manager = WatcherManager(config=config, progress_callback=progress_callback, interruption_check=interruption_check)
    
    return manager.run()