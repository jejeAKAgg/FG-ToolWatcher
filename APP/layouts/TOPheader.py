# layouts/header.py
import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtGui import QPixmap, Qt

def create_header(title_text, logo_path, logo_size=(120, 120)):
    """
    Crée un header avec logo + titre centré.
    """
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0,0,0,0)
    layout.setSpacing(15)

    # Logo
    logo_label = QLabel()
    logo_label.setAlignment(Qt.AlignCenter)
    if os.path.exists(logo_path):
        logo_pixmap = QPixmap(logo_path).scaled(logo_size[0], logo_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)

    # Titre
    title_label = QLabel(title_text)
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

    # Ajouter les widgets au layout avec stretches pour centrer
    layout.addStretch()
    layout.addWidget(logo_label)
    layout.addWidget(title_label)
    layout.addStretch()

    return container
