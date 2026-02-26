# GUI/__ASSETS/widgets/fade_transition.py
from PySide6.QtCore import (
    QPropertyAnimation,
    QEasingCurve,
    QSequentialAnimationGroup,
    QPauseAnimation,
)
from PySide6.QtWidgets import QGraphicsOpacityEffect


class FadeTransition:

    """
    Handles smooth fade-in and fade-out transitions between widgets in a QStackedWidget.
    """

    def __init__(self, stacked_widget):

        """
        Initializes the transition handler.

        Args:
            stacked_widget (QStackedWidget): The widget container where transitions occur.
        """

        self.stacked = stacked_widget
        self._current_group = None
        self._is_animating = False


    # === PUBLIC METHOD(S) ===
    def fade_to(self, new_widget, duration=400, on_start=None, on_finished=None):

        """
        Executes a sequential fade-out/fade-in transition to a new widget.

        Args:
            new_widget (QWidget): The target widget to display.
            duration (int): Total duration of the transition in milliseconds.
            on_start (callable, optional): Callback executed before the animation starts.
            on_finished (callable, optional): Callback executed after the animation ends.
        """

        if self._is_animating:
            return

        old_widget = self.stacked.currentWidget()

        if not old_widget or old_widget == new_widget:
            if on_start:
                on_start()
            self.stacked.setCurrentWidget(new_widget)
            if on_finished:
                on_finished()
            return

        self._is_animating = True

        if on_start:
            on_start()

        self._clear_effect(old_widget)
        self._clear_effect(new_widget)

        old_effect = QGraphicsOpacityEffect(old_widget)
        new_effect = QGraphicsOpacityEffect(new_widget)

        old_widget.setGraphicsEffect(old_effect)
        new_widget.setGraphicsEffect(new_effect)

        new_effect.setOpacity(0.0)

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

        pause = QPauseAnimation(30)

        def do_switch():
            self.stacked.setCurrentWidget(new_widget)

        pause.finished.connect(do_switch)
        group.addAnimation(pause)
        group.addAnimation(fade_in)

        def cleanup():
            self._clear_effect(old_widget)
            self._clear_effect(new_widget)
            self._is_animating = False
            if on_finished:
                on_finished()

        group.finished.connect(cleanup)

        self._current_group = group
        group.start()


    # === PRIVATE METHOD(S) ===
    def _clear_effect(self, widget):

        """
        Removes existing graphics effects from a widget to free resources.

        Args:
            widget (QWidget): The widget to clean up.
        """

        effect = widget.graphicsEffect()
        if effect:
            widget.setGraphicsEffect(None)