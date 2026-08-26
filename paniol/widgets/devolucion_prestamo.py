from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QComboBox, QTableWidgetItem, QPushButton,QLineEdit, QMessageBox, QHeaderView, QCheckBox, QWidget, QHBoxLayout, QSpinBox
from PyQt6.QtCore import pyqtSignal, Qt
from functools import partial
from ..app.core import db_manager
from ..repositories.loan_repository import LoanRepository
#from .dialogo_animado import AnimatedDialog

class DevolucionPrestamo(QDialog):
    devolucion_realizada = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.loan_repo = LoanRepository(db_manager)
        self.setWindowTitle("Centro de Devoluciones")
        self.setMinimumSize(800,500)

        layout = QVBoxLayout(self)
        filtro_layout = QHBoxLayout(self)
        self.filtro_label = QLabel("Filtrar por rotación:")
        self.filtro_rotacion = QComboBox()
        self.cargar_opciones_rotacion()
        self.filtro_rotacion.currentIndexChanged.connect(self.cargar_prestamos)

        filtro_layout.addWidget(self.filtro_label)
        filtro_layout.addWidget(self.filtro_rotacion)
        layout.addLayout(filtro_layout)

        scan_layout = QHBoxLayout()
        scan_label = QLabel("Escanear herramienta a devolver:")
        self.scan_line_edite = QLineEdit()
        self.scan_line_edite.setPlaceholderText("Escanear codigo aqui...")
        self.scan_line_edite.returnPressed.connect(self.devolucion_por_scan)
        scan_layout.addWidget(scan_label)
        scan_layout.addWidget(self.scan_line_edite)
        layout.addLayout(scan_layout)

        self.tabla_detalles = QTableWidget()
        self.tabla_detalles.setColumnCount(5)
        self.tabla_detalles.setHorizontalHeaderLabels(["Rotacion", "Elemento", "Cant. Pendiente","Cant a Devolver", "Acción"])
        header = self.tabla_detalles.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.tabla_detalles)


        self.cargar_prestamos()

    def cargar_opciones_rotacion(self):
        """Carga las rotaciones desde la DB para el ComboBox de filtro."""
        self.filtro_rotacion.clear()
        self.filtro_rotacion.addItem("Todas las Rotaciones", None) # Opción para no filtrar
        rotaciones = self.loan_repo.obtener_rotaciones()
        for r in rotaciones:
            self.filtro_rotacion.addItem(r.get('nombre'), r.get('id')) # type: ignore

    def cargar_prestamos(self):
        
        rotacion_id_filtro = self.filtro_rotacion.currentData()
        prestamos = self.loan_repo.obtener_prestamos_activos(rotacion_id=rotacion_id_filtro)
        self.tabla_detalles.setRowCount(0)
        
        if not prestamos:
            self.tabla_detalles.setRowCount(1)
            item_info = QTableWidgetItem("No hay préstamos con devoluciones pendientes.")
            item_info.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_detalles.setItem(0, 0, item_info)
            self.tabla_detalles.setSpan(0, 0, 1, self.tabla_detalles.columnCount())
            return
        for prestamo in prestamos:
            row = self.tabla_detalles.rowCount()
            self.tabla_detalles.insertRow(row)

            prestamo_id = prestamo['prestamo_id']
            cantidad_pendiente = prestamo['cantidad_pendiente']

            item_rotacion = QTableWidgetItem(prestamo['nombre_rotacion'])
            item_rotacion.setData(Qt.ItemDataRole.UserRole, prestamo)
            self.tabla_detalles.setItem(row, 0, item_rotacion)
            self.tabla_detalles.setItem(row, 1, QTableWidgetItem(prestamo['nombre_herramienta']))
            self.tabla_detalles.setItem(row, 2, QTableWidgetItem(str(cantidad_pendiente)))

            spinbox_devolver = QSpinBox()
            spinbox_devolver.setMinimum(1)
            spinbox_devolver.setMaximum(cantidad_pendiente)
            spinbox_devolver.setValue(1) # Sugerir devolver de a uno
            self.tabla_detalles.setCellWidget(row, 3, spinbox_devolver)

            btn_registrar = QPushButton("Registrar")
            btn_registrar.clicked.connect(
                partial(self.registrar_devolucion, prestamo_id, spinbox_devolver)
            )
            self.tabla_detalles.setCellWidget(row, 4, btn_registrar)


    #           checkbox_widget = QWidget()
    #          checkbox_layout = QHBoxLayout(checkbox_widget)
    #         checkbox = QCheckBox()
    #        checkbox_layout.addWidget(checkbox)
    #       checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    #      checkbox_layout.setContentsMargins(0, 0, 0, 0)
    #     
        #    checkbox.setProperty("id_prestamo_detalle", id_detalle)

