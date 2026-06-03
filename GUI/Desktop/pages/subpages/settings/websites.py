# GUI/Desktop/pages/subpages/settings/websites.py
import os
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton,
    QSizePolicy, QLayout, QWidgetItem
)
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize

from CORE.Services.setup import *
from CORE.Services.user import UserService
from CORE.Services.translator import TranslatorService

from GUI.__ASSETS.widgets.push_buttons import CustomPushButton



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

CACHE_VALUES = [0, 1, 3, 7, 14]
DISABLED_SITES = {"CIPAC", "GEORGES"}


# ================================================================
#   FLOW LAYOUT
# ================================================================

class FlowLayout(QLayout):

    def __init__(self, parent=None, h_spacing: int = 10, v_spacing: int = 10):
        super().__init__(parent)
        self._items: list[QWidgetItem] = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), dry_run=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, dry_run=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect: QRect, dry_run: bool) -> int:
        margins = self.contentsMargins()
        x = rect.x() + margins.left()
        y = rect.y() + margins.top()
        line_height = 0
        right_limit = rect.right() - margins.right()

        for item in self._items:
            item_size = item.sizeHint()
            next_x = x + item_size.width()

            if next_x > right_limit and line_height > 0:
                x = rect.x() + margins.left()
                y += line_height + self._v_spacing
                next_x = x + item_size.width()
                line_height = 0

            if not dry_run:
                item.setGeometry(QRect(QPoint(x, y), item_size))

            x = next_x + self._h_spacing
            line_height = max(line_height, item_size.height())

        return y + line_height - rect.y() + margins.bottom()


# ================================================================
#   WEBSITES PAGE
# ================================================================

