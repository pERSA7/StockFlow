# Gestión de novedades y recordatorios
import pymysql
from datetime import datetime
import traceback
from .base_repository import BaseRepository

class NotificationRepository(BaseRepository):

    def registrar_novedad_exportacion(self, tipo_exportacion):
                try:
                    with self._get_cursor() as cursor:
                        descripcion = f"Se ha exportado a Excel el reporte de '{tipo_exportacion}.'"
                        cursor.execute(
                            "INSERT INTO novedades (tipo_novedad, descripcion) VALUES (%s, %s)",
                            ("EXPORTACIÓN", descripcion)
                        )
                        self.conn.commit()
                        return True
                except Exception as e:
                    self.conn.rollback()
                    print(f"[ERROR] No se pudo registrar la novedad de exportacion: {e}")
                    return False    

    def obtener_novedades(self, limite=100):
            try:
                with self._get_cursor() as cursor:
                    cursor.execute(
                    "SELECT fecha, tipo_novedad, descripcion FROM novedades ORDER BY fecha DESC LIMIT %s",
                    (limite,)
                )
                return cursor.fetchall()
            except pymysql.MySQLError as e:
                print(f"[ERROR] Error al obtener novedades: {e}")
                return []    
            
    def registrar_novedad_personalizada(self, tipo_novedad, descripcion):
            """
            Registra una novedad manual o personalizada en la base de datos.
            """
            if not descripcion:
                print("[ERROR] La descripción de la novedad no puede estar vacía.")
                return False, "La descripción no puede estar vacía."

            try:
                with self._get_cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO novedades (tipo_novedad, descripcion) VALUES (%s, %s)",
                        (tipo_novedad, descripcion)
                    )
                    self.conn.commit()
                    print(f"[INFO] Novedad personalizada registrada con éxito: '{descripcion}'")
                    return True, "Novedad registrada con éxito."
            except pymysql.MySQLError as e:
                self.conn.rollback()
                print(f"[ERROR] Error de PyMySQL al registrar novedad personalizada: {e}")
                traceback.print_exc()
                return False, f"Error de base de datos: {e}"
            except Exception as e:
                self.conn.rollback()
                print(f"[FATAL ERROR] Error inesperado al registrar novedad: {e}")
                traceback.print_exc()
                return False, f"Error inesperado: {e}"    
            
    def obtener_recordatorios(self, estado='pendiente'):
            query = """
                SELECT id, titulo, descripcion, fecha_inicio, fecha_limite
                FROM recordatorios
                WHERE  estado = %s
                ORDER BY fecha_limite ASC
            """
            try:
                with self._get_cursor() as cursor:
                    cursor.execute(query, (estado,))
                    return cursor.fetchall()
            except pymysql.MySQLError as e:
                print(f"ERROR de PyMySQL al obtener recordatorios: {e}")
                traceback.print_exc()
                return []    
            
    def registrar_recordatorio(self, titulo, descripcion, fecha_inicio, fecha_limite):
            if not titulo or not fecha_inicio or not fecha_limite:
                print("[ERROR] Titulo, Fecha Inicio y Fecha Limite son obligatorios")
                return False, "Título, Fecha Inicio y Fecha Límite son obligatorios."    
            
            try:
                with self._get_cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO recordatorios (titulo, descripcion, fecha_inicio, fecha_limite) VALUES (%s, %s, %s, %s)",
                        (titulo, descripcion, fecha_inicio, fecha_limite)
                    )
                    self.conn.commit()
                    print("[INFO] Recordatorio registrado con éxito.")
                    return True, "Recordatorio registrado."
            except pymysql.MySQLError as e:
                self.conn.rollback() # type: ignore
                print(f"[ERROR] Error de PyMySQL al registrar recordatorio: {e}")
                traceback.print_exc()
                return False, f"Error de base de datos: {e}"
            
    def verificar_recordatorios_vencidos(self):
            # Busca recordatorios 'pendientes' cuya 'fecha_limite' ya haya pasado.
            ahora = datetime.now()
            recordatorios_vencidos = []
            try:
                with self._get_cursor() as cursor:
                    cursor.execute(
                        "SELECT id, titulo FROM recordatorios WHERE fecha_limite <= %s AND estado = 'pendiente'",
                        (ahora,)
                    )
                    recordatorios_vencidos = cursor.fetchall()

                    if not recordatorios_vencidos:
                        return []
                    
                    ids_vencidos = [r['id'] for r in recordatorios_vencidos]

                    format_strings = ','.join(['%s'] * len(ids_vencidos))
                    cursor.execute(
                        f"UPDATE recordatorios SET estado = 'completado' WHERE id IN ({format_strings})",
                        tuple(ids_vencidos)
                    )
                    self.conn.commit()
                    print(f"[INFO] {len(recordatorios_vencidos)} recordatorios marcados como 'completados'.")
                    return recordatorios_vencidos
                
            except pymysql.MySQLError as e:
                self.conn.rollback()
                print(f"[ERROR] Error de PyMySQL al verificar recordatorios vencidos: {e}")
                traceback.print_exc()
                return[]    