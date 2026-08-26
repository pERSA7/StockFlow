
from PyQt6.QtWidgets import QDialog, QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, pyqtSignal, Qt

class AnimatedDialog(QDialog):
    """
    Un QDialog base que implementa una animación de fundido (fade-in)
    al mostrarse y (fade-out) al cerrarse.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. Configurar el efecto de opacidad
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        # 2. Guardar una referencia a la animación
        self.animation = None 
        
        # 3. Definir duraciones
        self.fade_in_duration = 250  # Milisegundos para aparecer
        self.fade_out_duration = 200 # Milisegundos para desaparecer

    def showEvent(self, event):
        """
        Se ejecuta automáticamente justo antes de que se muestre el diálogo.
        Inicia la animación de FADE-IN.
        """
        super().showEvent(event)
        
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(self.fade_in_duration)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.animation.start()

    def start_fade_out(self, on_finished_callback):
        """
        Inicia una animación de FADE-OUT.
        Cuando termina, llama a la función 'on_finished_callback'.
        """
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(self.fade_out_duration)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.Type.InQuad)
        
        # Conecta la acción real de "cerrar" al final de la animación
        self.animation.finished.connect(on_finished_callback)
        self.animation.start()

    # --- Sobreescribimos los métodos de cierre ---

    def accept(self):
        """
        Sobrescribe accept() para animar la salida antes de aceptar.
        """
        self.start_fade_out(super().accept) # Llama al accept() original al terminar

    def reject(self):
        """
        Sobrescribe reject() para animar la salida antes de rechazar.
        """
        self.start_fade_out(super().reject) # Llama al reject() original al terminar

    def closeEvent(self, event):
        """
        Sobrescribe el evento de cierre (clic en la 'X') para animar la salida.
        """
        event.ignore() # Ignora el cierre inmediato
        self.start_fade_out(super().close) # Llama al close() original al terminar