#            if devuelto:
    #              checkbox.setChecked(True)
    #             checkbox.setEnabled(False) #Si ya esta devuelto
#
    #           checkbox.stateChanged.connect(self.marcar_como_devuelto)
    #          self.tabla_detalles.setCellWidget(row, 2, checkbox_widget)

    #     self.verificar_estado_completo()
    def devolucion_por_scan(self):
        codigo_escaneado = self.scan_line_edite.text().strip()
        if not codigo_escaneado:
            return
        
        filas_encontradas = []

        for row in range(self.tabla_detalles.rowCount()):
            item = self.tabla_detalles.item(row, 0)
            if not item: continue

            datos_prestamo = item.data(Qt.ItemDataRole.UserRole)
            if datos_prestamo and datos_prestamo.get('codigo', '').lower() == codigo_escaneado.lower():
                filas_encontradas.append(row)

        #Si se encuentra, proseguir a la devolocion
        if len(filas_encontradas) == 0:
            rotacion_actual = self.filtro_rotacion.currentText()
            QMessageBox.warning(self, "No encontrado", f"La herramienta con codigo '{codigo_escaneado}' no tiene prestamos pendientes en {rotacion_actual}.")
        elif len(filas_encontradas) > 1:
            QMessageBox.information(self, 
                                    "Ambigüedad Detectada",  # Este es el título
                        (f"La herramienta '{codigo_escaneado}' está prestada a múltiples rotaciones.\n\n"
                        "Por favor, seleccione una rotación específica en el filtro para registrar la devolución."))
            return
            
        else:
            fila = filas_encontradas[0]
            item = self.tabla_detalles.item(fila, 0)
            prestamo_encontrado = item.data(Qt.ItemDataRole.UserRole)

            if prestamo_encontrado:
                prestamo_id = prestamo_encontrado['prestamo_id']
                spinbox = self.tabla_detalles.cellWidget(fila, 3)

                if spinbox:
                    self.registrar_devolucion(prestamo_id, spinbox)
                else:
                    QMessageBox.warning(self, "Error Interno", "No se encontró el control de cantidad para esta fila.")

        self.scan_line_edite.clear()
        self.scan_line_edite.setFocus()
        


    def registrar_devolucion(self, prestamo_id, spinbox_devolver):
        cantidad_a_devolver = spinbox_devolver.value()
        exito = self.loan_repo.registrar_devolucion(prestamo_id, cantidad_a_devolver)
        if exito:
            QMessageBox.information(self, "Información", "Devolución registrada correctamente.")
            self.devolucion_realizada.emit()
            self.cargar_prestamos()
        else:
            QMessageBox.critical(self, "Error", f"Error al registrar la devolución")




# def marcar_como_devuelto(self, state):
#        checkbox = self.sender()
#        id_detalle = checkbox.property("id_prestamo_detalle")

#        if state == Qt.CheckState.Checked.value:
#            try:
#                db_manager.marcar_item_como_devuelto(id_detalle)
#                checkbox.setEnabled(False)
#                self.verificar_estado_completo()
#            except Exception as e:
#                QMessageBox.critical(self, "Error", f"Error al marcar el item como devuelto: {str(e)}")
#                checkbox.setChecked(False)

#    def verificar_estado_completo(self):
#        if db_manager.verificar_todos_items_devueltos(self.id_prestamo_db):
#            self.todos_los_items_devueltos.emit(self.id_prestamo_db)

