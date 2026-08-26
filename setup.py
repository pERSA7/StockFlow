import sys
from cx_Freeze import setup, Executable

# Configuración de tu aplicación
build_exe_options = {
    "packages": ["os", "PyQt6", "pymysql", "dotenv", "paniol"],
    "include_files": [
        ("paniol/assets", "assets"),
        (".env", ".env")  # Archivo de configuración de base de datos requerido
    ]
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"  # evita que se abra consola en apps con interfaz gráfica

setup(
    name="StockFlow",
    version="1.0",
    description="Sistema de Inventario Pañol",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "run.py",            # Tu script principal
            base=base,
            target_name="StockFlow.exe", # Nombre del archivo de salida
            icon="paniol/assets/STOCKFLOW_LOGO.ico" # Opcional, si tienes un ícono .ico
        )
    ]
)
