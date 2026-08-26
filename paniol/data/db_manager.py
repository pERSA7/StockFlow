#db_manager.py
import os
import sys
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv


class DatabaseManager:
    def __init__(self, dotenv_file=".env", prefix="DB_"):
        """
        Carga la configuración de la BD desde un archivo .env.
        Permite utilizar diferentes archivos y variables de entorno
        según el contexto (aplicación o setup).
        """

        if getattr(sys, 'frozen', False):
            dotenv_path = os.path.join(os.path.dirname(sys.executable), dotenv_file)
            
        else:
            dotenv_path = os.path.join(
                os.path.dirname(__file__),
                '..',
                '..',
                dotenv_file
            )

        load_dotenv(dotenv_path)

        required_vars = [
            f"{prefix}HOST",
            f"{prefix}USER",
            f"{prefix}PASSWORD",
            f"{prefix}NAME"
        ]

        missing_vars = [
            var for var in required_vars
            if not os.getenv(var)
        ]

        if missing_vars:
            raise RuntimeError(
                "Faltan variables de configuración de la BD: "
                + ", ".join(missing_vars)
        )

        self.db_config = {
            "host": os.getenv(f"{prefix}HOST"),
            "user": os.getenv(f"{prefix}USER"),
            "password": os.getenv(f"{prefix}PASSWORD"),
            "database": os.getenv(f"{prefix}NAME"),
            "port": int(os.getenv(f"{prefix}PORT", 3306)),
            "cursorclass": DictCursor  # ¡Configuramos el cursor por defecto aquí!
        }
        self.conn = None
        print(
            "[INFO] DatabaseManager inicializado. Listo para conectar."
            f"para el usuario '{self.db_config['user']}'."
            )

    # El gestor es capaz tanto de conectarse al servidor en general como a una base de datos específica.
    def connect(self, use_database=True):
        """Establece la conexión a la base de datos."""
        try:
            # Hacemos una copia para no modificar la configuración original de la instancia
            config = self.db_config.copy()
            if not use_database:
                config.pop("database", None) # <-- Si es False, quitamos el nombre de la BD

            if "cursorclass" not in config:
                config["cursorclass"] = DictCursor

            self.conn = pymysql.connect(**config)
            print("[INFO] Conexión a la base de datos establecida con éxito.")
            return True
        except pymysql.MySQLError as e:
            print(f"[FATAL ERROR] Falló la conexión a MySQL: {e}")
            self.conn = None
            return False

    def disconnect(self):
        """Cierra la conexión a la base de datos si está abierta."""
        if self.conn:
            self.conn.close()
            self.conn = None
            print("[INFO] Conexión a la base de datos cerrada.")

    def _get_cursor(self):
        """
        Devuelve un cursor. Si la conexión se perdió, intenta reconectar.
        Este es un método de ayuda interno.
        """
        # Verifica si la conexión está abierta y la "refresca" con ping()
        if self.conn and self.conn.open:
            try:
                # Intenta hacer un ping a la conexión. Si falla, reconectará.
                self.conn.ping(reconnect=True)
            except pymysql.MySQLError as e:
                print(f"[ERROR] Fallo en ping, intentando reconectar: {e}")
                self.connect()
        else:
            # Si no hay conexión o no está abierta, intenta conectarse.
            print("[WARN] La conexión no estaba activa. Intentando reconectar...")
            self.connect()
        
        if not self.conn or not self.conn.open:
            raise pymysql.MySQLError("No se pudo establecer una conexión con la base de datos.")
            
        return self.conn.cursor()