class WebsitesPage(QWidget):

    settings_saved = Signal()

    def __init__(self, config: UserService, translator: TranslatorService, parent=None):
        super().__init__(parent)

        self.configs    = config
        self.translator = translator

        self.sites = {
            "CIPAC":      "CIPAC",
            "CLABOTS":    "CLABOTS",
            "GEORGES":    "GEORGES",
            "FIXAMI":     "FIXAMI",
            "KLIUM":      "KLIUM",
            "LECOT":      "LECOT",
            "TOOLNATION": "TOOLNATION",
        }

        # === MAIN LAYOUT ===
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(60, 50, 60, 0)
        self.main_layout.setSpacing(10)
        self.main_layout.setAlignment(Qt.AlignTop)

        # --- TITLE ---
        self.title = QLabel(self.translator.get("page_settings_websites.category"))
        self.title.setStyleSheet("font-size: 26px; font-weight: 900; color: #000; margin-bottom: 15px;")
        self.main_layout.addWidget(self.title)

        # ── TOGGLE PILLS ─────────────────────────────────────────────
        self.site_toggles: dict[str, QPushButton] = {}
        selected_sites = self.configs.get("websites_to_watch", [])

        pills_widget = QWidget()
        flow = FlowLayout(pills_widget, h_spacing=10, v_spacing=10)

        for name in self.sites:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setFixedHeight(40)
            btn.setMinimumWidth(100)
            btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

            if name in DISABLED_SITES:
                btn.setChecked(False)
                btn.setEnabled(False)
                btn.setToolTip("Pas encore disponible")
                self._apply_disabled_style(btn)
            else:
                btn.setChecked(name in selected_sites)
                btn.setCursor(Qt.PointingHandCursor)
                self._apply_toggle_style(btn)
                btn.toggled.connect(lambda _checked, b=btn: (self._apply_toggle_style(b), self._check_changes()))

            self.site_toggles[name] = btn
            flow.addWidget(btn)

        self.main_layout.addWidget(pills_widget)
        self.main_layout.addSpacing(10)

        # ── CACHE DURATION SLIDER ─────────────────────────────────────
        cache_label_row = QHBoxLayout()

        self.cache_title = QLabel(self.translator.get("subpage_settings_websites_cache.title"))
        self.cache_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #000;")

        self.cache_value_label = QLabel()
        self.cache_value_label.setStyleSheet("font-size: 14px; font-weight: 900; color: #007e2d;")
        self.cache_value_label.setAlignment(Qt.AlignRight)

        cache_label_row.addWidget(self.cache_title)
        cache_label_row.addStretch()
        cache_label_row.addWidget(self.cache_value_label)
        self.main_layout.addLayout(cache_label_row)

        self.cache_slider = QSlider(Qt.Horizontal)
        self.cache_slider.setMinimum(0)
        self.cache_slider.setMaximum(len(CACHE_VALUES) - 1)
        self.cache_slider.setTickPosition(QSlider.TicksBelow)
        self.cache_slider.setTickInterval(1)
        self.cache_slider.setSingleStep(1)
        self.cache_slider.setPageStep(1)
        self.cache_slider.setFixedHeight(36)
        self.cache_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #ddd;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #007e2d;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #007e2d;
                border: 2px solid #007e2d;
                width: 20px;
                height: 20px;
                margin: -8px 0;
                border-radius: 10px;
            }
            QSlider::handle:horizontal:hover {
                background: #004d1a;
                border-color: #004d1a;
            }
        """)

        saved_cache  = self.configs.get("websites_cache_duration", 3)
        slider_index = CACHE_VALUES.index(saved_cache) if saved_cache in CACHE_VALUES else 1
        self.cache_slider.setValue(slider_index)
        self._update_cache_label(slider_index)

        self.cache_slider.valueChanged.connect(self._on_slider_changed)
        self.main_layout.addWidget(self.cache_slider)

        ticks_layout = QHBoxLayout()
        ticks_layout.setContentsMargins(0, 0, 0, 0)
        ticks_layout.setSpacing(0)
        for days in CACHE_VALUES:
            lbl = QLabel(str(days))
            lbl.setStyleSheet("font-size: 11px; color: #222;")
            lbl.setAlignment(Qt.AlignCenter)
            ticks_layout.addWidget(lbl, stretch=1)
        self.main_layout.addLayout(ticks_layout)

        # --- SAVE BUTTON ---
        self.save_button = CustomPushButton(
            width=110, height=50,
            bg_color="#4a7fa5", hover_color="#2e5f7e"
        )
        self.save_button.setText(self.translator.get("page_settings_save.button"))
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setEnabled(False)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()

        self.main_layout.addStretch()
        self.main_layout.addLayout(button_layout)


    # ====================================
    #           PUBLIC METHODS
    # ====================================

    def save_settings(self):
        selected = [
            name for name, btn in self.site_toggles.items()
            if btn.isChecked() and name not in DISABLED_SITES
        ]
        self.configs.set("websites_to_watch", selected)
        self.configs.set("websites_cache_duration", CACHE_VALUES[self.cache_slider.value()])
        self.save_button.setEnabled(False)
        self.settings_saved.emit()
        LOG.debug(f"[WebsitesPage] Sites : {selected} | Cache : {CACHE_VALUES[self.cache_slider.value()]}j")

    def retranslate_ui(self):
        self.title.setText(self.translator.get("page_settings_websites.category"))
        self.cache_title.setText(self.translator.get("subpage_settings_websites_cache.title"))
        self.save_button.setText(self.translator.get("page_settings_save.button"))
        self._update_cache_label(self.cache_slider.value())


    # ====================================
    #           PRIVATE METHODS
    # ====================================

    def _apply_toggle_style(self, btn: QPushButton):
        if btn.isChecked():
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 126, 45, 0.85);
                    color: #ffffff;
                    border: 2px solid rgba(0, 80, 28, 0.9);
                    border-bottom-color: rgba(0, 60, 20, 1);
                    border-radius: 20px;
                    padding: 0px 24px;
                    font-size: 13px;
                    font-weight: 800;
                    letter-spacing: 0.5px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 100, 35, 0.95);
                    border-color: rgba(0, 60, 20, 1);
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.4);
                    color: #1a1a1a;
                    border: 1.5px solid rgba(50, 50, 50, 0.55);
                    border-bottom-color: rgba(30, 30, 30, 0.75);
                    border-radius: 20px;
                    padding: 0px 24px;
                    font-size: 13px;
                    font-weight: 700;
                    letter-spacing: 0.3px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 126, 45, 0.12);
                    border-color: rgba(0, 126, 45, 0.75);
                    border-bottom-color: rgba(0, 80, 28, 0.9);
                    color: #007e2d;
                }
            """)

    def _apply_disabled_style(self, btn: QPushButton):
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.15);
                color: rgba(60, 60, 60, 0.35);
                border: 1.5px solid rgba(50, 50, 50, 0.18);
                border-radius: 20px;
                padding: 0px 24px;
                font-size: 13px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }
        """)

    def _on_slider_changed(self, index: int):
        self._update_cache_label(index)
        self._check_changes()

    def _update_cache_label(self, index: int):
        self.cache_value_label.setText(self._format_days(CACHE_VALUES[index]))

    def _format_days(self, days: int) -> str:
        return self.translator.get(f"subpage_settings_websites_{days}day.label")

    def _check_changes(self):
        current       = set(name for name, btn in self.site_toggles.items() if btn.isChecked())
        saved         = set(self.configs.get("websites_to_watch", []))
        cache_changed = CACHE_VALUES[self.cache_slider.value()] != self.configs.get("websites_cache_duration", 3)
        self.save_button.setEnabled(current != saved or cache_changed)
