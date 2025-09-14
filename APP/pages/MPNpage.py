import os
import sys

import logging

import Watcher

from logging.handlers import RotatingFileHandler

from PySide6.QtCore import Qt, QThread, Signal, QObject, QSize
from PySide6.QtGui import QIcon, QPixmap, QPalette, QBrush, QAction
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLabel, QTextEdit, QHBoxLayout, QMessageBox, QSizePolicy,
    QToolButton, QMenuBar, QMenu, QCheckBox
)

from UTILS.LOGmaker import *
from UTILS.TOOLSbox import *

class CalibrationPage(QWidget):
    def __init__(self, update_button=None, profile_button=None, settings_button=None, parent=None):
        super().__init__(parent)

        self.update_button = update_button
        self.profile_button = profile_button
        self.settings_button = settings_button

        layout = QVBoxLayout(self)
        label = QLabel("Page de calibration en construction 🚧", self)
        layout.addWidget(label)
        layout.addStretch()