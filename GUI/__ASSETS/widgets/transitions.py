# GUI/__assets/widgets/transitions.py

from PySide6.QtCore import (
    QEasingCurve,
    QPauseAnimation,
    QPropertyAnimation,
    QSequentialAnimationGroup
)
from PySide6.QtWidgets import QGraphicsOpacityEffect, QStackedLayout, QStackedWidget, QWidget


class Transition:

    """
    Base class for all transitions in a QStackedWidget or QStackedLayout.
    Handles the state, safety checks, and callbacks execution.
    """

    def __init__(self, stacked_container: QStackedWidget | QStackedLayout):

        """
        Initializes the base transition handler.

        Args:
            stacked_container (QStackedWidget | QStackedLayout): The container where transitions occur.
        """
        self.stacked = stacked_container
        self._current_group: QSequentialAnimationGroup | None = None
        self._is_animating: bool = False

    def switch_to(self, new_widget: QWidget, duration: int = 300, on_start=None, on_finished=None):

        """
        Entry point to trigger the transition to a new widget.

        Args:
            new_widget (QWidget): The target widget to display.
            duration (int): Total duration of the transition in milliseconds.
            on_start (callable, optional): Callback executed before the animation starts.
            on_finished (callable, optional): Callback executed after the animation ends.
        """
        if self._is_animating:
            return

        old_widget = self.stacked.currentWidget()

        # Immediate switch if no animation is needed
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

        # Delegate the actual animation logic to the child class
        self._perform_animation(old_widget, new_widget, duration, on_finished)

    def _perform_animation(self, old_widget: QWidget, new_widget: QWidget, duration: int, on_finished):
        """
        Must be implemented by subclasses to define the visual effect.
        """
        raise NotImplementedError("Subclasses must implement _perform_animation.")

    def _execute_switch(self, new_widget: QWidget):
        """
        Helper method for subclasses to physically switch the active widget mid-animation.
        """
        self.stacked.setCurrentWidget(new_widget)

    def _finalize_transition(self, on_finished):
        """
        Helper method for subclasses to clean up state and trigger the final callback.
        """
        self._is_animating = False
        self._current_group = None
        if on_finished:
            on_finished()


# === CUSTOM TRANSITION(S) ===
# --- FADE TRANSITION ---
class FadeTransition(Transition):

    """
    Handles smooth fade-in and fade-out transitions.
    """

    def _perform_animation(self, old_widget: QWidget, new_widget: QWidget, duration: int, on_finished):

        """
        Executes the opacity animations.
        """
        self._clear_effect(old_widget)
        self._clear_effect(new_widget)

        # Graphic effects must belong to their respective widgets
        old_effect = QGraphicsOpacityEffect(old_widget)
        new_effect = QGraphicsOpacityEffect(new_widget)

        old_widget.setGraphicsEffect(old_effect)
        new_widget.setGraphicsEffect(new_effect)
        new_effect.setOpacity(0.0)

        # Parent the animations to the container to secure C++ memory management
        group = QSequentialAnimationGroup(self.stacked)

        fade_out = QPropertyAnimation(old_effect, b"opacity", group)
        fade_out.setDuration(duration // 2)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)

        fade_in = QPropertyAnimation(new_effect, b"opacity", group)
        fade_in.setDuration(duration // 2)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)

        group.addAnimation(fade_out)

        # Small pause during the switch to avoid visual artifacts
        pause = QPauseAnimation(30, group)
        pause.finished.connect(lambda: self._execute_switch(new_widget))

        group.addAnimation(pause)
        group.addAnimation(fade_in)

        # Cleanup process when the whole animation ends
        def cleanup():
            self._clear_effect(old_widget)
            self._clear_effect(new_widget)
            self._finalize_transition(on_finished)

        group.finished.connect(cleanup)
        self._current_group = group
        group.start()

    def _clear_effect(self, widget: QWidget):
        """
        Removes existing graphics effects from a widget to free resources.
        """
        effect = widget.graphicsEffect()
        if effect:
            widget.setGraphicsEffect(None)
