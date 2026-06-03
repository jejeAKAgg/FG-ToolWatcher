# GUI/Desktop/pages/subpages/settings/system.py
import os
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel
)
from PySide6.QtCore import Qt

from CORE.Services.setup import *
from CORE.Services.user import UserService
from CORE.Services.translator import TranslatorService

from GUI.__ASSETS.widgets.push_buttons import CustomPushButton



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

class SystemPage(QWidget):

    """
    Sous-page des paramètres système.
    Fournit les actions système : mises à jour, redémarrage, réinitialisation.
    """

    def __init__(self, config: UserService, translator: TranslatorService, parent=None):
        super().__init__(parent)

        # === INTERNAL VARIABLE(S) ===
        self.configs    = config
        self.translator = translator

        # === MAIN LAYOUT ===
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(60, 50, 60, 0)
        self.main_layout.setSpacing(10)
        self.main_layout.setAlignment(Qt.AlignTop)

        # --- TITLE ---
        self.title = QLabel(self.translator.get("page_settings_system.category"))
        self.title.setStyleSheet("font-size: 26px; font-weight: 900; color: #000; margin-bottom: 20px;")
        self.main_layout.addWidget(self.title)

        # ── MISES À JOUR ─────────────────────────────────────────────
        self.update_button = CustomPushButton(
            width=240, height=46,
            bg_color="#0078d7", hover_color="#005a9e"
        )
        self.update_button.setText(self.translator.get("subpage_settings_system_update.button"))
        self.update_button.clicked.connect(self._check_updates)
        update_layout = QHBoxLayout()
        update_layout.addStretch()
        update_layout.addWidget(self.update_button)
        update_layout.addStretch()
        self.main_layout.addLayout(update_layout)

        self.main_layout.addSpacing(20)

        # ── REDÉMARRER ───────────────────────────────────────────────
        self.restart_button = CustomPushButton(
            width=240, height=46,
            bg_color="#555555", hover_color="#333333"
        )
        self.restart_button.setText(self.translator.get("subpage_settings_system_restart.button"))
        self.restart_button.clicked.connect(self._restart)
        restart_layout = QHBoxLayout()
        restart_layout.addStretch()
        restart_layout.addWidget(self.restart_button)
        restart_layout.addStretch()
        self.main_layout.addLayout(restart_layout)

        self.main_layout.addSpacing(20)

        # ── RÉINITIALISER ────────────────────────────────────────────
        self.reset_button = CustomPushButton(
            width=240, height=46,
            bg_color="#cc0000", hover_color="#880000"
        )
        self.reset_button.setText(self.translator.get("subpage_settings_system.reset", "Réinitialiser"))
        self.reset_button.clicked.connect(self._reset)
        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        reset_layout.addWidget(self.reset_button)
        reset_layout.addStretch()
        self.main_layout.addLayout(reset_layout)

        self.main_layout.addStretch()


    # ====================================
    #           PUBLIC METHODS
    # ====================================

    def retranslate_ui(self):
        self.title.setText(self.translator.get("page_settings_system.category"))
        self.update_button.setText(self.translator.get("subpage_settings_system_update.button"))
        self.restart_button.setText(self.translator.get("subpage_settings_system_restart.button"))
        self.reset_button.setText(self.translator.get("subpage_settings_system_reset.button"))


    # ====================================
    #           PRIVATE METHODS
    # ====================================

    def _check_updates(self):
        # TODO: implémenter la vérification des mises à jour
        LOG.debug("[SystemPage] Recherche de mises à jour...")

    def _restart(self):
        # TODO: implémenter le redémarrage de l'application
        LOG.debug("[SystemPage] Redémarrage...")

    def _reset(self):
        # TODO: implémenter la réinitialisation (avec confirmation)
        LOG.debug("[SystemPage] Réinitialisation...")
