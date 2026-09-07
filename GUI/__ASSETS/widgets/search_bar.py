# GUI/__assets/widgets/search_bar.py

from PySide6.QtWidgets import QLineEdit

class CustomSearchBar(QLineEdit):

    """
    A reusable and customizable search bar widget.
    Enforces a minimum width and handles its own visual states (focus, hover).
    """

    def __init__(self, placeholder: str = "", min_width: int = 300, height: int = 40,
                 bg_color: str = "#1E1E1E", text_color: str = "#FFFFFF",
                 border: str = "1px solid #333333", focus_border: str = "1px solid #00913e",
                 radius: str = "6px", padding: str = "0px 15px",
                 clear_button: bool = True, parent=None):

        """
        Initializes the custom search bar.

        Args:
            placeholder (str): The ghost text displayed when the bar is empty.
            min_width (int): Prevents the search bar from shrinking below this width.
            height (int): Fixed height of the search bar.
            bg_color (str): Background color in Hex.
            text_color (str): Text color in Hex.
            border (str): Default border CSS string.
            focus_border (str): Border CSS string when the user clicks inside.
            radius (str): Border radius CSS string.
            padding (str): Internal spacing CSS string.
            clear_button (bool): Whether to display the clear 'X' button when text is typed.
        """
        super().__init__(parent)

        self.setPlaceholderText(placeholder)
        self.setMinimumWidth(min_width)
        self.setFixedHeight(height)
        self.setClearButtonEnabled(clear_button)

        # --- Style Application ---
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {bg_color};
                color: {text_color};
                border: {border};
                border-radius: {radius};
                padding: {padding};
            }}
            QLineEdit:focus {{
                border: {focus_border};
            }}
        """)


# === CUSTOM BUTTON(S) ===
# --- DASHBOARD ---
class SearchBarDashboard(CustomSearchBar):
    """
    Preset for the Dashboard search bar.
    Size: Flexible width (min 350px) x 40px, dark gray background with green focus border.
    """
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(
            placeholder=placeholder,
            min_width=750,
            height=40,
            bg_color="#1E1E1E",
            text_color="#FFFFFF",
            border="1px solid #333333",
            focus_border="1px solid #00913e",
            radius="6px",
            padding="0px 20px",
            clear_button=True,
            parent=parent
        )
