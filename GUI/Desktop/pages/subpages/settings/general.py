# GUI/Desktop/pages/subpages/settings/general.py

import logging
import os
import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel, QHBoxLayout, QPushButton, QVBoxLayout, QWidget
)

from CORE.Services.setup import *
from CORE.Services.translator import TranslatorService
from CORE.Services.user import UserService

from GUI.__assets.widgets.buttons import CustomPushButton

LOG = logging.getLogger(__name__)

class GeneralPage(QWidget):

    """
    General settings subpage.
    Manages the application's behavior and system preferences.
    """

    settings_saved = Signal()

    def __init__(self, config: UserService, translator: TranslatorService, parent: QWidget | None = None):
        super().__init__(parent)

        self.configs    = config
        self.translator = translator

        self._toggles: dict[str, QPushButton] = {}
        self._labels:  dict[str, QLabel]      = {}  # Stores titles for dynamic retranslation

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(60, 50, 60, 0)
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._build_ui()

    # ====================================
    #           PUBLIC METHODS
    # ====================================

    def save_settings(self):
        """Saves current states of all toggles to the configuration service."""
        for key, btn in self._toggles.items():
            is_checked = btn.isChecked()
            self.configs.set(key, is_checked)

            if key == "system_launch_on_startup":
                self._apply_startup(is_checked)

        self.save_button.setEnabled(False)
        self.settings_saved.emit()
        LOG.debug("[GeneralPage] General settings successfully saved.")

    def retranslate_ui(self):
        """Dynamically updates the UI text based on the active language."""
        self.title.setText(self.translator.get("page_settings_general.category"))

        labels = {
            "system_launch_on_startup": self.translator.get("subpage_settings_general_startup.title"),
            "system_notify_on_finish": self.translator.get("subpage_settings_general_notification.title"),
            "system_open_on_finish": self.translator.get("subpage_settings_general_open.title"),
            "user_mail_send": self.translator.get("subpage_settings_general_send_email.title"),
        }
        descs = {
            "system_launch_on_startup": self.translator.get("subpage_settings_general_startup.subtitle"),
            "system_notify_on_finish": self.translator.get("subpage_settings_general_notification.subtitle"),
            "system_open_on_finish": self.translator.get("subpage_settings_general_open.subtitle"),
            "user_mail_send": self.translator.get("subpage_settings_general_send_email.subtitle"),
        }

        for key, lbl in self._labels.items():
            lbl.setText(labels[key])

        for key, btn in self._toggles.items():
            if hasattr(btn, "_desc_label"):
                btn._desc_label.setText(descs[key])

        self.save_button.setText(self.translator.get("page_settings_save.button"))

    # ====================================
    #           PRIVATE METHODS
    # ====================================

    def _build_ui(self):

        """
        Builds the graphical user interface for the main dashboard using reusable layouts.
        """
        LOG.debug("Building UI for DashboardPage...")

        # --- TITLE ---
        self.title = QLabel(self.translator.get("page_settings_general.category"))
        self.title.setStyleSheet("font-size: 26px; font-weight: 900; color: #000; margin-bottom: 10px;")
        self.main_layout.addWidget(self.title)

        # --- TOGGLES ---
        toggle_defs = [
            (
                "system_launch_on_startup",
                self.translator.get("subpage_settings_general_startup.title"),
                self.translator.get("subpage_settings_general_startup.subtitle"),
            ),
            (
                "system_notify_on_finish",
                self.translator.get("subpage_settings_general_notification.title"),
                self.translator.get("subpage_settings_general_notification.subtitle"),
            ),
            (
                "system_open_on_finish",
                self.translator.get("subpage_settings_general_open.title"),
                self.translator.get("subpage_settings_general_open.subtitle"),
            ),
            (
                "user_mail_send",
                self.translator.get("subpage_settings_general_send_email.title"),
                self.translator.get("subpage_settings_general_send_email.subtitle"),
            ),
        ]

        for key, label, description in toggle_defs:
            self.main_layout.addLayout(
                self._build_toggle_row(key, label, description)
            )

        # --- SAVE BUTTON ---
        self.save_button = CustomPushButton(
            width=110, height=50,
            bg_color="#4a7fa5", hover_color="#2e5f7e"
        )
        self.save_button.setText(self.translator.get("page_settings_save.button"))
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setEnabled(False)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()

        self.main_layout.addStretch()
        self.main_layout.addLayout(button_layout)

    def _build_toggle_row(self, key: str, label: str, description: str) -> QHBoxLayout:
        """
        Builds a row containing a text description and an iOS-style toggle button.
        """
        row = QHBoxLayout()
        row.setSpacing(20)

        # Left Column: Text
        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #000;")
        self._labels[key] = lbl

        desc = QLabel(description)
        desc.setStyleSheet("font-size: 12px; color: #111;")
        desc.setWordWrap(True)

        text_col.addWidget(lbl)
        text_col.addWidget(desc)

        # Right Column: Pill Toggle
        btn = QPushButton()
        btn.setCheckable(True)
        btn.setChecked(self.configs.get(key, False))
        btn.setFixedSize(56, 28)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn._desc_label = desc

        self._apply_pill_style(btn)

        btn.toggled.connect(lambda _checked, b=btn: (self._apply_pill_style(b), self._check_changes()))
        self._toggles[key] = btn

        row.addLayout(text_col, stretch=1)
        row.addWidget(btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        return row

    def _apply_pill_style(self, btn: QPushButton):
        """Applies a minimalist ON/OFF style resembling an iOS toggle switch."""
        if btn.isChecked():
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #007e2d;
                    border: 3px solid black;
                    border-radius: 14px;
                }
                QPushButton:hover { background-color: #004d1a; }
            """)
            btn.setText("●")
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ccc;
                    border: 3px solid black;
                    border-radius: 14px;
                    color: transparent;
                }
                QPushButton:hover { background-color: #aaa; }
            """)
            btn.setText("")

    def _apply_startup(self, enable: bool):
        """
        Adds or removes the application from system startup based on the OS.
        """
        try:
            exe_path = sys.executable

            if sys.platform.startswith("win"):
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0, winreg.KEY_SET_VALUE
                )
                if enable:
                    winreg.SetValueEx(key, "FG-ToolWatcher", 0, winreg.REG_SZ, exe_path)
                else:
                    try:
                        winreg.DeleteValue(key, "FG-ToolWatcher")
                    except FileNotFoundError:
                        pass
                winreg.CloseKey(key)

            elif sys.platform.startswith("linux"):
                autostart_dir = os.path.expanduser("~/.config/autostart")
                desktop_file  = os.path.join(autostart_dir, "fg-toolwatcher.desktop")
                os.makedirs(autostart_dir, exist_ok=True)

                if enable:
                    with open(desktop_file, "w") as f:
                        f.write(f"[Desktop Entry]\nType=Application\nExec={exe_path}\nHidden=false\nNoDisplay=false\nX-GNOME-Autostart-enabled=true\nName=FG-ToolWatcher\n")
                else:
                    if os.path.exists(desktop_file):
                        os.remove(desktop_file)

        except Exception as e:
            LOG.exception(f"[GeneralPage] Startup configuration error: {e}")

    def _check_changes(self):
        """Checks if any toggles differ from the saved configuration and updates the save button."""
        changed = any(
            btn.isChecked() != self.configs.get(key, False)
            for key, btn in self._toggles.items()
        )
        self.save_button.setEnabled(changed)
