# APP/layouts/BOTTOMbuttons.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QSizePolicy


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
    
    # Ajouter les boutons au layout
    layout.addWidget(info_button)
    layout.setSpacing(15)
    layout.addWidget(ticket_button)
    layout.addWidget(spacer)
    layout.addWidget(github_button)
    
    return container