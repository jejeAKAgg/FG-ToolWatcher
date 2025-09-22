# APP/pages/MAINpage.py

import os

import Watcher

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout
)

from APP.WIDGETS.MAINbuttons import CustomToolButton
from APP.WIDGETS.PROGRESSbar import CustomProgressBar

from APP.SERVICES.__init__ import *
from APP.UTILS.TOOLSbox import *
from APP.UTILS.LOGmaker import *


class WatcherThread(QThread):
    output = Signal(str)
    error = Signal(str)
    progress = Signal(int)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            Watcher.main_watcher(
                progress_callback=self.progress.emit,
            )
        except Exception as e:
            self.error.emit(str(e))


class MainPage(QWidget):

    calibration_requested = Signal()

    def __init__(self, update_button, profile_button, settings_button, config, parent=None):
        super().__init__(parent)

        self.update_button = update_button
        self.settings_button = settings_button
        self.profile_button = profile_button

        self.config = config

        # --- Thread watcher ---
        self.watcher_thread = WatcherThread()
        self.watcher_thread.progress.connect(self.update_progress)
        self.watcher_thread.finished.connect(self.on_watcher_finished)

        # --- Boutons Start/Stop/Calibrage ---
        self.start_button = CustomToolButton(
            text="Start",
            icon_path=os.path.join(BASE_TEMP_PATH, "APP", "ASSETS", "play.ico"),
            gradient=("#4caf50", "#2e7d32")
        )
        self.stop_button = CustomToolButton(
            text="Stop",
            icon_path=os.path.join(BASE_TEMP_PATH, "APP", "ASSETS", "stop.ico"),
            gradient=("#e53935", "#b71c1c")
        )
        self.calibrate_button = CustomToolButton(
            text="REFs/Articles",
            icon_path=os.path.join(BASE_TEMP_PATH, "APP", "ASSETS", "MPN.ico"),
            gradient=("#137BD6", "#218DEB")
        )
        self.stop_button.setEnabled(False)

        # Connexions
        self.start_button.clicked.connect(self.start_watcher)
        self.stop_button.clicked.connect(self.stop_watcher)
        self.calibrate_button.clicked.connect(self.request_calibration)

        # --- Barre de progression ---
        self.progress_widget = CustomProgressBar()


        # --- Layout boutons ---
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addSpacing(50)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addSpacing(50)
        buttons_layout.addWidget(self.calibrate_button)
        buttons_layout.addStretch()

        # --- Layout principal ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        main_layout.addLayout(buttons_layout)
        main_layout.setSpacing(75)
        main_layout.addWidget(self.progress_widget)
        main_layout.addStretch()

    # ---------------- Fonctions ----------------
    def start_watcher(self):
        if not self.watcher_thread.isRunning():
            self.progress_widget.reset()
            self.watcher_thread.start()
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.calibrate_button.setEnabled(False)
            self.update_button.setEnabled(False)
            self.profile_button.setEnabled(False)
            self.settings_button.setEnabled(False)

    def stop_watcher(self):
        if self.watcher_thread.isRunning():
            self.watcher_thread.terminate()
            kill_chromium_processes()
            self.progress_widget.reset()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.calibrate_button.setEnabled(True)
            self.update_button.setEnabled(True)
            self.profile_button.setEnabled(True)
            self.settings_button.setEnabled(True)

    def on_watcher_finished(self):
        self.progress_widget.set_value(100)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.calibrate_button.setEnabled(True)
        self.update_button.setEnabled(True)
        self.profile_button.setEnabled(True)
        self.settings_button.setEnabled(True)

    def update_progress(self, value: int):
        self.progress_widget.set_value(value)

    def request_calibration(self):
        self.calibration_requested.emit()