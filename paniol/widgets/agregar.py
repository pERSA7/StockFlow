from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QLineEdit, QPushButton, QFormLayout, QMessageBox, QSpinBox
from ..app.core import db_manager
from ..repositories.tool_repository import ToolRepository
from PyQt6.QtCore import pyqtSignal

class Agregar(QWidget):
    herramienta_agregada = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tool_repo = ToolRepository(db_manager)

        self.inventario_widget_ref = None 

        #self.inventario_widget_ref = inventario_widget_ref
        layout_principal = QVBoxLayout(self)
        self.setLayout(layout_principal)

        titulo_label = QLabel("Agregar Elemento")
        layout_principal.addWidget(titulo_label)

        form_layout = QFormLayout()
        
        self.nombre_input = QLineEdit()
        self.nombre_input.textChanged.connect(self.actualizar_codigo)
        self.codigo_input = QLineEdit()
        self.cantidad_input = QSpinBox()
        self.cantidad_input.setRange(1, 9999)

        form_layout.addRow("Nombre:", self.nombre_input)
        form_layout.addRow("Código:", self.codigo_input)
        form_layout.addRow("Cantidad:", self.cantidad_input)

        layout_principal.addLayout(form_layout)

        self.guardar_btn = QPushButton("Guardar")
        self.guardar_btn.clicked.connect(self.guardar_herramienta)

        layout_principal.addWidget(self.guardar_btn)

    def set_inventario_widget_ref(self, ref):
        self.inventario_widget_ref = ref

    def actualizar_codigo(self):
        nombre = self.nombre_input.text().strip()
        if len(nombre) >= 3:
            codigo = nombre[:3].upper()
            self.codigo_input.setText(codigo)
            self.codigo_input.setText(f"{codigo}-...")
        else:
            self.codigo_input.clear()

    def guardar_herramienta(self):
        nombre = self.nombre_input.text().strip()
        cantidad = self.cantidad_input.value()

        if not nombre or not len(nombre):
            QMessageBox.warning(self, "Error", "El nombre debe tener al menos 3 caracteres.")
            return
        
        exito, mensaje = self.tool_repo.agregar_herramienta(nombre, cantidad)
        
        if exito:
            QMessageBox.information(self, "Exito", mensaje)
            self.nombre_input.clear()
            self.codigo_input.clear()
            self.cantidad_input.setValue(1)

            if self.inventario_widget_ref and hasattr(self.inventario_widget_ref, 'obtener_inventario_completo'):
                self.inventario_widget_ref.obtener_inventario_completo()

            self.herramienta_agregada.emit()
            
        else:
            QMessageBox.warning(self, "Error de base de datos", mensaje)
        