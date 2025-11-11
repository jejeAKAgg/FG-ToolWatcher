# GUI/Desktop/pages/menu.py
import os

import CORE.Manager as Manager

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout
)

from CORE.Services.setup import *
from CORE.Services.user import UserService
from CORE.Services.translator import TranslatorService

from GUI.__ASSETS.widgets.main_buttons import CustomMainButton
from GUI.__ASSETS.widgets.regular_progress_bar import CustomProgressBar



class MainPage(QWidget):
    
    """
    Main widget for the "Main" page (Home).
    Contains controls to start/stop monitoring, a progress bar,
    and a button to access articles/refs.
    """

    calibration_requested = Signal()

    def __init__(self, config: UserService, translator: TranslatorService, parent = None):
        
        """
        Initializes the main page.

        Args:
            config (UserService): The user configuration service.
            update_button (CustomMainButton): External update button.
            settings_button (CustomMainButton): External settings button.
            profile_button (CustomMainButton): External profile button.
            parent (Optional[QWidget]): The parent widget.
        """
        
        super().__init__(parent)

        # === SERVICES & PARAMÈTRES ===
        self.config_service = config
        self.translator_service = translator

        # === THREAD WATCHER ===
        self.watcher_thread = WatcherThread(config=self.config_service, translator=translator, parent=self)
        self.watcher_thread.progress.connect(self.update_progress)
        self.watcher_thread.error.connect(self.on_watcher_error)
        self.watcher_thread.finished.connect(self.on_watcher_finished)

        # === WIDGETS UI ===
        # --- Boutons Start/Stop/Calibrage ---
        self.start_button = CustomMainButton(
            text="Start",
            icon_path=os.path.join(ASSETS_FOLDER, "icons", "play.ico"),
            gradient=("#4caf50", "#2e7d32")
        )
        self.stop_button = CustomMainButton(
            text="Stop",
            icon_path=os.path.join(ASSETS_FOLDER, "icons", "stop.ico"),
            gradient=("#e53935", "#b71c1c")
        )
        self.calibrate_button = CustomMainButton(
            text="REFs/Articles",
            icon_path=os.path.join(ASSETS_FOLDER, "icons", "MPN.ico"),
            gradient=("#137BD6", "#218DEB")
        )
        self.stop_button.setEnabled(False)

        # --- Barre de progression ---
        self.progress_widget = CustomProgressBar()

        # === LAYOUT ===
        # --- Layout boutons ---
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addSpacing(50)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addSpacing(50)
        buttons_layout.addWidget(self.calibrate_button)
        buttons_layout.addStretch()

        # --- Layout principal ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        main_layout.addLayout(buttons_layout)
        main_layout.addSpacing(75)
        main_layout.addWidget(self.progress_widget)
        main_layout.addStretch()

        # === CONNEXIONS ===
        self.start_button.clicked.connect(self.start_watcher)
        self.stop_button.clicked.connect(self.stop_watcher)
        self.calibrate_button.clicked.connect(self.request_calibration)


    def start_watcher(self):
        
        """
        Starts the watcher thread and updates the UI state.
        """
        
        if not self.watcher_thread.isRunning():
            self.progress_widget.reset()
            self.watcher_thread.start()
            self.set_controls_enabled(False)

    def stop_watcher(self):
        
        """
        Signals the watcher thread to stop gracefully and waits for it.
        """
        
        if self.watcher_thread.isRunning():
            print("[MainPage] Requesting watcher thread interruption...") # Debug print
            self.watcher_thread.requestInterruption() # Signal the thread to stop
                    
            print("[MainPage] Waiting for watcher thread to finish...") # Debug print


            if not self.watcher_thread.wait(5000): # Wait up to 5 seconds
                self.watcher_thread.terminate()
                self.watcher_thread.wait() # Waiting for force-terminate to be finished
                print("[MainPage] Warning: Watcher thread did not finish cleanly after 5s!")

            print("[MainPage] Watcher thread stopped.")

            self.progress_widget.reset()
            self.set_controls_enabled(True)
        else:
             print("[MainPage] stop_watcher called but thread wasn't running.") # Debug print

    def on_watcher_finished(self):
        
        """
        Slot executed when the watcher thread finishes normally.
        """
        
        if self.progress_widget.value() < 100:
             self.progress_widget.reset()
             
        self.set_controls_enabled(True)

    def on_watcher_error(self, error_msg: str):
        
        """
        Slot executed if the thread emits an error signal.
        """
        
        print(f"Erreur du WatcherThread : {error_msg}")

        self.set_controls_enabled(True)
        self.progress_widget.reset() # Reset the bar if an error occured

    def update_progress(self, value: int):
        
        """
        Updates the progress bar with the value received from the thread.
        """
        
        self.progress_widget.set_value(value)

    def request_calibration(self):
        
        """
        Emits a signal to request showing the calibration page.
        """
        
        self.calibration_requested.emit()

    def set_controls_enabled(self, enabled: bool):
        
        """
        Enables or disables all interactive controls while
        the watcher is running.

        Args:
            enabled (bool): True to enable, False to disable.
        """
        
        self.start_button.setEnabled(enabled)
        self.stop_button.setEnabled(not enabled)

        self.calibrate_button.setEnabled(enabled)

    def retranslate_ui(self):
        
        """
        Update the texte of every widget of the application depending the new user language input.
        """
        
        pass


# ===============================
#          THREAD SETUP
# ===============================

class WatcherThread(QThread):
    
    """
    Runs the main monitoring task (Manager.main_watcher) in a separate
    thread to avoid freezing the user interface.

    Signals:
        output (str): Emitted for output messages (currently unused).
        error (str): Emitted when an exception occurs during execution.
        progress (int): Emitted to report progress (0-100).
    """
    
    output = Signal(str)
    error = Signal(str)
    progress = Signal(int)

    def __init__(self, config: UserService, translator: TranslatorService, parent = None):
        
        """
        Initializes the watcher thread.

        Args:
            config_service (UserService): The user configuration service.
            parent (Optional[QWidget]): The parent widget.
        """
        
        super().__init__(parent)

        self.config_service = config
        self.translator_service = translator

    def run(self):
        
        """
        Main entry point for the thread. Starts the monitoring.
        """
        
        try:
            Manager.main_watcher(
                config=self.config_service,
                progress_callback=self.progress.emit,
                interruption_check=self.isInterruptionRequested
            )
            return
        except Exception as e:
            if not self.isInterruptionRequested():
                self.error.emit(str(e))
                print(e)
            print(e)