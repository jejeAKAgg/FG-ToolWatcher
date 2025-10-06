# APP/pages/SETUPpage.py

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from APP.ASSETS.WIDGETS.SPINNERbar import Spinner
from APP.SERVICES.__init__ import *
from APP.UTILS.LOGmaker import *
from APP.UTILS.TOOLSinstaller import *


Logger = logger("SETUP")

class SetupThread(QThread):
    message = Signal(str)
    finished_ok = Signal()

    def __init__(self, user_config=None, catalog_config=None):
        super().__init__()
        self.user_config = user_config
        self.catalog_config = catalog_config

    def run(self):
        steps = [
            ("Vérification de l'intégrité des dossiers et fichiers de l'application...", make_dirs),
            ("Initialisation de la configuration utilisateur...", lambda: self.user_config.load()),
            ("Initialisation du catalogue d'articles...", lambda: self.catalog_config.load()),
            ("Vérification de Chromium...", getCHROMIUMpackage),
            
            #("Vérification de Python...", getPYTHONpackage),                  [TEST ONLY]
            #("Vérification de pip/ensurepip...", getPIPpackage),              [TEST ONLY]
            #("Vérification des packages requis...", getREQUIREMENTSpackage),  [TEST ONLY]
        ]

        for msg, func in steps:
            self.message.emit(msg)
            QThread.msleep(1000)

            if func is not None and callable(func):
                try:
                    func()
                except Exception as e:
                    Logger.error(f"Erreur pendant {msg} : {e}")
                    self.message.emit(f"Erreur : {e}")
                    return
            
            QThread.msleep(1000)

        self.finished_ok.emit()


class SetupPage(QWidget):
    setup_finished = Signal()

    def __init__(self, update_button, profile_button, settings_button, user_config, catalog_config, parent=None):
        super().__init__(parent)

        self.update_button = update_button
        self.profile_button = profile_button
        self.settings_button = settings_button

        self.user_config = user_config
        self.catalog_config = catalog_config

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

        self.start_setup(user_config=self.user_config, catalog_config=self.catalog_config)

    def start_setup(self, user_config=None, catalog_config=None):
        if self.is_running:
            return

        self.is_running = True
        
        self.thread = SetupThread(user_config=user_config, catalog_config=catalog_config)
        self.thread.message.connect(self.label.setText)
        self.thread.finished_ok.connect(self.on_setup_finished)
        self.thread.start()

    def on_setup_finished(self):
        self.is_running = False
        self.setup_finished.emit()