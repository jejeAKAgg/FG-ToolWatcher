import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLabel, QTextEdit, QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QProcess, QSize
from PySide6.QtGui import QIcon, QPixmap, QPalette, QBrush
import os
from UTILS.NAMEformatter import *
from Chromium import download_chromium_and_driver
from Python import download_and_extract_python

class WatcherGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FG-ToolWatcher")
        self.setGeometry(300, 300, 1000, 800)

        # Téléchargements nécessaires
        download_chromium_and_driver()
        download_and_extract_python()

        # Choix de l'exécutable Python selon OS
        if sys.platform.startswith("win"):
            EXECUTABLE = resource_path("CORE/python/python.exe")
        else:
            EXECUTABLE = sys.executable

        watcher_script = resource_path("Watcher.py")
        if not os.path.exists(watcher_script):
            print(f"[ERROR] Le script Watcher.py est introuvable à {watcher_script}")

        self.process = QProcess(self)
        self.process.setProgram(EXECUTABLE)
        self.process.setArguments([watcher_script])
        
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.started.connect(self.process_started)
        self.process.finished.connect(self.process_finished)
        self.process.errorOccurred.connect(self.process_error)

        # --- Top Buttons: Update & Exit ---
        top_buttons_widget = QWidget()
        top_buttons_widget.setFixedHeight(50)
        top_buttons_layout = QHBoxLayout(top_buttons_widget)
        top_buttons_layout.setContentsMargins(5, 5, 5, 5)
        top_buttons_layout.setSpacing(0)

        self.update_button = QPushButton("Check")
        self.update_button.setFixedSize(100, 50)
        self.update_button.setIcon(QIcon(resource_path("ASSETS/update.ico")))
        self.update_button.setIconSize(QSize(30, 30))
        self.update_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                border-radius: 0;
                border: none;
                padding-left: 10px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #64B5F6;
            }
        """)
        self.update_button.clicked.connect(self.update_action)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.exit_button = QPushButton("Quitter")
        self.exit_button.setFixedSize(100, 50)
        self.exit_button.setIcon(QIcon(resource_path("ASSETS/exit.ico")))
        self.exit_button.setIconSize(QSize(30, 30))
        self.exit_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                border-radius: 0;
                border: none;
                padding-left: 10px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e57373;
            }
        """)
        self.exit_button.clicked.connect(self.exit_action)

        top_buttons_layout.addWidget(self.update_button)
        top_buttons_layout.addWidget(spacer)
        top_buttons_layout.addWidget(self.exit_button)

        # --- Buttons Start / Stop / Calibrate ---
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.calibrate_button = QPushButton("Calibrage")

        base_style = """
            QPushButton {
                border-radius: 20px;
                color: white;
                font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
                font-size: 25px;
                font-weight: bold;
                border: none;
                padding: 12px;
            }
            QPushButton:disabled {
                background: #a0a0a0 !important;
                color: #d0d0d0 !important;
            }
        """

        self.start_button.setFixedSize(200, 200)
        self.stop_button.setFixedSize(200, 200)
        self.calibrate_button.setFixedSize(200, 200)

        self.start_button.setStyleSheet(base_style + """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #4caf50, stop:1 #2e7d32);
            }
            QPushButton:hover:!disabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #81c784, stop:1 #388e3c);
            }
        """)

        self.stop_button.setStyleSheet(base_style + """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #e53935, stop:1 #b71c1c);
            }
            QPushButton:hover:!disabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #ef9a9a, stop:1 #d32f2f);
            }
        """)

        self.calibrate_button.setStyleSheet(base_style + """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #4facfe, stop:1 #00f2fe);
            }
            QPushButton:hover:!disabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #00f2fe, stop:1 #4facfe);
            }
        """)

        self.stop_button.setEnabled(False)

        self.start_button.clicked.connect(self.start_watcher)
        self.stop_button.clicked.connect(self.stop_watcher)
        self.calibrate_button.clicked.connect(self.calibrate_action)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addSpacing(50)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addSpacing(50)
        buttons_layout.addWidget(self.calibrate_button)
        buttons_layout.addStretch()

        # --- Label LOGS ---
        self.log_label = QLabel("LOGS")
        self.log_label.setAlignment(Qt.AlignCenter)
        self.log_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px 0;")

        # --- Zone de logs avec conteneur pour overlay Clear ---
        self.log_container = QWidget()
        self.log_container.setMinimumHeight(180)
        self.log_container.setStyleSheet("background: transparent;")

        self.log_area = QTextEdit(self.log_container)
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: white; font-family: Consolas, monospace; font-size: 12px;")
        self.log_area.setGeometry(0, 0, 1000, 180)

        self.clear_log_button = QPushButton(self.log_container)
        self.clear_log_button.setFixedSize(60, 30)
        clear_log_icon = QIcon(resource_path("ASSETS/clear.ico"))
        self.clear_log_button.setIcon(clear_log_icon)
        self.clear_log_button.setIconSize(QSize(25, 25))
        self.clear_log_button.setStyleSheet("""
            QPushButton {
                background-color: #777;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.clear_log_button.clicked.connect(self.clear_logs)
        self.clear_log_button.move(self.log_container.width() - self.clear_log_button.width() - 5, 5)
        self.clear_log_button.raise_()

        # --- Layout principal ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        main_layout.addWidget(top_buttons_widget)
        main_layout.addStretch()
        main_layout.addLayout(buttons_layout)
        main_layout.addStretch()
        main_layout.addWidget(self.log_label)
        main_layout.addWidget(self.log_container)

        # --- Background image ---
        bg_path = resource_path("ASSETS/FGbackground.jpg")
        if os.path.exists(bg_path):
            o_pixmap = QPixmap(bg_path).scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            palette = QPalette()
            palette.setBrush(QPalette.Window, QBrush(o_pixmap))
            self.setPalette(palette)
            self.setAutoFillBackground(True)

        # --- Overlay ---
        self.overlay = QWidget(self)
        self.overlay.setStyleSheet("background-color: rgba(255, 255, 255, 180);")
        self.overlay.setGeometry(0, 0, self.width(), self.height())
        self.overlay.lower()
        self.overlay.setAttribute(Qt.WA_TransparentForMouseEvents)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.setGeometry(0, 0, self.width(), self.height())
        self.log_area.setGeometry(0, 0, self.log_container.width(), self.log_container.height())
        self.clear_log_button.move(self.log_container.width() - self.clear_log_button.width() - 5, 5)

    def start_watcher(self):
        try:
            if self.process.state() == QProcess.NotRunning:
                self.log_area.clear()
                self.log_area.append("[INFO] Démarrage du process Watcher.py...")
                print("[INFO] Starting process...")
                self.process.start()  # <-- ici on lance sans argument, setProgram & setArguments ont déjà été fixés

                if not self.process.waitForStarted(5000):
                    self.log_area.append("[ERROR] Le process n'a pas démarré dans le temps imparti.")
                    print("[ERROR] Process failed to start.")
                    return

                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
            else:
                self.log_area.append("[WARNING] Le process est déjà en cours.")
        except Exception as e:
            self.log_area.append(f"[ERROR] Exception lors du démarrage: {e}")

    def stop_watcher(self):
        if self.process.state() == QProcess.Running:
            self.process.terminate()
            if not self.process.waitForFinished(3000):
                self.process.kill()
            self.log_area.append("[INFO] Process arrêté.")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
        else:
            self.log_area.append("[WARNING] Aucun process à arrêter.")

    def calibrate_action(self):
        self.log_area.append("[ACTION] Calibrage déclenché.")
        # Ajouter ici la logique spécifique au calibrage

    def update_action(self):
        self.log_area.append("[ACTION] Vérification / mise à jour déclenchée.")
        # Ajouter ici la logique de mise à jour

    def exit_action(self):
        self.log_area.append("[ACTION] Fermeture de l'application...")
        self.stop_watcher()
        self.close()

    def clear_logs(self):
        self.log_area.clear()

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode("utf-8")
        self.log_area.append(text)

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        text = bytes(data).decode("utf-8")
        self.log_area.append(f"[ERR] {text}")

    def process_started(self):
        self.log_area.append("[INFO] Process démarré.")

    def process_finished(self, exitCode, exitStatus):
        self.log_area.append(f"[INFO] Process terminé avec le code {exitCode}.")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def process_error(self, error):
        self.log_area.append(f"[ERROR] Erreur process: {error}")

def resource_path(relative_path):
    # Définition simple ici, adapter selon ton environnement
    base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WatcherGUI()
    window.show()
    sys.exit(app.exec())
