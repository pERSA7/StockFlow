from PyQt6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup

from .inventario import Inventario
from .prestamo import Prestamo
from .historial import Historial
from .agregar import Agregar
from .reposicion_baja import ReposicionBaja
from .novedades import Novedades
from .recordatorios import Recordatorios

class AreaCentral(QWidget):
    def __init__(self, parent=None): # Recibir la lista de nombres del inventario
        super().__init__(parent)

        #self.inventario_nombres = inventario_nombres #guardar la lista
        layout_principal = QVBoxLayout(self)
        self.setLayout(layout_principal)

        #self.widgets_vistas = {}

        self.stacked_widget = QStackedWidget()

        # Widget HIJOS
        try:
            self.prestamo = Prestamo() 
        except Exception as e:
            print(f"Error creando Prestamo: {e}")

        try:
            self.inventario = Inventario() # <<-- PASA LA CONEXIÓN
            print("[INVENTARIO] Inventario creado")
        except Exception as e:
            print(f"Error creando Inventario: {e}")

        try:
            self.historial = Historial() 
        except Exception as e:
            print(f"Error creando Historial: {e}")

        try:
            self.agregar = Agregar() 
        except Exception as e:
            print(f"Error creando Agregar: {e}")

        try:
            self.reposicion_baja = ReposicionBaja() 
        except Exception as e:
            print(f"Error creando Reposición/Baja: {e}")

        try:
            self.novedades = Novedades()
        except Exception as e:
            print(f"Error creando Novedades: {e}")

        try:
            self.recordatorios = Recordatorios()
        except Exception as e:
            print(f"Error creando Recordatorios: {e}")


        self.agregar.set_inventario_widget_ref(self.inventario)
        self.reposicion_baja.set_inventario_widget_ref(self.inventario)
        self.agregar.herramienta_agregada.connect(self.reposicion_baja.cargar_herramientas)
        self.prestamo.prestamos_actualizados.connect(self.historial.cargar_historial)
        self.agregar.herramienta_agregada.connect(self.novedades.cargar_novedades)
        self.reposicion_baja.inventario_actualizado.connect(self.novedades.cargar_novedades)

        self.stacked_widget.addWidget(self.prestamo)
        self.stacked_widget.addWidget(self.inventario)
        self.stacked_widget.addWidget(self.historial)
        self.stacked_widget.addWidget(self.agregar)
        self.stacked_widget.addWidget(self.reposicion_baja)
        self.stacked_widget.addWidget(self.novedades)
        self.stacked_widget.addWidget(self.recordatorios)

        layout_principal.addWidget(self.stacked_widget)

        # Mapeo de los ítems del sidebar a los índices del stacked widget
        self.vista_mapping = {
            "Préstamos": 0,
            "Inventario": 1,
            "Historial de Movimientos": 2,
            "Agregar Elemento": 3,
            "Reposición/Bajas": 4,
            "Novedades": 5,
            "Recordatorios": 6,
        }

        self.animation_group = None

    def cambiar_vista(self, texto_item):
        print(f"[DEBUG] Vista solicitada: {texto_item}")

        if texto_item not in self.vista_mapping:
            print(f"[ERROR] Vista no encontrada para: {texto_item}")
            return
        
        index_nuevo = self.vista_mapping[texto_item]
        index_actual = self.stacked_widget.currentIndex()

        if index_nuevo == index_actual:
            return
        
        widget_actual = self.stacked_widget.widget(index_actual)
        widget_nuevo = self.stacked_widget.widget(index_nuevo)

        # --- Lógica de Animación de Deslizamiento ---
        
        # 1. Preparar las posiciones
        ancho = self.stacked_widget.width()
        alto = self.stacked_widget.height()
        
        # Determinar dirección
        if index_nuevo > index_actual:
            # Desliza hacia la izquierda (el nuevo viene de la derecha)
            pos_inicial_nuevo = QPoint(ancho, 0)
            pos_final_actual = QPoint(-ancho, 0)
        else:
            # Desliza hacia la derecha (el nuevo viene de la izquierda)
            pos_inicial_nuevo = QPoint(-ancho, 0)
            pos_final_actual = QPoint(ancho, 0)

        # 2. Mover el widget nuevo a su posición inicial (fuera de pantalla)
        # Aseguramos que tenga el tamaño correcto antes de moverlo
        widget_nuevo.setGeometry(0, 0, ancho, alto)
        widget_nuevo.move(pos_inicial_nuevo)
        
        # 3. Hacer el widget nuevo el "actual" en el stack (para que sea visible)
        self.stacked_widget.setCurrentIndex(index_nuevo)
        
        # 4. Crear las animaciones
        duracion = 300 # 300 milisegundos
        curva = QEasingCurve.Type.InOutCubic # Curva suave de aceleración

        anim_actual = QPropertyAnimation(widget_actual, b"pos")
        anim_actual.setDuration(duracion)
        anim_actual.setStartValue(QPoint(0, 0)) # Posición actual
        anim_actual.setEndValue(pos_final_actual) # Mover fuera de pantalla
        anim_actual.setEasingCurve(curva)

        anim_nuevo = QPropertyAnimation(widget_nuevo, b"pos")
        anim_nuevo.setDuration(duracion)
        anim_nuevo.setStartValue(pos_inicial_nuevo) # Mover desde fuera
        anim_nuevo.setEndValue(QPoint(0, 0)) # Mover al centro
        anim_nuevo.setEasingCurve(curva)

        # 5. Agrupar y ejecutar
        # Guardamos la referencia en 'self.animation_group'
        self.animation_group = QParallelAnimationGroup()
        self.animation_group.addAnimation(anim_actual)
        self.animation_group.addAnimation(anim_nuevo)
        
        # IMPORTANTE: Resetear la posición del widget antiguo cuando la animación termine
        # para que esté listo si se vuelve a seleccionar.
        self.animation_group.finished.connect(lambda: widget_actual.move(0, 0))

        self.animation_group.start()

