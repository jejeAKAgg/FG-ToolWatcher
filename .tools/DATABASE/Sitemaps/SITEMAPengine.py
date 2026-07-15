# .tools/DATABASE/Sitemaps/SITEMAPengine.py
import os
import time

import cloudscraper
import gzip
import json
import logging
import sqlite3

from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Set
from urllib.parse import unquote

LOG = logging.getLogger(__name__)

class SITEMAPengine:

    # === INTERNAL PARAMETER(S) ===
    RESOURCES_FILE = ".tools/DATABASE/__resources/websites.json"
    DATABASE_PATH = ".tools/DATABASE/Sitemaps/db/"

    REQUEST_DELAY = 1.0  # politeness delay between HTTP calls
    MAX_RETRIES = 3
    RETRY_DELAY = 5      # in seconds

    def __init__(self, site_key: str):

        # === INTERNAL VARIABLE(S) ===
        self.WEBSITE = site_key.upper()
        self.WEBSITEcfg = self._load_config(config=self.RESOURCES_FILE, key=self.WEBSITE)

        self.DOMAIN = self.WEBSITEcfg.get("domain", "")
        self.SITEMAPindex: List[str] = self.WEBSITEcfg.get("sitemap_index", [])
        self.EXCLUDE_SEGMENTS: List[str] = self.WEBSITEcfg.get("sitemap_exclude_segments", [])

        # === INTERNAL SERVICE(S) ===
        self._init_schema(path=self.DATABASE_PATH, name=self.WEBSITE)

        # === PARAMETERS & OPTIONS SETUP (CloudSCRAPER) ===
        self.SESSION = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )

        self.HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Referer': f'https://www.{self.DOMAIN}/' if self.DOMAIN else '',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'DNT': '1' # Do Not Track
        }

    # === LOADER(S) ===
    def _load_config(self, config: str, key: str) -> dict:

        """
        Loads specific configuration from a given input.

        Fetches the required metadata for the specified site, including
        base URLs, sitemap locations, and the precise HTML selectors
        (tags, classes, or IDs) needed for product data extraction.
        """

        try:

            with open(config, encoding="utf-8") as f:
                CONFIGS = json.load(f)

            BALISES = CONFIGS.get(key)

            if not BALISES:
                raise KeyError(f"Key value '{key}' not in websites.json")

            return BALISES

        except Exception as e:
            LOG.error(f"An error occurred during READ: {e}")
            return {}
    
    # === INITIALIZER(S) ===
    def _init_schema(self, path: str, name: str) -> None:

        """
        Initializes the SQLite database schema for the target website.

        Connects to the site-specific database file (creating it if necessary) 
        and sets up the 'sitemap_urls' table. This table is used to track 
        discovered product URLs, their discovery timestamps, and their active 
        status, along with the necessary indices for query optimization.
        """

        with sqlite3.connect(os.path.join(path, f"{name}_sitemaps.db")) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sitemap_urls (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_key    TEXT NOT NULL,
                    url         TEXT NOT NULL,
                    first_seen  TEXT NOT NULL,
                    last_seen   TEXT NOT NULL,
                    is_active   INTEGER NOT NULL DEFAULT 1,
                    UNIQUE(site_key, url)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_site_active ON sitemap_urls(site_key, is_active)")

    # === SITEMAP FETCHER(s) ===
    def _fetch_raw(self, url: str) -> str | None:
        
        """
        Downloads a sitemap (plain XML or .gz) and 
        returns decoded text, with retry.
        """

        attempt = 0
        while attempt < self.MAX_RETRIES:
            try:
                response = self.SESSION.get(url, headers=self.HEADERS, timeout=20)
                response.raise_for_status()
                time.sleep(self.REQUEST_DELAY)

                if url.endswith(".gz"):
                    return gzip.decompress(response.content).decode("utf-8")
                return response.text

            except Exception as e:
                attempt += 1
                LOG.error(f"[{self.WEBSITE}] Fetch failed ({attempt}/{self.MAX_RETRIES}) for {url}: {e}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY)

        LOG.warning(f"[{self.WEBSITE}] Giving up on {url} after {self.MAX_RETRIES} attempts.")
        return None

    def _resolve(self, url: str, seen: Set[str], depth: int = 0) -> List[str]:
        
        """
        Resolves a single sitemap URL into a flat list of product URLs.

        If the sitemap is itself an index (contains <sitemap> entries),
        recurses into each child sitemap. If it's a urlset (contains
        <url>/<loc> entries), returns those URLs directly.
        """

        if url in seen:
            return []
        seen.add(url)

        if depth > 5:
            LOG.warning(f"[{self.WEBSITE}] Max recursion depth reached at {url}, stopping.")
            return []

        raw = self._fetch_raw(url)
        if raw is None:
            return []

        soup = BeautifulSoup(raw, "lxml-xml")

        # Case 1: sitemap index -> contains <sitemap><loc>child</loc></sitemap>
        child_sitemaps = [loc.text.strip() for loc in soup.select("sitemap > loc")]
        if child_sitemaps:
            LOG.info(f"[{self.WEBSITE}] {url} is an index with {len(child_sitemaps)} child sitemap(s).")
            urls: List[str] = []
            for child in child_sitemaps:
                urls.extend(self._resolve(child, seen, depth + 1))
            return urls

        # Case 2: urlset -> contains <url><loc>product</loc></url>
        product_urls = [unquote(loc.text.strip()) for loc in soup.select("url > loc")]
        LOG.info(f"[{self.WEBSITE}] {url} is a urlset with {len(product_urls)} URL(s).")
        return product_urls

    def _get_all_urls(self) -> List[str]:
        
        """
        Returns the deduplicated, filtered list of product URLs for this site,
        resolving every configured entry point.
        """

        if not self.SITEMAPindex:
            LOG.warning(f"[{self.WEBSITE}] No entry_points configured.")
            return []

        seen_sitemaps: Set[str] = set()
        all_urls: List[str] = []

        for entry in self.SITEMAPindex:
            all_urls.extend(self._resolve(entry, seen_sitemaps))

        deduped = sorted(set(self._filter(u) for u in all_urls) - {None})
        LOG.info(f"[{self.WEBSITE}] {len(deduped)} unique product URL(s) found.")
        return deduped

    def _filter(self, url: str) -> str | None:
        
        """
        Excludes non-product URLs (images, lang variants, root pages...).
        """

        segments = [s for s in url.split("/") if s]

        if len(segments) < 2:
            return None
        if segments[1] not in (self.DOMAIN, f"www.{self.DOMAIN}"):
            return None
        if any(s.lower() in {lang.lower() for lang in self.EXCLUDE_SEGMENTS} for s in segments):
            return None
        if url.endswith(("/", ".jpg", ".jpeg", ".png", ".gif", ".pdf")):
            return None

        return url

    # === SITEMAP SAVER(S) ===
    def _sync(self, path: str, name: str, site_key: str, current_urls: list[str]) -> dict:
        
        """
        Reconciles freshly fetched URLs with what's stored.
        Returns a small report: counts of new / reactivated / deactivated URLs.
        """

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_set = set(current_urls)
        report = {"new": 0, "reactivated": 0, "deactivated": 0, "unchanged": 0}

        with sqlite3.connect(os.path.join(path, f"{name}_sitemaps.db")) as conn:
            conn.row_factory = sqlite3.Row

            existing = conn.execute(
                "SELECT url, is_active FROM sitemap_urls WHERE site_key = ?", (site_key,)
            ).fetchall()
            existing_map = {row["url"]: row["is_active"] for row in existing}

            # Upsert of URLs
            for url in current_set:
                if url not in existing_map:
                    conn.execute(
                        "INSERT INTO sitemap_urls (site_key, url, first_seen, last_seen, is_active) "
                        "VALUES (?, ?, ?, ?, 1)",
                        (site_key, url, now, now),
                    )
                    report["new"] += 1
                else:
                    if existing_map[url] == 0:
                        report["reactivated"] += 1
                    else:
                        report["unchanged"] += 1
                    conn.execute(
                        "UPDATE sitemap_urls SET last_seen = ?, is_active = 1 WHERE site_key = ? AND url = ?",
                        (now, site_key, url),
                    )

            # Disabling 'dead' URLs
            disappeared = set(existing_map.keys()) - current_set
            for url in disappeared:
                if existing_map[url] == 1:  # only count newly deactivated
                    report["deactivated"] += 1
                conn.execute(
                    "UPDATE sitemap_urls SET is_active = 0 WHERE site_key = ? AND url = ?",
                    (site_key, url),
                )

            conn.commit()

        return report

    def _get_active_urls(self, path: str, name: str, site_key: str) -> list[str]:
        
        """
        Returns currently active URLs for a site.
        """

        with sqlite3.connect(os.path.join(path, f"{name}_sitemaps.db")) as conn:
            rows = conn.execute(
                "SELECT url FROM sitemap_urls WHERE site_key = ? AND is_active = 1", (site_key,)
            ).fetchall()
        return [r[0] for r in rows]



    # === MAIN ===
    def run(self) -> dict | None:
        
        """
        Executes the full sitemap processing pipeline for the target website.

        This method orchestrates the complete workflow:
        1. Retrieves and resolves all sitemap URLs defined in the configuration.
        2. Filters the collected links based on domain and exclusion rules.
        3. Synchronizes the discovered URLs with the local SQLite database, 
           tracking discovery status and updates.

        Returns:
            dict: A report dictionary containing counts of 'new', 'reactivated', 
                  'deactivated', and 'unchanged' URLs if successful.
            None: If the operation fails or no URLs are retrieved.
        """

        LOG.info(f"SITEMAPengine process started for {self.WEBSITE}")

        try:
            urls = self._get_all_urls()

            if not urls:
                LOG.warning(f"⚠️ No URLs found for {self.WEBSITE}.")
                return None

            report = self._sync(
                path=self.DATABASE_PATH,
                name=self.WEBSITE,
                site_key=self.WEBSITE,
                current_urls=urls
            )
            
            LOG.info(f"✅ Operation Successful! {self.WEBSITE} : {report}")
            return report

        except Exception as e:
            LOG.error(f"❌ Error! {self.WEBSITE} : {e}")
            return None