# CORE/Database/LOADERengine.py
import os
import time

import logging

import cloudscraper
import csv
import gzip
import json
import pandas as pd
import random
import requests

from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional
from urllib.parse import unquote

from CORE.Services.setup import *
from CORE.Services.parser import ProductDataParser



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

class LoaderEngine:

    """
    Generic product catalog scraping engine.

    Reads configuration (sitemaps, domains, CSS selectors, VAT rates)
    from CORE/__RESOURCES/websites.json and centralizes common logic:
    sitemap discovery, GZIP decompression, batch processing, and
    HTML/JSON-LD extraction.

    Each site-specific loader inherits from this class and passes its
    unique site key (e.g., "FIXAMI") to the constructor.

    Usage:
        class FIXAMIloader(LoaderEngine):
            def __init__(self):
                super().__init__("FIXAMI")

        if __name__ == "__main__":
            FIXAMIloader().run()

    """

    def __init__(self, site_key: str):

        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT = 0
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5
        self.SAVE_COUNTER = 0
        self.SAVE_THRESHOLD = 100
        self.WAIT_TIME = 3

        self.NAMESPACESurl = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        self.URLs: List[str] = []

        self.DB_COLS = [
            'EAN', 'MPN',
            'Brand', 'Article',
            'Base Price (HTVA)', 'Base Price (TVA)',
            'ArticleURL', 'Checked on'
        ]

        # === INTERNAL PARAMETER(S) ===
        self.WEBSITE = site_key.upper()
        self.WEBSITEcfg = self._load_site_config()

        self.DOMAIN = self.WEBSITEcfg.get("domain", "")
        self.SELECTORS = self.WEBSITEcfg.get("selectors", {})
        self.SITEMAPindex = self.WEBSITEcfg.get("sitemap_index") or ""
        self.SITEMAPurls = list(self.WEBSITEcfg.get("sitemap_manual") or [])
        self.VAT_RATE = float(self.WEBSITEcfg.get("vat_rate", 1.21))

        # === INTERNAL SERVICE(S) ===
        self.parser = ProductDataParser(brands_file_path=os.path.join(RESOURCES_FOLDER, 'brands.json'))

        # === PARAMETERS & OPTIONS SETUP (CloudSCRAPER) ===
        self.requests = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )

        self.REQUESTS_HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Referer': f'https://www.{self.DOMAIN}/' if self.DOMAIN else '',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'DNT': '1' # Do Not Track
        }


    # ─────────────
    #   LOADER(S)
    # ─────────────

    def _load_site_config(self) -> dict:

        """
        Loads site-specific configuration from websites.json.

        Fetches the required metadata for the specified site, including
        base URLs, sitemap locations, and the precise HTML selectors
        (tags, classes, or IDs) needed for product data extraction.

        """

        try:

            with open(os.path.join(RESOURCES_FOLDER, "websites.json"), encoding="utf-8") as f:
                CONFIGS = json.load(f)

            BALISES = CONFIGS.get(self.WEBSITE)

            if not BALISES:
                raise KeyError(f"Key value '{self.WEBSITE}' not in websites.json")

            return BALISES

        except Exception as e:
            LOG.exception(f"An error occurred during READ: {e}")
            return {}


    # ──────────────
    #   FETCHER(S)
    # ──────────────

    def _discover_sitemaps(self) -> None:

        """
        Dynamically retrieves product sitemap URLs (Sitemapp) from the given sitemap index.

        """

        LOG.info(f"Fetching sitemap index")

        if not self.SITEMAPindex:
            LOG.info("No sitemaps index for this website")
            return

        try:
            response = self.requests.get(self.SITEMAPindex, headers=self.REQUESTS_HEADERS)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "xml")

            self.SITEMAPurls = [loc.text.strip() for loc in soup.find_all('loc')]

            LOG.info(f"{len(self.SITEMAPurls)} sitemaps discovered.")

        except Exception as e:
            LOG.error(f"An error occured during the retrieve: {e}")

    def _fetch_and_decompress_sitemap(self, link: str) -> Optional[str]:

        """
        Downloads the sitemap (which may be a compressed .gz file) and returns the decompressed XML content.

        Args:
            link (str): The URL of the sitemap file (e.g., 'sitemap-index-1.xml' or 'sitemap-index-1.xml.gz').

        Returns:
            str | None: The decompressed XML content as a string, or None if the download or decompression fails.

        """

        LOG.info(f"Fetching sitemap: {link}")

        try:
            response = self.requests.get(link, headers=self.REQUESTS_HEADERS)
            response.raise_for_status()

            time.sleep(self.WAIT_TIME)

            if link.endswith('.gz'):
                LOG.info("Content is GZIP compressed. Decompressing...")

                return gzip.decompress(response.content).decode('utf-8')

            return response.text

        except requests.exceptions.HTTPError as e:
            LOG.exception(f"HTTP {e.response.status_code} one the following sitemap: {link}")

        except Exception as e:
            LOG.exception(f"An error occurred during the decompress of the following sitemap: {e}")

        return None

    def _extract_SITEMAPurls(self, link: str) -> List[str]:

        """
        Downloads the sitemap and extracts all <loc> URLs (applying filtering logic).

        """

        LOG.info(f"Downloading sitemap: {link}...")

        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT = 0
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5

        # === SEARCH ENGINE ===
        while self.ATTEMPT < self.MAX_RETRIES:
            try:
                ARTICLEpage = self._fetch_and_decompress_sitemap(link)

                if ARTICLEpage is None:
                    LOG.error(f"Sitemap empty or unavailable for {link}")

                    self.ATTEMPT += 1
                    time.sleep(self.RETRY_DELAY)

                    continue # Retry the download

                soup = BeautifulSoup(ARTICLEpage, "xml")

                for loc_tag in soup.find_all('loc'):
                    PRODUCTurl = unquote(loc_tag.text.strip())
                    SEGMENTSdata = [w for w in PRODUCTurl.split('/') if w]

                    if len(SEGMENTSdata) < 3:
                        continue

                    if len(SEGMENTSdata[-1]) < 15:
                        continue

                    if SEGMENTSdata[1] not in (self.DOMAIN, f'www.{self.DOMAIN}'):
                        continue

                    if any(S.lower() in {'nl', 'de', 'en', 'nl-be', 'nl-nl', 'de-de', 'en-be'} for S in SEGMENTSdata):
                        continue

                    if PRODUCTurl.endswith(('/', '.jpg', '.jpeg', '.png', '.gif', '.pdf')):
                        continue

                    self.URLs.append(PRODUCTurl)

                return list(set(self.URLs))  # Removing duplicates if any (though unlikely in a single sitemap)

            except Exception as e:
                LOG.exception(f"Error during sitemap extraction: {e}")

                self.ATTEMPT+=1
                if self.ATTEMPT == self.MAX_RETRIES:
                    LOG.warning(f"Abandoning after {self.MAX_RETRIES} attempts.")

                    return []

                time.sleep(self.RETRY_DELAY)

        return []


    # ──────────────────────
    #   LOADER(S)/SAVER(S)
    # ──────────────────────

    def _load_DBurls(self, csv_path: str) -> set:

        """
        Loads already processed URLs from the existing DB for restart logic (cache checker).

        """

        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path, usecols=['ArticleURL'], encoding='utf-8-sig')
                urls = set(df['ArticleURL'].astype(str).tolist())

                LOG.info(f"Existing database found for {csv_path}: {len(urls)} URLs already processed.")
                return urls

            except Exception as e:
                LOG.exception(f"Error loading existing DB: {e}. Full restart needed.")

        return set()

    def _save_batch(self, csv_path: str, batch_data: List[dict], is_emergency: bool = False) -> None:

        """
        Saves the current batch of data by appending it to the existing database file.

        """

        if not batch_data:
            return

        NEWdf = pd.DataFrame(batch_data)

        COLS = ['EAN', 'MPN', 'Brand', 'Article', 'Base Price (HTVA)', 'Base Price (TVA)', 'ArticleURL', 'Checked on']

        for col in COLS:
            if col not in NEWdf.columns:
                NEWdf[col] = "-" if "Price" not in col else 0.0
            elif "Price" in col:
                NEWdf[col] = pd.to_numeric(NEWdf[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0.0).astype(float)
            else:
                NEWdf[col] = NEWdf[col].astype(str)

        NEWdf = NEWdf[COLS]

        FILE = os.path.exists(csv_path)

        try:
            NEWdf.to_csv(
                csv_path,
                mode='a' if FILE else 'w',
                header=not FILE,
                index=False,
                encoding='utf-8-sig',
                quoting=csv.QUOTE_MINIMAL,
                quotechar='"'
            )

            if not is_emergency:
                LOG.info(f"Batch saved.")

        except Exception as e:
            LOG.exception(f"CRITICAL: Failed to merge batch due to {e}.")


    # ───────────────
    #   UTILITY/IES
    # ───────────────

    def _extract_field(self, soup: BeautifulSoup, field: str, jsonld: dict) -> str:

        """
        Extracts a product field from the soup or JSON-LD based on
        the selector configuration in websites.json.

        """

        sel = self.SELECTORS.get(field)
        result = None

        # --- JSON-LD (if available on the target website) ---
        if self.WEBSITEcfg.get("jsonld") is True:
            ld_map = {
                "ean": ["gtin13", "gtin", "gtin12", "gtin8", "isbn"],
                "mpn": ["mpn", "model"],
                "brand": ["brand"],
                "article": ["name"],
                "price": ["price"]
            }

            if field == "price":
                offers = jsonld.get("offers", {})
                if isinstance(offers, list) and offers:
                    result = offers[0].get("price")
                elif isinstance(offers, dict):
                    result = offers.get("price")
            else:
                for k in ld_map.get(field, []):
                    val = jsonld.get(k)
                    if val:
                        result = val.get("name") if isinstance(val, dict) else val
                        break

            # if DATA from JSON-LD, return
            if result:
                return str(result).strip()

        # --- else, fallback to HTML ---
        if isinstance(sel, dict):
            tag        = sel.get("tag")
            cls        = sel.get("class")
            id_        = sel.get("id")
            text_cont  = sel.get("text_contains")
            replace_   = sel.get("replace")
            use_attr   = sel.get("use_attr")
            attr_dict  = sel.get("attr")
            type_      = sel.get("type")
            target_    = sel.get("target")
            split_on   = sel.get("split")
            label_     = sel.get("label")

            # ── Type sibling (ex: dt -> dd) ──
            if type_ == "sibling" and text_cont:
                keywords = [text_cont] if isinstance(text_cont, str) else text_cont
                for el in soup.find_all(tag, class_=cls):
                    if any(kw.lower() in el.get_text().lower() for kw in keywords):
                        sibling = el.find_next_sibling(target_.split('.')[-1] if target_ else "dd")
                        if sibling:
                            result = sibling.get_text(strip=True)
                            break

            # ── Table with label (Clabots MPN) ──
            elif label_:
                for row in soup.find_all(tag, class_=cls):
                    label_el = row.find(True, string=lambda s: s and label_.lower() in s.lower())
                    if label_el:
                        # On cherche la valeur dans la même rangée
                        val_el = row.find_next(class_="attribute-table__column__value") or row.find_next("td")
                        if val_el:
                            result = val_el.get_text(strip=True)
                            break

            # ── Text contains simple (Klium/Lecot EAN) ──
            elif text_cont and not type_:
                keywords = [text_cont] if isinstance(text_cont, str) else text_cont
                find_kwargs = {k: v for k, v in [('class_', cls), ('id', id_)] if v}
                for el in soup.find_all(tag, **find_kwargs):
                    if any(kw.lower() in el.get_text().lower() for kw in keywords):
                        if target_ and '.' in target_:
                            t_tag, t_cls = target_.split('.', 1)
                            sub = el.find(t_tag, class_=t_cls)
                            result = sub.get_text(strip=True) if sub else None
                        else:
                            result = el.get_text(strip=True)
                        if result: break

            # ── Attribut custom / tag simple (Toolnation/Klium price) ──
            elif attr_dict or tag:
                find_kwargs = {k: v for k, v in [('class_', cls), ('id', id_)] if v}
                el = soup.find(tag, attr_dict) if attr_dict else soup.find(tag, **find_kwargs)
                if el:
                    child_tag = sel.get("child_tag")
                    if child_tag:
                        child = el.find(child_tag)
                        result = child.get_text(strip=True) if child else el.get_text(strip=True)
                    else:
                        result = el.get(use_attr) if use_attr else el.get_text(strip=True)

            # --- POST-TREATMENT ---
            if result and split_on:
                parts = result.upper().split(split_on.upper())
                result = parts[-1].strip().split()[0] if len(parts) > 1 else "-"

            if result and replace_:
                result = result.upper().replace(replace_.upper(), "").strip()

        return str(result).strip() if result and str(result).lower() != "none" else "-"

    def _clean_ean(self, raw: str) -> str:

        """
        Standardizes the EAN by removing non-alphanumeric characters
        (spaces, dots, dashes) and converting to uppercase.

        """

        cleaned = "".join(filter(str.isalnum, str(raw))).upper()

        return cleaned if cleaned else "-"

    def _clean_mpn(self, raw: str) -> str:

        """
        Cleans the MPN by removing known brand names and extra whitespace.
        Ensures the reference is standardized for database matching.

        """

        brands = sorted(self.parser.brands, key=len, reverse=True)
        cleaned = str(raw).lower()

        for b in brands:
            cleaned = cleaned.replace(b.lower(), "")

        return " ".join(cleaned.split()).strip().upper() or "-"


    # ─────────────
    #   EXTRACTOR
    # ─────────────

    def _ONLINEextract_FINALproduct(self, link: str) -> Optional[dict]:

        """
        Scrapes a product page and returns a normalized dictionary.

        Extracts raw data from the page using site-specific selectors
        and JSON-LD metadata, then formats it into a standard schema
        (EAN, MPN, Brand, Price) for database consistency.

        """

        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT = 0
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5

        # === INTERNAL PARAMETER(S) ===
        PRODUCTvar = {
            'EAN': "-",
            'MPN': "-",
            'Brand': "-",
            'Article': "-",
            'Base Price (HTVA)': 0.0,
            'Base Price (TVA)': 0.0,
            'ArticleURL': link,
            'Checked on': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        while self.ATTEMPT < self.MAX_RETRIES:
            try:
                response = self.requests.get(link, headers=self.REQUESTS_HEADERS)
                response.raise_for_status()

                time.sleep(self.WAIT_TIME) # Loading time (JS)

                ARTICLEpage = response.content

                soup = BeautifulSoup(ARTICLEpage, "html.parser")

                JSONdata = {}
                for s in soup.find_all('script', type='application/ld+json'):
                    try:
                        parsed = json.loads(s.string)
                        items = [parsed] if isinstance(parsed, dict) else (parsed if isinstance(parsed, list) else [])
                        for item in items:
                            if isinstance(item, dict) and item.get("@type") == "Product":
                                JSONdata = item
                                break
                        if JSONdata:
                            break
                    except (json.JSONDecodeError, Exception):
                        continue

                # ── EAN ──
                PRODUCTvar["EAN"] = self._clean_ean(self._extract_field(soup, "ean", JSONdata))

                # ── MPN ──
                PRODUCTvar["MPN"] = self._clean_mpn(self._extract_field(soup, "mpn", JSONdata))

                # ── Brand ──
                PRODUCTvar["Brand"] = self._extract_field(soup, "brand", JSONdata).upper()

                # ── Article ──
                ARTICLE = self._extract_field(soup, "article", JSONdata)
                PRODUCTvar["Article"] = " ".join(ARTICLE.split()).replace('"', '""').strip('"')

                # ── Price ──
                PRICE = self._extract_field(soup, "price", JSONdata)
                PRICE = self.parser.parse_price(str(PRICE))
                PRODUCTvar["Base Price (TVA)"]  = self.parser.format_price_for_excel(PRICE)
                PRODUCTvar["Base Price (HTVA)"] = self.parser.format_price_for_excel(round(PRICE / self.VAT_RATE, 2))

                return PRODUCTvar

            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 404:
                    LOG.warning(f"Invalid link (404 Not Found). Saving failure for future skip: {link}")
                    return PRODUCTvar

                LOG.exception(f"HTTP Error ({response.status_code}) for {link}: {http_err}")

                self.ATTEMPT+=1
                time.sleep(self.RETRY_DELAY)

            except Exception as e:
                LOG.exception(f"Error during data extraction for product {link}: {e}")

                self.ATTEMPT+=1
                time.sleep(self.RETRY_DELAY)

        LOG.warning(f"Abandoning after {self.MAX_RETRIES} attempts for product {link}")
        return None


    # ────────────
    #   EXECUTOR
    # ────────────

    def run(self) -> None:

        """
        Executes the complete scraping pipeline: discovery, extraction, and persistence.

        The workflow follows these stages:
            1. Initialization: Sets up output paths and loads processed URLs from existing
            databases (CSV and CSVnot) to support resume-on-failure.
            2. Discovery: Retrieves sitemap URLs via index discovery or manual configuration.
            3. Extraction: Iterates through discovered product URLs, filtering out
            previously processed items.
            4. Processing: Scrapes product data and categorizes results into 'success'
            (valid products) or 'fails' (missing EAN/MPN or invalid price).
            5. Batch Persistence: Periodically saves results to disk to minimize data loss.
            6. Finalization: Ensures remaining data is saved and handles critical errors
            via an emergency save routine.

        """

        CSVpathDB = os.path.join(DATA_SUBFOLDER_SOURCE, f"{self.WEBSITE}productsDB.csv")
        CSVpathDBnot = os.path.join(DATA_SUBFOLDER_SOURCE, f"{self.WEBSITE}productsDBnot.csv")

        DBurls = self._load_DBurls(CSVpathDB)
        DBurlsNOT = self._load_DBurls(CSVpathDBnot)

        PRODUCTS: List[dict] = []
        FAILS: List[dict] = []

        try:

            if self.SITEMAPindex and not self.WEBSITEcfg.get("sitemap_manual"):
                self._discover_sitemaps()

            for SITEMAPurl in self.SITEMAPurls:
                self._extract_SITEMAPurls(SITEMAPurl)

            self.URLs = [url for url in self.URLs if url not in DBurls and url not in DBurlsNOT]

            LOG.info(f"Found link(s): {len(self.URLs)}")

            for PRODUCTurl in self.URLs:
                try:
                    data = self._ONLINEextract_FINALproduct(PRODUCTurl)

                    LOG.debug(data)

                    if data is None: continue

                    if data and not pd.isna(data['Base Price (HTVA)']) and data['Base Price (HTVA)'] > 0: PRODUCTS.append(data)
                    else: FAILS.append(data)

                    self.SAVE_COUNTER += 1

                    if self.SAVE_COUNTER >= self.SAVE_THRESHOLD:
                        self._save_batch(CSVpathDB, PRODUCTS)
                        self._save_batch(CSVpathDBnot, FAILS)

                        self.SAVE_COUNTER = 0
                        PRODUCTS, FAILS = [], []

                    time.sleep(random.uniform(0.5, 1)) # Loading time (STABILITY)

                except Exception as e:
                    LOG.exception(f"An unexpected error occurred for URL {PRODUCTurl}: {e}")
                    continue

            if PRODUCTS: self._save_batch(CSVpathDB, PRODUCTS)
            if FAILS: self._save_batch(CSVpathDBnot, FAILS)

        except Exception as e:

            if PRODUCTS: self._save_batch(CSVpathDB, PRODUCTS, is_emergency=True)
            if FAILS:    self._save_batch(CSVpathDBnot, FAILS, is_emergency=True)

            LOG.warning(f"Emergency save triggered due to critical error: {e}")

        LOG.info(f"{self.WEBSITE} loader terminated...")
