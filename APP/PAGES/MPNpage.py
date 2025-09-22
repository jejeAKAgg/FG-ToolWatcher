# APP/pages/MPNpage.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from APP.SERVICES.__init__ import *

from APP.UTILS.LOGmaker import *
from APP.UTILS.TOOLSbox import *


class CalibrationPage(QWidget):
    def __init__(self, update_button, profile_button, settings_button, config, parent=None):
        super().__init__(parent)

        self.update_button = update_button
        self.profile_button = profile_button
        self.settings_button = settings_button

        self.config = config

        layout = QVBoxLayout(self)
        label = QLabel("Page de calibration en construction 🚧", self)
        layout.addWidget(label)
        layout.addStretch()