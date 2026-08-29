# GUI/__assets/layouts/bottom_buttons.py

from PySide6.QtWidgets import QHBoxLayout, QWidget

def create_bottom_bar(widgets: list, margins: int | list | tuple = 5) -> QWidget:

    """
    Creates a generic horizontal layout bar from a list of items.

    Args:
        widgets (list): A list of PySide6 widgets to add to the layout.
                        Use the string "STRETCH" or None within the list
                        to insert a flexible space (spacer) between widgets.

    Returns:
        QWidget: A container widget holding the configured horizontal layout.
    """
    container = QWidget()

    layout = QHBoxLayout(container)
    layout.setContentsMargins(*(margins if isinstance(margins, (list, tuple)) else [margins] * 4))
    layout.setSpacing(10)

    for item in widgets:
        if item is None or item == "STRETCH":
            layout.addStretch()
        else:
            layout.addWidget(item)

    return container
