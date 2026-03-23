# CORE/__AI/DATApreprocessing/lecot.py
import json
import os
import time

import logging

import cloudscraper
import html2text
import pandas as pd
import random

from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

from CORE.Services.setup import *
from CORE.Services.parser import ProductDataParser



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

class LECOTtuner:
    
    """
    Class to curate, clean, and prepare LECOT product data 
    for LLM Fine-tuning (training dataset generation).
    
    """
    
    def __init__(self, output_file: str, samples_correct: int = 1500, samples_neg: int = 500):
        
        """
        Initialize the tuner with source paths and sampling quotas.
        
        Args:
            output_file (str): Path to the final .jsonl dataset.
            samples_correct (int): Number of valid products to sample.
            samples_neg (int): Number of negative/error products to sample.
        
        """
        
        # === INTERNAL VARIABLE(S) ===
        self.SOURCES = [
            {"path": 'USER/DATA/LECOTproductsDB.csv', "count": samples_correct, "label": "CORRECT"},
            {"path": 'USER/DATA/LECOTproductsDBnot.csv', "count": samples_neg, "label": "NOT"}
        ]
        self.OUTPUT_FILE = output_file
        self.MAX_CHARS = 4096
        
        # === INTERNAL SERVICE(S) ===
        self.parser = ProductDataParser(brands_file_path=os.path.join(UTILS_FOLDER, 'brands.json'))

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
            'Referer': 'https://www.shop.lecot.be/',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'DNT': '1' # Do Not Track
        }

        self.html_parser = html2text.HTML2Text()
        self.html_parser.ignore_links = True
        self.html_parser.ignore_images = True
        self.html_parser.body_width = 0

    def clean_html(self, html_content: str, use_json: bool = True) -> str:
        
        """
        Cleans raw HTML into Markdown and optionally prepends a simplified JSON-LD block.
        
        Args:
            html_content (str): Raw HTML string from the response.
            use_json (bool): If True, extracts and includes a [DATA] block for the LLM.
        
        """
        
        if not html_content: return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        json_summary = ""
        if use_json:
            
            # Extract JSON-LD metadata for the "JSON mode" of training (with structured data in input)
            try:
                item = next((i for s in soup.find_all('script', type='application/ld+json') 
                             for i in ([json.loads(s.string)] if isinstance(json.loads(s.string), dict) 
                                       else (json.loads(s.string) if isinstance(json.loads(s.string), list) else [])) 
                             if isinstance(i, dict) and i.get("@type") == "Product"), {})
                
                if item.get('@type') == 'Product':
                    simplified = {
                        "ean": item.get('sku') or item.get('gtin13'),
                        "mpn": item.get('mpn') or item.get('sku'),
                        "p": item.get('offers', [{}])[0].get('price') if isinstance(item.get('offers'), list) else item.get('offers', {}).get('price'),
                        "brand": item.get('brand', {}).get('name') if isinstance(item.get('brand'), dict) else item.get('brand')
                    }
                    json_summary = f"[DATA]{json.dumps(simplified)}[/DATA]\n"
            except: pass

        # Remove non-essential HTML elements
        for tag in soup(['noscript', 'script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            tag.decompose()
        
        # Target the main content area
        main_node = soup.find('main') or soup.find('body')
        text_content = self.html_parser.handle(str(main_node)).strip()[:self.MAX_CHARS]
        return f"{json_summary}{text_content}"

    def process(self):
        
        """
        Main engine: loops through CSV sources, scrapes data, and generates the final JSONL dataset.
        
        """
        
        all_entries = []
        success_count = 0

        LOG.info(f"Starting LECOT Curation at {datetime.now().strftime('%H:%M:%S')}")

        for source in self.SOURCES:
            path, count, label = source["path"], source["count"], source["label"]
            if not os.path.exists(path):
                LOG.error(f"Source file missing: {path}")
                continue

            LOG.info(f"Loading Source {label}: {path}")
            df = pd.read_csv(path,
                             dtype={'EAN': str,
                                    'MPN': str,
                                    'Brand': str,
                                    'Article': str,
                                    'Base Price (HTVA)': float,
                                    'Base Price (TVA)': float,
                                    'ArticleURL': str,
                                    'Checked on': str
                                    },
                             encoding='utf-8-sig'
            )

            # Sample from rows containing valid URLs
            samples = df[df['ArticleURL'].notna()].sample(n=min(count, len(df)))

            for _, row in samples.iterrows():
                url = row['ArticleURL']
                # 50% chance to force "Raw Mode" (no JSON data in input) for model robustness
                force_raw_mode = random.random() < 0.50
                
                try:
                    response = self.requests.get(url, headers=self.REQUESTS_HEADERS)
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # 1. Détermination de val_p
                    if response.status_code != 200:
                        val_p = 0.0
                    else:
                        js_data = next((i for s in soup.find_all('script', type='application/ld+json') 
                                      for i in ([json.loads(s.string)] if isinstance(json.loads(s.string), dict) 
                                                else (json.loads(s.string) if isinstance(json.loads(s.string), list) else [])) 
                                      if isinstance(i, dict) and i.get("@type") == "Product"), {})

                        val_p = (lambda raw: self.parser.parse_price(str(raw)) if raw not in (None, "-", "") else 0.0)(
                            (e.get_text(strip=True) if (e := soup.find("p", class_="product-detail-price"))
                                else (
                                    (o[0].get("price") if isinstance(o := js_data.get("offers"), list) and o
                                    else (o.get("price") if isinstance(o, dict) else None))
                                ))
                        )

                    # 2. Calcul des prix finaux (SORTI DU ELSE)
                    final_htva = self.parser.format_price_for_excel(round(val_p / 1.21, 2))
                    final_ttc = self.parser.format_price_for_excel(val_p)

                    # Sécurité nan
                    if str(final_ttc) == 'nan':
                        final_ttc, final_htva = 0.0, 0.0

                    if label == "CORRECT":
                        is_invalid = (
                            val_p <= 0.0 or 
                            pd.isna(row.get('Article')) or 
                            str(row.get('Article')) == '-'
                        )
                        
                        if is_invalid:
                            LOG.error(f"Product no longer valid for 'CORRECT' section, skipping this one: {url}")
                            continue

                    # 3. Génération de l'entrée (SORTI DU ELSE)
                    markdown_input = self.clean_html(response.text, use_json=not force_raw_mode)

                    entry = {
                        "instruction": "Extraire EAN, MPN, Marque, Article, Prix HT et Prix TTC en JSON pour LECOT.",
                        "input": markdown_input,
                        "output": json.dumps({
                            "ean": str(row.get('EAN', '-')).strip('"') if pd.notna(row['EAN']) else "-",
                            "mpn": str(row.get('MPN', '-')).strip('"') if pd.notna(row['MPN']) else "-",
                            "produit": str(row.get('Article', '-')).strip('"') if pd.notna(row.get('Article')) else "-",
                            "prix_ht": final_htva,
                            "prix_ttc": final_ttc
                        }, ensure_ascii=False)
                    }
                    
                    all_entries.append(entry)
                    success_count += 1
                    
                    mode_label = "BRUT (Expert)" if force_raw_mode else "JSON (Normal)"
                    LOG.info(f"[{success_count}/{len(samples)}] {mode_label} OK | {final_htva}€ HT / {final_ttc}€ TTC | {url}...")
                    
                    time.sleep(random.uniform(2, 4))

                except Exception as e:
                    LOG.exception(f"[ERR] {url}: {e}")

        # Finalize dataset
        if all_entries:
            # Shuffle mixed sources (Correct + Neg) for better training performance
            random.shuffle(all_entries)
            
            out_path = Path(self.OUTPUT_FILE)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file (Overwrite mode 'w')
            with out_path.open('w', encoding='utf-8') as f:
                for item in all_entries:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
            LOG.info(f"Dataset generated: {len(all_entries)} entries in {self.OUTPUT_FILE}")