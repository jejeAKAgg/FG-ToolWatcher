from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt

from APP.ASSETS.WIDGETS.PUSHbuttons import CustomPushButton
from APP.SERVICES.__init__ import BASE_TEMP_PATH


class CatalogPage(QWidget):
    def __init__(self, update_button, profile_button, settings_button, user_config, catalog_config, parent=None):
        super().__init__(parent)

        # ===============================
        #         CONFIGS & REFS
        # ===============================
        self.update_button = update_button
        self.profile_button = profile_button
        self.settings_button = settings_button
        self.user_config = user_config
        self.catalog_config = catalog_config

        # ===============================
        #         LAYOUT PRINCIPAL
        # ===============================
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        # ---------------------------------------
        #           LISTE DES MPN
        # ---------------------------------------
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

        # ---------------------------------------
        #           ZONE D’AJOUT / SUPP
        # ---------------------------------------
        add_layout = QHBoxLayout()

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Entrer un nouveau MPN/article...")
        self.input_field.setStyleSheet("padding: 5px; font-size: 14px; border-radius: 5px;")
        add_layout.addWidget(self.input_field)

        self.add_button = QPushButton("➕ Ajouter")
        self.add_button.clicked.connect(self.add_mpn)
        add_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("🗑️ Supprimer")
        self.remove_button.clicked.connect(self.remove_mpn)
        add_layout.addWidget(self.remove_button)

        main_layout.addLayout(add_layout)

        # ---------------------------------------
        #           SYNCHRONISATION INITIALE
        # ---------------------------------------
        #self.refresh_list()

    # ====================================
    #           MÉTHODES
    # ====================================

    def refresh_list(self):
        """Recharge la liste locale et affiche les MPN."""
        self.catalog_config.sync_with_sheet()
        self.mpn_list.clear()
        self.mpn_list.addItems(self.catalog_config.get_all())

    def add_mpn(self):
        """Ajoute un MPN à la config."""
        mpn = self.input_field.text().strip()
        if not mpn:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un MPN valide.")
            return

        success = self.catalog_config.add(mpn)
        if not success:
            QMessageBox.information(self, "Info", "Ce MPN existe déjà.")
            return

        self.input_field.clear()
        self.refresh_list()

    def remove_mpn(self):
        """Supprime le MPN sélectionné."""
        selected = self.mpn_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un MPN à supprimer.")
            return

        mpn = selected.text()
        confirm = QMessageBox.question(
            self, "Confirmation", f"Supprimer {mpn} ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.catalog_config.remove(mpn)
            self.refresh_list()

    def save_mpn(self):
        """Sauvegarde manuellement (utile si plusieurs modifs locales)."""
        self.catalog_config.save()
        QMessageBox.information(self, "Succès", "Les MPN ont été sauvegardés localement et synchronisés.")