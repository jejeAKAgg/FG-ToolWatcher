# GUI/__assets/widgets/table.py

import logging
import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget


LOG = logging.getLogger(__name__)

class ComparisonTable(QTableWidget):

    """
    A customized QTableWidget for displaying price comparisons.
    Handles its own styling, column resizing, and URL click events.
    """

    COLUMN_HEADERS = [
        "EAN", "MPN", "Article", "Georges (€)", "Clabots (€)", "Fixami (€)",
        "Klium (€)", "Lecot (€)", "Toolnation (€)"
    ]

    def __init__(self, parent=None):
        super().__init__(0, 9, parent)

        # --- CONFIGURATION ---
        self.setHorizontalHeaderLabels(self.COLUMN_HEADERS)

        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.setMouseTracking(True)

        # Resizing
        for i, header in enumerate(self.COLUMN_HEADERS):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # --- STYLING ---
        self._apply_style()

        # --- EVENTS ---
        self.cellEntered.connect(self._on_cell_entered)
        self.cellClicked.connect(self._on_cell_clicked)

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget {
                color: #E0E0E0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }
            QTableWidget {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 6px;
                alternate-background-color: #252526;
                outline: none;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #333333;
            }
            QTableWidget::item:selected {
                background-color: #3A86FF;
                color: white;
            }
            QHeaderView::section {
                background-color: #2D2D30;
                color: #A0A0A0;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #00913e;
                font-weight: bold;
                text-transform: uppercase;
            }
            QScrollBar:vertical {
                border: none;
                background: #121212;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #3A3A3A;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #555555;
            }
        """)

    def _on_cell_entered(self, row, column):
        item = self.item(row, column)
        if item is not None:
            url = item.data(Qt.ItemDataRole.UserRole)
            if url:
                self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.viewport().setCursor(Qt.CursorShape.ArrowCursor)

    def _on_cell_clicked(self, row, column):
        item = self.item(row, column)
        if item is not None:
            url = item.data(Qt.ItemDataRole.UserRole)
            if url:
                LOG.debug(f"Opening URL: {url}")
                webbrowser.open(url)
