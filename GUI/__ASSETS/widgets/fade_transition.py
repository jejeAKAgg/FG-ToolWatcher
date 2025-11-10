# GUI/__ASSETS/widgets/fade_transition.py
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup, QPauseAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect


class FadeTransition:
    def __init__(self, stacked_widget):
        self.stacked = stacked_widget
        self._current_group = None  # garder une référence sinon GC tue l’anim

    def fade_to(self, new_widget, duration=800, on_start=None, on_finished=None):
        old_widget = self.stacked.currentWidget()
        if not old_widget or old_widget == new_widget:
            if on_start:
                on_start()
            self.stacked.setCurrentWidget(new_widget)
            if on_finished:
                on_finished()
            return

        # Si on_start existe → exécuter avant toute animation
        if on_start:
            try:
                on_start()
            except Exception as e:
                print(f"[FadeTransition] Erreur dans on_start: {e}")

        # Effets d’opacité
        old_effect = QGraphicsOpacityEffect(old_widget)
        new_effect = QGraphicsOpacityEffect(new_widget)
        old_widget.setGraphicsEffect(old_effect)
        new_widget.setGraphicsEffect(new_effect)

        new_effect.setOpacity(0.0)

        # Animation sortie
        fade_out = QPropertyAnimation(old_effect, b"opacity")
        fade_out.setDuration(duration // 2)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.InOutQuad)

        # Animation entrée
        fade_in = QPropertyAnimation(new_effect, b"opacity")
        fade_in.setDuration(duration // 2)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.InOutQuad)

        # Groupe séquentiel
        group = QSequentialAnimationGroup()

        # Étape 1 : fade out
        group.addAnimation(fade_out)

        # Étape 2 : pause + switch de page
        pause = QPauseAnimation(50)
        def do_switch():
            self.stacked.setCurrentWidget(new_widget)
            if on_finished:
                on_finished()
        pause.finished.connect(do_switch)
        group.addAnimation(pause)

        # Étape 3 : fade in
        group.addAnimation(fade_in)

        # Sauvegarde de la réf
        self._current_group = group
        group.start()