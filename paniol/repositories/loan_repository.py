# Gestión de préstamos activos, devoluciones e historial de movimientos
import pymysql
import traceback
from datetime import datetime
from .base_repository import BaseRepository

class LoanRepository(BaseRepository):

    def obtener_rotaciones(self):
        """Obtiene la lista completa de rotaciones."""
        rotaciones = []
        try:
            with self._get_cursor() as cursor:
                cursor.execute("SELECT id, nombre FROM rotacion ORDER BY nombre")
                rotaciones = cursor.fetchall()
            print(f"[DEBUG] Se encontraron {len(rotaciones)} rotaciones.")
        except pymysql.MySQLError as e:
            print(f"[ERROR] Error de PyMySQL en obtener_rotaciones: {e}")
        return rotaciones

    def obtener_movimientos(self, rotacion_id=None, tipo=None, desde_fecha=None, hasta_fecha=None):
            """
            Obtiene una lista de TODOS los movimientos (préstamos/devoluciones) con opciones de filtro.
            """
            query = """
                SELECT 
                    m.id AS movimiento_id,
                    h.codigo,
                    h.nombre AS nombre_herramienta,
                    r.nombre AS nombre_rotacion,
                    m.tipo,
                    m.cantidad,
                    m.fecha
                FROM movimientos m
                JOIN herramientas h ON m.herramienta_id = h.id
                JOIN rotacion r ON m.rotacion_id = r.id
                WHERE 1=1
            """
            params = []

            if rotacion_id:
                query += " AND m.rotacion_id = %s"
                params.append(rotacion_id)
            if tipo:
                query += " AND m.tipo = %s"
                params.append(tipo)
            if desde_fecha:
                query += " AND m.fecha >= %s"
                params.append(desde_fecha)
            if hasta_fecha:
                query += " AND m.fecha <= %s"
                params.append(hasta_fecha)
            
            query += " ORDER BY m.fecha DESC"

            movimientos = []
            try:
                with self._get_cursor() as cursor:
                    cursor.execute(query, params)
                    movimientos = cursor.fetchall()
                print(f"[DEBUG] Se encontraron {len(movimientos)} movimientos de historial.")
            except pymysql.MySQLError as e:
                print(f"[ERROR] Error de PyMySQL en obtener_movimientos (historial): {e}")
                traceback.print_exc()
            return movimientos
        
        #********************** PRESTAMOS ACTIVOS **************************
    def obtener_prestamos_activos(self, rotacion_id=None):
            """
            Obtiene la lista de préstamos que actualmente tienen unidades pendientes de devolución.
            """
            query = """
                SELECT 
                    pa.id AS prestamo_id,
                    h.id AS herramienta_id,
                    h.codigo,
                    h.nombre AS nombre_herramienta,
                    r.id AS rotacion_id,
                    r.nombre AS nombre_rotacion,
                    pa.cantidad_prestada,
                    pa.cantidad_devuelta,
                    (pa.cantidad_prestada - pa.cantidad_devuelta) AS cantidad_pendiente,
                    pa.fecha_prestamo
                FROM prestamos_activos pa
                JOIN herramientas h ON pa.herramienta_id = h.id
                JOIN rotacion r ON pa.rotacion_id = r.id
                WHERE pa.estado = 'activo' AND (pa.cantidad_prestada - pa.cantidad_devuelta) > 0
            """
            params = []

            if rotacion_id:
                query += " AND pa.rotacion_id = %s"
                params.append(rotacion_id)
            
            query += " ORDER BY pa.fecha_prestamo ASC"

            prestamos = []
            try:
                with self._get_cursor() as cursor:
                    cursor.execute(query, params)
                    prestamos = cursor.fetchall()
                print(f"[DEBUG] Se encontraron {len(prestamos)} préstamos activos.")
            except pymysql.MySQLError as e:
                print(f"[ERROR] Error de PyMySQL en obtener_prestamos_activos: {e}")
                traceback.print_exc()
            return prestamos

        # --- Lógica principal para registrar PRÉSTAMOS y DEVOLUCIONES ---
    def registrar_prestamo(self, herramienta_id, rotacion_id, cantidad):
            """
            Registra un préstamo. Decrementa cantidad_disponible, registra en movimientos
            e inserta un nuevo registro en prestamos_activos.
            """
            if cantidad <= 0:
                print("[ERROR] La cantidad para un préstamo debe ser mayor que 0.")
                return False

            try:
                with self._get_cursor() as cursor:
                    # 1. Obtener la cantidad disponible actual (para bloqueo)
                    cursor.execute("SELECT cantidad_disponible FROM herramientas WHERE id = %s FOR UPDATE", (herramienta_id,))
                    resultado = cursor.fetchone()
                    if not resultado:
                        print(f"[ERROR] Herramienta con ID {herramienta_id} no encontrada.")
                        return False
                    
                    cantidad_disponible_actual = resultado['cantidad_disponible'] # type: ignore

                    if cantidad_disponible_actual < cantidad:
                        print(f"[ERROR] Intento de préstamo de {cantidad} de herramienta {herramienta_id} excede la disponibilidad ({cantidad_disponible_actual}).")
                        return False
                    
                    nueva_cantidad_disponible = cantidad_disponible_actual - cantidad

                    # 2. Actualizar la cantidad_disponible en la tabla herramientas
                    cursor.execute(
                        "UPDATE herramientas SET cantidad_disponible = %s WHERE id = %s",
                        (nueva_cantidad_disponible, herramienta_id)
                    )

                    # 3. Registrar el movimiento en la tabla 'movimientos' (historial)
                    cursor.execute(
                        "INSERT INTO movimientos (herramienta_id, rotacion_id, tipo, cantidad) VALUES (%s, %s, %s, %s)",
                        (herramienta_id, rotacion_id, 'prestamo', cantidad)
                    )

                    # 4. Insertar un nuevo registro en 'prestamos_activos'
                    cursor.execute(
                        "INSERT INTO prestamos_activos (herramienta_id, rotacion_id, cantidad_prestada) VALUES (%s, %s, %s)",
                        (herramienta_id, rotacion_id, cantidad)
                    )
                    
                    self.conn.commit() # type: ignore
                    print(f"[INFO] Préstamo de {cantidad} unidades para herramienta {herramienta_id} registrado con éxito. Nueva disponible: {nueva_cantidad_disponible}")
                    return True

            except pymysql.MySQLError as e:
                self.conn.rollback() # type: ignore
                print(f"[ERROR] Error de PyMySQL al registrar préstamo: {e}")
                traceback.print_exc()
                return False
            except Exception as e:
                self.conn.rollback() # type: ignore
                print(f"[FATAL ERROR] Error inesperado al registrar préstamo: {e}")
                traceback.print_exc()
                return False    

    def registrar_devolucion(self, prestamo_id, cantidad_a_devolver):
            """
            Registra una devolución para un préstamo activo existente.
            Actualiza cantidad_disponible en herramientas, registra en movimientos
            y actualiza el registro en prestamos_activos.
            """
            if cantidad_a_devolver <= 0:
                print("[ERROR] La cantidad a devolver debe ser mayor que 0.")
                return False

            try:
                with self._get_cursor() as cursor:
                    # 1. Obtener detalles del préstamo activo (para bloqueo y validación)
                    cursor.execute("""
                        SELECT pa.herramienta_id, pa.rotacion_id, pa.cantidad_prestada, pa.cantidad_devuelta, h.cantidad_total, h.cantidad_disponible
                        FROM prestamos_activos pa
                        JOIN herramientas h ON pa.herramienta_id = h.id
                        WHERE pa.id = %s FOR UPDATE
                    """, (prestamo_id,))
                    prestamo_activo_info = cursor.fetchone()

                    if not prestamo_activo_info:
                        print(f"[ERROR] Préstamo activo con ID {prestamo_id} no encontrado.")
                        return False
                    
                    herramienta_id = prestamo_activo_info['herramienta_id'] # type: ignore
                    rotacion_id = prestamo_activo_info['rotacion_id'] # type: ignore
                    cantidad_prestada = prestamo_activo_info['cantidad_prestada'] # type: ignore
                    cantidad_devuelta_actual = prestamo_activo_info['cantidad_devuelta'] # type: ignore
                    cantidad_total_inventario = prestamo_activo_info['cantidad_total'] # type: ignore
                    cantidad_disponible_actual = prestamo_activo_info['cantidad_disponible'] # type: ignore

                    cantidad_pendiente = cantidad_prestada - cantidad_devuelta_actual

                    if cantidad_a_devolver > cantidad_pendiente:
                        print(f"[ERROR] Intento de devolver {cantidad_a_devolver} unidades, pero solo quedan {cantidad_pendiente} pendientes para el préstamo ID {prestamo_id}.")
                        return False
                    
                    nueva_cantidad_devuelta = cantidad_devuelta_actual + cantidad_a_devolver
                    nueva_cantidad_disponible = cantidad_disponible_actual + cantidad_a_devolver

                    # No permitimos que la cantidad disponible supere la cantidad total del inventario
                    if nueva_cantidad_disponible > cantidad_total_inventario:
                        print(f"[ERROR] La devolución de {cantidad_a_devolver} unidades excedería la cantidad total en inventario para la herramienta {herramienta_id}.")
                        return False

                    # 2. Actualizar la cantidad_disponible en la tabla herramientas
                    cursor.execute(
                        "UPDATE herramientas SET cantidad_disponible = %s WHERE id = %s",
                        (nueva_cantidad_disponible, herramienta_id)
                    )

                    # 3. Registrar el movimiento en la tabla 'movimientos' (historial)
                    cursor.execute(
                        "INSERT INTO movimientos (herramienta_id, rotacion_id, tipo, cantidad) VALUES (%s, %s, %s, %s)",
                        (herramienta_id, rotacion_id, 'devolucion', cantidad_a_devolver)
                    )

                    # 4. Actualizar el registro en 'prestamos_activos'
                    estado_nuevo = 'activo'
                    fecha_cierre = None
                    if nueva_cantidad_devuelta == cantidad_prestada:
                        estado_nuevo = 'completado'
                        fecha_cierre = datetime.now() # O usar CURRENT_TIMESTAMP en SQL

                    cursor.execute(
                        "UPDATE prestamos_activos SET cantidad_devuelta = %s, estado = %s, fecha_cierre = %s WHERE id = %s",
                        (nueva_cantidad_devuelta, estado_nuevo, fecha_cierre, prestamo_id)
                    )
                    
                    self.conn.commit() # type: ignore
                    print(f"[INFO] Devolución de {cantidad_a_devolver} unidades para préstamo ID {prestamo_id} registrada con éxito. Nueva disponible: {nueva_cantidad_disponible}. Estado del préstamo: {estado_nuevo}")
                    return True

            except pymysql.MySQLError as e:
                self.conn.rollback() # type: ignore
                print(f"[ERROR] Error de PyMySQL al registrar devolución: {e}")
                traceback.print_exc()
                return False
            except Exception as e:
                self.conn.rollback() # type: ignore
                print(f"[FATAL ERROR] Error inesperado al registrar devolución: {e}")
                traceback.print_exc()
                return False    
        
    def registrar_movimiento_herramienta(self, herramienta_id, rotacion_id, tipo_movimiento, cantidad):
            """
            Registra un movimiento (préstamo o devolución) de una herramienta
            y actualiza la cantidad_disponible.
            Args:
                herramienta_id (int): ID de la herramienta.
                rotacion_id (int): ID de la rotación (área/departamento).
                tipo_movimiento (str): 'prestamo' o 'devolucion'.
                cantidad (int): Cantidad de herramientas afectadas por el movimiento.
            Returns:
                bool: True si la operación fue exitosa, False en caso contrario.
            """
            try:
                with self._get_cursor() as cursor:
                    # 1. Obtener la cantidad disponible actual 
                    # (FOR UPDATE) bloquea la fila mientras se actualiza
                    cursor.execute("SELECT cantidad_disponible, cantidad_total FROM herramientas WHERE id = %s FOR UPDATE", (herramienta_id,))
                    resultado = cursor.fetchone()
                    if not resultado:
                        print(f"[ERROR] Herramienta con ID {herramienta_id} no encontrada.")
                        return False
                    
                    cantidad_disponible_actual = resultado['cantidad_disponible'] # type: ignore
                    cantidad_total_inventario = resultado['cantidad_total'] # type: ignore
                    nueva_cantidad_disponible = cantidad_disponible_actual

                    if tipo_movimiento == 'prestamo':
                        if cantidad_disponible_actual < cantidad:
                            print(f"[ERROR] Intento de préstamo de {cantidad} de herramienta {herramienta_id} excede la disponibilidad ({cantidad_disponible_actual}).")
                            return False
                        nueva_cantidad_disponible -= cantidad
                    elif tipo_movimiento == 'devolucion':
                        # Para devoluciones, la cantidad disponible puede exceder la total si se devuelve más de lo prestado
                        # o si la cantidad_total original no fue precisa.
                        # Aquí simplemente la aumentamos. Podrías añadir lógica para no exceder cantidad_total
                        # si lo consideras necesario para tu modelo de negocio.
                        # Por ejemplo: if nueva_cantidad_disponible + cantidad > cantidad_total: ...
                        # Una devolución no puede hacer que la disponible sea mayor que la total del pañol
                        if (cantidad_disponible_actual + cantidad) > cantidad_total_inventario:
                            print(f"[ERROR] Intento de devolución de {cantidad} de herramienta {herramienta_id} excede la capacidad total ({cantidad_total_inventario}). Disponible actual: {cantidad_disponible_actual}.")
                            return False
                        nueva_cantidad_disponible += cantidad
                    else:
                        print(f"[ERROR] Tipo de movimiento desconocido: {tipo_movimiento}")
                        return False

                    # 2. Actualizar la cantidad_disponible en la tabla herramientas
                    cursor.execute(
                        "UPDATE herramientas SET cantidad_disponible = %s WHERE id = %s",
                        (nueva_cantidad_disponible, herramienta_id)
                    )

                    # 3. Registrar el movimiento en la tabla 'movimientos'
                    cursor.execute(
                        "INSERT INTO movimientos (herramienta_id, rotacion_id, tipo, cantidad) VALUES (%s, %s, %s, %s)",
                        (herramienta_id, rotacion_id, tipo_movimiento, cantidad)
                    )
                    
                    self.conn.commit() # type: ignore # Confirmar la transacción
                    print(f"[INFO] Movimiento '{tipo_movimiento}' de {cantidad} unidades para herramienta {herramienta_id} registrado con éxito. Nueva disponible: {nueva_cantidad_disponible}")
                    return True

            except pymysql.MySQLError as e:
                self.conn.rollback() # type: ignore # Revertir cambios si hay un error
                print(f"[ERROR] Error de PyMySQL al registrar movimiento o actualizar herramienta: {e}")
                traceback.print_exc()
                return False
            except Exception as e:
                self.conn.rollback() # type: ignore # Revertir cambios si hay un error
                print(f"[FATAL ERROR] Error inesperado al registrar movimiento: {e}")
                traceback.print_exc()
                return False    

        
    def obtener_prestamos_completados(self, rotacion_id=None):
            """
            Obtiene solo los préstamos cuyo estado es 'completado', 
            con un filtro opcional por rotación.
            Busca en la tabla 'prestamos_activos'.
            """
            query = """
                SELECT 
                    pa.id AS prestamo_id,
                    h.codigo,
                    h.nombre AS nombre_herramienta,
                    r.nombre AS nombre_rotacion,
                    pa.cantidad_prestada,
                    pa.fecha_prestamo,
                    pa.fecha_cierre
                FROM prestamos_activos pa
                JOIN herramientas h ON pa.herramienta_id = h.id
                JOIN rotacion r ON pa.rotacion_id = r.id
                WHERE pa.estado = 'completado'
            """
            params = []

            # Si se proporciona un ID de rotación, se añade al filtro
            if rotacion_id:
                query += " AND pa.rotacion_id = %s"
                params.append(rotacion_id)
            
            query += " ORDER BY pa.fecha_cierre DESC"

            historial = []
            try:
                with self._get_cursor() as cursor:
                    cursor.execute(query, tuple(params))
                    historial = cursor.fetchall()
                print(f"[DEBUG] Se encontraron {len(historial)} préstamos completados en el historial.")
            except pymysql.MySQLError as e:
                print(f"[ERROR] Error de PyMySQL en obtener_prestamos_completados: {e}")
                traceback.print_exc()
            return historial    
    
