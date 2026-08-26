from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QTextEdit, 
QDateTimeEdit, QDialogButtonBox, QFormLayout, QMessageBox)
from PyQt6.QtCore import QDateTime
#from .dialogo_animado import AnimatedDialog

# ¡Importamos nuestra instancia compartida y el repositorio!
from ..app.core import db_manager
from ..repositories.notification_repository import NotificationRepository

class DialogoRecordatorio(QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Recordatorio")
        self.setMinimumWidth(350)

        self.db_manager = db_manager
        self.notification_repo = NotificationRepository(db_manager)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.txt_titulo = QLineEdit()
        self.txt_descripcion = QTextEdit()
        self.txt_descripcion.setPlaceholderText("Opcional...")

        self.tiempo_inicio = QDateTimeEdit()
        self.tiempo_inicio.setCalendarPopup(True)
        self.tiempo_inicio.setDateTime(QDateTime.currentDateTime())
        self.tiempo_inicio.setDisplayFormat("yyyy-MM-dd hh:mm ap")

        self.tiempo_limite = QDateTimeEdit()
        self.tiempo_limite.setCalendarPopup(True)
        self.tiempo_limite.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.tiempo_limite.setMinimumDateTime(QDateTime.currentDateTime())

        self.tiempo_inicio.dateTimeChanged.connect(self.actualizar_fecha_limite_minima)
        self.tiempo_limite.setMinimumDateTime(self.tiempo_inicio.dateTime())

        form_layout.addRow("Título: ", self.txt_titulo)
        form_layout.addRow("Descripción: ",self.txt_descripcion)
        form_layout.addRow("Fecha de Inicio: ",self.tiempo_inicio)
        form_layout.addRow("Fecha Limite: ",self.tiempo_limite)

        layout.addLayout(form_layout)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )

        botones.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
        botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")

        botones.accepted.connect(self.aceptar)
        botones.rejected.connect(self.reject)

        layout.addWidget(botones)

    def actualizar_fecha_limite_minima(self, nueva_fecha_inicio):
        #Este slot se activa cuando 'date_inicio' cambia.
        #Asegura que la fecha límite sea siempre igual o posterior a la de inicio.
        self.tiempo_limite.setMinimumDateTime(nueva_fecha_inicio)
        if self.tiempo_limite.dateTime() < nueva_fecha_inicio:
            self.tiempo_limite.setDateTime(nueva_fecha_inicio)


    def aceptar(self):
        titulo = self.txt_titulo.text().strip()
        descripcion = self.txt_descripcion.toPlainText().strip()
        fecha_inicio = self.tiempo_inicio.dateTime().toString("yyyy-MM-dd hh:mm:ss")
        fecha_limite = self.tiempo_limite.dateTime().toString("yyyy-MM-dd hh:mm:ss")

        if not titulo:
            QMessageBox.warning(self, "Datos incompletos", "El campo 'Titulo' es obligatorio")
            self.txt_titulo.setFocus()
            return
        
        exito, mensaje = self.notification_repo.registrar_recordatorio(titulo, descripcion, fecha_inicio, fecha_limite)

        if exito:
            QMessageBox.information(self, "Exito", "Recordatorio guardado correctamente.")
            super().accept()
        else:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el recordatorio:\n{mensaje}")