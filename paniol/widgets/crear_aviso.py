from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit,QPushButton, QHBoxLayout, QMessageBox
from PyQt6.QtCore import pyqtSignal
from ..app.core import db_manager
from ..repositories.notification_repository import NotificationRepository
#from .dialogo_animado import AnimatedDialog

class CrearAviso(QDialog):
    aviso_creado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.notification_repo = NotificationRepository(db_manager)
        self.setWindowTitle("Crear Aviso Personalizado")
        self.setMinimumSize(400, 250)

        layout_principal = QVBoxLayout()

        instrucciones_label = QLabel("Escriba el mensaje que quiera publicar en el panel de novedades:")
        layout_principal.addWidget(instrucciones_label)

        self.aviso_text_edit = QTextEdit()
        self.aviso_text_edit.setPlaceholderText("Ej: Se informa que en el dia de mañana se realizara mantenimiento en...")
        layout_principal.addWidget(self.aviso_text_edit)

        layout_botones = QHBoxLayout()
        layout_botones.addStretch()

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)

        self.btn_publicar = QPushButton("Publicar Aviso")
        self.btn_publicar.clicked.connect(self.publicar_aviso)
        self.btn_publicar.setDefault(True)

        layout_botones.addWidget(self.btn_cancelar)
        layout_botones.addWidget(self.btn_publicar)

        layout_principal.addLayout(layout_botones)
        self.setLayout(layout_principal)

    def publicar_aviso(self):
        descripcion = self.aviso_text_edit.toPlainText().strip()

        if not descripcion:
            QMessageBox.warning(self, "Mensaje vacio", "Por favor, escriba un mensaje antes de publicar.")
            return
        
        success, message = self.notification_repo.registrar_novedad_personalizada("AVISO", descripcion)

        if success:
            QMessageBox.information(self, "Exito", "El aviso se publico correctamente.")
            self.aviso_creado.emit()
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"No se pudo publicar el aviso:\n{message}")