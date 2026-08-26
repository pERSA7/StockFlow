from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidgetItem, QHeaderView, QTableWidget, QMessageBox, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

from .diag_recordatorio import DialogoRecordatorio
from ..app.core import db_manager
from ..repositories.notification_repository import NotificationRepository

class Recordatorios(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.db_manager = db_manager
        self.notification_repo = NotificationRepository(db_manager)

        layout_principal = QVBoxLayout(self)

        titulo_layout = QHBoxLayout()
        titulo_label = QLabel("Recordatorios")

        btn_recordatorio = QPushButton("Crear un nuevo Recordatorio")
        btn_recordatorio.setFixedSize(260, 30)
        btn_recordatorio.clicked.connect(self.abrir_dialogo)

        titulo_layout.addWidget(titulo_label)
        titulo_layout.addStretch()
        titulo_layout.addWidget(btn_recordatorio)

        layout_principal.addLayout(titulo_layout)

        self.tabla_recordatorios = QTableWidget()
        self.tabla_recordatorios.setColumnCount(4)
        self.tabla_recordatorios.setHorizontalHeaderLabels([
            "Título",
            "Descripción Recordatorio",
            "Fecha Inicio",
            "Fecha Limite"
        ])

        header = self.tabla_recordatorios.horizontalHeader()
        # Columna "Descripción" se estira para llenar el espacio
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        # Otras columnas se ajustan al contenido
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_recordatorios.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.tabla_recordatorios.verticalHeader().setVisible(False)

        layout_principal.addWidget(self.tabla_recordatorios)

        self.cargar_recordatorios()

    def cargar_recordatorios(self):
        try:
            self.tabla_recordatorios.setRowCount(0)
            recordatorios = self.notification_repo.obtener_recordatorios()

            if not recordatorios:
                self.tabla_recordatorios.setRowCount(1)
                item_vacio = QTableWidgetItem("No hay recordatorios pendientes.")
                item_vacio.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_recordatorios.setItem(0, 0, item_vacio)
                self.tabla_recordatorios.setSpan (0, 0, 1, 4)
                return
            
            for recordatorio in recordatorios:
                row = self.tabla_recordatorios.rowCount()
                self.tabla_recordatorios.insertRow(row)

                fecha_inicio_str = recordatorio['fecha_inicio'].strftime('%Y-%m-%d %H:%M')
                fecha_limite_str = recordatorio['fecha_limite'].strftime('%Y-%m-%d %H:%M')

                self.tabla_recordatorios.setItem(row, 0, QTableWidgetItem(recordatorio['titulo']))
                self.tabla_recordatorios.setItem(row, 1, QTableWidgetItem(recordatorio['descripcion']))
                self.tabla_recordatorios.setItem(row, 2, QTableWidgetItem(fecha_inicio_str))
                self.tabla_recordatorios.setItem(row, 3, QTableWidgetItem(fecha_limite_str))

        except Exception as e:
            print(f"Error al cargar recordatorios: {e}")
            QMessageBox.critical(self, "Error", f"No se puedieron cargar los recordatorios: {e}")

    def abrir_dialogo(self):
        dialogo = DialogoRecordatorio(self)
        if dialogo.exec():
            self.cargar_recordatorios()
        else: 
            print("[DEBUG] Creacion de recordatios cancelada")




