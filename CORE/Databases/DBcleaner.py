# CORE/__DATABASES/DBcleaner.py
import os
import logging
import pandas as pd

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional


LOG = logging.getLogger(__name__)


# ================================================================
#   CONSTANTS
# ================================================================

VALID_EAN_LENGTHS  = {8, 13}
PLACEHOLDER_VALUES = {"-", "", "nan", "none", "null", "0"}

MASTER_COLUMNS = [
    "Société", "EAN", "MPN", "Brand", "Article",
    "Base Price (HTVA)", "Base Price (TVA)",
    "ArticleURL", "Checked on"
]


# ================================================================
#   HELPERS
# ================================================================

def _normalize_mpn(raw) -> str:
    return str(raw).strip().upper()


def _normalize_ean(raw) -> Optional[str]:
    s = str(raw).strip().split(".")[0]
    if s.lower() in PLACEHOLDER_VALUES:
        return None
    if len(s) not in VALID_EAN_LENGTHS:
        return None
    return s


def _is_placeholder(value) -> bool:
    return str(value).strip().lower() in PLACEHOLDER_VALUES


# ================================================================
#   PRODUCT INDEXER
# ================================================================

class ProductIndexer:

    """
    Fusionne toutes les DB fournisseurs en une seule MASTER_DB.csv.

    Workflow :
        1. load()    — charge les CSV sources et collecte les votes EAN par MPN
        2. resolve() — tranche les conflits par vote majoritaire
        3. build()   — construit la MASTER_DB unifiée avec colonne Société
        4. export()  — sauvegarde MASTER_DB.csv

    Les CSV sources ne sont JAMAIS modifiés — la MASTER_DB est un fichier séparé.
    """

    def __init__(self, db_paths: list[str], output_dir: str):
        self.db_paths   = [Path(p) for p in db_paths]
        self.output_dir = Path(output_dir)
        self.mpn_votes: dict[str, list[str]] = {}
        self.mpn_articles: dict[str, set[str]] = {}  # MPN → noms d'articles vus
        self.mpn_to_ean: dict[str, Optional[str]] = {}
        self.ean_to_mpn: dict[str, Optional[str]] = {}
        self.dataframes: dict[str, pd.DataFrame] = {}
        self.unresolved: list[dict] = []



    # ────────────────────────────────────────────
    #   STEP 1 — CHARGEMENT
    # ────────────────────────────────────────────

    def load(self) -> None:
        """
        Charge les CSV sources et collecte les votes EAN par MPN.
        Ajoute une colonne Société déduite du nom du fichier.
        """

        for original_path in self.db_paths:
            try:
                df = pd.read_csv(original_path, dtype=str, encoding="utf-8-sig")
            except Exception as e:
                LOG.exception(f"[Indexer] Erreur lecture {original_path.name} : {e}")
                continue

            # Déduit le nom de la société depuis le nom de fichier
            # ex: CLABOTSproductsDB.csv → CLABOTS
            societe = original_path.stem.replace("productsDB", "").replace("ProductsDB", "").upper()
            df["Société"] = societe
            self.dataframes[societe] = df

            if "MPN" not in df.columns or "EAN" not in df.columns:
                LOG.warning(f"[Indexer] Colonnes MPN/EAN absentes dans {original_path.name}")
                continue

            for _, row in df.iterrows():
                mpn = _normalize_mpn(row["MPN"])
                ean = _normalize_ean(row["EAN"])

                if _is_placeholder(mpn) or ean is None:
                    continue

                if mpn not in self.mpn_votes:
                    self.mpn_votes[mpn] = []
                    self.mpn_articles[mpn] = set()
                self.mpn_votes[mpn].append(ean)
                article = str(row.get("Article", "")).strip()
                if article:
                    self.mpn_articles[mpn].add(article)

        LOG.info(
            f"[Indexer] {len(self.mpn_votes)} MPN distincts collectés "
            f"depuis {len(self.dataframes)} sources."
        )


    # ────────────────────────────────────────────
    #   STEP 2 — RÉSOLUTION PAR VOTE
    # ────────────────────────────────────────────

    def resolve(self) -> None:
        """
        Pour chaque MPN, tranche l'EAN gagnant par vote majoritaire.

        Règles :
            - 1 seule source          → confiance directe
            - 2+ sources, accord      → unanimité
            - 2+ sources, désaccord   → majorité simple gagne
            - Égalité parfaite        → conflit non résolu, exporté dans CONFLICTS.csv
        """

        unanime = majority = unresolved = 0

        for mpn, ean_list in self.mpn_votes.items():
            counter = Counter(ean_list)
            top_ean, top_count = counter.most_common(1)[0]
            total_votes = len(ean_list)

            if len(counter) == 1:
                self.mpn_to_ean[mpn] = top_ean
                self.ean_to_mpn[top_ean] = mpn
                unanime += 1

            elif top_count > total_votes / 2:
                self.mpn_to_ean[mpn] = top_ean
                self.ean_to_mpn[top_ean] = mpn
                majority += 1
                LOG.debug(
                    f"[Indexer] Majorité — MPN={mpn} → EAN={top_ean} "
                    f"({top_count}/{total_votes}) | perdants={dict(counter)}"
                )

            else:
                self.mpn_to_ean[mpn] = None
                articles = " | ".join(sorted(self.mpn_articles.get(mpn, set())))
                self.unresolved.append({"MPN": mpn, "Article(s)": articles, "votes": str(dict(counter))})
                unresolved += 1
                LOG.warning(f"[Indexer] Conflit non résolu — MPN={mpn} | votes={dict(counter)}")

        LOG.info(
            f"[Indexer] Résolution — "
            f"unanime: {unanime} | majorité: {majority} | non résolu: {unresolved}"
        )

        if self.unresolved:
            conflicts_path = self.output_dir / "CONFLICTS.csv"
            pd.DataFrame(self.unresolved).to_csv(conflicts_path, index=False, encoding="utf-8-sig")
            LOG.info(f"[Indexer] {len(self.unresolved)} conflits exportés → {conflicts_path}")


    # ────────────────────────────────────────────
    #   STEP 3 — CONSTRUCTION DE LA MASTER DB
    # ────────────────────────────────────────────

    def build(self) -> pd.DataFrame:
        """
        Fusionne tous les DataFrames et applique les EAN/MPN résolus.
        Chaque ligne conserve sa colonne Société d'origine.
        """

        frames = []

        for societe, df in self.dataframes.items():

            # Assure que toutes les colonnes standard existent
            for col in MASTER_COLUMNS:
                if col not in df.columns:
                    df[col] = "-"

            df = df[MASTER_COLUMNS].copy()

            for idx, row in df.iterrows():
                mpn = _normalize_mpn(row["MPN"])
                ean = _normalize_ean(row["EAN"])

                if not _is_placeholder(mpn):
                    df.at[idx, "MPN"] = mpn

                    resolved_ean = self.mpn_to_ean.get(mpn)
                    if resolved_ean and resolved_ean != ean:
                        df.at[idx, "EAN"] = resolved_ean

                if ean and _is_placeholder(row["MPN"]):
                    resolved_mpn = self.ean_to_mpn.get(ean)
                    if resolved_mpn:
                        df.at[idx, "MPN"] = resolved_mpn

            frames.append(df)
            LOG.debug(f"[Indexer] {societe} — {len(df)} lignes intégrées.")

        if not frames:
            LOG.warning("[Indexer] Aucune donnée à fusionner.")
            return pd.DataFrame(columns=MASTER_COLUMNS)

        master = pd.concat(frames, ignore_index=True)
        master.sort_values(by="Société", ascending=True, inplace=True, ignore_index=True)
        LOG.info(f"[Indexer] MASTER_DB construite — {len(master)} lignes au total.")
        return master


    # ────────────────────────────────────────────
    #   STEP 4 — EXPORT
    # ────────────────────────────────────────────

    def export(self, master: pd.DataFrame) -> Path:
        """Sauvegarde la MASTER_DB dans le dossier de sortie."""

        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / "MASTERproductsDB.csv"
        master.to_csv(path, index=False, encoding="utf-8-sig")
        LOG.info(f"[Indexer] MASTER_DB exportée → {path} ({len(master)} lignes)")
        return path


    # ────────────────────────────────────────────
    #   ENTRY POINT
    # ────────────────────────────────────────────

    def run(self) -> Optional[Path]:
        LOG.info("[Indexer] Démarrage...")
        self.load()
        self.resolve()
        master = self.build()
        path = self.export(master)
        LOG.info("[Indexer] Terminé.")
        return path


# ================================================================
#   STANDALONE
# ================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    DB_SOURCES = "USER/DATA/backup"
    DB_OUTPUT  = "USER/DATA"

    indexer = ProductIndexer(
        db_paths=[
            os.path.join(DB_SOURCES, "CLABOTSproductsDB.csv"),
            os.path.join(DB_SOURCES, "LECOTproductsDB.csv"),
            os.path.join(DB_SOURCES, "FIXAMIproductsDB.csv"),
            os.path.join(DB_SOURCES, "KLIUMproductsDB.csv"),
            os.path.join(DB_SOURCES, "TOOLNATIONproductsDB.csv"),
        ],
        output_dir=DB_OUTPUT
    )

    indexer.run()