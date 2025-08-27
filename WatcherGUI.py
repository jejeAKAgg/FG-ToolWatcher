import os
import sys

import logging

import Watcher

from logging.handlers import RotatingFileHandler

from PySide6.QtCore import Qt, QThread, Signal, QObject, QSize
from PySide6.QtGui import QIcon, QPixmap, QPalette, QBrush
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLabel, QTextEdit, QHBoxLayout, QMessageBox, QSizePolicy, QToolButton
)

from UTILS.LOGmaker import *
from UTILS.TOOLSbox import *


class StreamToSignal:
    def __init__(self, signal):
        self.signal = signal
    def write(self, msg):
        if msg.strip():
            self.signal.emit(msg)
    def flush(self):
        pass


class QtHandler(logging.Handler, QObject):
    log_signal = Signal(str)
    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)


class WatcherThread(QThread):
    output = Signal(str)
    error = Signal(str)

    def run(self):
        sys.stdout = StreamToSignal(self.output)
        sys.stderr = StreamToSignal(self.error)
        
        try:
            Watcher.main_watcher()
        except Exception as e:
            self.error.emit(str(e))
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__


class WatcherGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FG-ToolWatcher")
        self.setGeometry(300, 300, 1000, 700)

        # --- Icône de fenêtre ---
        icon_path = os.path.join(BASE_TEMP_PATH, "ASSETS", "FG-TWicoBG.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # --- Thread watcher ---
        self.watcher_thread = WatcherThread()

        # Connexion signaux output et error vers log_area
        self.watcher_thread.output.connect(self.log_area_append)
        self.watcher_thread.error.connect(self.log_area_append_error)

        # Connexion pour remettre les boutons à jour quand le thread se termine
        self.watcher_thread.finished.connect(self.on_watcher_finished)

        # --- Setup du handler Qt pour logger dans log_area ---
        self.qt_handler = QtHandler()
        self.qt_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(name)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"))
        self.qt_handler.log_signal.connect(self.log_area_append)

        root_logger = logging.getLogger("FGToolWatcher")
        # Retirer tous les handlers StreamHandler (console)
        for h in root_logger.handlers[:]:
            if isinstance(h, logging.StreamHandler):
                root_logger.removeHandler(h)
        root_logger.addHandler(self.qt_handler)

        # --- AJOUT DU FILEHANDLER POUR LOG DANS FICHIER ---
        log_path = os.path.join(BASE_SYSTEM_PATH, get_log_file_path())
        file_handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=2, encoding="utf-8-sig")
        file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(name)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"))
        root_logger.addHandler(file_handler)
        # ---------------------------------------------------

        root_logger.setLevel(logging.INFO)

        # --- Boutons Exit et Update en haut ---
        top_buttons_widget = QWidget()
        top_buttons_widget.setFixedHeight(50)
        top_buttons_layout = QHBoxLayout(top_buttons_widget)
        top_buttons_layout.setContentsMargins(5, 5, 5, 5)
        top_buttons_layout.setSpacing(0)

        self.update_button = QPushButton("")
        self.update_button.setFixedSize(100, 40)
        
        update_icon_path = os.path.join(BASE_TEMP_PATH, "ASSETS", "update.ico")
        self.update_button.setIcon(QIcon(update_icon_path))
        self.update_button.setIconSize(QSize(35, 35))
        self.update_button.setStyleSheet("""
            QPushButton {
                background-color: #DE1D4E;
                color: white;
                font-weight: bold;
                border-radius: 20;
                border: none;
            }
            QPushButton:hover:!disabled {
                background-color: #B2274B;
            }
            QPushButton:disabled {
                background-color: #A05C6A;
                color: #E0E0E0;
            }
        """)
        self.update_button.clicked.connect(self.update_action)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.settings_button = QPushButton("")
        self.settings_button.setFixedSize(100, 40)
        
        settings_icon_path = os.path.join(BASE_TEMP_PATH, "ASSETS", "settings.ico")
        self.settings_button.setIcon(QIcon(settings_icon_path))
        self.settings_button.setIconSize(QSize(35, 35))
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #DE1D4E;
                color: white;
                font-weight: bold;
                border-radius: 20;
                border: none;
            }
            QPushButton:hover:!disabled {
                background-color: #B2274B;
            }
            QPushButton:disabled {
                background-color: #A05C6A;
                color: #E0E0E0;
            }
        """)
        self.settings_button.clicked.connect(self.settings_action)

        top_buttons_layout.addWidget(self.update_button)
        top_buttons_layout.addWidget(spacer)
        top_buttons_layout.addWidget(self.settings_button)

        # --- Header logo + titre côte à côte ---
        logo_path = os.path.join(BASE_TEMP_PATH, "ASSETS", "FG-TWicoBG.ico")

        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(15)

        # Logo
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_label.setAlignment(Qt.AlignCenter)
            logo_pixmap = QPixmap(logo_path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        else:
            logo_label = QLabel()  # vide si pas trouvé

        # Titre stylisé
        title_label = QLabel("FG-ToolWatcher")
        title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 48px;
                font-weight: bold;
                font-family: "Segoe UI", Arial, sans-serif;
                color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                       stop:0 #007e2d, stop:1 #007e2d);
            }
        """)

        title_layout.addStretch()
        title_layout.addWidget(logo_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        

        # --- Bouton Start ---
        self.start_button = QToolButton()
        self.start_button.setText("Start")
        self.start_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)  # texte sous icône
        start_icon_path = os.path.join(BASE_TEMP_PATH, "ASSETS", "play.ico")
        if os.path.exists(start_icon_path):
            self.start_button.setIcon(QIcon(start_icon_path))
            self.start_button.setIconSize(QSize(96, 96))  # icône plus grande
        self.start_button.setFixedSize(200, 200)

        # --- Bouton Stop ---
        self.stop_button = QToolButton()
        self.stop_button.setText("Stop")
        self.stop_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        stop_icon_path = os.path.join(BASE_TEMP_PATH, "ASSETS", "stop.ico")
        if os.path.exists(stop_icon_path):
            self.stop_button.setIcon(QIcon(stop_icon_path))
            self.stop_button.setIconSize(QSize(96, 96))
        self.stop_button.setFixedSize(200, 200)

        # --- Bouton Calibrage ---
        self.calibrate_button = QToolButton()
        self.calibrate_button.setText("REFs/Articles")
        self.calibrate_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        calibrate_icon_path = os.path.join(BASE_TEMP_PATH, "ASSETS", "MPN.ico")
        if os.path.exists(calibrate_icon_path):
            self.calibrate_button.setIcon(QIcon(calibrate_icon_path))
            self.calibrate_button.setIconSize(QSize(96, 96))
        self.calibrate_button.setFixedSize(200, 200)

        # Styles (mêmes couleurs que ton code)
        base_style = """
            QToolButton {
                border-radius: 20px;
                color: white;
                font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
                font-size: 25px;
                font-weight: bold;
                border: none;
                padding: 12px;
            }
            QToolButton:disabled {
                background: #a0a0a0 !important;
                color: #d0d0d0 !important;
            }
        """

        self.start_button.setStyleSheet(base_style + """
            QToolButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #4caf50, stop:1 #2e7d32);
            }
            QToolButton:hover:!disabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #81c784, stop:1 #388e3c);
            }
        """)

        self.stop_button.setStyleSheet(base_style + """
            QToolButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #e53935, stop:1 #b71c1c);
            }
            QToolButton:hover:!disabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #ef9a9a, stop:1 #d32f2f);
            }
        """)

        self.calibrate_button.setStyleSheet(base_style + """
            QToolButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #137BD6, stop:1 #218DEB);
            }
            QToolButton:hover:!disabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #218DEB, stop:1 #137BD6);
            }
        """)

        # Connexions
        self.stop_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_watcher)
        self.stop_button.clicked.connect(self.stop_watcher)
        self.calibrate_button.clicked.connect(self.calibrate_action)

        # Layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addSpacing(50)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addSpacing(50)
        buttons_layout.addWidget(self.calibrate_button)
        buttons_layout.addStretch()


        # --- Zone de logs avec bouton Clear ---
        self.log_container = QWidget()
        self.log_container.setMinimumHeight(200)
        self.log_container.setStyleSheet("background: transparent;")

        # Layout principal vertical pour le log_container
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.setContentsMargins(5, 5, 5, 5)
        self.log_layout.setSpacing(5)

        # Layout horizontal pour le bouton Clear en haut à droite
        top_layout = QHBoxLayout()
        top_layout.addStretch()  # pousse le bouton à droite

        self.clear_log_button = QPushButton("", self.log_container)
        self.clear_log_button.setFixedSize(30, 30)

        clear_icon_path = os.path.join(BASE_TEMP_PATH, "ASSETS", "clear.ico")
        self.clear_log_button.setIcon(QIcon(clear_icon_path))
        self.clear_log_button.setIconSize(QSize(25, 25))
        self.clear_log_button.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
            }
        """)
        self.clear_log_button.clicked.connect(self.clear_logs)

        top_layout.addWidget(self.clear_log_button)
        self.log_layout.addLayout(top_layout)

        # Zone de texte pour les logs
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("""
            background-color: white;
            color: black;
            font-family: Consolas, monospace;
            font-size: 12px;
        """)

        # Ajout du QTextEdit au layout vertical (prend tout l’espace restant)
        self.log_layout.addWidget(self.log_area)

        # --- Layout principal ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        main_layout.addWidget(top_buttons_widget)
        main_layout.addWidget(title_container)  # logo + titre ici
        main_layout.addStretch()
        main_layout.addLayout(buttons_layout)
        main_layout.addStretch()
        main_layout.addWidget(self.log_container)

        # --- Background ---
        bg_path = os.path.join(BASE_TEMP_PATH, "ASSETS", "FGbackground.jpg")
        if os.path.exists(bg_path):
            o_pixmap = QPixmap(bg_path).scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            palette = QPalette()
            palette.setBrush(QPalette.Window, QBrush(o_pixmap))
            self.setPalette(palette)
            self.setAutoFillBackground(True)

        self.overlay = QWidget(self)
        self.overlay.setStyleSheet("background-color: rgba(255, 255, 255, 180);")
        self.overlay.setGeometry(0, 0, self.width(), self.height())
        self.overlay.lower()
        self.overlay.setAttribute(Qt.WA_TransparentForMouseEvents)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.setGeometry(0, 0, self.width(), self.height())

    def log_area_append(self, text):
        self.log_area.append(text.strip())

    def log_area_append_error(self, text):
        self.log_area.append(f"❗ {text.strip()}")

    def start_watcher(self):
        if not self.watcher_thread.isRunning():
            self.log_area.clear()
            self.watcher_thread.start()
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.calibrate_button.setEnabled(False)
            self.update_button.setEnabled(False)
            self.settings_button.setEnabled(False)
        else:
            self.log_area.append("Le watcher est déjà en cours.")

    def stop_watcher(self):
        if self.watcher_thread.isRunning():
            self.watcher_thread.terminate()
            kill_chromium_processes()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.calibrate_button.setEnabled(True)
            self.update_button.setEnabled(True)
            self.settings_button.setEnabled(True)

    def calibrate_action(self):
        QMessageBox.information(self, "Calibrage", "Fonction calibrage non implémentée.")

    def update_action(self):
        QMessageBox.information(self, "Update", "Fonction update non implémentée.")

    def settings_action(self):
        QMessageBox.information(self, "Settings", "Fonction update non implémentée.")

    def clear_logs(self):
        self.log_area.clear()

    def on_watcher_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.calibrate_button.setEnabled(True)
        self.update_button.setEnabled(True)
        self.settings_button.setEnabled(True)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WatcherGUI()
    window.show()
    sys.exit(app.exec())