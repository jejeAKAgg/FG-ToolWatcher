# GUI/Desktop/pages/setup.py
import logging

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from CORE.Services.setup import *
from CORE.Services.user import UserService
from CORE.Services.translator import TranslatorService

from GUI.__ASSETS.widgets.spinner_progress_bar import Spinner



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

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
            parent (Optional[QWidget]): The parent widget.
        """

        super().__init__(parent)

        # === INTERNAL VARIABLE(S) ===
        self.configs = config
        self.translator = translator

        # === INTERNAL PARAMETER(S) ===
        self.is_running = False 
        self.thread = None

        # === LAYOUT ===
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.spinner = Spinner(radius=40, dot_size=12, speed=80)
        self.label = QLabel(self.translator.get("page_setup_start.text"))
        self.label.setStyleSheet("color: black; font-weight: bold; font-size: 12pt;")
        self.label.setAlignment(Qt.AlignCenter)

        layout.addStretch()
        layout.addWidget(self.spinner, alignment=Qt.AlignHCenter)
        layout.addSpacing(15)
        layout.addWidget(self.label)
        layout.addStretch()

        self.start_setup()

    def start_setup(self):
        
        """
        Initiates the setup process in a new thread.
        """
        
        if self.is_running:
            return

        self.is_running = True
        
        self.thread = SetupThread(
            configs_service=self.configs,
            translator_service=self.translator,
            parent=self
        )
        
        self.thread.message.connect(self.label.setText)
        self.thread.finished_ok.connect(self.on_setup_finished)
        
        self.thread.start()

    def on_setup_finished(self):
        
        """
        Handles post-setup actions once the thread signals completion.
        """
        
        self.is_running = False
        self.setup_finished.emit()
    

    def retranslate_ui(self):
        
        """
        Update the texte of every widget of the application depending the new user language input.
        """
        
        pass


# ===============================
#          THREAD SETUP
# ===============================

class SetupThread(QThread):
    
    """
    Manages the sequential and potentially time-consuming initial setup tasks 
    (directory creation, config loading) in a separate thread to prevent GUI freezing.
    """
    
    message = Signal(str)
    finished_ok = Signal()

    def __init__(self, configs_service: UserService, translator_service: TranslatorService, parent=None):
        super().__init__(parent)
        
        self.configs_service = configs_service
        self.translator_service = translator_service

    def run(self):
        
        """
        Executes setup steps: creating directories and loading configurations.
        """
        
        try:
            steps = [
                (self.translator_service.get("page_setup_start.text"), lambda: None),
                (self.translator_service.get("page_setup_step1.text"), lambda: make_dirs),
                (self.translator_service.get("page_setup_complete.text"), lambda: None),
            ]

            for msg, func in steps:
                if self.isInterruptionRequested():
                    return
                self.message.emit(msg)
                self.msleep(1500) # Simulate time delay for user feedback
                func()

            if not self.isInterruptionRequested():
                self.finished_ok.emit()


        except Exception as e:
            LOG.exception(e)