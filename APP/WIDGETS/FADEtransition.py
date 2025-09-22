# APP/widgets/FadeTransition.py
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup
from PySide6.QtWidgets import QGraphicsOpacityEffect


class FadeTransition:
    def __init__(self, stacked_widget):
        self.stacked = stacked_widget
        self._current_group = None  # garder une ref

    def fade_to(self, new_widget, duration=800, on_finished=None):
        old_widget = self.stacked.currentWidget()
        if not old_widget or old_widget == new_widget:
            self.stacked.setCurrentWidget(new_widget)
            if on_finished:
                on_finished()
            return

        old_effect = QGraphicsOpacityEffect(old_widget)
        new_effect = QGraphicsOpacityEffect(new_widget)
        old_widget.setGraphicsEffect(old_effect)
        new_widget.setGraphicsEffect(new_effect)

        new_effect.setOpacity(0.0)  # important sinon ça reste transparent

        fade_out = QPropertyAnimation(old_effect, b"opacity")
        fade_out.setDuration(duration // 2)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.InOutQuad)

        fade_in = QPropertyAnimation(new_effect, b"opacity")
        fade_in.setDuration(duration // 2)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.InOutQuad)

        group = QSequentialAnimationGroup()
        group.addAnimation(fade_out)
        group.addPause(50)
        group.addAnimation(fade_in)

        def switch_page():
            self.stacked.setCurrentWidget(new_widget)
            if on_finished:
                on_finished()

        fade_out.finished.connect(switch_page)

        # garder la ref sinon GC tue l’anim
        self._current_group = group
        group.start()