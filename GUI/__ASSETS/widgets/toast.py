# GUI/__assets/widgets/toast.py

from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class ToastNotification(QWidget):

    """
    A floating widget that appears at the bottom of the screen to display a message.
    Ensures only one active notification is visible at a time.
    """

    # Shared class variable to keep track of the currently visible toast
    _active_toast = None

    def __init__(self, parent: QWidget, message: str, duration: int = 3000):

        """
        Initializes the toast notification.

        Args:
            parent (QWidget): The parent widget (usually the main window).
            message (str): The text to display.
            duration (int): Duration in milliseconds before the toast hides.
        """
        super().__init__(parent)

        self.duration = duration

        # Allows mouse clicks to pass through if the widget overlaps other buttons
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("ToastContainer")

        # --- TOAST CSS ---
        self.setStyleSheet("""
            #ToastContainer {
                background-color: #00913e;
                border-radius: 10px;
                border: 1px solid #009536;
            }
            QLabel {
                background-color: transparent;
                color: white;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
        """)

        # --- UI SETUP ---
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.adjustSize()
        self.setFixedHeight(50)

        # --- POSITION CALCULATIONS ---
        margin_bottom = 10

        self.start_pos = QPoint(
            (parent.width() - self.width()) // 2,
            parent.height()
        )
        self.end_pos = QPoint(
            (parent.width() - self.width()) // 2,
            parent.height() - self.height() - margin_bottom
        )

        self.move(self.start_pos)

        # --- ANIMATIONS ---
        self.anim_in = QPropertyAnimation(self, b"pos")
        self.anim_in.setDuration(400)
        self.anim_in.setStartValue(self.start_pos)
        self.anim_in.setEndValue(self.end_pos)
        self.anim_in.setEasingCurve(QEasingCurve.Type.OutBack)

        self.anim_out = QPropertyAnimation(self, b"pos")
        self.anim_out.setDuration(300)
        self.anim_out.setStartValue(self.end_pos)
        self.anim_out.setEndValue(self.start_pos)
        self.anim_out.setEasingCurve(QEasingCurve.Type.InBack)

        # Connect the exit animation to the new safe cleanup method
        self.anim_out.finished.connect(self._cleanup)

        # --- SECURE TIMER ---
        # Attached to 'self' so it is destroyed when the widget is destroyed
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.anim_out.start)

    def show_toast(self):
        """
        Triggers the appearance of the toast, immediately replacing any existing one.
        """
        # 1. Handle collisions (If a toast is already on screen)
        if ToastNotification._active_toast is not None:
            try:
                # Force delete the previous toast from memory
                ToastNotification._active_toast.deleteLater()
            except RuntimeError:
                # Failsafe in case the C++ object was already deleted
                pass

        # 2. Register self as the new active toast
        ToastNotification._active_toast = self

        # 3. Launch the normal display sequence
        self.show()
        self.raise_()
        self.anim_in.start()

        # Start the timer for the exit animation
        self.timer.start(self.duration)

    def _cleanup(self):
        """
        Cleans up the widget and clears the class reference to avoid dangling C++ pointers.
        """
        # Only clear the class variable if it still points to this exact instance
        if ToastNotification._active_toast is self:
            ToastNotification._active_toast = None

        self.deleteLater()
