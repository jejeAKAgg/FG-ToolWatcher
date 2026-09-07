# GUI/Desktop/pages/dashboard.py

import logging
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLayout,
    QStackedWidget, QVBoxLayout, QWidget
)

from CORE.Services.setup import *
from CORE.Services.translator import TranslatorService
from CORE.Services.user import UserService

from GUI.Desktop.pages.subpages.dashboard.quickadd import QuickAddDialog

from GUI.__assets.layouts.bottom_buttons import create_bottom_bar
from GUI.__assets.layouts.top_buttons import create_top_bar
from GUI.__assets.widgets.buttons import (
    DashboardAnalyseButton, DashboardButton,
    DashboardCheckableButton, DashboardTaxSwitchButton
)
from GUI.__assets.widgets.search_bar import SearchBarDashboard
from GUI.__assets.widgets.table import ComparisonTable
from GUI.__assets.widgets.toast import ToastNotification


LOG = logging.getLogger(__name__)

class DashboardPage(QWidget):

    """
    Main widget for the "Dashboard" page.
    Contains controls to search articles, update prices,
    analyze margins, and a data table.
    """

    def __init__(self, config: UserService, translator: TranslatorService, parent=None):

        """
        Initializes the dashboard page.

        Args:
            config (UserService): The user configuration service.
            translator (TranslatorService): The translator service.
            parent (Optional[QWidget]): The parent widget.
        """
        super().__init__(parent)

        # === INTERNAL SERVICE(S) ===
        self.config = config
        self.translator = translator

        # === UI BUILDER(S) ===
        self._build_ui()


    # === PUBLIC METHOD(S) ===
    def retranslate_ui(self):

        """
        Updates the text of every widget of the application depending on the new user language input.
        """
        LOG.debug("Retranslating UI in DashboardPage...")

        self.search_bar.setPlaceholderText(self.translator.get("page_menu_search.bar"))
        self.lbl_htva.setText(self.translator.get("page_menu_tax_toggle_off.label"))
        self.lbl_tva.setText(self.translator.get("page_menu_tax_toggle_on.label"))

    # === PRIVATE METHOD(S) ===
    def _build_ui(self):

        """
        Builds the graphical user interface for the main dashboard using reusable layouts.
        """
        LOG.debug("Building UI for DashboardPage...")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # --- TOP BAR (Search & Actions) ---
        self.search_bar = SearchBarDashboard(placeholder=self.translator.get("page_menu_search.bar"))

        # Quick Add Button
        self.btn_quick_add = DashboardButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "quickadd_White.svg"))

        # --- TAX SWITCH BUTTON ---
        self.btn_tax_toggle = DashboardTaxSwitchButton()

        # Tax Switch internal layout
        self.toggle_layout = QHBoxLayout(self.btn_tax_toggle)
        self.toggle_layout.setContentsMargins(15, 0, 15, 0)
        self.toggle_layout.setSpacing(8)
        self.toggle_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self.lbl_htva = QLabel(self.translator.get("page_menu_tax_toggle_off.label"))
        self.lbl_htva.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_htva.setStyleSheet("background-color: transparent; color: #00913e; font-weight: bold; font-size: 13px;")
        self.lbl_htva.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.lbl_switch_icon = QLabel()
        self.lbl_switch_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_switch_icon.setStyleSheet("background-color: transparent;")
        self.lbl_switch_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Load and recolor SVG
        raw_svg = open(os.path.join(ASSETS_FOLDER, "icons", "switch_White.svg"), "rb").read()
        white_svg = raw_svg.replace(b"#000000", b"#FFFFFF").replace(b"currentColor", b"#FFFFFF")
        self.lbl_switch_icon.setPixmap(QPixmap.fromImage(QImage.fromData(white_svg)).scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        self.lbl_tva = QLabel(self.translator.get("page_menu_tax_toggle_on.label"))
        self.lbl_tva.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_tva.setStyleSheet("background-color: transparent; color: #555555; font-weight: bold; font-size: 13px;")
        self.lbl_tva.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.toggle_layout.addWidget(self.lbl_htva)
        self.toggle_layout.addWidget(self.lbl_switch_icon)
        self.toggle_layout.addWidget(self.lbl_tva)

        # --- TOP BAR ---
        TOP_BAR = create_top_bar(
            left_widgets=[self.search_bar, self.btn_quick_add],
            center_widgets=None,
            right_widgets=[self.btn_tax_toggle],
            margins=0
        )
        self.main_layout.addWidget(TOP_BAR)

        # --- PAGES MANAGER ---
        self.stacked_widget = QStackedWidget()

        # --- COMPARISON TABLE ---
        self.table = ComparisonTable()

        # --- COMPARISON GRAPHS ---
        self.graph_page = QWidget()
        self.graph_layout = QVBoxLayout(self.graph_page)

        self.graph_placeholder = QLabel("📊 Visual analysis zone under construction...")
        self.graph_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.graph_placeholder.setStyleSheet("font-size: 24px; color: #555555;")
        self.graph_layout.addWidget(self.graph_placeholder)

        # --- PAGE(S) ---
        self.stacked_widget.addWidget(self.table)        # index 0
        self.stacked_widget.addWidget(self.graph_page)   # index 1

        self.main_layout.addWidget(self.stacked_widget)

        # --- BOTTOM BAR (Exports & Actions) ---
        self.btn_update = DashboardButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "refresh_White.svg"))
        self.btn_save = DashboardButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "save_White.svg"))
        self.btn_email = DashboardButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "mail_White.svg"))
        self.btn_analyze = DashboardAnalyseButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "analyze_White.svg"))
        self.btn_filter = DashboardButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "filter_White.svg"))
        self.btn_view_toggle = DashboardCheckableButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "table_White.svg"))

        # Applying the reusable bottom bar layout with a stretch in the middle
        BOTTOM_BAR = create_bottom_bar(
            widgets=[
                self.btn_update,
                self.btn_save,
                self.btn_email,
                self.btn_analyze,
                "STRETCH",
                self.btn_filter,
                self.btn_view_toggle
            ],
            margins=0
        )
        self.main_layout.addWidget(BOTTOM_BAR)

        # --- EVENT(S) ---
        self.btn_tax_toggle.toggled.connect(self._on_tax_toggled)
        self.btn_quick_add.clicked.connect(self._open_quick_add_dialog)
        self.btn_filter.clicked.connect(self._open_filter_dialog)
        self.btn_view_toggle.toggled.connect(self._on_view_toggled)

    def _on_tax_toggled(self, checked):
        """
        Triggered when the tax toggle button is clicked.
        Updates the UI text and signals that the table data should reflect HTVA or TVAC.
        """
        if checked:
            # TVAC mode ACTIVE
            self.lbl_htva.setStyleSheet("background-color: transparent; color: #555555; font-weight: bold; font-size: 13px;")
            self.lbl_tva.setStyleSheet("background-color: transparent; color: #00913e; font-weight: bold; font-size: 13px;")
            LOG.debug("Tax switch activated: TVAC mode.")
        else:
            # HTVA mode ACTIVE
            self.lbl_htva.setStyleSheet("background-color: transparent; color: #00913e; font-weight: bold; font-size: 13px;")
            self.lbl_tva.setStyleSheet("background-color: transparent; color: #555555; font-weight: bold; font-size: 13px;")
            LOG.debug("Tax switch deactivated: HTVA mode.")

    def _on_view_toggled(self, checked):
        """
        Triggered when the view toggle button is clicked.
        Switches between the Table view (index 0) and the Graph view (index 1).
        """
        if checked:
            raw_svg = open(os.path.join(ASSETS_FOLDER, "icons", "graph_White.svg"), "rb").read()
            white_svg = raw_svg.replace(b"#000000", b"#FFFFFF").replace(b"currentColor", b"#FFFFFF")
            self.btn_view_toggle.setIcon(QIcon(QPixmap.fromImage(QImage.fromData(white_svg))))

            self.stacked_widget.setCurrentIndex(1)
            LOG.debug("Switched to Graph View.")

            # Show a temporary notification
            toast = ToastNotification(parent=self.window(), message="Graph view activated", duration=3000)
            toast.show_toast()
        else:
            raw_svg = open(os.path.join(ASSETS_FOLDER, "icons", "table_White.svg"), "rb").read()
            white_svg = raw_svg.replace(b"#000000", b"#FFFFFF").replace(b"currentColor", b"#FFFFFF")
            self.btn_view_toggle.setIcon(QIcon(QPixmap.fromImage(QImage.fromData(white_svg))))

            self.stacked_widget.setCurrentIndex(0)
            LOG.debug("Switched to Table View.")

    def _open_quick_add_dialog(self):
        """
        Opens the dialog for selecting brands and categories to add to the dashboard.
        """
        LOG.debug("Opening 'Quick Add' dialog...")

        # TODO: These lists should be retrieved dynamically via an SQLite query
        fake_brands = ["Makita", "Bosch", "DeWalt", "Wiha"]
        fake_categories = ["Drills", "Screwdrivers", "Workwear", "PPE"]

        dialog = QuickAddDialog(brands=fake_brands, categories=fake_categories, parent=self)

        # .exec() blocks the main application loop until the window is closed
        if dialog.exec():
            selected_brand, selected_category = dialog.get_selection()
            LOG.debug(f"Batch validated -> Brand: {selected_brand} | Category: {selected_category}")

            # --- ADDITION LOGIC ---
            # Construct the SQL query with dynamic requests (AND Brand = ? AND Category = ?)
            # then add the results to self.config.set_catalog_items(...)

    def _open_filter_dialog(self):
        """
        Opens the dialog for filtering specific websites or tool states.
        """
        LOG.debug("Opening 'Filter' dialog...")
        return
