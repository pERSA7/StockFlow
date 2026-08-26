from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QPushButton
#from .prestamo import Prestamo
from PyQt6.QtCore import QTimer, Qt, QSize
from PyQt6.QtGui import QIcon
from ..app.core import db_manager
from ..repositories.loan_repository import LoanRepository
from .ui_utils import exportar_tabla_a_excel

class Historial(QWidget):
    def __init__(self, parent=None): # <--- Ahora sí acepta la conexión
        super().__init__(parent)
        self.loan_repo = LoanRepository(db_manager)
        
        layout = QVBoxLayout(self)
        
        titulo_label = QLabel("Historial de Préstamos")
        layout.addWidget(titulo_label)

        # Filtro de rotaciones
        filtro_layout = QHBoxLayout()
        rotaciones_label = QLabel("Filtrar por Rotaciones:")
        self.rotacion_combo = QComboBox()


        filtrar_btn = QPushButton("Filtrar")
        filtrar_btn.clicked.connect(self.cargar_historial)

        exportar_btn = QPushButton("Exportar a Excel")
        exportar_btn.setObjectName("excelButton")
        exportar_btn.setIcon(QIcon("C:/proyectos/taller-escuela/paniol/style/excel.ico"))
        exportar_btn.clicked.connect(self.exportar_historial)
        
        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(7)  # Define el número de columnas
        self.tabla_historial.setHorizontalHeaderLabels([
            "ID Préstamo",
            "Elementos",
            "Codigo",
            "Rotación",
            "Cantidad",
            "Fecha Préstamo",
            "Fecha Devolución"
        ])
         # *** CONFIGURAR EL REDIMENSIONAMIENTO DE LAS CABECERAS ***
        header = self.tabla_historial.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.tabla_historial.verticalHeader().setVisible(False)

        filtro_layout.addWidget(rotaciones_label)
        filtro_layout.addWidget(self.rotacion_combo)
        filtro_layout.addWidget(filtrar_btn)
        filtro_layout.addWidget(exportar_btn)
        layout.addLayout(filtro_layout)

        layout.addWidget(self.tabla_historial)

        self.setLayout(layout)

        self.cargar_filtro()
        QTimer.singleShot(0, self.cargar_historial)

    def cargar_filtro(self):
        self.rotacion_combo.clear()
        self.rotacion_combo.addItem("Todos", userData=None)
        try:
            rotaciones_db = self.loan_repo.obtener_rotaciones() # Llama a la función del Repo
            for r in rotaciones_db:
                # Añadimos el nombre y el ID como dato asociado
                self.rotacion_combo.addItem(r.get('nombre'), r.get('id'))
        except Exception as e:
            print(f"Error al cargar rotaciones: {e}")

    def cargar_historial(self):
        self.tabla_historial.setRowCount(0)

        rotacion_id = self.rotacion_combo.currentData()

        historial_db = self.loan_repo.obtener_prestamos_completados(rotacion_id)

        for row_num, registro in enumerate(historial_db):
            self.tabla_historial.insertRow(row_num)

            fecha_prestamo_str = registro['fecha_prestamo'].strftime("%Y-%m-%d %H:%M") if registro.get('fecha_prestamo') else "N/A" # Formatea la fecha a 'YYYY-MM-DD
            fecha_cierre_str = registro['fecha_cierre'].strftime("%Y-%m-%d %H:%M") if registro.get('fecha_cierre') else "N/A"

            items = [
                str(registro['prestamo_id']),
                registro['nombre_herramienta'],
                registro['codigo'],
                registro['nombre_rotacion'],
                str(registro['cantidad_prestada']),
                fecha_prestamo_str,
                fecha_cierre_str
            ]

            for col_num, data in enumerate(items):
                item = QTableWidgetItem(data)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tabla_historial.setItem(row_num, col_num, item)
        
    def exportar_historial(self):
        exportar_tabla_a_excel(self.tabla_historial, self, "Historial de Prestamos")