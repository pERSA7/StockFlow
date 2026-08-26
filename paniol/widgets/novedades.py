from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidgetItem, QHeaderView, QTableWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import QTimer
from ..app.core import db_manager
from ..repositories.notification_repository import NotificationRepository
from .crear_aviso import CrearAviso

class Novedades(QWidget):
    def __init__ (self, parent=None):
        super().__init__(parent)
        self.notification_repo = NotificationRepository(db_manager)
        layout_principal = QVBoxLayout(self)

    # Etiqueta de la vista
        titulo_layout = QHBoxLayout()
        titulo_label = QLabel("Novedades")
        titulo_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.btn_crear_aviso = QPushButton("Crear Aviso Personalizado")
        self.btn_crear_aviso.clicked.connect(self.abrir_dialogo_crear_aviso)

        titulo_layout.addWidget(titulo_label)
        titulo_layout.addStretch()
        titulo_layout.addWidget(self.btn_crear_aviso)
        layout_principal.addLayout(titulo_layout)

        self.tabla_novedades = QTableWidget()
        self.tabla_novedades.setColumnCount(3)
        self.tabla_novedades.setHorizontalHeaderLabels(["Fecha", "Tipo de evento", "Descripción"])

        header = self.tabla_novedades.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        self.tabla_novedades.verticalHeader().setVisible(False)

        layout_principal.addWidget(self.tabla_novedades)

        QTimer.singleShot(0, self.cargar_novedades)

    def abrir_dialogo_crear_aviso(self):
        """
        Crea y muestra la ventana de diálogo para escribir un nuevo aviso.
        """
        dialogo = CrearAviso(self)
        # Conectamos la señal 'aviso_creado' del diálogo a nuestro método 'cargar_novedades'
        # Esto hará que la tabla se refresque automáticamente al publicar un aviso.
        dialogo.aviso_creado.connect(self.cargar_novedades) # <--- 3. Conectamos la señal para refrescar
        dialogo.exec()


    def cargar_novedades(self):
        novedades = self.notification_repo.obtener_novedades()
        self.tabla_novedades.setRowCount(0)
        for row_num, novedad in enumerate(novedades):
            self.tabla_novedades.insertRow(row_num)
            
            # Formatear fecha para que sea más legible
            fecha_str = novedad['fecha'].strftime("%Y-%m-%d %H:%M:%S")
            
            self.tabla_novedades.setItem(row_num, 0, QTableWidgetItem(fecha_str))
            self.tabla_novedades.setItem(row_num, 1, QTableWidgetItem(novedad['tipo_novedad']))
            self.tabla_novedades.setItem(row_num, 2, QTableWidgetItem(novedad['descripcion']))

