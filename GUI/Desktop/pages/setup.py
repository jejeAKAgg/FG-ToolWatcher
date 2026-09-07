# GUI/Desktop/pages/setup.py

import logging

from PySide6.QtCore import  Qt, QThread, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from CORE.Services.setup import *
from CORE.Services.translator import TranslatorService
from CORE.Services.user import UserService

from GUI.__assets.widgets.progress_bar import SpinnerProgressBar


LOG = logging.getLogger(__name__)

class SetupPage(QWidget):

    """
    QSide6 widget dedicated to the initial application setup process.
    It displays a spinner and messages while the setup thread is running.
    """
    setup_finished = Signal()

    def __init__(self, config: UserService, translator: TranslatorService, parent=None):

        """
        Initializes the SetupPage UI components and layout.

        Args:
            config (UserService): The service instance for managing user settings.
            translator (TranslatorService): The translator service.
            parent (Optional[QWidget]): The parent widget.
        """
        super().__init__(parent)

        # === INTERNAL SERVICE(S) ===
        self.config = config
        self.translator = translator

        # === INTERNAL VARIABLE(S) ===
        self.current_step_key = "page_setup_start.text"

        # === INTERNAL PARAMETER(S) ===
        self.is_running = False
        self.thread = None

        # === UI BUILDER(S) ===
        self._build_ui()
        self._apply_stylesheet()

        self.start_setup()   # Automatic start of the process


    # === PUBLIC METHOD(S) ===
    def retranslate_ui(self):

        """
        Updates the text of every widget of the application depending on the new user language input.
        """
        LOG.debug("Retranslating UI in SetupPage...")

        if self.is_running:
            self.label.setText(self.translator.get(self.current_step_key))

    def start_setup(self):

        """
        Initiates the setup process in a new thread.
        """
        LOG.debug("Setup starting...")

        if self.is_running:
            return

        self.is_running = True

        self.thread = SetupThread(
            config=self.config,
            translator=self.translator,
            parent=self
        )

        self.thread.setup_message.connect(self.on_setup_step_changed)
        self.thread.setup_finished.connect(self.on_setup_finished)
        self.thread.setup_error.connect(self.on_setup_error)

        self.thread.start()

    def on_setup_step_changed(self, step_key: str):

        """
        Receives the translation key emitted from the background thread and updates the displayed label.

        Args:
            step_key (str): The translation identifier for the current setup phase.
        """
        LOG.debug(f"New setup step ({step_key})...")

        self.current_step_key = step_key
        self.label.setText(self.translator.get(self.current_step_key))

    def on_setup_finished(self):

        """
        Handles post-setup actions once the thread signals completion.
        """
        LOG.debug(f"Setup finished...")

        self.is_running = False
        self.spinner.stop()
        self.setup_finished.emit()

    def on_setup_error(self, error_msg: str):

        """
        Handles worker thread failures, halts animations, and presents the error details.

        Args:
            error_msg (str): The exception message returned by the worker thread.
        """
        LOG.debug(f"Setup failed: {error_msg}")

        self.is_running = False
        self.spinner.stop()
        self.label.setStyleSheet("color: red; font-weight: bold; font-size: 12pt;")
        self.label.setText(f"Setup Error: {error_msg}")


    # === PRIVATE METHOD(S) ===
    def _build_ui(self):

        """
        Builds the graphical user interface for the setup page.
        """
        LOG.debug("Building UI for SetupPage...")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.spinner = SpinnerProgressBar(radius=40, dot_size=12, speed=80)

        self.label = QLabel(self.translator.get(self.current_step_key))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addStretch()
        self.main_layout.addWidget(self.spinner, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.addSpacing(15)
        self.main_layout.addWidget(self.label)
        self.main_layout.addStretch()

    def _apply_stylesheet(self):

        """
        Applies the CSS (QSS) styling to the page elements.
        """
        LOG.debug("Applying CSS for SetupPage UI...")

        self.label.setStyleSheet("color: black; font-weight: bold; font-size: 12pt;")


# === THREAD(S) SETUP ===
class SetupThread(QThread):

    """
    Manages the sequential and potentially time-consuming initial setup tasks
    (directory creation, config loading) in a separate thread to prevent GUI freezing.
    """
    setup_message = Signal(str)
    setup_finished = Signal()
    setup_error = Signal(str)

    def __init__(self, config: UserService, translator: TranslatorService, parent=None):

        """
        Initializes the setup worker thread.

        Args:
            config (UserService): User configuration service.
            translator (TranslatorService): Translation provider service.
            parent (Optional[QObject]): Parent QObject managing thread lifecycle.
        """
        super().__init__(parent)

        # === INTERNAL SERVICE(S) ===
        self.config = config
        self.translator = translator

    def run(self):

        """
        Executes setup steps: creating directories and loading configurations.
        """
        LOG.debug("Running SetupThread...")

        try:
            steps = [
                ("page_setup_start.text", 3000, lambda: None),
                ("page_setup_step1.text", 1500, lambda: make_dirs()),
                ("TODO: DB update", 1500, lambda: None),
                ("page_setup_complete.text", 1500, lambda: None),
            ]

            for msg_key, sleep, func in steps:
                if self.isInterruptionRequested():
                    return
                self.setup_message.emit(msg_key)
                self.msleep(sleep) # Simulate time delay for user feedback
                func()

            if not self.isInterruptionRequested():
                self.setup_finished.emit()

        except Exception as e:
            self.setup_error.emit(str(e))
