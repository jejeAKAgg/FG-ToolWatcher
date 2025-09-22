# APP/pages/SETUPpage.py

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from APP.WIDGETS.SPINNERbar import Spinner

from APP.SERVICES.__init__ import *

from APP.UTILS.LOGmaker import *
from APP.UTILS.TOOLSinstaller import *


Logger = logger("SETUP")

class SetupThread(QThread):
    message = Signal(str)
    finished_ok = Signal()

    def run(self):
        steps = [
            ("Vérification de Chromium...", getCHROMIUMpackage),
            ("Vérification de Python...", getPYTHONpackage),
            ("Vérification de pip/ensurepip...", getPIPpackage),
            ("Vérification des packages requis...", getREQUIREMENTSpackage),
        ]

        for msg, func in steps:
            self.message.emit(msg)
            try:
                func()
            except Exception as e:
                Logger.error(f"Erreur pendant {msg} : {e}")
                self.message.emit(f"Erreur : {e}")
                return

        self.finished_ok.emit()


class SetupPage(QWidget):
    setup_finished = Signal()

    def __init__(self, update_button, profile_button, settings_button, parent=None):
        super().__init__(parent)

        self.update_button = update_button
        self.profile_button = profile_button
        self.settings_button = settings_button

        self.is_running = False 

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.spinner = Spinner(radius=40, dot_size=12, speed=80)
        self.label = QLabel("Préparation de l'application...")
        self.label.setStyleSheet("color: black; font-weight: bold; font-size: 12pt;")
        self.label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.spinner, alignment=Qt.AlignHCenter)
        layout.addSpacing(15)
        layout.addWidget(self.label)

        self.start_setup()  # lancement initial

    def start_setup(self):
        if self.is_running:
            return

        self.is_running = True
        
        self.thread = SetupThread()
        self.thread.message.connect(self.label.setText)
        self.thread.finished_ok.connect(self.on_setup_finished)
        self.thread.start()

    def on_setup_finished(self):
        self.is_running = False

        self.setup_finished.emit()