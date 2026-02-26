# GUI/__ASSETS/widgets/push_buttons.py
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import QPushButton


class CustomPushButton(QPushButton):
    """
    A versatile QPushButton that supports custom solid colors or 
    semi-transparent glass effects based on the alpha value.
    """

    def __init__(self, icon_path=None, icon_size_width=30, icon_size_height=30, width=100, height=45,
                 text="",
                 bg_color="#82714E", 
                 hover_color="#7A6F58",
                 text_color="#FFFFFF",
                 alpha=1.0,
                 parent=None):
        """
        Initializes the button with custom colors and optional transparency.

        Args:
            icon_path (str, optional): Path to the icon file.
            bg_color (str): Hex code for the default background.
            hover_color (str): Hex code for the hover state.
            text_color (str): Hex code for the text color.
            alpha (float): Transparency level (1.0 for solid, < 1.0 for transparent).
        """
        super().__init__(text, parent)

        self.setFixedSize(width, height)
        self.setCursor(Qt.PointingHandCursor)

        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(icon_size_width, icon_size_height))

        # --- Dynamic Color & Alpha Logic ---
        bg_qcolor = QColor(bg_color)
        hover_qcolor = QColor(hover_color)

        if alpha < 1.0:
            # Mode Transparent : On applique l'alpha aux couleurs fournies
            bg_qcolor.setAlphaF(alpha)
            hover_qcolor.setAlphaF(min(alpha + 0.15, 1.0))
            
            final_bg = bg_qcolor.name(QColor.NameFormat.HexArgb)
            final_hover = hover_qcolor.name(QColor.NameFormat.HexArgb)
            border_style = "1px solid rgba(255, 255, 255, 0.1)"
        else:
            # Mode Solide : On utilise tes couleurs Hex exactes
            final_bg = bg_color
            final_hover = hover_color
            border_style = "none"

        # --- Style ---
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {final_bg};
                color: {text_color};
                font-family: "Arial Black";
                font-size: 14px;
                font-weight: bold;
                border-radius: 15px;
                border: {border_style};
                padding: 5px;
            }}
            
            QPushButton:hover {{
                background-color: {final_hover};
            }}

            QPushButton:pressed {{
                background-color: {hover_qcolor.darker(110).name()};
                font-size: 13px;
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