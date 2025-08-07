import re
import requests
import time
import random
import pandas as pd
import sys
import os

from datetime import datetime

from typing import Optional

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from UTILS.LOGmaker import logger
from UTILS.NAMEformatter import *

from UTILS.EXCELreader import EXCELreader
from UTILS.WEBsearch import WEBsearch

# ====================
#     LOGGER SETUP
# ====================
Logger = logger("UTILS")


KNOWN_BRANDS = [
    "3M", "ABB", "Bosch", "Contimac", "Cembre", "Dewalt", "Eaton", "Facom",
    "Festool", "Fluke", "Hager", "HellermannTyton", "Hikoki", "Karcher",
    "Klauke", "Knipex", "Kraftwerk", "Legrand", "Makita", "Meno", "Milwaukee",
    "Petzl", "Phoenix Contact", "Rothenberger", "Schneider", "Siemens",
    "Solid", "Soudal", "Weidmüller", "Wago"
]

BLACKLIST_TERMS = ["ral", "color", "silirub", "silicone", "acrylique", "cartouche", "colle"]


def resource_path(relative_path):
    """
    Obtenir le chemin absolu vers une ressource, fonctionnant dans
    un environnement normal ou dans un exécutable PyInstaller.
    """
    try:
        # PyInstaller crée un dossier temporaire _MEIPASS où il extrait les fichiers
        base_path = sys._MEIPASS
    except AttributeError:
        # Sinon on est en environnement de dev
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def parse_price(text: str | None) -> float | None:
    if not text:
        return None

    # Supprime symboles monétaires, libellés inutiles, et espaces spéciaux
    clean = (
        text.replace('€', '')
            .replace('HTVA', '')
            .replace('TTC', '')
            .replace('\xa0', '')
            .replace('\u200e', '')
            .strip()
    )

    # Supprime tous les caractères non numériques sauf , et .
    clean = re.sub(r"[^\d,\.]", "", clean)

    # Si le prix est en format européen : "1.003,09"
    if ',' in clean and clean.count('.') >= 1:
        # On suppose que . est un séparateur de milliers
        clean = clean.replace('.', '').replace(',', '.')
    elif ',' in clean:
        # Si uniquement une virgule, c'est probablement un séparateur décimal
        clean = clean.replace(',', '.')

    try:
        return float(clean)
    except ValueError:
        return None
    
def calculate_missing_price(htva: float | None, tva: float | None, tva_rate: float = 0.21) -> tuple[float | None, float | None]:
    """
    Calcule le prix manquant (HTVA ou TVA) si l'autre est présent.
    """
    if htva is not None and tva is None:
        tva = htva * (1 + tva_rate)
    elif tva is not None and htva is None:
        htva = tva / (1 + tva_rate)
    return htva, tva
    
def format_price_for_excel(price: float | None) -> str:
    return f"{price:.2f}".replace('.', ',') if price is not None else ""

def accept_cookies(driver, site_name):
    cookie_buttons = {
        "fixami": "ac",
        "klium": "CybotCookiebotDialogBodyButtonAccept"
    }

    button_id = cookie_buttons.get(site_name.lower())

    if not button_id:
        Logger.info(f"[{site_name}] Aucun bouton de cookie défini.")
        return

    try:
        accept_button = driver.find_element(By.ID, button_id)
        if accept_button.is_displayed():
            accept_button.click()
            Logger.info(f"Cookies acceptés pour {site_name}: {driver.current_url}.")
            time.sleep(5)
    except Exception:
        Logger.info(f"Pas de cookies à accepter ou déjà acceptés pour {site_name}: {driver.current_url}.")

def extract_offers_FIXAMI(soup: BeautifulSoup) -> Optional[str]:
    offers = []

    for offer_block in soup.select("div.sc-cd80083d-1"):
        quantity_label = offer_block.select_one("label.sc-cd80083d-2")
        price_label = offer_block.select_one("label.sc-cd80083d-4")
        discount_label = offer_block.select_one("label.sc-cd80083d-5")

        if quantity_label and price_label:
            quantity_text = quantity_label.get_text(strip=True)
            price_text = price_label.get_text(strip=True).replace(',', '.')

            try:
                price = float(price_text)
            except ValueError:
                continue

            discount_text = f" ({discount_label.get_text(strip=True)})" if discount_label else ""
            offers.append(f"{quantity_text}: {price:.2f}€{discount_text}")

    return "\n".join(offers) if offers else "-"

def extract_offers_KLIUM(soup: BeautifulSoup) -> Optional[str]:
    offers = []

    # Sélectionne tous les blocs d'offres
    for offer_div in soup.select("div.prod_discount_btn"):
        label = offer_div.find("label", class_="prod_discount_label")
        if not label:
            continue
        
        quantity_span = label.select_one("span.label-discount-text")
        price_span = label.select_one("span.label-discount-price")
        discount_span = label.select_one("span.label-discount.discounted-price")

        if quantity_span and price_span:
            quantity_text = quantity_span.get_text(strip=True)
            price_text = price_span.get_text(strip=True).replace('\xa0', '').replace(',', '.').replace('€', '')
            try:
                price = float(price_text)
            except ValueError:
                continue

            discount_text = f" ({discount_span.get_text(strip=True)})" if discount_span else ""
            offers.append(f"{quantity_text}: {price:.2f}€{discount_text}")

    return "\n".join(offers) if offers else "-"


