# GUI/__assets/widgets/buttons.py
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import QPushButton


class CustomPushButton(QPushButton):

    """
    A versatile QPushButton that supports custom solid colors,
    semi-transparent glass effects, dynamic fonts, and custom borders.
    """

    def __init__(self, icon_path=None, icon_size_width = None, icon_size_height = None,
                 width = None, height = None,
                 text="", text_color="none", font_family="none", font_size=15,
                 bg_color="none", border="none",
                 hover_color="none", hover_border="none",
                 radius="none",
                 alpha=1.0,
                 parent=None):

        """
        Initializes the button with custom colors, optional transparency, typography, and borders.

        Args:
            icon_path (str, optional): Path to the icon file.
            text_color (str): Hex code for the text color.
            font_family (str): Font family name to use.
            font_size (int): Base font size in pixels.
            bg_color (str): Hex code for the default background.
            border (str): CSS border string (e.g., "1px solid #3E3E42").
            hover_color (str): Hex code for the hover state.
            hover_border (str): CSS border string for hover state.
            radius (str): Overrides the default border-radius.
            alpha (float): Transparency level (1.0 for solid, < 1.0 for transparent).
        """
        super().__init__(text, parent)

        self.setFixedSize(width, height)
        self.setCursor(Qt.PointingHandCursor)

        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(icon_size_width, icon_size_height))

        # --- Color & Alpha Logic ---
        bg_qcolor = QColor(bg_color)
        hover_qcolor = QColor(hover_color)

        if alpha < 1.0:
            bg_qcolor.setAlphaF(alpha)
            hover_qcolor.setAlphaF(min(alpha + 0.15, 1.0))

        final_bg = bg_qcolor.name(QColor.NameFormat.HexArgb)
        final_hover = hover_qcolor.name(QColor.NameFormat.HexArgb)
        pressed_bg = hover_qcolor.darker(110).name(QColor.NameFormat.HexArgb)

        # --- Style Application ---
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {final_bg};
                color: {text_color};
                font-family: "{font_family}";
                font-size: {font_size}px;
                font-weight: bold;
                border-radius: {radius};
                border: {border};
                padding: 0px 20px;
            }}
            QPushButton:hover {{
                background-color: {final_hover};
                border: {hover_border};
            }}
            QPushButton:pressed {{
                background-color: {pressed_bg};
                font-size: {max(font_size - 2, 8)}px;
            }}
            QPushButton:disabled {{
                background-color: #A0A0A0;
                color: #D0D0D0;
                border: none;
            }}
        """)

    def setText(self, text):

        """
        Updates the button text dynamically.
        """
        super().setText(text)


# === CUSTOM BUTTON(S) ===
# --- GLOBAL ---
class MenuButton(CustomPushButton):
    """
    Preset for the large buttons in the main menu (e.g., Settings).
    Size: 100x50, dark gray background.
    """
    def __init__(self, icon_path=None, parent=None):
        super().__init__(
            icon_path=icon_path if isinstance(icon_path, str) else None, icon_size_width=35, icon_size_height=35,
            width=100, height=50,
            bg_color="#2D2D30", border="1px solid #3E3E42",
            hover_color="#333336", hover_border="1px solid #00913e",
            radius="15px",
            parent=parent
        )

class UpdateButton(CustomPushButton):
    """
    Preset for the square refresh/synchronization buttons.
    Size: 50x50, dark gray background.
    """
    def __init__(self, icon_path=None, parent=None):
        super().__init__(
            icon_path=icon_path if isinstance(icon_path, str) else None, icon_size_width=35, icon_size_height=35,
            width=50, height=50,
            bg_color="#2D2D30", border="1px solid #3E3E42",
            hover_color="#333336", hover_border="1px solid #00913e",
            radius="25px",
            parent=parent
        )

class LanguageButton(CustomPushButton):
    """
    Preset for the small language selection buttons.
    Size: 55x35, gray background with a transparency effect (alpha 0.5).
    """
    def __init__(self, icon_path=None, parent=None):
        super().__init__(
            icon_path=icon_path if isinstance(icon_path, str) else None, icon_size_width=35, icon_size_height=35,
            width=55, height=35,
            bg_color="#818386", hover_color="#6d6e70",
            radius="15px",
            alpha=0.5,
            parent=parent
        )

# --- DASHBOARD ---
class DashboardButton(CustomPushButton):
    """
    Preset for the large buttons in the Dashboard.
    Size: 40x40, dark gray background.
    """
    def __init__(self, icon_path=None, parent=None):
        super().__init__(
            icon_path=icon_path if isinstance(icon_path, str) else None, icon_size_width=20, icon_size_height=20,
            width=40, height=40,
            bg_color="#2D2D30", border="1px solid #3E3E42",
            hover_color="#333336", hover_border="1px solid #00913e",
            radius="6px",
            parent=parent
        )

class DashboardTaxSwitchButton(CustomPushButton):
    """
    Preset for the wide tax toggle switch button.
    Size: 200x40, dark gray background, checkable.
    """
    def __init__(self, parent=None):
        super().__init__(
            width=200, height=40,
            bg_color="#2D2D30", border="1px solid #3E3E42",
            hover_color="#333336", hover_border="1px solid #00913e",
            radius="6px",
            parent=parent
        )
        self.setCheckable(True)

class DashboardAnalyseButton(CustomPushButton):
    """
    Preset for the primary action buttons.
    Pure green background, no border.
    """
    def __init__(self, icon_path=None, parent=None):
        super().__init__(
            icon_path=icon_path if isinstance(icon_path, str) else None, icon_size_width=20, icon_size_height=20,
            width=40, height=40,
            bg_color="#00913e", border="none",
            hover_color="#009536", hover_border="1px solid #3E3E42",
            radius="6px",
            parent=parent
        )

class DashboardCheckableButton(CustomPushButton):
    """
    Preset for checkable square buttons (e.g., Table/Graph view toggle).
    Size: 40x40, dark gray background, supports a toggled state.
    """
    def __init__(self, icon_path=None, parent=None):
        super().__init__(
            icon_path=icon_path if isinstance(icon_path, str) else None, icon_size_width=20, icon_size_height=20,
            width=40, height=40,
            bg_color="#2D2D30",  border="1px solid #3E3E42",
            hover_color="#333336", hover_border="1px solid #00913e",
            radius="6px",
            parent=parent
        )
        self.setCheckable(True)
