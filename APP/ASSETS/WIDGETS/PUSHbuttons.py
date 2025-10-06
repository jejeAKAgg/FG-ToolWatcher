# APP/widgets/PUSHbuttons.py
from PySide6.QtCore import QSize, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton, QToolTip


class CustomPushButton(QPushButton):
    def __init__(self, icon_path, width=100, height=45,
                 bg_color="#82714E", hover_color="#7A6F58",
                 text_color="white", tip=None,
                 tooltip_delay=1000, tooltip_duration=3000,
                 parent=None):
        super().__init__(parent)

        self.setFixedSize(width, height)

        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(35, 35))

        # --- Tooltip custom ---
        self.tooltip_text = tip
        self.tooltip_delay = tooltip_delay      # temps avant affichage (ms)
        self.tooltip_duration = tooltip_duration  # temps avant disparition (ms)

        self._show_timer = QTimer(self)
        self._hide_timer = QTimer(self)

        self._show_timer.setSingleShot(True)
        self._hide_timer.setSingleShot(True)

        self._show_timer.timeout.connect(self._show_tooltip)
        self._hide_timer.timeout.connect(QToolTip.hideText)

        # --- Style ---
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                font-weight: bold;
                border-radius: 20px;
                border: none;
            }}
            QPushButton:hover:!disabled {{
                background-color: {hover_color};
            }}
            QPushButton:disabled {{
                background: #a0a0a0; 
                color: #d0d0d0;
            }}
        """)

    # ---------- Gestion survol ----------
    def enterEvent(self, event):
        if self.tooltip_text:
            self._show_timer.start(self.tooltip_delay)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._show_timer.stop()
        self._hide_timer.stop()
        QToolTip.hideText()
        super().leaveEvent(event)

    # ---------- Affichage / masquage ----------
    def _show_tooltip(self):
        if self.tooltip_text:
            pos = self.mapToGlobal(self.rect().center())
            QToolTip.showText(pos, self.tooltip_text, self)
            self._hide_timer.start(self.tooltip_duration)