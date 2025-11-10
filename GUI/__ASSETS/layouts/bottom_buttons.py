# GUI/__ASSETS/layouts/bottom_buttons.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QSizePolicy


def create_bottom_buttons(info_button, ticket_button, github_button) -> QWidget:
    
    """
    Creates a button bar at the bottom of the window.
    Args:
        info_button (QPushButton): Button to display application information.
        github_button (QPushButton): Button to open the project's GitHub page.
        version (str): Program version displayed in the info message.
    """
    
    container = QWidget()
    
    layout = QHBoxLayout(container)
    layout.setContentsMargins(5, 5, 5, 5)
    layout.setSpacing(10)
    
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    layout.addWidget(info_button)
    layout.setSpacing(15)
    layout.addWidget(ticket_button)
    layout.addWidget(spacer)
    layout.addWidget(github_button)
    
    return container