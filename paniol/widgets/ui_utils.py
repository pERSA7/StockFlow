from PyQt6.QtWidgets import QMessageBox, QFileDialog, QTableView, QTableWidget
from PyQt6.QtCore import Qt
import pandas as pd
from ..app.core import db_manager
from ..repositories.notification_repository import NotificationRepository

def exportar_tabla_a_excel (table, parent_widget, nombre_reporte="Datos"):
    file_path, _ = QFileDialog.getSaveFileName(
        parent_widget,
        "Guardar Archivo Excel",
        "",
    "Archivos Excel (*.xlsx);; Todos los Archivos (*)"
    )

    if not file_path:
        return

    try:
        headers = []
        data = []
        if isinstance(table, QTableView):
            model = table.model()
            if not model:
                QMessageBox.warning(parent_widget, "Error", "La tabla no tiene un modelo de datos asociados.")
                return
        
            visible_columns_indices = []

            for column in range(model.columnCount()):
                if not table.isColumnHidden(column):
                    headers.append(model.headerData(column, Qt.Orientation.Horizontal))
                    visible_columns_indices.append(column)

            for row in range(model.rowCount()):
                if not table.isRowHidden(row):
                    row_data = []
                    for col_idx in visible_columns_indices:
                        index = model.index(row, col_idx)
                        cell_data = model.data(index, Qt.ItemDataRole.DisplayRole)
                        row_data.append(str(cell_data) if cell_data is not None else "")
                    data.append(row_data)

        elif isinstance(table, QTableWidget):
            # Lógica para QTableWidget (usada en Historial)
            visible_columns_indices = []
            for column in range(table.columnCount()):
                if not table.isColumnHidden(column):
                    header_item = table.horizontalHeaderItem(column)
                    headers.append(header_item.text() if header_item else f'Columna {column + 1}')
                    visible_columns_indices.append(column)
            
            for row in range(table.rowCount()):
                if not table.isRowHidden(row):
                    row_data = []
                    for col_idx in visible_columns_indices:
                        item = table.item(row, col_idx)
                        # Asegurarse de que el item existe y tiene texto antes de añadirlo
                        row_data.append(item.text() if item and item.text() else "")
                    data.append(row_data)
        
        else:
            raise TypeError("El widget proporcionado no es un QTableView o QTableWidget.")

        df = pd.DataFrame(data, columns=headers)
        df.to_excel(file_path, index=False)
        
        notification_repo = NotificationRepository(db_manager)
        notification_repo.registrar_novedad_exportacion(nombre_reporte)

        QMessageBox.information(parent_widget, "Exito", "La tabla se ha exportado correctamente.")

    except Exception as e:
        QMessageBox.critical(parent_widget, "Error", f"Error al exportar la tabla: {str(e)}")