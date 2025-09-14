# layouts/top_buttons.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy

def create_top_buttons(update_button, profile_button, settings_button):
    container = QWidget()
    
    layout = QHBoxLayout(container)
    layout.setContentsMargins(5,5,5,5)
    layout.setSpacing(0)
    
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    
    layout.addWidget(settings_button)
    layout.addSpacing(15)
    layout.addWidget(update_button)
    layout.addWidget(spacer)
    layout.addWidget(profile_button)
    
    return container