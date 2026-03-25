# CORE/Watchers/klium.py
import os
import time
import logging
import cloudscraper
import json
import pandas as pd
import random
import requests

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from functools import reduce
from thefuzz import fuzz, process

from CORE.Services.setup import *
from CORE.Services.parser import ProductDataParser
from CORE.Services.user import UserService



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

class KLIUMwatcher:

    """
    Watcher pour Fixami (fixami.be).

    Reçoit une liste de dicts {name, mpn, ean} depuis le Manager.
    Recherche dans la DB locale par EAN d'abord, puis MPN en fallback.
    """

    def __init__(self, items: List[dict], config: UserService):
        
        # === INPUT VARIABLE(S) ===
        self.items  = items
        self.config = config

        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT    = 0
        self.CACHE_DELAY = self.config.get(key="cache_duration", default=3)

        self.DEFAULT_COLUMNS = [
            'Société', 'Article',
            'Base Price (HTVA)', 'Base Price (TVA)',
            'Price (HTVA)', 'Price (TVA)',
            'Price Evolution', 'Offers',
            'ArticleURL', 'Checked on', 'Recherche',
        ]

        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5
        self.WAIT_TIME   = 3
        
        self.SOCIETE = "KLIUM"

        # === INTERNAL SERVICE(S) ===
        self.parser = ProductDataParser(
            brands_file_path=os.path.join(UTILS_FOLDER, 'brands.json')
        )

        # === CLOUDSCRAPER SETUP ===
        self.requests = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )
        self.REQUESTS_HEADERS = {
            'User-Agent':      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Referer':         'https://www.klium.be/',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept':          'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Connection':      'keep-alive',
            'DNT':             '1',
        }

        # === DB CACHE (chargée une seule fois pour tout le run) ===
        self._db_df: Optional[pd.DataFrame] = self._load_db()


    # ────────────────────────────────────────────
    #   DB
    # ────────────────────────────────────────────

    def _load_db(self) -> Optional[pd.DataFrame]:

        """Charge la MASTER_DB et filtre sur FIXAMI."""

        master_path = os.path.join(DATA_SUBFOLDER, "MASTERproductsDB.csv")

        if not os.path.exists(master_path):
            LOG.warning(f"[KLIUMwatcher] MASTER_DB introuvable : {master_path}")
            return None

        try:
            df = pd.read_csv(master_path, encoding='utf-8-sig', dtype=str)
            df = df[df["Société"].str.upper() == self.SOCIETE].copy()
            df['EAN'] = df['EAN'].str.strip().str.upper()
            df['MPN'] = df['MPN'].str.strip().str.upper()
            LOG.debug(f"[KLIUMwatcher] DB chargée — {len(df)} produits.")
            return df.reset_index(drop=True)
        except Exception as e:
            LOG.exception(f"[KLIUMwatcher] Erreur chargement MASTER_DB : {e}")
            return None

    def _extract_DBproduct(self, item: dict) -> Optional[Dict[str, Any]]:
        if self._db_df is None:
            return None

        ean = str(item.get("ean", "-")).strip().upper()
        mpn = str(item.get("mpn", "-")).strip().upper()
        name = str(item.get("name", "")).strip()

        # 1. EAN exact
        if ean not in ("-", "", "NAN"):
            match = self._db_df[self._db_df['EAN'] == ean]
            if not match.empty:
                LOG.debug(f"Match EAN {ean}")
                return match.iloc[0].to_dict()

        # 2. MPN exact
        if mpn not in ("-", "", "NAN"):
            match = self._db_df[self._db_df['MPN'] == mpn]
            if not match.empty:
                LOG.debug(f"Match MPN exact {mpn}")
                return match.iloc[0].to_dict()

        # 3. MPN partiel — l'un contient l'autre (DGA901ZKU ↔ DGA901ZKU1)
        if mpn not in ("-", "", "NAN"):
            match = self._db_df[
                self._db_df['MPN'].apply(
                    lambda x: (mpn in x or x in mpn) and abs(len(mpn) - len(x)) <= 3
                )
            ]
            if not match.empty:
                LOG.debug(f"Match MPN partiel {mpn} → {match.iloc[0]['MPN']}")
                return match.iloc[0].to_dict()

        # 4. Fuzzy sur le nom d'article — dernier recours
        if name:
            result = process.extractOne(
                name,
                self._db_df['Article'].tolist(),
                scorer=fuzz.token_set_ratio
            )
            if result and result[1] >= 80:
                match = self._db_df[self._db_df['Article'] == result[0]]
                LOG.debug(f"Match fuzzy '{name}' → '{result[0]}' ({result[1]}%)")
                return match.iloc[0].to_dict()

        LOG.debug(f"Aucun match — EAN={ean} / MPN={mpn} / Article={name}")
        return None


    # ────────────────────────────────────────────
    #   CACHE
    # ────────────────────────────────────────────

    def _cache_checker(
        self,
        path: Optional[str] = None,
        cache_df: Optional[pd.DataFrame] = None,
        item: Optional[str] = None
    ) -> pd.DataFrame | dict | None:

        if path:
            if os.path.exists(path):
                try:
                    if os.path.getsize(path) == 0:
                        return pd.DataFrame(columns=self.DEFAULT_COLUMNS)
                    df = pd.read_csv(path, encoding='utf-8-sig')
                    for col in set(self.DEFAULT_COLUMNS) - set(df.columns):
                        df[col] = None
                    return df[self.DEFAULT_COLUMNS]
                except pd.errors.EmptyDataError:
                    return pd.DataFrame(columns=self.DEFAULT_COLUMNS)
                except Exception as e:
                    LOG.exception(f"Error loading cache '{path}': {e}")
                    return pd.DataFrame(columns=self.DEFAULT_COLUMNS)
            return pd.DataFrame(columns=self.DEFAULT_COLUMNS)

        elif cache_df is not None and item:
            if cache_df.empty or 'Recherche' not in cache_df.columns:
                return None
            row = cache_df[cache_df['Recherche'] == item]
            if row.empty:
                return None
            row_dict = row.iloc[0].to_dict()
            try:
                last_checked = pd.to_datetime(row_dict.get("Checked on"))
                if datetime.now() - last_checked <= timedelta(days=self.CACHE_DELAY):
                    return row_dict
            except Exception:
                pass
            return None

        return None


    # ────────────────────────────────────────────
    #   SCRAPING
    # ────────────────────────────────────────────

    def _extract_FINALproduct(self, db_row: Dict[str, Any], item_name: str) -> Optional[dict]:

        """
        Scrape la page produit Fixami à partir du lien stocké en DB.

        Args:
            db_row    : ligne de la DB locale (contient ArticleURL, prix de base, etc.)
            item_name : nom de l'article côté Georges (pour le champ 'Local REF')
        """

        self.ATTEMPT = 0
        link = db_row.get('ArticleURL', '-')

        PRODUCTvar = {
            'Société':            "KLIUM",
            'Article':            db_row.get('Article', '-'),
            'Base Price (HTVA)':  db_row.get('Base Price (HTVA)', 0.0),
            'Base Price (TVA)':   db_row.get('Base Price (TVA)', 0.0),
            'Price (HTVA)':       0.0,
            'Price (TVA)':        0.0,
            'Price Evolution':    "-",
            'Offers':             "-",
            'ArticleURL':         link,
            'Checked on':         datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Recherche':          item_name,
        }

        while self.ATTEMPT < self.MAX_RETRIES:
            try:
                response = self.requests.get(link, headers=self.REQUESTS_HEADERS)
                response.raise_for_status()
                time.sleep(self.WAIT_TIME)

                soup     = BeautifulSoup(response.content, "html.parser")
                JSONdata = next(
                    (
                        i
                        for s in soup.find_all('script', type='application/ld+json')
                        for i in ([json.loads(s.string)] if isinstance(json.loads(s.string), dict) else (json.loads(s.string) if isinstance(json.loads(s.string), list) else []))
                        if isinstance(i, dict) and i.get("@type") == "Product"
                    ),
                    {}
                )

                # --- Prix ---
                PRODUCTvar['Price (HTVA)'], PRODUCTvar['Price (TVA)'] = (
                    lambda p: (
                        self.parser.format_price_for_excel(round(p / 1.21, 2)),
                        self.parser.format_price_for_excel(p),
                    )
                )(
                    (lambda raw: self.parser.parse_price(str(raw)) if raw not in (None, "-", "") else 0.0)(
                        (
                        (m := soup.find("span", class_="current-price-value")) and m.get("content") or
                        (o[0].get("price") if isinstance(o := JSONdata.get("offers"), list) and o
                        else (o.get("price") if isinstance(o, dict) else None))
                    )
                    )
                )

                # --- Price Evolution ---
                try:
                    base = float(str(db_row.get('Base Price (HTVA)', 0)).replace(',', '.'))
                    current = float(str(PRODUCTvar['Price (HTVA)']).replace(',', '.'))

                    if base > 0 and current > 0:
                        diff = round(current - base, 2)
                        pct  = round((diff / base) * 100, 1)

                        if diff > 0:
                            PRODUCTvar['Price Evolution'] = f"+{diff}€ (+{pct}%)"
                        elif diff < 0:
                            PRODUCTvar['Price Evolution'] = f"{diff}€ ({pct}%)"
                        else:
                            PRODUCTvar['Price Evolution'] = "="
                    else:
                        PRODUCTvar['Price Evolution'] = "-"

                except Exception:
                    PRODUCTvar['Price Evolution'] = "-"

                return PRODUCTvar

            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 404:
                    LOG.warning(f"[KLIUMwatcher] 404 pour {link}")
                    return PRODUCTvar
                LOG.exception(f"[KLIUMwatcher] HTTP {response.status_code} : {http_err}")
                self.ATTEMPT += 1
                time.sleep(self.RETRY_DELAY)

            except Exception as e:
                LOG.exception(f"[KLIUMwatcher] Erreur extraction {link} : {e}")
                self.ATTEMPT += 1
                time.sleep(self.RETRY_DELAY)

        LOG.warning(f"[KLIUMwatcher] Abandon après {self.MAX_RETRIES} tentatives pour {link}")
        return None


    # ────────────────────────────────────────────
    #   RUN
    # ────────────────────────────────────────────

    def run(self) -> pd.DataFrame:

        CSVpath  = os.path.join(RESULTS_SUBFOLDER_TEMP, "KLIUMproducts.csv")
        XLSXpath = os.path.join(RESULTS_SUBFOLDER_TEMP, "KLIUMproducts.xlsx")

        CACHEdata = self._cache_checker(path=CSVpath)
        PRODUCTS: List[dict] = []

        try:
            for item in self.items:

                # item est un dict {name, mpn, ean}
                item_name = item.get("name", "-")

                # Vérif cache sur le nom Georges
                if CACHED := self._cache_checker(cache_df=CACHEdata, item=item_name):
                    LOG.debug(f"[KLIUMwatcher] Cache hit : {item_name}")
                    PRODUCTS.append(CACHED)
                    continue

                # Recherche en DB par EAN / MPN
                db_row = self._extract_DBproduct(item)

                if db_row:
                    result = self._extract_FINALproduct(db_row=db_row, item_name=item_name)
                    if result:
                        PRODUCTS.append(result)
                else:
                    LOG.warning(f"[KLIUMwatcher] Produit absent de la DB Fixami — {item_name} (EAN={item.get('ean')} / MPN={item.get('mpn')})")

                time.sleep(random.uniform(1.5, 3))

        except Exception as e:
            LOG.error(f"[KLIUMwatcher] Erreur fatale : {e}")

        df = pd.DataFrame(PRODUCTS)
        df.to_csv(CSVpath,  index=False, encoding='utf-8-sig')
        df.to_excel(XLSXpath, index=False)

        LOG.debug("[KLIUMwatcher] Terminé.")
        return df