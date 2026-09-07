# GUI/Desktop/pages/subpages/dashboard/quickadd.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class QuickAddDialog(QDialog):

    """Modal dialog allowing selection of a brand and/or category

    for batch addition to the catalog.
    """

    def __init__(self, brands: list[str], categories: list[str], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ajout Rapide par Lot")
        self.setFixedSize(450, 260)

        # --- Modal-specific stylesheet ---
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
                color: #E0E0E0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }
            QLabel {
                font-weight: bold;
                color: #A0A0A0;
                margin-top: 5px;
            }
            QComboBox {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 5px 10px;
                min-height: 35px;
                color: white;
            }
            QComboBox:focus { border: 1px solid #3A86FF; }
            QPushButton {
                background-color: #2D2D30;
                border: 1px solid #3E3E42;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover { background-color: #3E3E42; }
            QPushButton#BtnAdd { background-color: #007e2d; border: none; }
            QPushButton#BtnAdd:hover { background-color: #006022; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Dropdown menus ---
        self.combo_brand = QComboBox()
        self.combo_brand.addItem("Toutes les marques")
        self.combo_brand.addItems(brands)

        self.combo_category = QComboBox()
        self.combo_category.addItem("Toutes les catégories")
        self.combo_category.addItems(categories)

        layout.addWidget(QLabel("Filtrer par Marque :"))
        layout.addWidget(self.combo_brand)

        layout.addWidget(QLabel("Filtrer par Catégorie :"))
        layout.addWidget(self.combo_category)

        layout.addStretch()

        # --- Action buttons ---
        btn_layout = QHBoxLayout()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)  # Closes dialog without action

        self.btn_add = QPushButton("Ajouter le lot")
        self.btn_add.setObjectName("BtnAdd")
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.clicked.connect(self.accept)  # Closes dialog and confirms

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_add)

        layout.addLayout(btn_layout)

    def get_selection(self) -> tuple[str | None, str | None]:
        """Returns the selected (brand, category) tuple.

        Returns None for a field if 'Toutes les...' is selected.
        """
        brand = self.combo_brand.currentText()
        category = self.combo_category.currentText()

        return (
            brand if brand != "Toutes les marques" else None,
            category if category != "Toutes les catégories" else None,
        )
