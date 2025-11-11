# GUI/Desktop/pages/search.py
import pandas as pd

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QPushButton, QCompleter
)
from PySide6.QtCore import Qt, QStringListModel

from CORE.Services.setup import *
from CORE.Services.user import UserService
from CORE.Services.translator import TranslatorService



class SearchPage(QWidget):
    def __init__(self, config: UserService, translator: TranslatorService, parent=None):
        super().__init__(parent)

        # === INTERNAL VARIABLE(S) ===       
        self.configs = config
        self.translator = translator

        # === INTERNAL PARAMETER(S) ===
        self.completer_model = QStringListModel(self)


        # === MAIN LAYOUT ===
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

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

        main_layout.addLayout(add_layout)

        # --- Auto-completer module ---
        self._load_completer_data()
        
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)        # Ignoring case
        self.completer.setFilterMode(Qt.MatchContains)               # Finds text matching
        self.completer.setCompletionMode(QCompleter.PopupCompletion) # Shows pop-up

        self.input_field.textChanged.connect(self._update_completer)

        self._refresh_list()
        

    # ====================================
    #             FUNCTIONS
    # ====================================

    def _refresh_list(self):
        
        """
        Refresh the QListWidget with Article(s) saved by the user.
        """
        
        self.mpn_list.clear()
        saved_mpns = self.configs.get_catalog_items() 
        self.mpn_list.addItems(saved_mpns)

    def _add_mpn(self):
        
        """
        Add the user input into the local MPN.json file.
        """
        
        INPUT = self.input_field.text().strip()
        
        if not INPUT:
            return

        CATALOG = self.configs.get_catalog_items()
        
        if INPUT not in CATALOG:
            CATALOG.append(INPUT)
            self.configs.set_catalog_items(items=CATALOG)
            self._refresh_list()     # Updating interface
        
        self.input_field.clear()     # Cleaning input field

    def _remove_mpn(self):
        
        """
        Delete the article selected by the user.
        """
        
        selected_items = self.mpn_list.selectedItems()
        if not selected_items:
            return

        INPUT = selected_items[0].text()
        
        CATALOG = self.configs.get_catalog_items()
        
        if INPUT in CATALOG:
            CATALOG.remove(INPUT)
            self.configs.set_catalog_items(items=CATALOG)
            self._refresh_list()     # Updating interface
    
    def _update_completer(self, text: str):
        
        """
        Disable or enable the completer depending the text lenght (3 characters by default).
        """
        
        if len(text) >= 3:
            if self.input_field.completer() is None:
                self.input_field.setCompleter(self.completer)
        else:
            if self.input_field.completer() is not None:
                self.input_field.setCompleter(None)

    def _load_completer_data(self):
        
        """
        Load articles suggestions from 'FGproductsDB.csv' based on user input
        """
        
        csv_path = os.path.join(DATABASE_FOLDER, "FGproductsDB.csv")
        suggestions = []
        
        if os.path.exists(csv_path):
            print(f"[SearchPage] Chargement du compléteur depuis : {csv_path}")
            try:

                df = pd.read_csv(csv_path, usecols=['Article'], encoding='utf-8-sig')
                df.dropna(subset=['Article'], inplace=True)

                suggestions = df['Article'].astype(str).unique().tolist()
                print(f"[SearchPage] {len(suggestions)} suggestions chargées.")
            except Exception as e:
                print(f"Erreur lors de la lecture du CSV pour le compléteur : {e}")
        else:
            print(f"Avertissement : Fichier master DB introuvable pour le compléteur : {csv_path}")
            
        # Updating model with new suggestions
        self.completer_model.setStringList(suggestions)

    def retranslate_ui(self):
        
        """
        Update the texte of every widget of the application depending the new user language input.
        """
        
        self.input_field.setPlaceholderText(self.translator.get("page_search_input.placeholder"))
        self.add_button.setText(self.translator.get("page_search_add.button"))
        self.remove_button.setText(self.translator.get("page_search_remove.button"))