def is_probable_brand(word: str) -> bool:
    """
    Heuristique simple : mot non blacklisté, majuscule initiale, longueur correcte.
    """
    return (
        word.lower() not in BLACKLIST_TERMS
        and word[0].isupper()
        and len(word) > 2
    )

def extract_brand(product_name: str) -> str | None:
    """
    Détecte une marque connue dans le nom du produit.
    """
    for brand in KNOWN_BRANDS:
        if brand.lower() in product_name.lower():
            return brand.upper()
    return None

def extract_brand_from_all_sources(product_name: str, html: str | None = None) -> str | None:
    """
    Tente de détecter la marque depuis le HTML (balise .fabricant), sinon depuis le nom du produit.
    """
    if html:
        soup = BeautifulSoup(html, "html.parser")
        fabricant_tag = soup.find("div", class_="fabricant")
        if fabricant_tag:
            text = fabricant_tag.get_text(strip=True)
            for brand in KNOWN_BRANDS:
                if brand.lower() in text.lower():
                    return brand.upper()
            # Si non trouvé dans la liste, on retourne quand même le texte
            #return text.upper()

    return extract_brand(product_name)

def clean_product_name(product_name: str) -> str:
    """
    Nettoie les éléments inutiles dans le nom (quantité, taille, parenthèses...).
    """
    name = product_name.strip()

    # Supprime le contenu entre parenthèses
    name = re.sub(r'\(.*?\)', '', name)

    # Supprime les RAL/codes couleur (RAL 5011, RAL5011)
    name = re.sub(r'\bRAL\s?-?\d{4}\b', '', name, flags=re.IGNORECASE)

    # Supprime les références types : EAN, REF, etc.
    name = re.sub(r'\b(Ref|Réf|EAN|CIPAC|Code)[\.:]?\s?\w+\b', '', name, flags=re.IGNORECASE)

    # Supprime les tailles / unités
    name = re.sub(r'\b\d+\s?(pcs|pièces|x|unités?|mm|cm|m|ml|g|kg)\b', '', name, flags=re.IGNORECASE)

    # Normalisation des séparateurs
    name = re.sub(r'[-_/|]+', ' ', name)
    name = re.sub(r'\s+', ' ', name)

    return name.strip()

import re

def extract_cipac_ref(soup):
    p_ref = soup.find('p', class_='ref')
    if p_ref:
        text = p_ref.get_text(separator=' ').strip()  # on remplace les <br> par des espaces
        # Regex pour récupérer la valeur après "Réf. :"
        match = re.search(r'Réf\. :\s*(\S+)', text)
        if match:
            return match.group(1)
    return None

def extract_clabots_ref(soup):
    rows = soup.select('div.attribute-table__row')
    for row in rows:
        label = row.select_one('div.attribute-table__column__label')
        value = row.select_one('div.attribute-table__column__value')
        if label and value:
            if label.get_text(strip=True) == "Code article du fournisseur":
                return value.get_text(strip=True)
    return None

def extract_fixami_ref(soup):
    dt = soup.find('dt', string=lambda x: x and "Code du modèle" in x)
    if dt:
        dd = dt.find_next_sibling('dd')
        if dd:
            p = dd.find('p', attrs={'type': 'BODY_BOLD'})
            if p:
                return p.get_text(strip=True)
    return None

def extract_klium_ref(soup):
    supplier_ref_li = soup.find('li', id='supplier_reference_value')
    if supplier_ref_li:
        span = supplier_ref_li.find('span')
        if span:
            span.extract()  # enlève le span
        
        ref_text = supplier_ref_li.get_text(strip=True)

        # Supprimer la marque si elle est en début de chaîne (insensible à la casse)
        for brand in KNOWN_BRANDS:
            if ref_text.lower().startswith(brand.lower() + ' '):
                # Enlever la marque + espace
                ref_text = ref_text[len(brand)+1:]
                break
        
        return ref_text
    return None

def extract_product_name(product_name: str) -> str:
    """
    Extrait le nom du produit en supprimant la marque détectée.
    """
    brand = extract_brand(product_name)
    cleaned = clean_product_name(product_name)

    if brand:
        # Supprime la marque du nom s'il y a correspondance
        pattern = re.compile(re.escape(brand), re.IGNORECASE)
        cleaned = pattern.sub('', cleaned).strip()

    return cleaned.title()

def standardize_name(product_name: str, html: str | None = None) -> str:
    """
    Renvoie le nom standardisé du produit : 'Marque - Nom Produit'.
    Utilise le HTML si fourni pour détecter plus intelligemment la marque.
    """
    brand = extract_brand_from_all_sources(product_name, html)
    model = extract_product_name(product_name)

    if brand:
        return f"{brand} - {model.upper()}"
    return model.upper()