# Script es para crear la base de datos, tablas, e importar datos iniciales (ej: desde CSV). 
# Es un script que ejecutás una vez o cuando necesites recrear la base.
#db_setup.py
import os
import csv
import sys # Importar sys para sys.exit
import traceback
from pymysql import Error

# --- Importar nuestro gestor de base de datos ---
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..')
    )

if project_root not in sys.path:
    sys.path.insert(0, project_root) # Añade al principio para priorizar

from paniol.data.db_manager import DatabaseManager # Usamos la instancia única

db_manager = DatabaseManager(
    dotenv_file=".env.setup",
    prefix="SETUP_DB_"
)

print("[INFO] Iniciando db_setup.py con DatabaseManager...")

# 1. Conectar a MySQL sin base de datos para crearla
if not db_manager.connect(use_database=False):
    print("[ERROR] No se pudo conectar a MySQL. Abortando.")
    sys.exit(1)

with db_manager.conn.cursor() as cursor:
    cursor.execute("SELECT USER(), CURRENT_USER()")
    usuario = cursor.fetchone()
    print(f"Usuario Mysql utilizado: {usuario}")

try:
    with db_manager.conn.cursor() as cursor: # type: ignore
        print("[INFO] Creando la base de datos 'db_paniol' si no existe...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS db_paniol CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")
    db_manager.conn.commit() # type: ignore
    print("[INFO] Base de datos 'db_paniol' verificada/creada.")
finally:
    db_manager.disconnect() # Cerramos la conexión sin base de datos

# 2. Conectar a la base 'db_paniol' para crear tablas
if not db_manager.connect(): # Ahora conectamos con la configuración por defecto (con DB)
    print("[FATAL ERROR] No se pudo conectar a la base de datos 'db_paniol'. Abortando.")
    sys.exit(1)
    
