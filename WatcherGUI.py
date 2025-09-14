import os
import sys

from APP.pages.MAINpage import MainPage
from APP.pages.SETTINGSpage import SettingsPage
from APP.pages.MPNpage import CalibrationPage
from APP.pages.SETUPpage import *  # <-- à créer si pas déjà fait
from APP.widgets.FADEtransition import FadeTransition



from APP.layouts.BOTTOMbuttons import create_bottom_buttons
from APP.layouts.TOPbuttons import create_top_buttons
from APP.layouts.TOPheader import create_header
from APP.widgets.MAINbackground import BackgroundOverlay
from APP.widgets.PUSHbuttons import CustomPushButton


from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtWidgets import QStackedLayout

from UTILS.LOGmaker import *
from UTILS.TOOLSbox import *


class WatcherGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FG-ToolWatcher")
        self.setGeometry(300, 300, 1000, 700)
        self.setFixedSize(1000, 700)

        # --- Icône de fenêtre ---
        icon_path = os.path.join(BASE_TEMP_PATH, "ASSETS", "FG-TWicoBG.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # --- Background ---
        self.background_widget = BackgroundOverlay(
            bg_path=os.path.join(BASE_TEMP_PATH, "ASSETS", "FGbackground.jpg"),
            parent=self
        )
        self.background_widget.setGeometry(0, 0, self.width(), self.height())
        self.background_widget.lower()

        # --- TOP BAR UTILS buttons & TITLE ---
        self.update_button = CustomPushButton(os.path.join(BASE_TEMP_PATH, "ASSETS", "update.ico"))
        self.profile_button = CustomPushButton(os.path.join(BASE_TEMP_PATH, "ASSETS", "profile.ico"))
        self.settings_button = CustomPushButton(os.path.join(BASE_TEMP_PATH, "ASSETS", "settings.ico"))
        
        self.update_button.clicked.connect(self.restart_setup)
        self.settings_button.clicked.connect(self.toggle_settings)

        TOP_BAR = create_top_buttons(self.update_button, self.profile_button, self.settings_button)
        HEADER = create_header("FG-ToolWatcher", os.path.join(BASE_TEMP_PATH, "ASSETS", "FG-TWicoBG.ico"))

        # --- BOTTOM BAR UTILS buttons ---
        self.info_button = CustomPushButton(os.path.join(BASE_TEMP_PATH, "ASSETS", "info.ico"))
        self.ticket_button = CustomPushButton(os.path.join(BASE_TEMP_PATH, "ASSETS", "problem.ico"))
        self.github_button = CustomPushButton(os.path.join(BASE_TEMP_PATH, "ASSETS", "github.ico"))

        BOTTOM_BAR = create_bottom_buttons(self.info_button, self.ticket_button, self.github_button)

        # --- Pages ---
        self.stack = QStackedLayout()
        self.stack_container = QWidget()

        self.setup_page = SetupPage(update_button=self.update_button, profile_button=self.profile_button, settings_button=self.settings_button, parent=self.stack_container)
        self.main_page = MainPage(update_button=self.update_button, profile_button=self.profile_button, settings_button=self.settings_button, parent=self.stack_container)
        self.calibration_page = CalibrationPage(update_button=self.update_button, profile_button=self.profile_button, settings_button=self.settings_button, parent=self.stack_container)
        self.settings_page = SettingsPage(update_button=self.update_button, profile_button=self.profile_button, settings_button=self.settings_button, parent=self.stack_container)

        self.transition = FadeTransition(self.stack)

        self.setup_page.setup_finished.connect(self.show_main_page)
        self.main_page.calibrate_button.clicked.connect(self.toggle_calibration)

        self.stack.addWidget(self.setup_page)       # index 0
        self.stack.addWidget(self.main_page)        # index 1
        self.stack.addWidget(self.calibration_page) # index 2
        self.stack.addWidget(self.settings_page)    # index 3

        self.stack_container.setLayout(self.stack)

        # --- Layout principal ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(20)
        
        main_layout.addWidget(TOP_BAR)
        main_layout.addWidget(HEADER)
        main_layout.addWidget(self.stack_container)
        main_layout.addWidget(BOTTOM_BAR)
        
        main_layout.addStretch()


    # ---------------- Fonctions ----------------
    def restart_setup(self):
        self.setup_page.label.setText("Préparation de l'application...")  # reset texte
        self.setup_page.start_setup()  # relance du thread
        self.transition.fade_to(self.setup_page)


    def show_main_page(self):
        self.transition.fade_to(self.main_page)

    def toggle_calibration(self):
        if self.stack.currentIndex() != 2:
            self.stack.setCurrentIndex(2)
            self.pushbuttons_action()
        else:
            self.stack.setCurrentIndex(1)
            self.pushbuttons_action()

    def toggle_settings(self):
            if self.stack.currentIndex() == 1:
                self.stack.setCurrentIndex(3)
                self.pushbuttons_action()
                self.update_button.setEnabled(False)
                self.profile_button.setEnabled(False)
            else:
                self.stack.setCurrentIndex(1)
                self.pushbuttons_action()
                self.update_button.setEnabled(True)
                self.profile_button.setEnabled(True)

    def pushbuttons_action(self):
        if self.stack.currentIndex() != 1 :
            self.settings_button.setText("Menu")
        else:
            self.settings_button.setText("")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WatcherGUI()
    window.show()
    sys.exit(app.exec())