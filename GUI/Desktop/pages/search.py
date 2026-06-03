# GUI/Desktop/pages/search.py
import logging
import sqlite3

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QPushButton, QCompleter, QListWidgetItem,
    QScrollArea, QFrame, QLabel
)
from PySide6.QtCore import Qt, QStringListModel

from CORE.Services.setup import *
from CORE.Services.user import UserService
from CORE.Services.translator import TranslatorService



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

class SearchPage(QWidget):
    def __init__(self, config: UserService, translator: TranslatorService, parent=None):
        super().__init__(parent)

        # === INTERNAL VARIABLE(S) ===
        self.SEARCH_FILTER_COMPANY = None  # None = search across all companies

        self.completer_model = QStringListModel(self)
        self._suggestion_map: dict[str, dict] = {} # For a confirmed complete search by name → result: complete dict {name, mpn, ean}
        self._search_index: dict[str, dict] = {} # For a confirmed complete search by EAN → result: complete dict {name, mpn, ean}
        self._db_conn: sqlite3.Connection | None = None

        # === INTERNAL PARAMETER(S) ===
        self.configs = config
        self.translator = translator


        # === MAIN LAYOUT — horizontal split ===
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── LEFT : catalogue list + search input ──
        left_widget = QWidget()
        main_layout = QVBoxLayout(left_widget)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- Article(s) list ---
        self.mpn_list = QListWidget()
        self.mpn_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #666;
                border-radius: 10px;
                background-color: #1e1e1e;
                color: white;
                font-size: 14px;
                padding: 10px;
            }
            QListWidget::item:selected {
                background-color: #0078d7;
            }
        """)
        main_layout.addWidget(self.mpn_list, stretch=1)

        # --- Input/Adding/Removing zone ---
        add_layout = QHBoxLayout()

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(self.translator.get("page_search_input.placeholder"))
        self.input_field.setStyleSheet("padding: 5px; font-size: 14px; border-radius: 5px;")
        add_layout.addWidget(self.input_field)

        self.add_button = QPushButton(self.translator.get("page_search_add.button"))
        self.add_button.clicked.connect(self._add_mpn)
        add_layout.addWidget(self.add_button)

        self.remove_button = QPushButton(self.translator.get("page_search_remove.button"))
        self.remove_button.clicked.connect(self._remove_mpn)
        add_layout.addWidget(self.remove_button)

        self.clear_button = QPushButton(self.translator.get("page_search_remove_all.button"))
        self.clear_button.setStyleSheet("color: #e74c3c;")
        self.clear_button.clicked.connect(self._clear_all)
        add_layout.addWidget(self.clear_button)

        main_layout.addLayout(add_layout)

        # --- Auto-completer module ---
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)

        self.input_field.textChanged.connect(self._update_completer)

        # ── RIGHT : quick access by brand ──
        right_widget = QWidget()
        right_widget.setFixedWidth(180)
        right_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 20, 0.6);
                border-left: 1px solid #444;
            }
        """)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 12, 8, 12)
        right_layout.setSpacing(6)

        brand_title = QLabel(self.translator.get("page_search_rapid_access.label"))
        brand_title.setStyleSheet("color: #aaa; font-size: 11px; font-weight: bold; letter-spacing: 1px; text-transform: uppercase;")
        brand_title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(brand_title)

        # Scrollable brand buttons
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._brand_container = QWidget()
        self._brand_container.setStyleSheet("background: transparent;")
        self._brand_layout = QVBoxLayout(self._brand_container)
        self._brand_layout.setSpacing(5)
        self._brand_layout.setContentsMargins(0, 0, 0, 0)
        self._brand_layout.addStretch()

        scroll.setWidget(self._brand_container)
        right_layout.addWidget(scroll, stretch=1)

        # Assemble
        root_layout.addWidget(left_widget, stretch=1)
        root_layout.addWidget(right_widget)

        self._init_db_connection()
        self._load_brand_buttons()
        self._refresh_list()


    # ====================================
    #             FUNCTIONS
    # ====================================

    def _init_db_connection(self):

        """
        Opens a persistent SQLite connection at startup.
        Reused for every query — avoids opening/closing on each keystroke.

        """

        db_path = os.path.join(DATA_SUBFOLDER, "MASTERproductsDB.db")
        if os.path.exists(db_path):
            self._db_conn = sqlite3.connect(db_path, check_same_thread=False)
            LOG.debug("SQLite connection opened.")
        else:
            LOG.warning(f"MASTERproductsDB.db not found: {db_path}")

    def closeEvent(self, event):

        """
        Closes the SQLite connection when the widget is destroyed.

        """

        if self._db_conn:
            self._db_conn.close()
            self._db_conn = None
            LOG.debug("[SearchPage] SQLite connection closed.")
        super().closeEvent(event)

    def _refresh_list(self):

        """
        Refresh the QListWidget with Article(s) saved by the user.
        Displays only the name, while storing the full dict in each item's UserRole.

        """

        self.mpn_list.clear()
        saved_items = self.configs.get_catalog_items()

        for item in saved_items:
            if isinstance(item, str):
                item = {"name": item, "mpn": "-", "ean": "-"}

            list_item = QListWidgetItem(item["name"])
            list_item.setData(Qt.UserRole, item)
            self.mpn_list.addItem(list_item)

    def _add_mpn(self):

        """
        Adds the selected article to the catalog.
        Retrieves EAN + MPN from _suggestion_map if available,
        otherwise records only the manually entered name.

        """

        INPUT = self.input_field.text().strip()
        if not INPUT:
            return

        # First by name cache, then SQLite lookup by EAN/MPN, then manual
        item_data = self._suggestion_map.get(INPUT)

        if not item_data and self._db_conn:
            try:
                inp = INPUT.upper()
                if self.SEARCH_FILTER_COMPANY:
                    row = self._db_conn.execute(
                        "SELECT Article, MPN, EAN, Brand FROM products WHERE Company = ? AND (EAN = ? OR MPN = ?) LIMIT 1",
                        (self.SEARCH_FILTER_COMPANY, inp, inp)
                    ).fetchone()
                else:
                    row = self._db_conn.execute(
                        "SELECT Article, MPN, EAN, Brand FROM products WHERE EAN = ? OR MPN = ? LIMIT 1",
                        (inp, inp)
                    ).fetchone()
                if row:
                    item_data = {"name": row[0], "mpn": row[1] or "-", "ean": row[2] or "-", "brand": row[3] or "-"}
            except Exception:
                pass

        if not item_data:
            item_data = {"name": INPUT, "mpn": "-", "ean": "-"}

        CATALOG = self.configs.get_catalog_items()

        # Avoiding duplicates
        existing_names = [
            i["name"] if isinstance(i, dict) else i
            for i in CATALOG
        ]

        if item_data["name"] not in existing_names:
            CATALOG.append(item_data)
            self.configs.set_catalog_items(items=CATALOG)
        self._refresh_list()

        self.input_field.clear()

    def _remove_mpn(self):

        """
        Removes the selected article from the catalog.

        """

        selected_items = self.mpn_list.selectedItems()
        if not selected_items:
            return

        item_data = selected_items[0].data(Qt.UserRole)
        target_name = item_data["name"] if isinstance(item_data, dict) else selected_items[0].text()

        CATALOG = self.configs.get_catalog_items()
        CATALOG = [
            i for i in CATALOG
            if (i["name"] if isinstance(i, dict) else i) != target_name
        ]

        self.configs.set_catalog_items(items=CATALOG)
        self._refresh_list()

    def _update_completer(self, text: str):

        """
        Queries SQLite on each keystroke — no data loaded at startup.
        Index B-tree on Article column → ~1ms per query, no GIL issue.

        """

        if len(text) >= 3:
            if not self._db_conn:
                return

            try:
                if self.SEARCH_FILTER_COMPANY:
                    rows = self._db_conn.execute(
                        """SELECT Article, MPN, EAN, Brand FROM products
                           WHERE Company = ? AND (Article LIKE ? OR EAN LIKE ? OR MPN LIKE ?)
                           LIMIT 200""",
                        (self.SEARCH_FILTER_COMPANY, f"%{text}%", f"%{text}%", f"%{text}%")
                    ).fetchall()
                else:
                    rows = self._db_conn.execute(
                        """SELECT Article, MPN, EAN, Brand FROM products
                           WHERE Article LIKE ? OR EAN LIKE ? OR MPN LIKE ?
                           GROUP BY
                               CASE WHEN EAN NOT IN ('-', '', 'NAN') THEN EAN
                                    WHEN MPN NOT IN ('-', '', 'NAN') THEN MPN
                                    ELSE Article
                               END
                           LIMIT 200""",
                        (f"%{text}%", f"%{text}%", f"%{text}%")
                    ).fetchall()

                # Cache results in _suggestion_map for _add_mpn lookup
                for article, mpn, ean, brand in rows:
                    self._suggestion_map[article] = {"name": article, "mpn": mpn or "-", "ean": ean or "-", "brand": brand or "-"}

                self.completer_model.setStringList([r[0] for r in rows])
                if self.input_field.completer() is None:
                    self.input_field.setCompleter(self.completer)

            except Exception as e:
                LOG.exception(f"SQLite query error: {e}")
        else:
            self.completer_model.setStringList([])
            if self.input_field.completer() is not None:
                self.input_field.setCompleter(None)

    def _clear_all(self):

        """
        Removes all articles from the catalog after confirmation.

        """

        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Tout supprimer",
            "Supprimer tous les articles du catalogue ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.configs.set_catalog_items(items=[])
            self._refresh_list()
            LOG.debug("[SearchPage] Catalogue cleared.")

    def _load_brand_buttons(self):

        """
        Loads distinct brands from SQLite and creates a quick-access button for each.
        Deduplicates case-insensitively to handle fragmented brand names.

        """

        if not self._db_conn:
            return

        try:
            rows = self._db_conn.execute(
                "SELECT DISTINCT Brand FROM products WHERE Brand NOT IN ('-', '', 'NAN', 'NONE') ORDER BY Brand"
            ).fetchall()

            # Deduplicate case-insensitively
            seen = {}
            brands = []
            for (brand,) in rows:
                key = brand.strip().upper()
                if key not in seen:
                    seen[key] = brand.strip()
                    brands.append(brand.strip())

            # Remove stretch, add buttons, re-add stretch
            while self._brand_layout.count():
                item = self._brand_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            for brand in brands:
                btn = QPushButton(brand)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(50, 50, 50, 0.7);
                        color: #ddd;
                        border: 1px solid #555;
                        border-radius: 6px;
                        padding: 6px 8px;
                        font-size: 12px;
                        text-align: left;
                    }
                    QPushButton:hover {
                        background-color: rgba(80, 80, 80, 0.9);
                        color: white;
                        border-color: #888;
                    }
                """)
                btn.clicked.connect(lambda checked, b=brand: self._add_brand(b))
                self._brand_layout.addWidget(btn)

            self._brand_layout.addStretch()

        except Exception as e:
            LOG.exception(f"[SearchPage] Error loading brands: {e}")

    def _add_brand(self, brand: str):

        """
        Adds all articles of the given brand to the catalog.
        Skips articles already present.

        """

        if not self._db_conn:
            return

        try:
            rows = self._db_conn.execute(
                "SELECT Article, MPN, EAN, Brand FROM products WHERE UPPER(Brand) = UPPER(?) GROUP BY CASE WHEN EAN NOT IN ('-', '', 'NAN') THEN EAN WHEN MPN NOT IN ('-', '', 'NAN') THEN MPN ELSE Article END",
                (brand,)
            ).fetchall()

            if not rows:
                return

            CATALOG = self.configs.get_catalog_items()
            existing = {
                (i["name"] if isinstance(i, dict) else i)
                for i in CATALOG
            }

            added = 0
            for article, mpn, ean, brand in rows:
                if article not in existing:
                    CATALOG.append({"name": article, "mpn": mpn or "-", "ean": ean or "-", "brand": brand or "-"})
                    existing.add(article)
                    added += 1

            if added > 0:
                self.configs.set_catalog_items(items=CATALOG)
                self._refresh_list()
                LOG.debug(f"[SearchPage] Added {added} articles for brand {brand}.")

        except Exception as e:
            LOG.exception(f"[SearchPage] Error adding brand {brand}: {e}")

    def retranslate_ui(self):

        """
        Update the texte of every widget of the application depending the new user language input.

        """

        self.input_field.setPlaceholderText(self.translator.get("page_search_input.placeholder"))

        self.add_button.setText(self.translator.get("page_search_add.button"))
        self.remove_button.setText(self.translator.get("page_search_remove.button"))
        self.clear_button.setText(self.translator.get("page_search_remove_all.button"))

        self.brand_title.setText(self.translator.get("page_search_rapid_access.label"))
