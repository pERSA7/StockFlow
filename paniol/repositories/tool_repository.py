# Gestión de herramientas (inventario, altas, bajas, stock)
import os
import pymysql 
import traceback
from .base_repository import BaseRepository

class ToolRepository(BaseRepository):

    def obtener_herramientas(self):
            """
            Obtiene la lista completa de herramientas.
            Método de la clase y usa la conexión interna.
            """
            herramientas = []
            try:
                # Usamos 'with' para que el cursor se cierre solo
                with self._get_cursor() as cursor:
                    cursor.execute("""
                        SELECT id, codigo, nombre, cantidad_total, cantidad_disponible, fecha_inventario
                        FROM herramientas
                        ORDER BY nombre
                    """)
                    herramientas = cursor.fetchall()
                print(f"[DEBUG] Se encontraron {len(herramientas)} herramientas.")
            except pymysql.MySQLError as e:
                print(f"[ERROR] Error de PyMySQL en obtener_herramientas: {e}")
            
            return herramientas

    def reponer_stock_inventario (self, herramienta_id, cantidad_a_reponer):
                if cantidad_a_reponer <= 0:
                    return False, "La cantidad a reponer debe ser mayor que 0."
                
                try:
                    with self._get_cursor() as cursor:
                        cursor.execute("SELECT nombre FROM herramientas WHERE id = %s FOR UPDATE", (herramienta_id,))
                        herramienta = cursor.fetchone()
                        
                        if not herramienta:
                            return False, "Herramienta no encontrada"
                        
                        cursor.execute("""
                            UPDATE herramientas 
                            SET cantidad_total = cantidad_total + %s, 
                                cantidad_disponible = cantidad_disponible + %s 
                            WHERE id = %s
                        """, (cantidad_a_reponer, cantidad_a_reponer, herramienta_id))
        
                        nombre_herramienta = herramienta['nombre']
                        descripcion_novedad = f"Se repuso el stock de '{nombre_herramienta}' con {cantidad_a_reponer} unidades."
                        cursor.execute(
                            "INSERT INTO novedades (tipo_novedad, descripcion) VALUES (%s, %s)",
                            ("REPOSICIÓN", descripcion_novedad)
                        )
        
                        
                        self.conn.commit() # type: ignore
                        return True, f"Stock repuesto con éxito. Se añadieron {cantidad_a_reponer} unidades."
        
                except pymysql.MySQLError as e:
                    self.conn.rollback()  # type: ignore
                    print(f"[ERROR] Error de PyMySQL al reponer stock: {e}")
                    traceback.print_exc()
                    return False, f"Error de base de datos: {e}"
                
        

    def buscar_herramienta_por_nombre(self,nombre_parcial):
                try:
                    with self._get_cursor() as cursor:
                        cursor.execute("SELECT nombre, cantidad_disponible FROM herramientas WHERE nombre LIKE %s", (f"%{nombre_parcial}%",))
                        return cursor.fetchall()
                except pymysql.MySQLError as e:
                    print(f"[ERROR] Error de PyMySQL al buscar herramienta por nombre: {e}")
                    return []
        


    def agregar_herramienta(self, nombre, cantidad):
                if not nombre or cantidad <= 0:
                    print("[ERROR] Nombre de herramienta y cantidad deben ser proporcionados.")
                    return False, "Datos invalidos."
                
                try:
                    with self._get_cursor() as cursor:
                        prefijo_codigo = nombre[:3].upper()
                        cursor.execute(
                            "SELECT codigo FROM herramientas WHERE codigo LIKE %s ORDER BY codigo DESC LIMIT 1",
                            (f"{prefijo_codigo}%",)
                        )
                        ultimo_codigo_info = cursor.fetchone()

                        nuevo_numero = 1
                        if ultimo_codigo_info:
                            try:
                                ultimo_numero = int(ultimo_codigo_info['codigo'][3:])
                                nuevo_numero = ultimo_numero + 1
                            except (IndexError, ValueError):
                                nuevo_numero = 1
                        
                        nuevo_codigo = f"{prefijo_codigo}{nuevo_numero:03d}"

                        cursor.execute("""
                            INSERT INTO herramientas (nombre, codigo, cantidad_total, cantidad_disponible, fecha_inventario)
                            VALUES (%s, %s, %s, %s, NOW())
                        """, (nombre, nuevo_codigo, cantidad, cantidad))

                        descripcion_novedad = f"Se ha agregado '{nombre}' ({nuevo_codigo}) con {cantidad} unidades"
                        cursor.execute(
                            "INSERT INTO novedades (tipo_novedad, descripcion) VALUES (%s, %s)",
                        ("ALTA", descripcion_novedad)
                        )

                        self.conn.commit() # type: ignore # Confirmar la transacción
                        print(f"[INFO] Herramienta '{nombre}' agregada con éxito con el código '{nuevo_codigo}'.")
                        return True, "Herramienta agregada con éxito."
                    
                        
                    
                except pymysql.MySQLError as e:
                    self.conn.rollback()  # type: ignore # Revertir cambios si hay un error
                    print(f"[ERROR] Error de PyMySQL al agregar herramienta: {e}")
                    traceback.print_exc()
                    return False, f"Error de base de datos: {e}"
                except Exception as e:
                    self.conn.rollback()  # type: ignore
                    print(f"[FATAL ERROR] Error inesperado al agregar herramienta: {e}")
                    traceback.print_exc()
                    return False, f"Error inesperado: {e}"


    def dar_de_baja_herramienta (self, herramienta_id, cantidad_a_bajar):
                if cantidad_a_bajar <= 0:
                    return False, "Cantidad a bajar debe ser mayor que 0."
                
                try:
                    with self._get_cursor() as cursor:
                        cursor.execute("SELECT nombre, cantidad_total, cantidad_disponible FROM herramientas WHERE id = %s FOR UPDATE", (herramienta_id,))
                        herramienta = cursor.fetchone()

                        if not herramienta:
                            return False, "Herramienta no encontrada."
                        
                        if cantidad_a_bajar > herramienta['cantidad_total']:
                            return False, "Cantidad a bajar excede la cantidad total."
                        
                        nueva_cantidad_total = herramienta['cantidad_total'] - cantidad_a_bajar
                        nueva_cantidad_disponible = herramienta['cantidad_disponible'] - cantidad_a_bajar

                        if nueva_cantidad_total < 0: nueva_cantidad_total = 0
                        if nueva_cantidad_disponible < 0: nueva_cantidad_disponible = 0

                        cursor.execute ("""
                            UPDATE herramientas SET cantidad_total = %s, cantidad_disponible = %s 
                            WHERE id = %s
                        """, (nueva_cantidad_total, nueva_cantidad_disponible, herramienta_id)
                        )

                        nombre_herramienta = herramienta['nombre']
                        descripcion_novedad = f"Se han dado de baja {cantidad_a_bajar} unidades de '{nombre_herramienta}'."
                        cursor.execute (
                            "INSERT INTO novedades (tipo_novedad, descripcion) VALUES (%s, %s)",
                            ("BAJA", descripcion_novedad)
                        )
                        self.conn.commit()
                        return True, "Herramienta dada de baja con éxito."
                except pymysql.MySQLError as e:
                    self.conn.rollback()
                    print(f"[ERROR] Error al dar de baja herramienta: {e}")


    def eliminar_herramienta(self, herramienta_id):
            try:
                with self._get_cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) as cuenta FROM prestamos_activos WHERE herramienta_id = %s AND estado = 'activo'", (herramienta_id,))
                    resultado = cursor.fetchone()
                    if resultado and resultado['cuenta'] > 0:
                        return False, "La herramienta tiene prestamos activos y no puede ser eliminada."
                    
                    cursor.execute("SELECT nombre FROM herramientas WHERE id = %s", (herramienta_id,))
                    herramienta = cursor.fetchone()

                    if not herramienta:
                        return False, "La herramienta que intentas eliminar no existe."
                    
                    nombre_herramienta = herramienta['nombre']

                    cursor.execute("DELETE FROM herramientas WHERE id = %s", (herramienta_id,))

                    descripcion_novedad = f"La herramienta '{nombre_herramienta}' ha sido ELIMINADA con exito del inventario."
                    cursor.execute(
                        "INSERT INTO novedades (tipo_novedad, descripcion) VALUES (%s, %s)",
                        ("ELIMINACIÓN", descripcion_novedad)
                    )

                    self.conn.commit()
                    return True, "Herramienta eliminada con éxito."
                
            except Exception as e:
                self.conn.rollback()
                print(f"[ERROR] Error al eliminar herramienta: {e}")
                return False, "Ocurrio un error en la base de datos"


