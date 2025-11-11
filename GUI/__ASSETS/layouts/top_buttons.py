# GUI/__ASSETS/layouts/top_buttons.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QGridLayout
from PySide6.QtCore import Qt

def create_top_buttons(update_button, profile_button, settings_button, english_button, french_button, netherlands_button):
    
    """
    Creates the main top bar, with the language bar
    perfectly centered using a QGridLayout.
    """
    
    container = QWidget()

    layout = QGridLayout(container)
    layout.setContentsMargins(5, 5, 5, 5)
    layout.setSpacing(10)
    
    # --- LEFT top side ---
    left_layout = QHBoxLayout()
    left_layout.setSpacing(15)
    left_layout.addWidget(settings_button)
    left_layout.addWidget(update_button)
    
    # --- MID top side ---
    center_layout = QHBoxLayout()
    center_layout.setSpacing(10) 
    center_layout.addWidget(english_button)
    center_layout.addWidget(french_button)
    center_layout.addWidget(netherlands_button)
    
    # --- RIGHT top side ---
    right_layout = QHBoxLayout()
    right_layout.setSpacing(15)
    right_layout.addWidget(profile_button)

    # --- Assembling and attributing weight to each column ---
    layout.addLayout(left_layout, 0, 0, Qt.AlignmentFlag.AlignLeft)
    layout.addLayout(center_layout, 0, 1, Qt.AlignmentFlag.AlignCenter)
    layout.addLayout(right_layout, 0, 2, Qt.AlignmentFlag.AlignRight)

    layout.setColumnStretch(0, 1)
    layout.setColumnStretch(1, 0)
    layout.setColumnStretch(2, 1)
    
    return container