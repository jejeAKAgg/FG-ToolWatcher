# CORE/Database/DBindexer.py
import os
import sqlite3

import logging

import pandas as pd

from collections import Counter
from pathlib import Path
from typing import Optional

from CORE.Services.setup import *



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

class DBIndexer:

    """
    Merges all supplier databases into a single unified MASTERproductsDB.csv.

    Workflow:
        1. load()    — Import source CSVs and aggregate EAN "votes" per MPN.
        2. resolve() — Resolve conflicts using a majority voting logic.
        3. build()   — Construct the unified MASTERproductsDB including a 'Company' column.
        4. export()  — Save the final MASTERproductsDB.csv to disk.

    Note: Source CSV files are NEVER modified; the MASTERproductsDB is generated as a separate file.

    """

    def __init__(self, db_paths: list[str], output_dir: str):

        # === INTERNAL VARIABLE(S)
        self.VALID_EAN_LENGTHS = {8, 13}
        self.FILENAME_TO_SOCIETE = {
            "CLABOTSproductsDB": "CLABOTS",
            "FIXAMIproductsDB": "FIXAMI",
            "LECOTproductsDB": "LECOT",
            "KLIUMproductsDB": "KLIUM",
            "TOOLNATIONproductsDB": "TOOLNATION",
            "GEORGESproductsDB": "GEORGES"
        }
        self.MASTER_COLUMNS = [
            "Company", "EAN", "MPN",
            "Brand", "Article",
            "Base Price (HTVA)", "Base Price (TVA)",
            "ArticleURL", "Checked on"
        ]
        self.REVIEW_COLUMNS = [
            "Type",
            "Société", "Article",
            "MPN", "EAN",
            "ArticleURL",
            "Details",
            "MPN_correction", "EAN_correction", "Resolved"
        ]

        self.MPN_VOTES: dict[str, list[str]] = {}
        self.MPN_ARTICLES: dict[str, set[str]] = {}
        self.MPN_TO_EAN: dict[str, Optional[str]] = {}
        self.EAN_TO_MPN: dict[str, Optional[str]] = {}

        self.DATAFRAMES: dict[str, pd.DataFrame] = {}
        self.REVIEW_ITEMS: list[dict] = []  # Conflicts + unidentifiable

        # === INTERNAL PARAMETER(S) ===
        self.DB_PATHS   = [Path(p) for p in db_paths]
        self.OUTPUT_DIR = Path(output_dir)


    def load(self) -> None:

        """
        Loads source CSV files and aggregates EAN "votes" per MPN.

        A 'Company' column is added to the dataset, derived from the
        respective source filename.

        """

        for PATH in self.DB_PATHS:

            try:
                DB = pd.read_csv(PATH, dtype=str, encoding="utf-8-sig")
            except Exception as e:
                LOG.exception(f"A READ error occured {PATH.name} : {e}")
                continue

            self.NAME = self.FILENAME_TO_SOCIETE.get(PATH.stem, "UNKNOWN").upper()

            DB["Company"] = self.NAME
            self.DATAFRAMES[self.NAME] = DB

            if "MPN" not in DB.columns or "EAN" not in DB.columns:
                LOG.warning(f"MPN/EAN columns missing in {PATH.name}")
                continue

            for _, row in DB.iterrows():
                mpn = self._normalize_mpn(row["MPN"])
                ean = self._normalize_ean(row["EAN"])

                if self._is_placeholder(mpn) or ean is None:
                    continue

                if mpn not in self.MPN_VOTES:
                    self.MPN_VOTES[mpn] = []
                    self.MPN_ARTICLES[mpn] = set()
                self.MPN_VOTES[mpn].append(ean)
                article = str(row.get("Article", "")).strip()
                if article:
                    self.MPN_ARTICLES[mpn].add(article)

        LOG.info(f"Collected {len(self.MPN_VOTES)} distinct MPNs from {len(self.DATAFRAMES)} sources.")

    def resolve(self) -> None:

        """
        Resolves the winning EAN for each MPN using a majority voting logic.

        Resolution Rules:
            - Single source          → Direct trust/assignment.
            - 2+ sources, agreement  → Unanimity confirmed.
            - 2+ sources, agreement  → Simple majority wins.
            - Perfect tie            → Unresolved conflict; exported to CONFLICTS.csv.

        """

        unanime = majority = unresolved = 0

        for mpn, ean_list in self.MPN_VOTES.items():
            counter = Counter(ean_list)
            top_ean, top_count = counter.most_common(1)[0]
            total_votes = len(ean_list)

            if len(counter) == 1:
                unanime+=1

                self.MPN_TO_EAN[mpn] = top_ean
                self.EAN_TO_MPN[top_ean] = mpn

            elif top_count > total_votes / 2:
                majority+=1

                self.MPN_TO_EAN[mpn] = top_ean
                self.EAN_TO_MPN[top_ean] = mpn

                LOG.debug(f"Majority — MPN={mpn} → EAN={top_ean} ({top_count}/{total_votes}) | losers={dict(counter)}")

            else:
                unresolved += 1

                self.MPN_TO_EAN[mpn] = None
                self.REVIEW_ITEMS.append({
                    "Type":            "CONFLICT",
                    "Société":         "-",
                    "Article":         " | ".join(sorted(self.MPN_ARTICLES.get(mpn, set()))),
                    "MPN":             mpn,
                    "EAN":             "-",
                    "ArticleURL":      "-",
                    "Details":         f"votes={str(dict(counter))}",
                    "MPN_correction":  "",
                    "EAN_correction":  "",
                    "Resolved":        "0",
                })

                LOG.warning(f"Unresolved conflict — MPN={mpn} | votes={dict(counter)}")

        LOG.info(f"Resolution — unanimous: {unanime} | majority: {majority} | unresolved: {unresolved}")

        # REVIEW_ITEMS export is handled by export_review() in run()

    def build(self) -> pd.DataFrame:

        """
        Merges all DataFrames and applies the resolved EAN/MPN mappings.

        Each record retains its original 'Company' column to ensure
        traceability across the unified dataset.

        """

        frames = []

        for societe, df in self.DATAFRAMES.items():

            # Assuring the default columns are there
            for col in self.MASTER_COLUMNS:
                if col not in df.columns:
                    df[col] = "-"

            df = df[self.MASTER_COLUMNS].copy()

            for idx, row in df.iterrows():
                mpn = self._normalize_mpn(row["MPN"])
                ean = self._normalize_ean(row["EAN"])

                if not self._is_placeholder(mpn):
                    df.at[idx, "MPN"] = mpn

                    resolved_ean = self.MPN_TO_EAN.get(mpn)
                    if resolved_ean and resolved_ean != ean:
                        df.at[idx, "EAN"] = resolved_ean

                if ean and self._is_placeholder(row["MPN"]):
                    resolved_mpn = self.EAN_TO_MPN.get(ean)
                    if resolved_mpn:
                        df.at[idx, "MPN"] = resolved_mpn

            frames.append(df)

            LOG.debug(f"{societe} — {len(df)} lines integrated.")

        if not frames:
            LOG.warning("No data to merge.")
            return pd.DataFrame(columns=self.MASTER_COLUMNS)

        master = pd.concat(frames, ignore_index=True)
        master.sort_values(by="Company", ascending=True, inplace=True, ignore_index=True)

        LOG.info(f"MASTERproductsDB built — {len(master)} total lines.")
        return master

    def export(self, master: pd.DataFrame) -> Path:

        """
        Saves the MASTER_DB to the designated output folder.

        """

        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        master.to_csv(os.path.join(self.OUTPUT_DIR, "MASTERproductsDB.csv"), index=False, encoding="utf-8-sig")

        LOG.info(f"MASTERproductsDB exported → {os.path.join(self.OUTPUT_DIR, "MASTERproductsDB.csv")} ({len(master)} lines).")
        return os.path.join(self.OUTPUT_DIR, "MASTERproductsDB.csv")


    # === Private Function(s) ===
    def _normalize_ean(self, raw) -> Optional[str]:
        s = str(raw).strip().split(".")[0]
        if s.lower() in {"-", "", "nan", "none", "null", "0"}:
            return None
        if len(s) not in self.VALID_EAN_LENGTHS:
            return None
        return s

    def _is_placeholder(self, value) -> bool:
        return str(value).strip().lower() in {"-", "", "nan", "none", "null", "0"}

    def _normalize_mpn(self, raw) -> str:
        return str(raw).strip().upper()

    def collect_unidentifiable(self) -> None:

        """
        Collects articles with neither EAN nor MPN — cannot be cross-referenced.
        Stored in REVIEW_ITEMS with Type="UNIDENT" for human intervention.

        """

        count = 0
        for societe, df in self.DATAFRAMES.items():
            for _, row in df.iterrows():
                mpn     = self._normalize_mpn(row.get("MPN", "-"))
                ean     = self._normalize_ean(row.get("EAN", "-"))
                article = str(row.get("Article", "")).strip()

                if self._is_placeholder(mpn) and ean is None and article:
                    self.REVIEW_ITEMS.append({
                        "Type":           "UNIDENT",
                        "Société":        societe,
                        "Article":        article,
                        "MPN":            "-",
                        "EAN":            "-",
                        "ArticleURL":     str(row.get("ArticleURL", "-")),
                        "Details":        "No EAN or MPN found",
                        "MPN_correction": "",
                        "EAN_correction": "",
                        "Resolved":       "0",
                    })
                    count += 1

        LOG.info(f"{count} unidentifiable articles collected.")

    def export_review(self) -> str:

        """
        Exports REVIEW_ITEMS (conflicts + unidentifiable + fuzzy) to
        REVIEWproductsDB.csv and REVIEWproductsDB.db.

        The .db allows the future GUI correction page to:
          - Display items needing human review
          - Accept MPN_correction / EAN_correction input
          - Mark items as Resolved=1
          - Re-trigger indexing

        """

        if not self.REVIEW_ITEMS:
            LOG.info("No review items to export.")
            return ""

        df = pd.DataFrame(self.REVIEW_ITEMS)

        # Ensure all columns exist
        for col in self.REVIEW_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df = df[self.REVIEW_COLUMNS]

        # CSV export
        csv_path = os.path.join(self.OUTPUT_DIR, "REVIEWproductsDB.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")

        # SQLite export
        db_path = os.path.join(self.OUTPUT_DIR, "REVIEWproductsDB.db")
        try:
            conn = sqlite3.connect(db_path)
            df.to_sql("review", conn, if_exists="replace", index=True, index_label="id")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_type     ON review (Type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_resolved ON review (Resolved)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mpn      ON review (MPN)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ean      ON review (EAN)")
            conn.commit()
            conn.close()
        except Exception as e:
            LOG.exception(f"SQLite review export error : {e}")

        conflicts = sum(1 for r in self.REVIEW_ITEMS if r["Type"] == "CONFLICT")
        unidents  = sum(1 for r in self.REVIEW_ITEMS if r["Type"] == "UNIDENT")

        LOG.info(
            f"REVIEWproductsDB exported — "
            f"conflicts: {conflicts} | unidentifiable: {unidents} | "
            f"total: {len(self.REVIEW_ITEMS)}"
        )

        return csv_path

    def export_sqlite(self, master: pd.DataFrame) -> str:

        """
        Exports the MASTER_DB to a SQLite database with indexes on
        Article, EAN and MPN for fast lookups from SearchPage.

        Called automatically after export() in run().

        """

        db_path = os.path.join(self.OUTPUT_DIR, "MASTERproductsDB.db")

        try:
            conn = sqlite3.connect(db_path)

            # Write DataFrame to SQLite
            master.to_sql("products", conn, if_exists="replace", index=False)

            # Create indexes for fast search
            conn.execute("CREATE INDEX IF NOT EXISTS idx_article ON products (Article)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ean     ON products (EAN)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mpn     ON products (MPN)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_company ON products (Company)")

            conn.commit()
            conn.close()

            LOG.info(f"MASTERproductsDB.db exported → {db_path} ({len(master)} lines).")

        except Exception as e:
            LOG.exception(f"SQLite export error : {e}")

        return db_path

    # === RUN ===
    def run(self) -> Optional[Path]:
        LOG.info("Starting...")

        self.load()
        self.resolve()
        self.collect_unidentifiable()

        master = self.build()
        path = self.export(master)
        self.export_sqlite(master)
        self.export_review()

        LOG.info("Finished.")
        return path


# ================================================================
#   STANDALONE
# ================================================================

if __name__ == "__main__":

    indexer = DBIndexer(
        db_paths=[
            os.path.join(DATA_SUBFOLDER_SOURCE, "CLABOTSproductsDB.csv"),
            os.path.join(DATA_SUBFOLDER_SOURCE, "LECOTproductsDB.csv"),
            os.path.join(DATA_SUBFOLDER_SOURCE, "FIXAMIproductsDB.csv"),
            os.path.join(DATA_SUBFOLDER_SOURCE, "KLIUMproductsDB.csv"),
            os.path.join(DATA_SUBFOLDER_SOURCE, "TOOLNATIONproductsDB.csv"),
        ],
        output_dir=DATA_SUBFOLDER
    )

    indexer.run()
