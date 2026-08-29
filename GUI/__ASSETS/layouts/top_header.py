# GUI/__assets/layouts/top_header.py

import os

from PySide6.QtGui import QFont, QFontDatabase, QPixmap, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from CORE.Services.setup import ASSETS_FOLDER

def create_header(widgets: list) -> QWidget:

    """
    Creates a generic horizontal header layout from a list of items.
    Use "STRETCH" or None to insert flexible spaces.
    """
    container = QWidget()

    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(15)

    for item in widgets:
        if item is None or item == "STRETCH":
            layout.addStretch()
        else:
            layout.addWidget(item)

    return container

def create_logo_widget(image_path: str, size: tuple = (120, 120)) -> QLabel:
    """Helper to create a QLabel containing a scaled image."""
    label = QLabel()
    label.setAlignment(Qt.AlignCenter)
    if os.path.exists(image_path):
        pixmap = QPixmap(image_path).scaled(size[0], size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(pixmap)
    return label

def create_title_widget(text: str, font_size: int = 28, text_color: str = "#000000") -> QLabel:
    """Helper to create a stylized title label using Montserrat."""
    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)

    font_path = os.path.join(ASSETS_FOLDER, "fonts", "Montserrat-Black.ttf")

    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            custom_font = QFont(font_family, font_size, QFont.Weight.Black)
            label.setFont(custom_font)
    else:
        label.setFont(QFont("Arial Black", font_size, QFont.Weight.Black))

    label.setStyleSheet(f"color: {text_color}; letter-spacing: 2px;")
    return label
