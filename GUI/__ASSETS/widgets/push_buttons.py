# GUI/__ASSETS/widgets/push_buttons.py
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import QPushButton


class CustomPushButton(QPushButton):
    def __init__(self, icon_path, icon_size_width=35, icon_size_height=35, width=100, height=45,
                 bg_color="#82714E", hover_color="#7A6F58",
                 alpha=1.0,
                 text_color="white",
                 parent=None):
        super().__init__(parent)

        self.setFixedSize(width, height)

        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(icon_size_width, icon_size_height))

        bg_qcolor = QColor(bg_color)
        hover_qcolor = QColor(hover_color)

        # 2. Modifier les objets (ces appels retournent None)
        bg_qcolor.setAlphaF(alpha)
        hover_qcolor.setAlphaF(alpha)

        # 3. Récupérer le nom à partir des objets qui ont été modifiés
        final_bg_color = bg_qcolor.name(QColor.NameFormat.HexArgb)
        final_hover_color = hover_qcolor.name(QColor.NameFormat.HexArgb)

        # --- Style ---
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {final_bg_color};
                color: {text_color};
                font-weight: bold;
                border-radius: 20px;
                border: none;
            }}
            QPushButton:hover:!disabled {{
                background-color: {final_hover_color};
            }}
            QPushButton:disabled {{
                background: #a0a0a0; 
                color: #d0d0d0;
            }}
        """)