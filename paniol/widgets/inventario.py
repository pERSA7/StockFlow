from PyQt6.QtWidgets import (
    QAbstractItemView, QWidget, QVBoxLayout, QTableView, QHeaderView, QLabel, QLineEdit, QPushButton, QHBoxLayout
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer, QSize

# ¡Importamos nuestra instancia compartida!
from ..app.core import db_manager
from ..repositories.tool_repository import ToolRepository
from .ui_utils import exportar_tabla_a_excel

class Inventario(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout_principal = QVBoxLayout(self)

        self.db_manager = db_manager
        self.tool_repo = ToolRepository(db_manager)

        # Etiqueta de la vista
        titulo_label = QLabel("Inventario Actual")
        layout_principal.addWidget(titulo_label) 

        controles_layout = QHBoxLayout()
        self.cuadro_busqueda = QLineEdit()
        self.cuadro_busqueda.setPlaceholderText("Buscar Herramienta...")
        self.cuadro_busqueda.textChanged.connect(self.filtrar_tabla_inventario)
        self.cuadro_busqueda.returnPressed.connect(self.realizar_busqueda_scan)

        self.exportar_btn = QPushButton("Exportar a Excel")
        self.exportar_btn.setObjectName("excelButton")
        self.exportar_btn.setIcon(QIcon("C:/proyectos/taller-escuela/paniol/style/excel.ico"))
        self.exportar_btn.clicked.connect(self.exportar_inventario)

        controles_layout.addWidget(self.cuadro_busqueda)
        controles_layout.addStretch()
        controles_layout.addWidget(self.exportar_btn)
        layout_principal.addLayout(controles_layout)

        # Crear la vista de tabla
        self.tabla_inventario = QTableView()
        layout_principal.addWidget(self.tabla_inventario)
        # Deshabilita la edición para toda la vista
        self.tabla_inventario.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        # Al hacer clic se selecciona la fila completa. No en una celda individual
        self.tabla_inventario.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        # Crear el modelo de datos
        self.modelo_tabla = QStandardItemModel()
        self.modelo_tabla.setHorizontalHeaderLabels(["Código", "Nombre", "Cantidad", "Fecha Inventario"])
        self.tabla_inventario.setModel(self.modelo_tabla)

        # *** CONFIGURAR EL REDIMENSIONAMIENTO DE LAS CABECERAS ***
        header = self.tabla_inventario.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.setLayout(layout_principal)

        # Es una buena práctica cargar los datos iniciales un poco después
        # para no bloquear la creación de la UI.
        # Muestra las herramientas que viene de la base de datos a la aplicacion después de iniciar
        QTimer.singleShot(0, self.obtener_inventario_completo)

    """
    Este método ahora se encarga de pedir los datos al gestor y poblar la tabla.
    """
    def obtener_inventario_completo(self):
        # llamamos al metodo del REPOSITORIO
        herramientas = self.tool_repo.obtener_herramientas()
        # Limpiar modelo (evita duplicados si se refresca)
        self.modelo_tabla.removeRows(0, self.modelo_tabla.rowCount())
        
        for h in herramientas:
            fila = [
                QStandardItem(h.get("codigo")), # type: ignore
                QStandardItem(h.get("nombre")), # type: ignore
                QStandardItem(str(h.get("cantidad_total"))), # type: ignore
                QStandardItem(h.get("fecha_inventario").strftime("%Y-%m-%d")) # type: ignore
            ]
            self.modelo_tabla.appendRow(fila)
    
    def filtrar_tabla_inventario(self):
        texto_busqueda = self.cuadro_busqueda.text().lower()

        for i in range(self.modelo_tabla.rowCount()):
            item_codigo = self.modelo_tabla.item(i, 0)
            item_nombre = self.modelo_tabla.item(i, 1)

            texto_codigo = item_codigo.text().lower() if item_codigo else ""
            texto_nombre = item_nombre.text().lower() if item_nombre else ""

            if texto_busqueda in texto_codigo or texto_busqueda in texto_nombre:
                self.tabla_inventario.setRowHidden(i, False)
            else:
                self.tabla_inventario.setRowHidden(i, True)

    def exportar_inventario(self):
        exportar_tabla_a_excel(self.tabla_inventario, self, "Inventario General")

    def realizar_busqueda_scan(self):
        self.filtrar_tabla_inventario()
        self.cuadro_busqueda.selectAll()