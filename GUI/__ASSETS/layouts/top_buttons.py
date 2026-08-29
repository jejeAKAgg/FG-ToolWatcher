# GUI/__assets/layouts/top_buttons.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QWidget


def create_top_bar(left_widgets: list = None, center_widgets: list = None, right_widgets: list = None, margins: int | list | tuple = 5) -> QWidget:

    """
    Creates the main top bar with three distinct layout zones (left, center, right),
    ensuring the center zone is perfectly aligned in the middle using a QGridLayout.

    Args:
        left_widgets (list, optional): Widgets to display on the left.
        center_widgets (list, optional): Widgets to display perfectly centered.
        right_widgets (list, optional): Widgets to display on the right.

    Note:
        You can use the string "STRETCH" or None within any of these lists
        to insert a flexible space between items in that specific zone.

    Returns:
        QWidget: A container widget holding the configured grid layout.
    """
    container = QWidget()

    layout = QGridLayout(container)
    layout.setContentsMargins(*(margins if isinstance(margins, (list, tuple)) else [margins] * 4))
    layout.setSpacing(10)

    # Helper function to generate a QHBoxLayout for each zone
    def build_zone_layout(widgets, default_spacing=15):
        zone_layout = QHBoxLayout()
        zone_layout.setSpacing(default_spacing)

        if widgets:
            for item in widgets:
                if item is None or item == "STRETCH":
                    zone_layout.addStretch()
                else:
                    zone_layout.addWidget(item)
        return zone_layout

    # --- Build the 3 zones ---
    left_layout = build_zone_layout(left_widgets, default_spacing=15)
    center_layout = build_zone_layout(center_widgets, default_spacing=10)
    right_layout = build_zone_layout(right_widgets, default_spacing=15)

    # --- Assembling and attributing weight to each column ---
    layout.addLayout(left_layout, 0, 0, Qt.AlignmentFlag.AlignLeft)
    layout.addLayout(center_layout, 0, 1, Qt.AlignmentFlag.AlignCenter)
    layout.addLayout(right_layout, 0, 2, Qt.AlignmentFlag.AlignRight)

    layout.setColumnStretch(0, 1)
    layout.setColumnStretch(1, 0)
    layout.setColumnStretch(2, 1)

    return container
