from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox
import os
from UTILS.TOOLSbox import *
import glob

class BugReportDialog(QDialog):
    def __init__(self, log_file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Signaler un problème")
        self.setMinimumSize(400, 300)

        self.log_file_path = log_file_path

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
        if not desc:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer une description.")
            return

        if not self.log_file_path or not os.path.exists(self.log_file_path):
            QMessageBox.warning(self, "Erreur", "Aucun fichier log trouvé.")
            return

        try:
            MAILconfig = JSONloader(os.path.join(BASE_TEMP_PATH, "CONFIGS", "EMAILconfig.json"))
            body = f"Description utilisateur:\n{desc}\n\nLog joint automatiquement ({os.path.basename(self.log_file_path)})."

            MAILsender(
                sender_email=MAILconfig["Source"],
                password=MAILconfig["Password"],
                recipient_email=MAILconfig["Target"],  # ton adresse
                subject="[Bug Report] FG-ToolWatcher",
                body=body,
                filename=self.log_file_path
            )
            QMessageBox.information(self, "Succès", "Le rapport a été envoyé avec succès.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec de l'envoi du rapport : {e}")