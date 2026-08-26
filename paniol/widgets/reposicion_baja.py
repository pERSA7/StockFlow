from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout, QPushButton, QComboBox, QSpinBox, QMessageBox, QRadioButton
from PyQt6.QtCore import pyqtSignal
from ..app.core import db_manager   
from ..repositories.tool_repository import ToolRepository

class ReposicionBaja(QWidget):
    inventario_actualizado = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tool_repo = ToolRepository(db_manager)
        
        self.inventario_widget_ref = None
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        titulo_label = QLabel("Gestion de Bajas de Inventario")
        titulo_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(titulo_label)

        accion_layout = QHBoxLayout()
        self.accion_aumentar = QRadioButton ("Aumentar Cantidad (Reposición)")
        self.accion_baja = QRadioButton ("Reducir Cantidad")
        self.accion_eliminar = QRadioButton ("Eliminar Elemento")
        self.accion_aumentar.setChecked(True)

        accion_layout.addWidget(self.accion_aumentar)
        accion_layout.addWidget(self.accion_baja)
        accion_layout.addWidget(self.accion_eliminar)
        layout.addLayout(accion_layout)

        self.accion_aumentar.toggled.connect(self.actualizar_ui_segun_accion)
        self.accion_baja.toggled.connect(self.actualizar_ui_segun_accion)
        self.accion_eliminar.toggled.connect(self.actualizar_ui_segun_accion)

        form_layout = QFormLayout()
        self.herramienta_combo = QComboBox()

        self.cantidad_label = QLabel("Cantidad a Aumentar:")
        self.cantidad_input = QSpinBox()
        self.cantidad_input.setRange(1, 9999)

        form_layout.addRow("Seleccionar Herramienta:", self.herramienta_combo)
        form_layout.addRow(self.cantidad_label, self.cantidad_input)
        layout.addLayout(form_layout)

        self.aceptar_btn = QPushButton("Confirmar Acción")
        self.aceptar_btn.clicked.connect(self.confirmar_accion)
        layout.addWidget(self.aceptar_btn)
        layout.addStretch()

        self.cargar_herramientas()
        self.actualizar_ui_segun_accion()

    def set_inventario_widget_ref(self, ref):
        self.inventario_widget_ref = ref
        if self.inventario_widget_ref:
            self.inventario_actualizado.connect(self.inventario_widget_ref.obtener_inventario_completo)

    def cargar_herramientas(self):
        self.herramienta_combo.clear()
        herramientas = self.tool_repo.obtener_herramientas()
        for h in herramientas:
            self.herramienta_combo.addItem(f"{h['nombre']} ({h['codigo']})", h['id'])

    def actualizar_ui_segun_accion(self):
        if self.accion_aumentar.isChecked():
            self.cantidad_label.setText("Cantidad a aumentar:")
            self.cantidad_input.setEnabled(True)
        elif self.accion_baja.isChecked():
            self.cantidad_label.setText("Cantidad a dar de baja:")
            self.cantidad_input.setEnabled(True)
        elif self.accion_eliminar.isChecked():
            self.cantidad_label.setText("No es necesario ingresar cantidad.")
            self.cantidad_input.setEnabled(False)
        
    def confirmar_accion(self):
        herramienta_id = self.herramienta_combo.currentData()
        if not herramienta_id:
            QMessageBox.warning(self, "Error", "Por favor, seleccione una herramienta.")
            return
        
        # Logica para aumentar la cantidad
        if self.accion_aumentar.isChecked():
            cantidad = self.cantidad_input.value()
            confirm_msg = f"Esta seguro de aumentar {cantidad} unidades de la herramienta {self.herramienta_combo.currentText()}?"
            respuesta = QMessageBox.question(self, "Confirmar Reposición", confirm_msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if respuesta == QMessageBox.StandardButton.Yes:
                exito, mensaje = self.tool_repo.reponer_stock_inventario(herramienta_id, cantidad)
                if exito:
                    QMessageBox.information(self, "Exito", mensaje)
                    self.inventario_actualizado.emit()
                    self.cargar_herramientas()
                else:
                    QMessageBox.warning(self, "Error", mensaje)
        
        # Logica para dar de baja
        if self.accion_baja.isChecked():
            cantidad = self.cantidad_input.value()
            confirm_msg = f"Esta seguro de dar de baja {cantidad} unidades de la herramienta {self.herramienta_combo.currentText()}?"
            respuesta = QMessageBox.question(self, "Confirmar Baja", confirm_msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if respuesta == QMessageBox.StandardButton.Yes:
                exito, mensaje = self.tool_repo.dar_de_baja_herramienta(herramienta_id, cantidad)
                if exito:
                    QMessageBox.information(self, "Exito", mensaje)
                    self.inventario_actualizado.emit()
                    self.cargar_herramientas()
                else:
                    QMessageBox.warning(self, "Error", mensaje)

        # Logica para eliminar
        elif self.accion_eliminar.isChecked():
            confirm_msg = f"Esta seguro de eliminar la herramienta {self.herramienta_combo.currentText()}?"
            respuesta = QMessageBox.question(self, "Confirmar Eliminación", confirm_msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if respuesta == QMessageBox.StandardButton.Yes:
                exito, mensaje = self.tool_repo.eliminar_herramienta(herramienta_id)
                if exito:
                    QMessageBox.information(self, "Exito", mensaje)
                    self.inventario_actualizado.emit()
                    self.cargar_herramientas()
                else:
                    QMessageBox.warning(self, "Error", mensaje)



