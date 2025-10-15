# APP/SERVICES/CacheService.py
import os
from datetime import datetime, timedelta
import pandas as pd

class CacheService:
    """
    Service for safely loading and checking cache CSV files for product data.
    """

    DEFAULT_COLUMNS = [
        'MPN','Société','Article','ArticleURL','Marque',
        'Prix (HTVA)','Prix (TVA)','Ancien Prix (HTVA)',
        'Evolution du prix','Offres','Stock','Checked on'
    ]

    def __init__(self, cache_duration_days: int = 3):
        """
        Args:
            cache_duration_days (int): Durée de validité du cache en jours (par défaut 3)
        """
        self.cache_duration_days = cache_duration_days

    def load_cache(self, path: str) -> pd.DataFrame:
        """
        Charge un fichier CSV de cache en toute sécurité.

        Si le fichier n'existe pas ou échoue à charger, retourne un DataFrame vide
        avec les colonnes par défaut.
        """
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, encoding='utf-8-sig')
                missing_cols = set(self.DEFAULT_COLUMNS) - set(df.columns)
                for col in missing_cols:
                    df[col] = None
                return df[self.DEFAULT_COLUMNS]
            except Exception as e:
                print(f"⚠️ Error loading cache '{path}': {e}")
                return pd.DataFrame(columns=self.DEFAULT_COLUMNS)
        else:
            return pd.DataFrame(columns=self.DEFAULT_COLUMNS)

    def check_cache(self, cache_df: pd.DataFrame, MPN: str) -> dict | None:
        """
        Vérifie si un MPN existe dans le cache et si le cache est encore valide.

        Args:
            cache_df (pd.DataFrame): DataFrame de cache
            MPN (str): Référence produit à vérifier

        Returns:
            dict | None: Ligne du cache si valide, sinon None
        """

        if cache_df.empty or 'MPN' not in cache_df.columns:
            return None

        row = cache_df[cache_df['MPN'] == MPN]
        if row.empty:
            return None

        row_dict = row.iloc[0].to_dict()
        checked_on_str = row_dict.get("Checked on")

        try:
            last_checked = pd.to_datetime(checked_on_str)
            if datetime.now() - last_checked <= timedelta(days=self.cache_duration_days):
                return row_dict
        except Exception:
            return None

        return None