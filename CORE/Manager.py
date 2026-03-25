# CORE/Manager.py
import os
import sys

import logging

import json
import requests
import subprocess

import pandas as pd

from CORE.Services.mail import MailService
from CORE.Services.user import UserService
from CORE.Services.setup import *

from CORE.Search.watchers.clabots import CLABOTSwatcher
from CORE.Search.watchers.fixami import FIXAMIwatcher
from CORE.Search.watchers.klium import KLIUMwatcher
from CORE.Search.watchers.lecot import LECOTwatcher
from CORE.Search.watchers.toolnation import TOOLNATIONwatcher



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
            #'CIPAC':        'CIPACwatcher',
            'CLABOTS':      CLABOTSwatcher,
            #'GEORGES':      FGwatcher,
            'FIXAMI':       FIXAMIwatcher,
            'KLIUM':        KLIUMwatcher,
            'LECOT':        LECOTwatcher,
            'TOOLNATION':   TOOLNATIONwatcher,
        }

    def _update_progress(self, percentage: int):
        if self.progress_callback:
            self.progress_callback(percentage)

    def _load_items(self) -> list[dict] | None:

        """
        Loads catalog items.
        Normalizes each entry into a dict {name, mpn, ean}
        (maintains compatibility with legacy string-based catalogs).

        Returns:
            List[dict] | None

        """

        raw_items = self.config_service.get_catalog_items()
        if not raw_items:
            LOG.debug("No article found in the catalog.")
            return None

        items = []
        for item in raw_items:
            if isinstance(item, str):
                items.append({"name": item, "mpn": "-", "ean": "-"})
            elif isinstance(item, dict):
                items.append({
                    "name": item.get("name", "-"),
                    "mpn":  item.get("mpn",  "-"),
                    "ean":  item.get("ean",  "-"),
                })

        LOG.debug(f"{len(items)} articles loaded from the catalog.")
        return items

    def _check_internet_connection(self, timeout: int = 5) -> bool:

        """
        Network status checker.

        """

        try:
            response = requests.head("https://dns.google", timeout=timeout)
            if response.status_code >= 200:
                LOG.info("Internet connection check successful.")
                return True
        except (requests.ConnectionError, requests.Timeout) as e:
            LOG.exception(f"Internet connection check failed: {e}")

        return False

    def _run_site_watchers(self, items: list[dict]):

        """
        Starts the selected watchers using the enriched items list.

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
            if self._interrupted():
                break

            LOG.info(f"Starting watcher: {site} ({idx}/{total_sites})")

            site_start = 5 + int((idx - 1) / total_sites * 90)
            site_end   = 5 + int(idx / total_sites * 90)

            def site_progress(pct, start=site_start, end=site_end):
                global_pct = start + int(pct / 100 * (end - start))
                self._update_progress(global_pct)

            watcher_cls = self.sites_mapping[site]

            try:
                watcher_instance = watcher_cls(
                    items=items,
                    config=self.config_service,
                    progress_callback=site_progress
                )
                df = watcher_instance.run()
                if df is not None:
                    self.dfs.append(df)

            except Exception as e:
                LOG.exception(f"An error occurred during {watcher_cls} execution: {e}")
                continue

    def _export_results(self):

        if not self.dfs:
            LOG.info("No result(s) to export.")
            return None, None

        try:
            final_df = pd.concat(self.dfs, ignore_index=True)

            csv_path  = os.path.join(RESULTS_SUBFOLDER, "FG-ToolWatcher_RESULTS.csv")
            xlsx_path = os.path.join(RESULTS_SUBFOLDER, "FG-ToolWatcher_RESULTS.xlsx")

            final_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            final_df.to_excel(xlsx_path, index=False)

            LOG.info(f"Results exported to {xlsx_path}")
            self._open_results_folder()
            return csv_path, xlsx_path

        except Exception as e:
            LOG.exception(f"An error occured during the exportation of the results: {e}")
            return None, None

    def _open_results_folder(self):

        """
        If the option is enabled, automatically opens
        the file explorer at the exact location of the results output.

        """

        if not self.config_service.get("system_open_on_finish", False):
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(RESULTS_SUBFOLDER)
            elif sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", RESULTS_SUBFOLDER])
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", RESULTS_SUBFOLDER])
        except Exception as e:
            LOG.exception(f"An error occurred during the file explorer opening: {e}")

    def _send_email(self, xlsx_file: str) -> bool:

        """
        Sends the XLSX report via email.
        Reads SMTP configuration from __UTILS/secrets.json (not exposed in the GUI).

        Args:
            xlsx_file (str): Path to the XLSX file to be sent.

        Returns:
            bool: True if sent successfully, False otherwise.

        """

        recipient  = self.config_service.get("user_mail",      "")
        first_name = self.config_service.get("user_firstname", "")

        if not recipient:
            LOG.warning("No recipient email address given, email not sent.")
            return False

        secrets_path = os.path.join(RESOURCES_FOLDER, "secrets.json")
        if not os.path.exists(secrets_path):
            LOG.warning(f"secrets.json not found: {secrets_path}")
            return False

        try:
            with open(secrets_path, encoding="utf-8") as f:
                secrets = json.load(f)

            smtp_server   = secrets.get("smtp_server",   "smtp.gmail.com")
            smtp_port     = secrets.get("smtp_port",     465)
            smtp_sender   = secrets.get("smtp_sender",   recipient)
            smtp_password = secrets.get("smtp_password", "")

            if not smtp_password:
                LOG.warning("smtp_password not available in secrets.json, email not sent.")
                return False

            mail_service = MailService(
                sender_email=smtp_sender,
                password=smtp_password,
                smtp_server=smtp_server,
                smtp_port=int(smtp_port)
            )

            subject = "FG-ToolWatcher — Rapport de prix"
            body    = f"Bonjour {first_name},\n\nVeuillez trouver ci-joint le rapport de prix généré par FG-ToolWatcher.\n\nCordialement,\nFG-ToolWatcher"

            mail_service.send_mail(
                recipients=recipient,
                subject=subject,
                body=body,
                attachments=[xlsx_file] if xlsx_file and os.path.exists(xlsx_file) else None
            )

            LOG.info(f"Email sent to {recipient}.")
            return True

        except Exception as e:
            LOG.exception(f"An error occurred during the sending of the email: {e}")
            return False

    def _interrupted(self) -> bool:
        return bool(self.interruption_check and self.interruption_check())

    def run(self):
        LOG.debug("Starting Manager.py...")

        try:
            self._update_progress(0)
            items = self._load_items()

            if not items:
                LOG.info("No article to watch. Process stopping...")
                self._update_progress(100)
                return None, None

            if not self._check_internet_connection(): return None, None

            if self._interrupted(): return None, None
            self._update_progress(5)

            self._run_site_watchers(items)

            if self._interrupted(): return None, None
            self._update_progress(95)

            csv_path, xlsx_path = self._export_results()

            if self.config_service.get("user_mail_send", True) and xlsx_path:
                self._send_email(xlsx_path)

            self._update_progress(100)
            return csv_path, xlsx_path

        except Exception as e:
            LOG.exception(f"An error occured: {e}")
            self._update_progress(100)
            return None, None
