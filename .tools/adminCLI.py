# .tools/adminCLI.py
import os
import sys

import logging

import sqlite3
import pandas as pd

from concurrent.futures import ProcessPoolExecutor, as_completed

from DATABASE.Loaders.LOADERengine import LoaderEngine
from DATABASE.Sitemaps.SITEMAPengine import SITEMAPengine

def process_loader(site: str) -> str:
    """
    Initializes and runs the LoaderEngine for the given site.
    """
    loader = LoaderEngine(site)
    loader.run()
    return site

def process_sitemap(site: str) -> str:
    """
    Initializes and runs the SITEMAPengine for the given site.
    """
    moteur = SITEMAPengine(site)
    moteur.run()
    return site

if __name__ == "__main__":

    # === ARGs ===
    ARGS = sys.argv[1:]

    # === LOGGING configuration ===
    if "--debug" in ARGS:
        LEVEL = logging.DEBUG
        ARGS.remove("--debug")
    else:
        LEVEL = logging.INFO

    # --- LOGGING SYSTEM ---
    logging.basicConfig(
        level=LEVEL,
        format='%(asctime)s [%(processName)s] %(message)s',
        datefmt='%H:%M:%S'
    )

    # === Router ===
    if len(ARGS) == 1 and ARGS[0] == '--sitemap':
        SITES = ["CLABOTS", "FIXAMI", "KLIUM", "LECOT", "TOOLNATION"]

        with ProcessPoolExecutor(max_workers=len(SITES)) as executor:
            # Submitting the tasks
            futures = {executor.submit(process_sitemap, site): site for site in SITES}
            
            # 'as_completed' to capture the end of each task
            for future in as_completed(futures):
                site = futures[future]
                try:
                    # Checking tast end status
                    future.result() 
                except Exception as exc:
                    logging.error(f"❌ The process for {site} crashed unexpectedly: {exc}")

    elif len(ARGS) == 1 and ARGS[0] == '--loader':
        SITES = ["CLABOTS", "FIXAMI", "KLIUM", "LECOT", "TOOLNATION"]

        with ProcessPoolExecutor(max_workers=len(SITES)) as executor:
            # Submitting the tasks
            futures = {executor.submit(process_loader, site): site for site in SITES}
            
            # 'as_completed' to capture the end of each task
            for future in as_completed(futures):
                site = futures[future]
                try:
                    # Checking task end status
                    future.result() 
                except Exception as exc:
                    logging.error(f"❌ The LOADER process for {site} crashed unexpectedly: {exc}")

    else:
        print(f"Invalid / Unrecognized arguments: {ARGS}")
        print("---------------------------------------------")
        print("Usage(s):")
        print("1) python adminCLI.py [--debug] : Run the full cycle")
        print("2) python adminCLI.py --loader [--debug] : Fetch the products based on the sitemaps")
        print("3) python adminCLI.py --sitemap [--debug] : Fetch the sitemaps")
        print("---------------------------------------------")
        sys.exit(1)