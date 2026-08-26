from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QToolBar, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

class Header(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)  # Hacer que la barra de herramientas no sea movible

        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 0, 10, 0) # Añadir márgenes horizontales

        header_label = QLabel("Pañol Escuela - Sistema de Inventario")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        header_label.setFont(font)
        header_layout.addWidget(header_label)
        header_widget.setLayout(header_layout)

        self.addWidget(header_widget)

        # *** ESPACIO PARA FUTURAS ACCIONES ***
        # Ejemplo de cómo podrías añadir una acción:
        # action_ejemplo = QAction(QIcon("ruta/al/icono.png"), "Ejemplo", self)
        # self.addAction(action_ejemplo)
        # self.widgetForAction(action_ejemplo).setStyleSheet("padding: 5px;") # Ejemplo de estilo

        # Añadir un widget de espaciado a la derecha para alinear el título a la izquierda o centrado
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header_layout.addWidget(spacer)