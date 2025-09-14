# layouts/BOTTOMbuttons.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QMessageBox
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from APP.widgets.BUGreport import *

def create_bottom_buttons(info_button, ticket_button, github_button, version="V0.1"):
    """
    Crée une barre de boutons en bas de la fenêtre.
    - info_button : bouton pour afficher les infos
    - github_button : bouton pour ouvrir GitHub
    - version : version du programme affichée dans le message info
    """
    container = QWidget()
    
    layout = QHBoxLayout(container)
    layout.setContentsMargins(5, 5, 5, 5)
    layout.setSpacing(0)
    
    # Spacer pour séparer les boutons
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    
    # Connexions
    info_button.clicked.connect(lambda: show_info(version, parent=container))
    ticket_button.clicked.connect(lambda: open_bug_report())
    github_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/jejeAKAgg/FG-ToolWatcher")))
    
    # Ajouter les boutons au layout
    layout.addWidget(info_button)
    layout.setSpacing(15)
    layout.addWidget(ticket_button)
    layout.addWidget(spacer)
    layout.addWidget(github_button)
    
    return container

def open_bug_report():
    log_file = get_last_log_file(LOGS_FOLDER)
    dialog = BugReportDialog(log_file)
    dialog.exec()

def get_last_log_file(logs_folder):
    log_files = glob.glob(os.path.join(logs_folder, "*.log"))
    if not log_files:
        return None
    return max(log_files, key=os.path.getctime)  # plus récent par date de création


def show_info(version, parent=None):
    """Affiche une fenêtre d'information avec le créateur et la version"""
    QMessageBox.information(parent, "À propos", f"Créé par Jérôme LECHAT\nVersion : {version}")