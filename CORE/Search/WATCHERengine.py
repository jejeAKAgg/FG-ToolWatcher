# CORE/Search/WATCHERengine.py
from __future__ import annotations

import os
import json
import logging
import random
import time

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from CORE.Services.setup import *
from CORE.Services.user import UserService

if TYPE_CHECKING:
    import pandas as pd
    from bs4 import BeautifulSoup



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

class WatcherEngine:

    """
    Generic real-time price monitoring engine.

    Loads site-specific configurations (price selectors, VAT rates, domains)
    from CORE/DATABASE/websites.json.

    Each dedicated watcher inherits from this class and passes its
    unique site key (e.g., "FIXAMI") to the constructor.

    Usage:
        class FIXAMIwatcher(WatcherEngine):
            def __init__(self, items, config):
                super().__init__("FIXAMI", items, config)

    """

    MAX_RETRIES = 3
    RETRY_DELAY = 5
    WAIT_TIME = 3

    def __init__(self, site_key: str, items: list[dict[str, Any]], config: UserService, progress_callback=None):

        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT = 0


        self.DEFAULT_COLUMNS = [
            'Société',
            'EAN', 'MPN',
            'Marque', 'Article',
            'Prix enregistré (HTVA)', 'Prix enregistré (TVA)',
            'Prix détecté (HTVA)', 'Prix détecté (TVA)',
            'Evolution du prix', 'Offres',
            'ArticleURL', 'Vérifié', 'Recherche',
        ]

        # === INTERNAL PARAMETER(S) ===
        self.WEBSITE = site_key.upper()
        self.WEBSITEcfg = self._load_site_config()

        self.DOMAIN = self.WEBSITEcfg.get("domain", "")
        self.SELECTORS = self.WEBSITEcfg.get("selectors", {})
        self.SITEMAPindex = self.WEBSITEcfg.get("sitemap_index") or ""
        self.SITEMAPurls = list(self.WEBSITEcfg.get("sitemap_manual") or [])
        self.VAT_RATE = float(self.WEBSITEcfg.get("vat_rate", 1.21))

        self.ITEMS = items
        self.CONFIG = config
        self.PROGRESS = progress_callback

        self.CACHE_DELAY = self.CONFIG.get(key="cache_duration", default=3)

        # === LAZY PARAMETER(S) ===
        self._DB = None
        self._PARSER = None
        self._REQUESTS = None

        # === PARAMETERS & OPTIONS SETUP (CloudSCRAPER) ===
        self.REQUESTS_HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Referer': f'https://www.{self.DOMAIN}/' if self.DOMAIN else '',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'DNT': '1' # Do Not Track
        }


    @property
    def DB(self):

        """
        Lazy load for the DB system.

        """

        if self._DB is None:
            self._DB = self._load_db()
        return self._DB

    @property
    def PD(self):

        """
        Lazy load for the DataFrame system

        """

        import pandas as pd
        return pd

    @property
    def parser(self):

        """
        Lazy load for the Parser system

        """

        if self._PARSER is None:
            from CORE.Services.parser import ProductDataParser
            self._PARSER = ProductDataParser(brands_file_path=os.path.join(RESOURCES_FOLDER, 'brands.json'))
        return self._PARSER

    @property
    def requests(self):

        """
        Lazy load for the Request system

        """

        if self._REQUESTS is None:
            import cloudscraper
            self._REQUESTS = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )
        return self._REQUESTS


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


    # ──────────────────────
    #   LOADER(S)/SAVER(S)
    # ──────────────────────

    def _load_db(self) -> pd.DataFrame | None:

        """
        Loads the MASTER_DB and filters records for the current company.

        """

        if not os.path.exists(os.path.join(DATA_SUBFOLDER, "MASTERproductsDB.csv")):
            LOG.warning(f"MASTERproductsDB not found: {os.path.join(DATA_SUBFOLDER, "MASTERproductsDB.csv")}")
            return None

        try:
            df = self.PD.read_csv(os.path.join(DATA_SUBFOLDER, "MASTERproductsDB.csv"), encoding='utf-8-sig', dtype=str)
            df = df[df["Company"].str.upper() == self.WEBSITE].copy()

            df['EAN'] = df['EAN'].str.strip().str.upper()
            df['MPN'] = df['MPN'].str.strip().str.upper()

            LOG.debug(f"DB loaded — {len(df)} products.")
            return df.reset_index(drop=True)

        except Exception as e:
            LOG.exception(f"An error occurred during LOADING MASTERproductsDB: {e}")
            return None

    def _extract_DBproduct(self, item: dict) -> dict[str, Any]:

        """
        Searches for a product in the database using a tiered fallback strategy:
        EAN → Exact MPN → Partial MPN → Fuzzy Name matching.

        """

        if self.DB is None: return None

        ean   = str(item.get("ean",   "-")).strip().upper()
        mpn   = str(item.get("mpn",   "-")).strip().upper()
        name  = str(item.get("name",  "")).strip()
        brand = str(item.get("brand", "-")).strip().upper()

        # --- EAN (100% match only) ---
        if ean not in ("-", "", "NAN"):
            match = self.DB[self.DB['EAN'] == ean]
            if not match.empty:
                LOG.debug(f"Full Match EAN {ean}")
                return match.iloc[0].to_dict()

        # --- MPN match → refine by EAN + Brand ---
        PLACEHOLDERS = {"-", "", "NAN", "NONE"}

        if mpn not in PLACEHOLDERS:
            for _, row in self.DB[self.DB['MPN'] == mpn].iterrows():
                row_ean    = str(row.get('EAN',   '-')).strip().upper()
                row_brand  = str(row.get('Brand', '-')).strip().upper()
                item_brand = str(item.get('brand', '-')).strip().upper()

                ean_ok       = ean        not in PLACEHOLDERS
                row_ean_ok   = row_ean    not in PLACEHOLDERS
                brand_ok     = item_brand not in PLACEHOLDERS
                row_brand_ok = row_brand  not in PLACEHOLDERS

                # EAN match → 100% certain
                if ean_ok and row_ean_ok:
                    if ean == row_ean:
                        LOG.debug(f"Match MPN+EAN {mpn}/{ean}")
                        return row.to_dict()
                    # EAN mismatch → brand decides
                    if brand_ok and row_brand_ok:
                        if item_brand == row_brand:
                            LOG.debug(f"Match MPN+Brand (EAN mismatch) {mpn}/{item_brand}")
                            return row.to_dict()
                        LOG.debug(f"Rejected MPN {mpn} — EAN+Brand mismatch")
                        continue
                    LOG.debug(f"Match MPN (EAN mismatch, Brand unknown) {mpn} — benefit of doubt")
                    return row.to_dict()

                # EAN absent one side → brand decides
                if brand_ok and row_brand_ok:
                    if item_brand == row_brand:
                        LOG.debug(f"Match MPN+Brand (EAN absent) {mpn}/{item_brand}")
                        return row.to_dict()
                    LOG.debug(f"Rejected MPN {mpn} — EAN absent, Brand mismatch ({item_brand} vs {row_brand})")
                    continue
                # Both unknown → benefit of doubt
                LOG.debug(f"Match MPN (EAN+Brand absent) {mpn} — benefit of doubt")
                return row.to_dict()

        LOG.debug(f"No Match — EAN={ean} / MPN={mpn} / Article={name}")
        return None


    # ─────────
    #   CACHE
    # ─────────

    def _cache_checker(self, path: str | None = None, cache_df: pd.DataFrame | None = None, item: str | None = None) -> pd.DataFrame | dict | None:
        if path:
            if os.path.exists(path):
                try:
                    if os.path.getsize(path) == 0:
                        return self.PD.DataFrame(columns=self.DEFAULT_COLUMNS)

                    df = self.PD.read_csv(path, encoding='utf-8-sig')
                    for col in set(self.DEFAULT_COLUMNS) - set(df.columns):
                        df[col] = None

                    return df[self.DEFAULT_COLUMNS]

                except self.PD.errors.EmptyDataError:
                    return self.PD.DataFrame(columns=self.DEFAULT_COLUMNS)

                except Exception as e:
                    LOG.exception(f"An error occurred '{path}': {e}")
                    return self.PD.DataFrame(columns=self.DEFAULT_COLUMNS)

            return self.PD.DataFrame(columns=self.DEFAULT_COLUMNS)

        elif cache_df is not None and item:
            if cache_df.empty or 'Recherche' not in cache_df.columns:
                return None

            row = cache_df[cache_df['Recherche'] == item]
            if row.empty:
                return None

            row_dict = row.iloc[0].to_dict()
            try:
                last_checked = self.PD.to_datetime(row_dict.get("Checked on"))
                if datetime.now() - last_checked <= timedelta(days=self.CACHE_DELAY):
                    return row_dict

            except Exception:
                pass

            return None

        return None


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

            # Validate before returning — reject MPN if == EAN (JSON-LD often sets mpn=sku=ean)
            if result:
                result_str = str(result).strip()
                if result_str not in {"-", "", "NAN", "NONE", "NULL"}:
                    if field == "mpn":
                        ean_val = next(
                            (str(jsonld.get(k)).strip() for k in ["gtin13", "gtin", "gtin12", "gtin8", "isbn", "sku"] if jsonld.get(k)),
                            None
                        )
                        if ean_val and result_str == ean_val:
                            pass  # MPN == EAN → fallback to HTML
                        else:
                            return result_str
                    else:
                        return result_str

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
                if split_on:
                    # find_all + pick element containing the keyword (avoids wrong divs like "Cadeau!")
                    candidates = soup.find_all(tag, attr_dict) if attr_dict else soup.find_all(tag, **find_kwargs)
                    el = next((c for c in candidates if split_on.upper() in c.get_text().upper()), None)
                else:
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
                if len(parts) > 1:
                    raw = parts[-1].strip().split()[0] if parts[-1].strip() else "-"
                    result = raw.split("|")[0].strip() or "-"
                else:
                    result = "-"

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

    def _compute_price_evolution(self, base: float, current: float) -> str:

        """
        Calculates the difference and percentage change between two prices.

        Compares a reference price (base) with a newly detected price (current)
        to return a formatted string representing the trend.

        Args:
            base (float): The original reference price from the database.
            current (float): The new price extracted during the current run.

        Returns:
            str: A formatted string:
                - "+X.XX€ (+Y.Y%)" if the price increased.
                - "X.XX€ (Y.Y%)" if the price decreased.
                - "=" if the price remained unchanged.
                - "-" if one of the prices is invalid (0 or negative).

        """

        if base > 0 and current > 0:
            diff = round(current - base, 2)
            pct  = round((diff / base) * 100, 1)
            if diff > 0:   return f"+{diff}€ (+{pct}%)"
            elif diff < 0: return f"{diff}€ ({pct}%)"
            else:          return "="
        return "-"



    def _extract_offers(self, soup: BeautifulSoup) -> str:

        """
        Extracts discount/volume offer tiers from the product page.
        Returns a formatted string like "1x→9.36€ | 12x→8.89€ (-5%) | 24x→8.66€ (-7.5%)"
        or "-" if no offers found.

        """

        offers_cfg = self.SELECTORS.get("offers")
        if not offers_cfg:
            return "-"

        mode = offers_cfg.get("mode")
        results = []

        try:
            # ── KLIUM mode : section.product-discounts ──
            if mode == "klium":
                container = soup.select_one(offers_cfg["container"])
                if not container:
                    return "-"
                for item in container.select(offers_cfg["item"]):
                    qty_el   = item.select_one(offers_cfg["qty"])
                    price_el = item.select_one(offers_cfg["price"])
                    if qty_el and price_el:
                        qty   = qty_el.get_text(strip=True)
                        price = price_el.get_text(strip=True)
                        results.append(f"{qty} → {price}")

            # ── FIXAMI mode : radio inputs + labels ──
            elif mode == "fixami":
                for radio in soup.select('input[name="variant"]'):
                    radio_id = radio.get("id", "")
                    labels = soup.select(f'label[for="{radio_id}"]')
                    if len(labels) >= 2:
                        qty   = labels[0].get_text(strip=True)
                        price = labels[1].get_text(strip=True)
                        pct   = labels[2].get_text(strip=True) if len(labels) >= 3 else ""
                        entry = f"{qty} → {price}€"
                        if pct:
                            entry += f" ({pct})"
                        results.append(entry)

        except Exception as e:
            LOG.exception(f"[WATCHERengine] Error extracting offers: {e}")

        return " | ".join(results) if results else "-"

    # ─────────────
    #   EXTRACTOR
    # ─────────────

    def _extract_FINALproduct(self, db_row: dict[str, Any], item_name: str) -> dict | None:

        """
        Scrapes the product page and returns a result dictionary.

        """

        from bs4 import BeautifulSoup

        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT = 0
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5

        # === INTERNAL PARAMETER(S) ===
        PRODUCTvar = {
            'Société': self.WEBSITE,
            'EAN': db_row.get('EAN', '-'),
            'MPN': db_row.get('MPN', '-'),
            'Marque': db_row.get('Brand', '-'),
            'Article': db_row.get('Article', '-'),
            'Prix enregistré (HTVA)': db_row.get('Base Price (HTVA)', 0.0),
            'Prix enreigstré (TVA)': db_row.get('Base Price (TVA)', 0.0),
            'Prix détecté (HTVA)': 0.0,
            'Prix détecté (TVA)': 0.0,
            'Evolution du prix': "-",
            'Offres': "-",
            'ArticleURL': db_row.get('ArticleURL', '-'),
            'Vérifié': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Recherche': item_name,
        }

        while self.ATTEMPT < self.MAX_RETRIES:
            try:
                response = self.requests.get(db_row.get('ArticleURL', '-'), headers=self.REQUESTS_HEADERS)
                response.raise_for_status()

                time.sleep(self.WAIT_TIME) # Loading time (JS)

                ARTICLEpage = response.content

                soup = BeautifulSoup(ARTICLEpage, "lxml")

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

                # ── Price ──
                PRICE = self._extract_field(soup, "price", JSONdata)
                PRICE = self.parser.parse_price(str(PRICE))
                PRODUCTvar["Prix détecté (TVA)"]  = self.parser.format_price_for_excel(PRICE)
                PRODUCTvar["Prix détecté (HTVA)"] = self.parser.format_price_for_excel(round(PRICE / self.VAT_RATE, 2))

                # ── Evolution ──
                try:
                    PRODUCTvar['Evolution du prix'] = self._compute_price_evolution(float(str(db_row.get('Base Price (TVA)', 0)).replace(',', '.')), PRICE)
                except Exception:
                    PRODUCTvar['Evolution du prix'] = "-"

                # ── Offers ──
                PRODUCTvar['Offres'] = self._extract_offers(soup)

                return PRODUCTvar

            except self.requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    LOG.warning(f"Error 404 : {db_row.get('ArticleURL', '-')}")
                    return PRODUCTvar

                LOG.exception(f"Error HTTP {e.response.status_code} : {db_row.get('ArticleURL', '-')}")

                self.ATTEMPT += 1
                time.sleep(self.RETRY_DELAY)

            except Exception as e:
                LOG.exception(f"Error during data extraction for product {db_row.get('ArticleURL', '-')}: {e}")

                self.ATTEMPT+=1
                time.sleep(self.RETRY_DELAY)

        LOG.warning(f"Abandoning after {self.MAX_RETRIES} attempts for product {db_row.get('ArticleURL', '-')}")
        return None


    # ────────────
    #   EXECUTOR
    # ────────────

    def run(self) -> pd.DataFrame:

        CSVpath = os.path.join(RESULTS_SUBFOLDER_TEMP, f"{self.WEBSITE}products.csv")
        XLSXpath = os.path.join(RESULTS_SUBFOLDER_TEMP, f"{self.WEBSITE}products.xlsx")

        CACHEdata = self._cache_checker(path=CSVpath)

        ITEMSlenght = len(self.ITEMS)

        PRODUCTS: list[dict[str, Any]] = []

        try:
            for idx, ITEM in enumerate(self.ITEMS, 1):
                ITEMname = ITEM.get("name", "-")

                # Cache hit
                if cached := self._cache_checker(cache_df=CACHEdata, item=ITEMname):
                    PRODUCTS.append(cached)
                    LOG.debug(f"Cache hit: {ITEMname}")
                else:
                    # DB search
                    DATA = self._extract_DBproduct(ITEM)
                    if DATA:
                        result = self._extract_FINALproduct(db_row=DATA, item_name=ITEMname)
                        if result:
                            PRODUCTS.append(result)
                    else:
                        LOG.warning(f"Product missing from database — {ITEMname} (EAN={ITEM.get('ean')} / MPN={ITEM.get('mpn')})")

                    time.sleep(random.uniform(1.5, 3))

                # Progress callback
                if self.PROGRESS and ITEMSlenght > 0:
                    self.PROGRESS(int(idx / ITEMSlenght * 100))

        except Exception as e:
            LOG.error(f"A fatal error occurred: {e}")

        df = self.PD.DataFrame(PRODUCTS)
        df.to_csv(CSVpath,  index=False, encoding='utf-8-sig')
        df.to_excel(XLSXpath, index=False)

        LOG.debug(f"{self.WEBSITE}watcher processed finished.")
        return df