# Conectar ahora sí a la base 'db_paniol'
try:
    with db_manager.conn.cursor() as cursor: # type: ignore
        print ("[INFO] Conectado a la base de datos 'db_paniol'.")
        # Crear tablas
        print("[INFO] Creando tabla 'herramientas' si no existe...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS herramientas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            codigo VARCHAR(50) NOT NULL UNIQUE,
            nombre VARCHAR(200) NOT NULL,
            cantidad_total INT NOT NULL CHECK (cantidad_total >= 0),
            cantidad_disponible INT NOT NULL CHECK (cantidad_disponible >= 0),
            fecha_inventario DATETIME NOT NULL
        );
        ''')
        print("[INFO] Tabla 'herramientas' verificada/creada.")

        print("[INFO] Creando tabla 'rotacion' si no existe...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rotacion (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(30) NOT NULL
        );
        ''')
        print("[INFO] Tabla 'rotacion' verificada/creada.")

        # Agregar índice UNIQUE para evitar nombres duplicados en rotacion
        try:
            print("[INFO] Intentando añadir índice único a 'rotacion.nombre'...")
            cursor.execute('''
            ALTER TABLE rotacion
            ADD UNIQUE (nombre);
            ''')
            print("[INFO] Índice único en 'rotacion.nombre' añadido (o ya existía).")
        except Error as e: # Captura el Error específico de PyMySQL
            # Puede fallar si ya existe el índice, ignoramos el error
            if e.args[0] == 1061: # MySQL error code for 'Duplicate key name' or 'Duplicate entry' for index
                print(f"[WARNING] El índice único en 'rotacion.nombre' ya existe. Ignorando: {e}")
            else:
                print(f"[ERROR] Error de PyMySQL al agregar índice único en rotacion.nombre: {e}")
                traceback.print_exc()
                # Decide si quieres salir o continuar si es un error grave
        except Exception as e:
            print(f"[ERROR] Error inesperado al agregar índice único en rotacion.nombre: {e}")
            traceback.print_exc()

        # Insertar rotaciones iniciales
        print("[INFO] Insertando rotaciones iniciales si no existen...")
        rotaciones_iniciales = ["Ajuste", "Carpinteria", "Electricidad", "Herreria"]
        for nombre_rotacion in rotaciones_iniciales:
            cursor.execute("""
                INSERT IGNORE INTO rotacion (nombre) VALUES (%s)
            """, (nombre_rotacion,))
        print("[INFO] Rotaciones iniciales procesadas.")

        # Crear tabla movimientos (registro de todo: préstamo o devolución)
        print("[INFO] Creando tabla 'movimientos' si no existe...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            herramienta_id INT NOT NULL,
            rotacion_id INT NOT NULL,
            tipo ENUM('prestamo', 'devolucion') NOT NULL,
            cantidad INT NOT NULL CHECK (cantidad > 0), -- Cantidad de herramientas en este movimiento
            fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (herramienta_id) REFERENCES herramientas(id) ON DELETE CASCADE,
            FOREIGN KEY (rotacion_id) REFERENCES rotacion(id) ON DELETE CASCADE
        );
        """)
        print("[INFO] Tabla 'movimientos' verificada/creada.")

        # AÑADIR ALTER TABLE PARA 'movimientos' - ESTO ES LO NUEVO
        try:
            # Primero intenta añadir la columna 'cantidad'
            cursor.execute("ALTER TABLE movimientos ADD COLUMN cantidad INT NOT NULL DEFAULT 1 AFTER tipo")
            print("[INFO] Columna 'cantidad' añadida a 'movimientos'.")
            # Luego, si se añadió, podrías añadir la restricción CHECK
            cursor.execute("ALTER TABLE movimientos ADD CONSTRAINT chk_cantidad_movimientos CHECK (cantidad > 0)")
            print("[INFO] Restricción CHECK 'cantidad > 0' añadida a 'movimientos'.")
        except Error as e:
            if "Duplicate column name 'cantidad'" in str(e):
                print("[INFO] Columna 'cantidad' ya existe en 'movimientos'.")
            elif "constraint 'chk_cantidad_movimientos' already exists" in str(e):
                print("[INFO] Restricción 'chk_cantidad_movimientos' ya existe.")
            else:
                print(f"[ERROR] Error de PyMySQL al añadir columna o restricción 'cantidad' a 'movimientos': {e}")
                traceback.print_exc()
        except Exception as e:
            print(f"[ERROR] Error inesperado al añadir columna o restricción 'cantidad' a 'movimientos': {e}")
            traceback.print_exc()
        # FIN DE LA PARTE NUEVA PARA MOVIMIENTOS

        # --- NUEVA TABLA: prestamos_activos ---
        print("[INFO] Creando tabla 'prestamos_activos' si no existe...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prestamos_activos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            herramienta_id INT NOT NULL,
            rotacion_id INT NOT NULL,
            cantidad_prestada INT NOT NULL CHECK (cantidad_prestada > 0),
            cantidad_devuelta INT NOT NULL DEFAULT 0 CHECK (cantidad_devuelta >= 0),
            fecha_prestamo DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            fecha_cierre DATETIME NULL,
            estado ENUM('activo', 'completado') NOT NULL DEFAULT 'activo',
            FOREIGN KEY (herramienta_id) REFERENCES herramientas(id) ON DELETE CASCADE,
            FOREIGN KEY (rotacion_id) REFERENCES rotacion(id) ON DELETE CASCADE,
            CHECK (cantidad_devuelta <= cantidad_prestada)
        );
        """)
        print("[INFO] Tabla 'prestamos_activos' verificada/creada.")
        
        # (Opcional) Puedes añadir ALTER TABLE para prestamos_activos si en el futuro añades más columnas
        # o haces cambios que necesiten migración en vez de solo creación.
        try:
            cursor.execute("ALTER TABLE prestamos_activos ADD COLUMN estado ENUM('activo', 'completado') NOT NULL DEFAULT 'activo' AFTER fecha_cierre")
        except Error as e:
            if "Duplicate column name 'estado'" not in str(e): print(f"[WARNING] {e}")
            else: print("[INFO] Columna 'estado' ya existe en 'prestamos_activos'.")
        
        try:
            cursor.execute("ALTER TABLE prestamos_activos ADD CONSTRAINT chk_devuelta_no_mayor CHECK (cantidad_devuelta <= cantidad_prestada)")
        except Error as e:
            if "constraint 'chk_devuelta_no_mayor' already exists" in str(e): print("[INFO] Restricción 'chk_devuelta_no_mayor' ya existe.")
            else: print(f"[WARNING] {e}")



        print("Creando tabla de novedades si no existe...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS novedades(
	            id INT auto_increment PRIMARY KEY,
	            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
	            tipo_novedad VARCHAR(100),
	            descripcion TEXT
            );
        """)

        try:
            print("[INFO] Tabla 'novedades' verificada/creada.")
        except Exception as e:
            print(f"[ERROR] Error al crear la tabla 'novedades': {e}")
        # --- FIN NUEVA TABLA ---

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recordatorios(
                id INT auto_increment PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                descripcion TEXT,
                fecha_inicio DATE,
                fecha_limite date,
                estado VARCHAR (20) DEFAULT 'pendiente'
            );
        """)
        try:
            print("[INFO] Tabla 'recordatorios' verificada/creada.")
        except Exception as e:
            print(f"[ERROR] Error al crear la tabla 'recordatorios': {e}")

        try:
            cursor.execute("ALTER TABLE recordatorios MODIFY COLUMN fecha_inicio DATETIME, MODIFY COLUMN fecha_limite DATETIME;")
            print("Se ha modificado fecha_inicio y fecha_limite ambos por DATETIME")
        except Exception as e:
            print(f"Problema al cambiar recordatorios: {e}")

        # Ruta del CSV
        ruta_csv = os.path.join("datos", "inventario_completo.csv") 

        # Importar herramientas desde el CSV
        if os.path.exists(ruta_csv):
            print(f"[INFO] Archivo CSV '{ruta_csv}' encontrado. Importando herramientas...")
            with open(ruta_csv, newline='', encoding='utf-8-sig') as archivo:
                # Usar DictReader es crucial aquí, y DictCursor para el cursor si quieres dicts.
                lector = csv.DictReader(archivo)
                
                for fila in lector:
                    codigo = fila['Código'].strip()
                    nombre = fila['Nombre'].strip()
                    cantidad = int(fila['Cantidad'].strip())
                    fecha = fila['Fecha Inventario'].strip()

                    try:
                        cursor.execute("""
                            INSERT INTO herramientas (codigo, nombre, cantidad_total, cantidad_disponible, fecha_inventario)
                            VALUES (%s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                nombre = VALUES(nombre),
                                cantidad_total = VALUES(cantidad_total),
                                cantidad_disponible = VALUES(cantidad_total),
                                fecha_inventario = VALUES(fecha_inventario)
                        """, (codigo, nombre, cantidad, cantidad, fecha))
                    except Error as e: # Captura el Error específico de PyMySQL
                        print(f"[ERROR] Error de PyMySQL con herramienta {codigo}: {e}")
                        traceback.print_exc()
                    except Exception as e:
                        print(f"[ERROR] Error inesperado con herramienta {codigo}: {e}")
                        traceback.print_exc()
            print("[INFO] CSV importado con éxito.")
        else:
            print(f"[WARNING] No se encontró el archivo '{ruta_csv}'. No se importarán herramientas desde CSV.")
    
    # Finalizar y confirmar todos los cambios
    db_manager.conn.commit() # type: ignore
    print("[INFO] OK. Base de datos y tablas configuradas con éxito.")

except Error as e:
    print(f"[FATAL ERROR] Error de PyMySQL durante la configuración: {e}")
    traceback.print_exc()
    db_manager.conn.rollback() # type: ignore # Revertir cambios en caso de error
    sys.exit(1)
finally:
    # Asegurarnos de cerrar la conexión al final
    db_manager.disconnect()