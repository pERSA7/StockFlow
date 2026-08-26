from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QTableWidget, QDateTimeEdit,
    QPushButton, QHBoxLayout, QComboBox, QListWidget, QListWidgetItem,
    QTableWidgetItem, QSpinBox, QMessageBox, QWidget, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal # Importa pyqtSignal
import datetime
import traceback # Importar traceback para depuración

from ..app.core import db_manager
from ..repositories.tool_repository import ToolRepository
from ..repositories.loan_repository import LoanRepository
#from .dialogo_animado import AnimatedDialog

class RegistrarPrestamo(QDialog):
    # Señal para notificar a la ventana principal que se ha registrado un préstamo
    prestamo_registrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Nuevo Préstamo")
        self.setMinimumSize(500, 650) # Un tamaño inicial razonable

        layout_principal = QVBoxLayout(self)
        self.setLayout(layout_principal)

        self.db_manager = db_manager # Usamos la instancia compartida
        self.tool_repo = ToolRepository(db_manager)
        self.loan_repo = LoanRepository(db_manager)

        # Formato de cada elemento en herramientas_a_prestar:
        # { 'id': int, 'codigo': str, 'nombre': str, 'cantidad_disponible_inicial_dialogo': int, 
        # 'cantidad_total_inventario': int, 'cantidad_seleccionada': int }
        self.herramientas_disponibles_cache = {} # Cache para búsqueda rápida de herramientas
        
        # Inicializar herramientas a prestar
        self.herramientas_a_prestar = [] # Lista para almacenar diccionarios de herramientas seleccionadas
        # Formato de cada elemento en herramientas_a_prestar:
        # { 'id': int, 'codigo': str, 'nombre': str, 'cantidad_disponible_original': int, 'cantidad_seleccionada': int }

        # Nombre de la ROTACION
        rotacion_layout = QHBoxLayout()
        rotacion_label = QLabel("Rotacion:")
        self.rotacion_combo = QComboBox()
        self.cargar_rotaciones()

        rotacion_layout.addWidget(rotacion_label)
        rotacion_layout.addWidget(self.rotacion_combo)
        layout_principal.addLayout(rotacion_layout)

        # Etiqueta para BUSCAR HERRAMIENTAS
        buscar_layout = QHBoxLayout()
        buscar_label = QLabel("Buscar Herramienta:")
        self.buscar_line_edit = QLineEdit()
        self.buscar_line_edit.setPlaceholderText("Filtrar por código o nombre...")
        self.buscar_line_edit.textChanged.connect(self.filtrar_lista_herramientas)
        self.buscar_line_edit.returnPressed.connect(self.agregar_herramienta_por_scan)

        buscar_layout.addWidget(buscar_label)
        buscar_layout.addWidget(self.buscar_line_edit)
        layout_principal.addLayout(buscar_layout)

        # Lista de herramientas del inventario (para seleccionar)
        herramientas_label = QLabel("Herramientas Disponibles:")
        self.lista_herramientas = QListWidget(self)
        self.lista_herramientas.itemDoubleClicked.connect(self.seleccionar_herramienta_desde_lista) # Doble click para agregar
        layout_principal.addWidget(herramientas_label)
        layout_principal.addWidget(self.lista_herramientas)
        self.cargar_lista_herramientas() # Cargar las herramientas al inicio

        # Controles para añadir la cantidad al préstamo
        cantidad_seleccion_layout = QHBoxLayout()
        self.cantidad_spinbox = QSpinBox()
        self.cantidad_spinbox.setMinimum(1)
        self.cantidad_spinbox.setMaximum(9999) # Un valor máximo alto
        self.cantidad_spinbox.setValue(1) # Valor por defecto

        self.agregar_al_prestamo_btn = QPushButton("Agregar Seleccionados")
        self.agregar_al_prestamo_btn.clicked.connect(self.agregar_herramientas_al_prestamo)
        self.agregar_al_prestamo_btn.setAutoDefault(False)

        cantidad_seleccion_layout.addWidget(QLabel("Cantidad a prestar:"))
        cantidad_seleccion_layout.addWidget(self.cantidad_spinbox)
        cantidad_seleccion_layout.addWidget(self.agregar_al_prestamo_btn)
        layout_principal.addLayout(cantidad_seleccion_layout)

        # Herramientas a Prestar (Tabla)
        self.h_prestamo_label = QLabel("Herramientas a Prestar:")
        self.herramientas_tabla = QTableWidget(0, 4) # ID, Código, Nombre, Cantidad
        self.herramientas_tabla.setHorizontalHeaderLabels(["ID (oculto)", "Código", "Nombre", "Cantidad"])
        self.herramientas_tabla.setColumnHidden(0, True) # Ocultar columna de ID
        self.herramientas_tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows) # Seleccionar filas completas
        header = self.herramientas_tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.herramientas_tabla.verticalHeader().setVisible(False)
        layout_principal.addWidget(self.h_prestamo_label)
        layout_principal.addWidget(self.herramientas_tabla)

        # Botón para eliminar Herramientas del préstamo
        self.eliminar_elemento_btn = QPushButton("Eliminar Seleccionado del Préstamo")
        self.eliminar_elemento_btn.clicked.connect(self.eliminar_elemento_del_prestamo)
        self.eliminar_elemento_btn.setAutoDefault(False)
        layout_principal.addWidget(self.eliminar_elemento_btn)

        # Fecha y Hora del Préstamo (Solo lectura)
        fecha_layout = QHBoxLayout()
        fecha_label = QLabel("Fecha y Hora Préstamo:")
        self.fecha_prestamo = QLabel(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        fecha_layout.addWidget(fecha_label)
        fecha_layout.addWidget(self.fecha_prestamo)
        layout_principal.addLayout(fecha_layout)

        # Botón Registrar Préstamo
        self.registrar_btn = QPushButton("Registrar Préstamo")
        self.registrar_btn.clicked.connect(self.validar_y_registrar_prestamo)
        self.registrar_btn.setAutoDefault(False)
        layout_principal.addWidget(self.registrar_btn)

    def cargar_rotaciones(self):
        """Carga las rotaciones en el QComboBox."""
        self.rotacion_combo.clear()
        rotaciones = self.loan_repo.obtener_rotaciones()
        self.rotacion_combo.addItem("Seleccione una Rotación", -1) # Opción por defecto
        for r in rotaciones:
            self.rotacion_combo.addItem(r.get('nombre'), r.get('id')) # type: ignore

    def cargar_lista_herramientas(self):
        """Carga las herramientas disponibles en el QListWidget."""
        self.lista_herramientas.clear()
        self.herramientas_disponibles_cache = {} # Limpiar la caché, almacenará el estado ORIGINAL de la DB
        herramientas = self.tool_repo.obtener_herramientas() # Obtiene todas las herramientas
        for h in herramientas:
            # Almacenar el estado ORIGINAL de la DB en el caché por ID
            # Asumimos que db_manager.obtener_herramientas() devuelve 'cantidad_total' también. 
            self.herramientas_disponibles_cache[h['id']] = { # type: ignore
                'id': h['id'], # type: ignore
                'codigo': h['codigo'], # type: ignore
                'nombre': h['nombre'], # type: ignore
                'cantidad_total': h.get('cantidad_total', 0), # Obtener cantidad_total # type: ignore
                'cantidad_disponible': h.get('cantidad_disponible', 0) # Cantidad disponible inicial de la DB # type: ignore
            }
            # Solo mostrar herramientas con cantidad_disponible > 0 (original DB)
            if h.get('cantidad_disponible', 0) > 0: # type: ignore
                # Crear una *copia* del diccionario de la herramienta para el item de la lista.
                # Es la 'cantidad_disponible' de esta copia la que se manipulará en la UI.
                tool_data_for_list_item = h.copy()  # type: ignore

                texto_a_mostrar = f"{tool_data_for_list_item['nombre']} ({tool_data_for_list_item['codigo']}) - Disp: {tool_data_for_list_item['cantidad_disponible']}"
                list_widget_item = QListWidgetItem(texto_a_mostrar)
                # Almacenamos la COPIA en UserRole para fácil acceso y modificación local
                list_widget_item.setData(Qt.ItemDataRole.UserRole, tool_data_for_list_item)
                self.lista_herramientas.addItem(list_widget_item)
                #self.herramientas_disponibles_cache[h['id']] = h # type: ignore # Guardar en caché por ID

    def filtrar_lista_herramientas(self):
        """Filtra la lista de herramientas disponibles según el texto de búsqueda."""
        texto_busqueda = self.buscar_line_edit.text().lower()
        for i in range(self.lista_herramientas.count()):
            item = self.lista_herramientas.item(i)
            herramienta_data = item.data(Qt.ItemDataRole.UserRole) # type: ignore
            if texto_busqueda in herramienta_data['nombre'].lower() or \
            texto_busqueda in herramienta_data['codigo'].lower():
                # Asegurarse de que solo se muestren si hay stock disponible también
                if herramienta_data['cantidad_disponible'] > 0:
                    item.setHidden(False) # type: ignore
                else:
                    item.setHidden(True) # type: ignore # Ocultar si no hay disponibles aunque coincida el filtro
            else:
                item.setHidden(True) # type: ignore

    def seleccionar_herramienta_desde_lista(self):
        """
        Maneja el doble clic en la lista de herramientas para pre-seleccionar.
        Establece el QSpinBox a 1 y conecta el botón de agregar.
        """
        selected_item = self.lista_herramientas.currentItem()
        if selected_item:
            herramienta_data = selected_item.data(Qt.ItemDataRole.UserRole)
            # Podrías establecer la cantidad disponible máxima en el spinbox
            self.cantidad_spinbox.setMaximum(herramienta_data['cantidad_disponible'])
            self.cantidad_spinbox.setValue(1) # Por defecto 1
            # O directamente llamar a agregar_herramientas_al_prestamo si quieres que se agregue de inmediato
            # self.agregar_herramientas_al_prestamo()


    def agregar_herramientas_al_prestamo(self):
        """
        Agrega la herramienta seleccionada de la lista a la tabla de préstamo (acción manual).
        """
        selected_item = self.lista_herramientas.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Advertencia", "Por favor, seleccione una herramienta de la lista.")
            return

        herramienta_data_in_list = selected_item.data(Qt.ItemDataRole.UserRole)
        herramienta_id = herramienta_data_in_list['id']
        cantidad_a_prestar = self.cantidad_spinbox.value()

        # Obtener el estado ORIGINAL de la herramienta del caché (desde la DB)
        original_db_tool_data = self.herramientas_disponibles_cache.get(herramienta_id)
        if not original_db_tool_data:
            QMessageBox.critical(self, "Error Interno", "No se encontró la herramienta en el caché original. Contacte soporte.")
            return

        original_db_available_qty = original_db_tool_data['cantidad_disponible']
        current_ui_available_qty = herramienta_data_in_list['cantidad_disponible']

        if cantidad_a_prestar <= 0:
            QMessageBox.warning(self, "Advertencia", "La cantidad a prestar debe ser mayor a cero.")
            return

        if cantidad_a_prestar > current_ui_available_qty:
            QMessageBox.warning(self, "Advertencia", 
                                f"No hay suficiente stock. Disponible: {herramienta_data_in_list['nombre']}. Actual: {current_ui_available_qty}, Solicitado: {cantidad_a_prestar}")
            return

        # Verificar si la herramienta ya está en la tabla de préstamo
        item_encontrado = False
        for i in range(self.herramientas_tabla.rowCount()):
            item_id_in_table = self.herramientas_tabla.item(i, 0).data(Qt.ItemDataRole.UserRole) # type: ignore
            if item_id_in_table == herramienta_id:
                current_qty_in_table = int(self.herramientas_tabla.item(i, 3).text()) # type: ignore
                new_total_qty_in_table = current_qty_in_table + cantidad_a_prestar
                
                if new_total_qty_in_table > original_db_available_qty:
                    QMessageBox.warning(self, "Advertencia", 
                                        f"La cantidad total seleccionada ({new_total_qty_in_table}) excede la cantidad disponible original ({original_db_available_qty}) para {herramienta_data_in_list['nombre']}.")
                    return
                
                self.herramientas_tabla.item(i, 3).setText(str(new_total_qty_in_table)) # type: ignore
                
                for h_loan in self.herramientas_a_prestar:
                    if h_loan['id'] == herramienta_id:
                        h_loan['cantidad_seleccionada'] = new_total_qty_in_table
                        break
                
                item_encontrado = True
                break
        
        if not item_encontrado:
            # Si no está, añadir una nueva fila
            row_position = self.herramientas_tabla.rowCount()
            self.herramientas_tabla.insertRow(row_position)
            
            id_item = QTableWidgetItem()
            id_item.setData(Qt.ItemDataRole.UserRole, herramienta_id)
            self.herramientas_tabla.setItem(row_position, 0, id_item)
            
            self.herramientas_tabla.setItem(row_position, 1, QTableWidgetItem(herramienta_data_in_list['codigo']))
            self.herramientas_tabla.setItem(row_position, 2, QTableWidgetItem(herramienta_data_in_list['nombre']))
            self.herramientas_tabla.setItem(row_position, 3, QTableWidgetItem(str(cantidad_a_prestar)))
            
            self.herramientas_a_prestar.append({
                'id': herramienta_id,
                'codigo': herramienta_data_in_list['codigo'],
                'nombre': herramienta_data_in_list['nombre'],
                'cantidad_disponible_inicial_dialogo': original_db_available_qty,
                'cantidad_total_inventario': original_db_tool_data['cantidad_total'],
                'cantidad_seleccionada': cantidad_a_prestar
            })

        # Llamada a la nueva función de recalcular disponibilidad
        self.recalcular_disponibilidad_en_lista(herramienta_id)

        self.cantidad_spinbox.setValue(1)


    def recalcular_disponibilidad_en_lista(self, herramienta_id):
        """
        Recalcula y actualiza la cantidad disponible mostrada en el QListWidget.
        Toma la cantidad original de la DB y resta la cantidad total seleccionada en la tabla.
        """
        original_db_tool_data = self.herramientas_disponibles_cache.get(herramienta_id)
        if not original_db_tool_data:
            return

        cantidad_disponible_inicial_db = original_db_tool_data['cantidad_disponible']

        # Sumar la cantidad total seleccionada para esta herramienta en la tabla
        cantidad_total_prestada = 0
        for h_loan in self.herramientas_a_prestar:
            if h_loan['id'] == herramienta_id:
                cantidad_total_prestada = h_loan['cantidad_seleccionada']
                break
                
        nueva_cantidad_disponible = cantidad_disponible_inicial_db - cantidad_total_prestada
        
        # Encontrar y actualizar el item en el QListWidget
        for i in range(self.lista_herramientas.count()):
            item = self.lista_herramientas.item(i)
            herramienta_data_in_list = item.data(Qt.ItemDataRole.UserRole) # type: ignore
            
            if herramienta_data_in_list['id'] == herramienta_id:
                herramienta_data_in_list['cantidad_disponible'] = nueva_cantidad_disponible
                item.setText(f"{herramienta_data_in_list['nombre']} ({herramienta_data_in_list['codigo']}) - Disp: {nueva_cantidad_disponible}") # type: ignore
                item.setHidden(nueva_cantidad_disponible <= 0) # type: ignore
                break


    def eliminar_elemento_del_prestamo(self):
        """
        Elimina la fila seleccionada de la tabla de préstamo y revierte la cantidad.
        """
        selected_rows = self.herramientas_tabla.selectionModel().selectedRows() # type: ignore
        if not selected_rows:
            QMessageBox.warning(self, "Advertencia", "Por favor, seleccione una fila para eliminar.")
            return

        # Usaremos un set para almacenar los IDs de las herramientas a actualizar
        ids_a_actualizar = set()

        for index in sorted(selected_rows, reverse=True):
            row = index.row()
            herramienta_id = self.herramientas_tabla.item(row, 0).data(Qt.ItemDataRole.UserRole) # type: ignore
            ids_a_actualizar.add(herramienta_id)
            
            self.herramientas_a_prestar = [h for h in self.herramientas_a_prestar if h['id'] != herramienta_id]
            
            self.herramientas_tabla.removeRow(row)
        
        # Recalcular la disponibilidad para cada herramienta que fue afectada
        for tool_id in ids_a_actualizar:
            self.recalcular_disponibilidad_en_lista(tool_id)

    def actualizar_disponibilidad_en_lista(self, herramienta_id, cantidad_cambiada, tipo_cambio):
        """
        Actualiza la cantidad disponible mostrada en el QListWidget del diálogo.
        Nota: Esto NO actualiza la base de datos, solo el estado interno de la UI.
        """
        # Obtener los datos originales de la herramienta desde el caché principal (DB original)
        original_db_tool_data = self.herramientas_disponibles_cache.get(herramienta_id)
        if not original_db_tool_data:
            print(f"[ERROR] Herramienta ID {herramienta_id} no encontrada en el caché original de herramientas disponibles.")
            return

        # Cantidad disponible de la herramienta cuando el diálogo se cargó por primera vez
        cantidad_disponible_inicial_db = original_db_tool_data['cantidad_disponible']

        for i in range(self.lista_herramientas.count()):
            item = self.lista_herramientas.item(i)
            # Esta herramienta_data_in_list es la COPIA que se modifica para el estado de la UI
            herramienta_data_in_list = item.data(Qt.ItemDataRole.UserRole) # type: ignore
            
            if herramienta_data_in_list['id'] == herramienta_id:
                if tipo_cambio == 'prestamo':
                    herramienta_data_in_list['cantidad_disponible'] -= cantidad_cambiada
                elif tipo_cambio == 'devolucion':
                    herramienta_data_in_list['cantidad_disponible'] += cantidad_cambiada
                
                # **CLAVE PARA ARREGLAR EL "3"**
                # Asegurarse de que la cantidad disponible en la UI no exceda la cantidad que estaba
                # disponible originalmente en la base de datos al abrir el diálogo.
                if herramienta_data_in_list['cantidad_disponible'] > cantidad_disponible_inicial_db:
                    herramienta_data_in_list['cantidad_disponible'] = cantidad_disponible_inicial_db
                
                # (Opcional, pero buena práctica: Asegurarse de que no exceda la cantidad total del inventario tampoco)
                # if herramienta_data_in_list['cantidad_disponible'] > original_db_tool_data['cantidad_total']:
                #     herramienta_data_in_list['cantidad_disponible'] = original_db_tool_data['cantidad_total']


                # Actualizar el texto del item en la QListWidget
                item.setText(f"{herramienta_data_in_list['nombre']} ({herramienta_data_in_list['codigo']}) - Disp: {herramienta_data_in_list['cantidad_disponible']}") # type: ignore
                
                # Si la cantidad disponible llega a 0, ocultar la herramienta
                item.setHidden(herramienta_data_in_list['cantidad_disponible'] <= 0) # type: ignore
                
                # No es necesario actualizar self.herramientas_disponibles_cache aquí,
                # ya que ahora guarda el estado original de la DB y no el estado mutado del UI.
                break

    def validar_y_registrar_prestamo(self):
        """
        Valida los datos y registra el préstamo en la base de datos.
        """
        selected_rotacion_id = self.rotacion_combo.currentData()
        if selected_rotacion_id == -1: # El valor por defecto "Seleccione una Rotación"
            QMessageBox.warning(self, "Error de Validación", "Por favor, seleccione una rotación/área.")
            return

        if not self.herramientas_a_prestar:
            QMessageBox.warning(self, "Error de Validación", "Por favor, agregue al menos una herramienta al préstamo.")
            return
        
        # Confirmación final antes de registrar
        respuesta = QMessageBox.question(self, "Confirmar Préstamo", 
                                        "¿Está seguro de que desea registrar este préstamo?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if respuesta == QMessageBox.StandardButton.No:
            return

        # Procesar cada herramienta en el préstamo
        exito_general = True
        for herramienta_en_prestamo in self.herramientas_a_prestar:
            herramienta_id = herramienta_en_prestamo['id']
            cantidad_prestada = herramienta_en_prestamo['cantidad_seleccionada']

            # ¡¡¡AQUÍ ESTÁ EL CAMBIO CLAVE!!!
            # Debemos usar el nuevo método registrar_prestamo que también inserta en prestamos_activos.
            registrado = self.loan_repo.registrar_prestamo(
                herramienta_id, 
                selected_rotacion_id, 
                cantidad_prestada
            )
            
            if not registrado:
                exito_general = False
                QMessageBox.critical(self, "Error de Registro", 
                                    f"No se pudo registrar el préstamo para {herramienta_en_prestamo['nombre']}. Verifique la disponibilidad o la base de datos.")
                break # Sale del bucle si hay un error en una herramienta

        if exito_general:
            QMessageBox.information(self, "Préstamo Registrado", "El préstamo ha sido registrado exitosamente.")
            self.prestamo_registrado.emit() # Emitir señal de éxito
            self.accept() # Cierra el diálogo

    def agregar_herramienta_por_scan(self):
        """
        Busca una herramienta por código exacto (escaneado) y la agrega al préstamo.
        """
        
        codigo_escaneado = self.buscar_line_edit.text().strip()
        if not codigo_escaneado:
            return

        item_encontrado = None
        # Busca en la lista de herramientas disponibles el que coincida exactamente
        for i in range(self.lista_herramientas.count()):
            item = self.lista_herramientas.item(i)
            datos_herramienta = item.data(Qt.ItemDataRole.UserRole)
            if datos_herramienta['codigo'].lower() == codigo_escaneado.lower():
                item_encontrado = item
                break

        if item_encontrado:
            
            # Si se encuentra, lo seleccionamos en la lista
            self.lista_herramientas.setCurrentItem(item_encontrado)
            # Establecemos la cantidad a 1
            self.cantidad_spinbox.setValue(1)
            # Llamamos a la función que ya tienes para agregar a la tabla
            self.agregar_herramientas_al_prestamo()
            # Limpiamos el campo de búsqueda para el siguiente escaneo
            self.buscar_line_edit.clear()
            
        else:
            QMessageBox.warning(self, "No Encontrado", f"No se encontró ninguna herramienta con el código '{codigo_escaneado}'.")
            self.buscar_line_edit.selectAll()





    # Puedes eliminar generar_id o adaptarlo para otros fines si es necesario
    # Tu código actual tiene self.id_prestamo y self.id_valor para mostrar un ID,
    # pero como estamos registrando movimientos individuales, el ID del préstamo
    # como un concepto único para un conjunto de herramientas podría no ser necesario
    # o debería generarse y gestionarse de otra manera si realmente lo necesitas.
    # Por ahora, me centraré en registrar movimientos atómicos.

    # El código original tiene esta línea, la elimino ya que el id_prestamo no es central al movimiento
    # self.id_prestamo = self.generar_id() if self.generar_id else "Error-ID"