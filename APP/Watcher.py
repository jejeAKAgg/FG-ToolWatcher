# Watcher.py
import os

from APP.WEBSITES.CIPACwatcher import CIPACwatcher
from APP.WEBSITES.CLABOTSwatcher import CLABOTSwatcher
from APP.WEBSITES.FGwatcher import FGwatcher
from APP.WEBSITES.FIXAMIwatcher import FIXAMIwatcher
from APP.WEBSITES.KLIUMwatcher import KLIUMwatcher
from APP.WEBSITES.LECOTwatcher import LECOTwatcher

from APP.SERVICES.__init__ import *

from APP.UTILS.LOGmaker import *
from APP.UTILS.EXCELutils import *
from APP.UTILS.TOOLSbox import *

Logger = logger("WATCHER")


def main_watcher(config, progress_callback=None):
    
    """
    Lancement du watcher principal.
    :param config: dict contenant les options utilisateur
    :param progress_callback: fonction pour suivre la progression (0-100)
    """
    
    Logger.info("Démarrage de Watcher...")

    # --- Détermination des sites à surveiller ---
    sites_mapping = {
        "CIPAC": CIPACwatcher,
        "CLABOTS": CLABOTSwatcher,
        "FG": FGwatcher,
        "FIXAMI": FIXAMIwatcher,
        "KLIUM": KLIUMwatcher,
        "LECOT": LECOTwatcher,
    }

    selected_sites = [site for site in config.get("websites_to_watch", []) if site in sites_mapping]
    Logger.info(f"Sites sélectionnés : {selected_sites}")

    # --- Calcul dynamique du nombre d'étapes ---
    steps = 1 + len(selected_sites) + 3  # 1 pour lecture Excel, len(selected_sites) pour chaque site, 2 pour CSV/XLSX
    if config.get("send_email", False):
        steps += 1
    current = 0

    def update_progress():
        nonlocal current
        current += 1
        if progress_callback:
            progress_callback(int(current / steps * 100))

    # --- Lecture des MPN/Articles ---
    Logger.info("Réception des données [REFs/Articles] et synchronisation...")
    ITEMs = EXCELreader("MPNs/Articles")
    update_progress()

    # --- Lancement des watchers ---
    dfs = []
    for site in selected_sites:
        Logger.info(f"Démarrage de {site}watcher...")
        df = sites_mapping[site](ITEMs, config)
        dfs.append(df)
        update_progress()

    # --- Filtrer les DataFrames None ---
    dfs = [df for df in dfs if df is not None]

    # --- Génération CSV/XLSX si au moins un DataFrame valide ---
    if dfs:
        Logger.info("Génération du CSV...")
        FINALcsv = FINALcsvCONVERTER(dfs)
        update_progress()

        Logger.info("Génération du XLSX...")
        FINALxlsx = FINALxlsxCONVERTER(dfs)
        update_progress()
    else:
        Logger.warning("Aucun DataFrame valide, CSV/XLSX non générés")
        FINALcsv = None
        FINALxlsx = None
        current += 2
        if progress_callback:
            progress_callback(int(current / steps * 100))

    # --- Envoi résultats sur Google SHEETS ---
    Logger.info("Envoi des résultats pour la version WEB...")
    EXCELsender(FINALcsv)
    update_progress()

    # --- Envoi email si configuré ---
    if FINALxlsx and config.get("send_email", False):
        Logger.info("Envoi des résultats par email...")
        MAILconfig = JSONloader(os.path.join(BASE_TEMP_PATH, "APP", "CONFIGS", "EMAILconfig.json"))
        body = "\n".join(MAILconfig.get("BodyLines", []))
        MAILsender(
            sender_email=MAILconfig["Source"],
            password=MAILconfig["Password"],
            recipient_email=config.get("user_mail", MAILconfig["Target"]),
            subject=MAILconfig["Subject"],
            body=body,
            filename=FINALxlsx
        )
        update_progress()

    Logger.info("Analyse terminée.")