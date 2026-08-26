# widgets/ventana.py
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QMessageBox # Asegúrate de importar QApplication si no lo tenías
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer
import os
import sys
import traceback

# ¡Importamos nuestra instancia compartida!
from ..app.core import db_manager
from ..repositories.notification_repository import NotificationRepository

from .header import Header
from .sidebar import Sidebar
from .area_central import AreaCentral

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StockFlow")
        self.setWindowIcon(QIcon(resource_path("/assets/STOCKFLOW_LOGO.png")))
        self.resize(600, 400)
        self.setGeometry(0, 30, 1200, 500)

        print("[DEBUG] Intentando obtener conexión a la base de datos...") # <-- ESTE ES CLAVE
        self.db_manager = db_manager
        self.notification_repo = NotificationRepository(db_manager)
        # Conectar usando el gestor
        if not self.db_manager.connect():
            QMessageBox.critical(self, "Error de Conexión", 
            "No se pudo establecer conexión con la base de datos. La aplicación se cerrará.")
            sys.exit(1)

        # Si llegamos aquí, la conexión es exitosa.
        print("[INFO] Conexión DB verificada. Procediendo a crear la interfaz...") # <-- ESTE ES CLAVE

        # *** CONTENEDOR PRINCIPAL (VERTICAL) ***
        main_layout = QVBoxLayout()
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # *** HEADER IMPORTADO ***
        try:
            self.header = Header(self) 
            main_layout.addWidget(self.header)
            print("Header creada OK - Punto de control 1")
        except Exception as e:
            print(f"Error al crear el header: {e}")
            traceback.print_exc() # Añadir traceback
            sys.exit(1) 

        # *** CONTENEDOR PRINCIPAL (HORIZONTAL) PARA SIDEBAR Y ÁREA CENTRAL ***
        body_layout = QHBoxLayout()
        main_layout.addLayout(body_layout)

        # *** SIDEBAR IMPORTADO ***
        try:
            self.sidebar = Sidebar(self) 
            body_layout.addWidget(self.sidebar)
            print("Sidebar creada OK - Punto de control 2") 
        except Exception as e:
            print(f"Error al crear la sidebar: {e}")
            traceback.print_exc() # Añadir traceback
            sys.exit(1)

        # *** ÁREA CENTRAL DEL CONTENIDO PRINCIPAL ***
        try:
            self.area_central = AreaCentral(self) # Pasa la conexión
            body_layout.addWidget(self.area_central) 
            print("Area Central creada OK - Punto de control 3") 
        except Exception as e:
            print(f"Error al crear el area central: {e}")
            traceback.print_exc() # Imprime el traceback
            sys.exit(1)

        try:
            self.conectar_señales()
            print("Señales conectadas OK - Punto de control 4") 
        except Exception as e:
            print(f"Error al conectar señales: {e}")
            traceback.print_exc() # Añadir traceback
            sys.exit(1)

        self.iniciar_verificador_recordatorios()

    def conectar_señales(self):
        if hasattr(self, "sidebar") and hasattr(self, "area_central"):
            self.sidebar.vista_seleccionada_signal.connect(self.area_central.cambiar_vista)
        else:
            print("No se pudo conectar señales: faltan componentes.")

    def iniciar_verificador_recordatorios(self):
        self.timer_recordatorios = QTimer()
        self.timer_recordatorios.timeout.connect(self.chequear_recordatorios_vencidos)
        self.timer_recordatorios.start(60000)
        print("[INFO] Vigilante de recordatorios iniciado. Chequeando cada 1 minuto")
        QTimer.singleShot(0, self.chequear_recordatorios_vencidos)

    def chequear_recordatorios_vencidos(self):
        print("[DEBUG] Chequeando recordatorios vencidos...")
        vencidos = self.notification_repo.verificar_recordatorios_vencidos()

        if vencidos:
            titulos = "\n- ".join([r['titulo'] for r in vencidos])
            QMessageBox.information(self,
            "Recordatorios finalizados",
            f"Los siguiente recordatorios han finalizado:\n\n-{titulos}"
            )

            # 2. Refrescar la vista de recordatorios (si existe)
            # Esto hará que los recordatorios desaparezcan de la lista de "pendientes"
            if hasattr(self, 'area_central') and hasattr(self.area_central, 'recordatorios'):
                print("[INFO] Refrescando la lista de recordatorios.")
                self.area_central.recordatorios.cargar_recordatorios()

    def closeEvent(self, a0):
        # Desconectar usando el gestor
        db_manager.disconnect()
        super().closeEvent(a0)


