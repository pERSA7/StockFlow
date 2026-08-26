from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QHeaderView, QTableWidgetItem, QDialog, QComboBox, QInputDialog, QMessageBox, QLineEdit, QCompleter
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal

from .registrar_prestamo import RegistrarPrestamo # Suponiendo que este diálogo sigue siendo para iniciar préstamos
from .devolucion_prestamo import DevolucionPrestamo
from ..app.core import db_manager 
from ..repositories.loan_repository import LoanRepository

class Prestamo(QWidget):

    prestamos_actualizados = pyqtSignal()


    def __init__(self, parent=None):
        super().__init__(parent)

        self.loan_repo = LoanRepository(db_manager)
        self.prestamos_activos = []

        layout_principal = QVBoxLayout(self)
        
        titulo_label = QLabel("Préstamos Activos")
        titulo_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        layout_principal.addWidget(titulo_label)
        
        # --- Controles de Filtro ---
        filtro_layout = QHBoxLayout()
        
        rotacion_label = QLabel("Filtrar por Rotación:")
        self.rotacion_combo = QComboBox()
        self.cargar_opciones_rotacion() 
        self.rotacion_combo.currentIndexChanged.connect(self.actualizar_tabla_prestamos_activos) 


        filtrar_btn = QPushButton("Actualizar Préstamos") 
        filtrar_btn.clicked.connect(self.actualizar_tabla_prestamos_activos) 


        filtro_layout.addWidget(rotacion_label)
        filtro_layout.addWidget(self.rotacion_combo)
        filtro_layout.addStretch(1) # Empuja el botón a la derecha
        filtro_layout.addWidget(filtrar_btn)
        layout_principal.addLayout(filtro_layout)

        # --- Tabla para mostrar los PRÉSTAMOS ACTIVOS ---
        self.tabla_prestamos_activos = QTableWidget() 
        self.tabla_prestamos_activos.setColumnCount(8) 
        self.tabla_prestamos_activos.setHorizontalHeaderLabels([
            "ID Préstamo", 
            "Código",
            "Herramienta",
            "Rotación",
            "Cantidad Prestada",
            "Cantidad Devuelta",
            "Cantidad Pendiente",
            "Fecha Préstamo"
        ])
        self.tabla_prestamos_activos.setColumnHidden(6, True) # Oculta la columna Cantidad Pendiente
        self.tabla_prestamos_activos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows) # Seleccionar filas completas

        # Configurar el redimensionamiento de las cabeceras
        header = self.tabla_prestamos_activos.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Columna ID
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Columna Código
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) 
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        self.tabla_prestamos_activos.verticalHeader().setVisible(False)
        
        layout_principal.addWidget(self.tabla_prestamos_activos)

        # ¡Clickear la fila! Conecta la señal cellDoubleClicked para iniciar el proceso de devolución
        #self.tabla_prestamos_activos.cellDoubleClicked.connect(self.manejar_doble_click_prestamo)

        # --- Botones de acción ---
        boton_layout = QHBoxLayout()
        self.nuevo_prestamo_btn = QPushButton("Registrar Nuevo Préstamo")
        self.devolver_prestamo_btn = QPushButton("Devolver")
        self.devolver_prestamo_btn.clicked.connect(self.abrir_centro_devoluciones)
        self.nuevo_prestamo_btn.clicked.connect(self.abrir_dialogo_prestamo)
        boton_layout.addWidget(self.nuevo_prestamo_btn)
        boton_layout.addWidget(self.devolver_prestamo_btn)

        layout_principal.addLayout(boton_layout)
        self.setLayout(layout_principal)

        self.inventario_widget_ref = None 
        
        # Cargar los préstamos activos iniciales al abrir la vista
        QTimer.singleShot(0, self.actualizar_tabla_prestamos_activos)
        


    def cargar_opciones_rotacion(self):
        """Carga las rotaciones desde la DB para el ComboBox de filtro."""
        self.rotacion_combo.clear()
        self.rotacion_combo.addItem("Todas las Rotaciones", None) # Opción para no filtrar
        rotaciones = self.loan_repo.obtener_rotaciones()
        for r in rotaciones:
            self.rotacion_combo.addItem(r.get('nombre'), r.get('id')) # type: ignore

    def actualizar_tabla_prestamos_activos(self):
        """
        Carga y muestra los préstamos activos (pendientes de devolución) en la tabla,
        aplicando los filtros seleccionados.
        """
        rotacion_id_filtro = self.rotacion_combo.currentData() 

        self.prestamos_activos = self.loan_repo.obtener_prestamos_activos(
            rotacion_id=rotacion_id_filtro
        )

        self.tabla_prestamos_activos.setRowCount(0) # Limpiar tabla

        for row_num, p in enumerate(self.prestamos_activos):
            self.tabla_prestamos_activos.insertRow(row_num)
            
            # Las columnas de ID deben ser no editables
            item_id = QTableWidgetItem(str(p['prestamo_id'])) # type: ignore
            item_id.setFlags(item_id.flags() & ~Qt.ItemFlag.ItemIsEditable) 
            self.tabla_prestamos_activos.setItem(row_num, 0, item_id)

            item_codigo = QTableWidgetItem(p['codigo']) # type: ignore
            item_codigo.setFlags(item_codigo.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_prestamos_activos.setItem(row_num, 1, item_codigo)

            item_herramienta = QTableWidgetItem(p['nombre_herramienta']) # type: ignore
            item_herramienta.setFlags(item_herramienta.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_prestamos_activos.setItem(row_num, 2, item_herramienta)

            item_rotacion = QTableWidgetItem(p['nombre_rotacion']) # type: ignore
            item_rotacion.setFlags(item_rotacion.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_prestamos_activos.setItem(row_num, 3, item_rotacion)
            
            item_cant_prestada = QTableWidgetItem(str(p['cantidad_prestada'])) # type: ignore
            item_cant_prestada.setFlags(item_cant_prestada.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_prestamos_activos.setItem(row_num, 4, item_cant_prestada)
            
            item_cant_devuelta = QTableWidgetItem(str(p['cantidad_devuelta'])) # type: ignore
            item_cant_devuelta.setFlags(item_cant_devuelta.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_prestamos_activos.setItem(row_num, 5, item_cant_devuelta)

            item_cant_pendiente = QTableWidgetItem(str(p['cantidad_pendiente'])) # type: ignore
            # Esta es la columna clave para la interacción de devolución
            item_cant_pendiente.setFlags(item_cant_pendiente.flags() & ~Qt.ItemFlag.ItemIsEditable) # Será solo informativo
            self.tabla_prestamos_activos.setItem(row_num, 6, item_cant_pendiente)
            
            fecha_str = p['fecha_prestamo'].strftime("%Y-%m-%d %H:%M") if p['fecha_prestamo'] else "" # type: ignore
            item_fecha = QTableWidgetItem(fecha_str)
            item_fecha.setFlags(item_fecha.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_prestamos_activos.setItem(row_num, 7, item_fecha)


    def abrir_dialogo_prestamo(self):
        """Abre el diálogo para registrar un nuevo préstamo."""
        dialogo = RegistrarPrestamo(self) 
        dialogo.prestamo_registrado.connect(self.on_cambio_en_prestamos) # Conectar la señal a nuestro slot unificado
        dialogo.exec() 

    def on_cambio_en_prestamos(self):
        """
        Slot que se ejecuta cuando un préstamo es registrado o una devolución es procesada.
        Aquí refrescamos la tabla de préstamos activos y la vista de inventario.
        """
        self.actualizar_tabla_prestamos_activos()
        
        # Si tienes una referencia al widget de Inventario para refrescarlo:
        if self.inventario_widget_ref and hasattr(self.inventario_widget_ref, 'obtener_inventario_completo'):
            self.inventario_widget_ref.obtener_inventario_completo()
            print("[INFO] Inventario actualizado desde el módulo de Préstamos.")

        self.prestamos_actualizados.emit()

    def abrir_centro_devoluciones(self):
        dialogo = DevolucionPrestamo(self)

        dialogo.devolucion_realizada.connect(self.on_cambio_en_prestamos)
        dialogo.exec()