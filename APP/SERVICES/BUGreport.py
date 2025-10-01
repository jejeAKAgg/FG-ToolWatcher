# APP/widgets/BUGreport.py

import os
import glob

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox

from APP.SERVICES.__init__ import *

from APP.UTILS.TOOLSbox import *


class BugReportDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.config = config

        self.setWindowTitle("Signaler un problème")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Décrivez votre problème :"))
        self.description = QTextEdit()
        self.description.setPlaceholderText("Expliquez ce qui s'est passé...")
        layout.addWidget(self.description)

        send_button = QPushButton("Envoyer")
        send_button.clicked.connect(self.send_report)
        layout.addWidget(send_button)

    def send_report(self):
        desc = self.description.toPlainText().strip()
        log_file = self.get_last_log_file(LOGS_SUBFOLDER)
        
        if not desc:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer une description.")
            return
        
        if not log_file:
            QMessageBox.warning(self, "Erreur", "Aucun fichier log trouvé.")
            return

        try:
            MAILconfig = JSONloader(os.path.join(BASE_TEMP_PATH, "APP", "CONFIGS", "EMAILconfig.json"))
            body = f"De: {self.config.get('user_lastname')} {self.config.get('user_firstname')}.\n\n Description du problème:\n{desc}.\n\n\n Contact: {self.config.get('user_mail')}"
            MAILsender(
                sender_email=MAILconfig["Source"],
                password=MAILconfig["Password"],
                recipient_email=MAILconfig["Target_REPORT"],
                subject=MAILconfig["Subject_REPORT"],
                body=body,
                filename=log_file
            )
            QMessageBox.information(self, "Succès", "Le rapport a été envoyé avec succès.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec de l'envoi du rapport : {e}")

    def get_last_log_file(self, logs_folder):
        log_files = glob.glob(os.path.join(logs_folder, "*.log"))
        if not log_files:
            return None
        return max(log_files, key=os.path.getctime)  # plus récent par date de création

