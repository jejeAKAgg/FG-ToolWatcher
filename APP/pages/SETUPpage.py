# APP/pages/SETUPpage.py
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from UTILS.TOOLSinstaller import getCHROMIUMpackage, getPYTHONpackage, getPIPpackage, getREQUIREMENTSpackage
from UTILS.LOGmaker import logger
from APP.widgets.SPINNERbar import Spinner

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
        # Désactive les boutons top bar pendant le setup
        self.update_button.setEnabled(False)
        self.profile_button.setEnabled(False)
        self.settings_button.setEnabled(False)

        # Crée un nouveau thread
        self.thread = SetupThread()
        self.thread.message.connect(self.label.setText)
        self.thread.finished_ok.connect(self.on_setup_finished)
        self.thread.start()

    def on_setup_finished(self):
        self.setup_finished.emit()

        # Réactive les boutons
        self.update_button.setEnabled(True)
        self.profile_button.setEnabled(True)
        self.settings_button.setEnabled(True)