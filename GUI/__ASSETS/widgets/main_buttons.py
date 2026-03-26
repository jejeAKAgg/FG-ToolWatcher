# GUI/__ASSETS/widgets/main_buttons.py
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QToolButton


class CustomMainButton(QToolButton):

    """
    Glassmorphism-style main button.
    Dark frosted glass look with colored bottom accent and glow on hover.

    """

    ACCENT_COLORS = {
        "green":  ("#2ecc71", "#27ae60", "rgba(46, 204, 113, 80)"),
        "red":    ("#e74c3c", "#c0392b", "rgba(231, 76,  60,  80)"),
        "blue":   ("#3498db", "#2980b9", "rgba(52,  152, 219, 80)"),
        "gray":   ("#95a5a6", "#7f8c8d", "rgba(149, 165, 166, 80)"),
        "purple": ("#9b59b6", "#8e44ad", "rgba(155, 89, 182, 80)"),
        "teal": ("#1abc9c", "#16a085", "rgba(26, 188, 156, 80)"),
    }

    def __init__(self, text: str, icon_path: str, width: int = 200, height: int = 200, gradient: tuple = ("green", "darkgreen")):
        super().__init__()

        # Detect accent color from gradient tuple
        color_key = "green"
        g0 = gradient[0].lower()
        if "red" in g0 or "b71" in g0 or "e53" in g0:
            color_key = "red"
        elif "blue" in g0 or "137" in g0 or "218" in g0:
            color_key = "blue"
        elif "gray" in g0 or "grey" in g0 or "a0a" in g0:
            color_key = "gray"
        elif "9b5" in g0 or "8e4" in g0 or "purple" in g0 or "violet" in g0:
            color_key = "purple"
        elif "1ab" in g0 or "16a" in g0 or "teal" in g0 or "cyan" in g0:
            color_key = "teal"

        accent, accent_dark, glow = self.ACCENT_COLORS[color_key]

        self.setFixedSize(width, height)

        # Slim button (height < 80): text only, centered
        if height < 80:
            self.setText(text)
            self.setToolButtonStyle(Qt.ToolButtonTextOnly)
            self.setStyleSheet(f"""
                QToolButton {{
                    border-radius: 15px;
                    color: rgba(0, 0, 0, 0.85);
                    font-size: 16px;
                    font-weight: 800;
                    letter-spacing: 1px;
                    border-top: 5px solid rgba(0, 0, 0, 1);
                    border-left: 5px solid rgba(0, 0, 0, 1);
                    border-right: 5px solid rgba(0, 0, 0, 1);
                    border-bottom: 5px solid {accent};
                    padding: 0px;
                    background: rgba(129, 131, 134, 0.5);
                }}
                QToolButton:hover:!disabled {{
                    background: rgba(109, 110, 112, 0.5);
                    border-top: 5px solid rgba(0, 0, 0, 1);
                    border-left: 5px solid rgba(0, 0, 0, 1);
                    border-right: 5px solid rgba(0, 0, 0, 1);
                    border-bottom: 5px solid {accent};
                    color: black;
                }}
                QToolButton:disabled {{
                    background: rgba(160, 160, 160, 0.01);
                    border-top: 5px solid rgba(0, 0, 0, 1);
                    border-left: 5px solid rgba(0, 0, 0, 1);
                    border-right: 5px solid rgba(0, 0, 0, 1);
                    border-bottom: 5px solid {accent};
                    color: rgba(0, 0, 0, 0.5);
                }}
            """)

        # Square button: icon + text below
        else:
            self.setText(text)
            self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            if icon_path:
                self.setIcon(QIcon(icon_path))
                self.setIconSize(QSize(100, 100))
            self.setStyleSheet(f"""
                QToolButton {{
                    border-radius: 25px;
                    color: rgba(0, 0, 0, 0.85);
                    font-size: 20px;
                    font-weight: 800;
                    letter-spacing: 2px;
                    border-top: 5px solid rgba(0, 0, 0, 1);
                    border-left: 5px solid rgba(0, 0, 0, 1);
                    border-right: 5px solid rgba(0, 0, 0, 1);
                    border-bottom: 5px solid {accent};
                    padding-top: 18px;
                    padding-bottom: 8px;
                    background: rgba(129, 131, 134, 0.5);
                }}
                QToolButton:hover:!disabled {{
                    background: rgba(109, 110, 112, 0.5);
                    border-top: 5px solid rgba(0, 0, 0, 1);
                    border-left: 5px solid rgba(0, 0, 0, 1);
                    border-right: 5px solid rgba(0, 0, 0, 1);
                    border-bottom: 5px solid {accent};
                    color: black;
                }}
                QToolButton:disabled {{
                    background: rgba(160, 160, 160, 0.01);
                    border-top: 5px solid rgba(0, 0, 0, 1);
                    border-left: 5px solid rgba(0, 0, 0, 1);
                    border-right: 5px solid rgba(0, 0, 0, 1);
                    border-bottom: 5px solid {accent};
                    color: rgba(0, 0, 0, 0.5);
                }}
            """)
