import sys, os
from PyQt6.QtWidgets import QApplication
from .widgets.ventana import MainWindow  # Importa la clase MainWindow desde ventana.py
from qt_material import apply_stylesheet

# Cargar estilo desde pañol/style/estilo.qss
ruta_estilo = os.path.join(os.path.dirname(__file__), "style", "estilo.qss")

def main():
    app = QApplication(sys.argv)

    # Cargar estilo desde archivo QSS (ruta relativa segura)
    if os.path.exists(ruta_estilo):
        with open(ruta_estilo, "r") as estilo:
            app.setStyleSheet(estilo.read())
    else:
        print("Archivo 'estilo.qss' no encontrado.")
    #apply_stylesheet(app, theme="light_cyan.xml")
    

    #VENTANA PRINCIPAL
    try:
        window = MainWindow()
        window.show()
    except Exception as e:
        print(f"[FATAL ERROR] Ocurrió un error al crear o mostrar la MainWindow: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) # Salir si MainWindow falla

    # Inicia el bucle de eventos de la aplicación PyQt
    exit_code = app.exec()
    print(f"[INFO] Aplicación PyQt terminada con código: {exit_code}") # Este se mostrará al cerrar la ventana
    sys.exit(exit_code)
