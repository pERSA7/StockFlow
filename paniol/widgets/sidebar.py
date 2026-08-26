from PyQt6.QtWidgets import QListWidget,QHBoxLayout, QVBoxLayout, QWidget, QLabel, QSizePolicy, QTreeWidget, QTreeWidgetItem
from .prestamo import Prestamo
from PyQt6.QtCore import pyqtSignal, Qt


class Sidebar(QWidget):
        # --- AÑADIR SEÑALES ---
# Señal que emite el texto del ítem seleccionado (ej. "Inventario Actual")
        vista_seleccionada_signal = pyqtSignal(str)
        # Señal para filtrar préstamos por estado
        estado_prestamo_seleccionado_signal = pyqtSignal(str)
        # Señal para mostrar todos los préstamos
        mostrar_todos_prestamos_activos_signal = pyqtSignal()
        def __init__(self, parent=None):
                super().__init__(parent)
                self.setFixedWidth(200)
                layout_principal = QVBoxLayout(self)

        # *** AÑADIR con QLabel "Menu" ***
                titulo_label = QLabel("Menu")
        # personalizar la fuente y la alineación 
                layout_principal.addWidget(titulo_label)


        # *** CREAR Y AÑADIR LA LISTA DE OPCIONES (VERTICAL) ***
                self.lista_menu = QListWidget()
                self.lista_menu.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                opciones = ["Préstamos", "Inventario", "Historial de Movimientos", "Agregar Elemento", "Reposición/Bajas", "Novedades", "Recordatorios"]
                self.lista_menu.addItems(opciones)
                layout_principal.addWidget(self.lista_menu) # Añadir la lista al layout del contenedor

                self.lista_menu.itemClicked.connect(self.handle_sidebar_click)
        
                self.setLayout(layout_principal)


        def handle_sidebar_click(self, item):
                texto = item.text()
                self.vista_seleccionada_signal.emit(texto)

