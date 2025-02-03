import os
import sys
import camelot
import pandas as pd
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
                             QTableWidget, QTableWidgetItem, QSpinBox, QListWidget, QLabel,
                             QMessageBox, QLineEdit, QComboBox, QListWidgetItem, QDialog, QInputDialog)
from PyQt5.QtCore import Qt
from app.models.database import ConcesionesDB

class PdfTableExtractor(QDialog):
    def __init__(self):
        super().__init__()
        self.tables = []  # Lista de todas las tablas extraídas del PDF
        self.selected_tables = []  # Lista de tablas seleccionadas por el usuario
        self.current_page = None  # Página actual seleccionada
        self.temp_csv_path = "temp_combined_table.csv"  # Ruta del archivo CSV temporal
        self.filters = {}  # Diccionario para guardar los filtros por tabla
        self.db = ConcesionesDB()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Extractor de Tablas PDF")
        self.setGeometry(200, 200, 1200, 800)  # Ventana más grande

        main_layout = QHBoxLayout()
        
        # Controles izquierdos (Filtrado)
        control_layout = QVBoxLayout()
        
        # Botón para cargar PDF
        self.btn_load = QPushButton('Cargar PDF', self)
        self.btn_load.clicked.connect(self.load_pdf_options)
        control_layout.addWidget(self.btn_load)
        
        # Sección de filtros
        control_layout.addWidget(QLabel('Filtros:'))
        
        # Selector de hojas
        control_layout.addWidget(QLabel('Seleccionar Hoja:'))
        self.page_selector = QComboBox()
        self.page_selector.currentIndexChanged.connect(self.update_table_selector)
        control_layout.addWidget(self.page_selector)
        
        # Selector de tablas
        control_layout.addWidget(QLabel('Seleccionar Tabla:'))
        self.table_selector = QListWidget()
        self.table_selector.itemClicked.connect(self.show_table)
        control_layout.addWidget(self.table_selector)
        
        # Controles de filas
        control_layout.addWidget(QLabel('Fila inicial:'))
        self.spin_start = QSpinBox()
        self.spin_start.valueChanged.connect(self.update_filtered_table)
        control_layout.addWidget(self.spin_start)
        control_layout.addWidget(QLabel('Fila final:'))
        self.spin_end = QSpinBox()
        self.spin_end.valueChanged.connect(self.update_filtered_table)
        control_layout.addWidget(self.spin_end)
        
        # Filas a eliminar
        control_layout.addWidget(QLabel('Filas a eliminar (ej. 7,10,11):'))
        self.exclude_rows_input = QLineEdit()
        self.exclude_rows_input.setPlaceholderText("Ejemplo: 7,10,11")
        self.exclude_rows_input.textChanged.connect(self.update_filtered_table)
        control_layout.addWidget(self.exclude_rows_input)
        
        # Lista de columnas
        control_layout.addWidget(QLabel('Columnas:'))
        self.column_list = QListWidget()
        self.column_list.itemChanged.connect(self.update_filtered_table)
        control_layout.addWidget(self.column_list)
        
        # Botón para guardar cambios a la tabla seleccionada
        self.btn_save_changes = QPushButton('Guardar cambios a la tabla seleccionada', self)
        self.btn_save_changes.clicked.connect(self.save_table_filters)
        control_layout.addWidget(self.btn_save_changes)
        
        main_layout.addLayout(control_layout)
        
        # Controles derechos (Combinación y previsualización)
        right_layout = QVBoxLayout()
        
        # Botón 1: Seleccionar tablas a combinar
        self.btn_select_tables = QPushButton('1. Seleccionar Tablas para Combinar', self)
        self.btn_select_tables.clicked.connect(self.select_tables_to_combine)
        right_layout.addWidget(self.btn_select_tables)
        
        # Botón 2: Combinar tablas seleccionadas
        self.btn_combine_tables = QPushButton('2. Combinar Tablas Seleccionadas', self)
        self.btn_combine_tables.clicked.connect(self.combine_selected_tables)
        self.btn_combine_tables.setEnabled(False)  # Deshabilitado inicialmente
        right_layout.addWidget(self.btn_combine_tables)
        
        # Botón 3: Previsualizar la tabla final
        self.btn_preview_final = QPushButton('3. Previsualizar Tabla Final', self)
        self.btn_preview_final.clicked.connect(self.preview_final_table)
        self.btn_preview_final.setEnabled(False)  # Deshabilitado inicialmente
        right_layout.addWidget(self.btn_preview_final)
        
        # Botón 4: Finalizar la unión
        self.btn_finalize_union = QPushButton('4. Finalizar Unión', self)
        self.btn_finalize_union.clicked.connect(self.finalize_union)
        self.btn_finalize_union.setEnabled(False)  # Deshabilitado inicialmente
        right_layout.addWidget(self.btn_finalize_union)
        
        # Tablas
        table_layout = QVBoxLayout()
        self.original_table = QTableWidget()
        self.filtered_table = QTableWidget()
        table_layout.addWidget(QLabel('Tabla Original:'))
        table_layout.addWidget(self.original_table)
        table_layout.addWidget(QLabel('Tabla Filtrada:'))
        table_layout.addWidget(self.filtered_table)
        right_layout.addLayout(table_layout)
        
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)

    def load_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar PDF", "", "PDF Files (*.pdf)")
        if file_path:
            try:
                # Leer todas las tablas de todas las páginas
                self.tables = camelot.read_pdf(file_path, flavor='stream', pages='all')
                if self.tables:
                    self.page_selector.clear()
                    pages = sorted(set(table.page for table in self.tables))
                    for page in pages:
                        self.page_selector.addItem(f"Hoja {page}")
                    self.current_page = pages[0]
                    self.update_table_selector()
                else:
                    QMessageBox.warning(self, "Error", "No se encontraron tablas en el PDF")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al procesar PDF: {str(e)}")

    def update_table_selector(self):
        selected_page = int(self.page_selector.currentText().split(" ")[1])
        self.current_page = selected_page
        self.table_selector.clear()
        for i, table in enumerate(self.tables):
            if table.page == selected_page:
                self.table_selector.addItem(f"Tabla {i + 1}")

    def show_table(self, item):
        table_index = self.table_selector.row(item)
        table = self.tables[table_index]
        self.show_table_data(table)

    def show_table_data(self, table):
        df = table.df
        # Configurar tabla original
        self.original_table.setRowCount(df.shape[0])
        self.original_table.setColumnCount(df.shape[1])
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                self.original_table.setItem(i, j, QTableWidgetItem(df.iloc[i, j]))
        
        # Configurar controles
        self.spin_start.setMaximum(df.shape[0])
        self.spin_end.setMaximum(df.shape[0])
        self.spin_end.setValue(df.shape[0])
        self.column_list.clear()
        for col in range(df.shape[1]):
            item = QListWidgetItem(f"Columna {col + 1}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.column_list.addItem(item)
        
        # Aplicar filtros guardados si existen
        table_id = id(table)
        if table_id in self.filters:
            filters = self.filters[table_id]
            self.spin_start.setValue(filters['start_row'])
            self.spin_end.setValue(filters['end_row'])
            self.exclude_rows_input.setText(",".join(map(str, filters['exclude_rows'])))
            for col in range(df.shape[1]):
                self.column_list.item(col).setCheckState(Qt.Checked if col in filters['selected_columns'] else Qt.Unchecked)
        
        self.update_filtered_table()

    def update_filtered_table(self):
        table_index = self.table_selector.currentRow()
        if table_index < 0 or table_index >= len(self.tables):
            return
        
        table = self.tables[table_index]
        df = table.df
        max_rows = df.shape[0]
        start_row = min(self.spin_start.value(), max_rows)
        end_row = min(self.spin_end.value(), max_rows)
        selected_columns = [i for i in range(self.column_list.count())
                            if self.column_list.item(i).checkState() == Qt.Checked]
        max_columns = df.shape[1]
        selected_columns = [col for col in selected_columns if col < max_columns]
        exclude_rows = []
        try:
            exclude_rows = [int(row.strip()) - 1 for row in self.exclude_rows_input.text().split(",") if row.strip()]
            exclude_rows = [row for row in exclude_rows if row >= 0 and row < max_rows]
        except ValueError:
            QMessageBox.warning(self, "Advertencia", "Las filas excluidas deben ser números separados por comas.")
        
        try:
            filtered_df = df.iloc[start_row:end_row, selected_columns]
            rows_to_keep = [i for i in range(filtered_df.shape[0]) if i + start_row not in exclude_rows]
            filtered_df = filtered_df.iloc[rows_to_keep]
            
            # Mostrar la tabla filtrada
            self.filtered_table.setRowCount(filtered_df.shape[0])
            self.filtered_table.setColumnCount(filtered_df.shape[1])
            for i in range(filtered_df.shape[0]):
                for j in range(filtered_df.shape[1]):
                    self.filtered_table.setItem(i, j, QTableWidgetItem(filtered_df.iloc[i, j]))
        except IndexError as e:
            QMessageBox.critical(self, "Error", f"Error al filtrar la tabla: {str(e)}")

    def save_table_filters(self):
        table_index = self.table_selector.currentRow()
        if table_index < 0 or table_index >= len(self.tables):
            QMessageBox.warning(self, "Advertencia", "No hay una tabla seleccionada para guardar cambios.")
            return
        
        table = self.tables[table_index]
        table_id = id(table)
        df = table.df
        max_rows = df.shape[0]
        start_row = min(self.spin_start.value(), max_rows)
        end_row = min(self.spin_end.value(), max_rows)
        selected_columns = [i for i in range(self.column_list.count())
                            if self.column_list.item(i).checkState() == Qt.Checked]
        max_columns = df.shape[1]
        selected_columns = [col for col in selected_columns if col < max_columns]
        exclude_rows = []
        try:
            exclude_rows = [int(row.strip()) - 1 for row in self.exclude_rows_input.text().split(",") if row.strip()]
            exclude_rows = [row for row in exclude_rows if row >= 0 and row < max_rows]
        except ValueError:
            QMessageBox.warning(self, "Advertencia", "Las filas excluidas deben ser números separados por comas.")
        
        # Guardar los filtros aplicados
        self.filters[table_id] = {
            'start_row': start_row,
            'end_row': end_row,
            'exclude_rows': exclude_rows,
            'selected_columns': selected_columns
        }
        QMessageBox.information(self, "Éxito", "Cambios guardados correctamente.")

    def select_tables_to_combine(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Seleccionar Tablas para Combinar")
        layout = QVBoxLayout()
        list_widget = QListWidget()
        
        for i, table in enumerate(self.tables):
            page_number = table.page
            table_index = i + 1
            item = QListWidgetItem(f"Página {page_number} - Tabla {table_index}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            list_widget.addItem(item)
        
        layout.addWidget(list_widget)
        btn_ok = QPushButton("Aceptar")
        btn_ok.clicked.connect(dialog.accept)
        layout.addWidget(btn_ok)
        dialog.setLayout(layout)
        
        if dialog.exec_():
            self.selected_tables = []
            for i in range(list_widget.count()):
                if list_widget.item(i).checkState() == Qt.Checked:
                    self.selected_tables.append(self.tables[i])
            # Habilitar botones relacionados con la combinación
            self.btn_combine_tables.setEnabled(True)
            self.btn_preview_final.setEnabled(True)
            self.btn_finalize_union.setEnabled(True)

    def combine_selected_tables(self):
        if not self.selected_tables:
            QMessageBox.warning(self, "Advertencia", "No se han seleccionado tablas para combinar.")
            return
        
        # Verificar que todas las tablas tengan el mismo número de columnas
        num_columns = self.selected_tables[0].df.shape[1]
        for table in self.selected_tables:
            if table.df.shape[1] != num_columns:
                QMessageBox.warning(self, "Advertencia", "No todas las tablas tienen el mismo número de columnas.")
                return
        
        # Aplicar filtros a las tablas seleccionadas
        combined_dfs = []
        for table in self.selected_tables:
            table_id = id(table)
            df = table.df
            if table_id in self.filters:
                filters = self.filters[table_id]
                start_row = filters['start_row']
                end_row = filters['end_row']
                exclude_rows = filters['exclude_rows']
                selected_columns = filters['selected_columns']
                
                filtered_df = df.iloc[start_row:end_row, selected_columns]
                rows_to_keep = [i for i in range(filtered_df.shape[0]) if i + start_row not in exclude_rows]
                filtered_df = filtered_df.iloc[rows_to_keep]
            else:
                filtered_df = df
            
            combined_dfs.append(filtered_df)
        
        # Combinar las tablas usando pd.concat()
        combined_df = pd.concat(combined_dfs, ignore_index=True)
        
        # Guardar la tabla combinada en un archivo CSV temporal
        combined_df.to_csv(self.temp_csv_path, index=False)
        QMessageBox.information(self, "Éxito", "Tablas combinadas y guardadas en un archivo temporal.")

    def preview_final_table(self):
        if not os.path.exists(self.temp_csv_path):
            QMessageBox.warning(self, "Advertencia", "No hay una tabla final para previsualizar.")
            return
        
        # Cargar el archivo CSV temporal
        combined_df = pd.read_csv(self.temp_csv_path)
        
        # Mostrar la tabla en una nueva ventana
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Previsualización de la Tabla Final")
        layout = QVBoxLayout()
        
        table_widget = QTableWidget()
        table_widget.setRowCount(combined_df.shape[0])
        table_widget.setColumnCount(combined_df.shape[1])
        for i in range(combined_df.shape[0]):
            for j in range(combined_df.shape[1]):
                table_widget.setItem(i, j, QTableWidgetItem(str(combined_df.iloc[i, j])))
        
        layout.addWidget(table_widget)
        
        btn_close = QPushButton("Listo")
        btn_close.clicked.connect(preview_dialog.close)
        layout.addWidget(btn_close)
        
        preview_dialog.setLayout(layout)
        preview_dialog.exec_()

    def finalize_union(self):
        if not os.path.exists(self.temp_csv_path):
            QMessageBox.warning(self, "Advertencia", "No hay una tabla final para finalizar.")
            return

        # Abrir la previsualización de la tabla final
        self.preview_final_table()

        # Determinar si el archivo fue cargado desde una concesión
        loaded_from_concesion = hasattr(self, 'selected_concesion_id')

        # Mostrar opciones de guardado
        options = []
        if loaded_from_concesion:
            options.append(f"Guardar en la concesión actual (ID: {self.selected_concesion_id})")
        else:
            options.append("Seleccionar una concesión para guardar")
        options.append("Guardar en el sistema de archivos")

        choice, ok = QInputDialog.getItem(self, "Guardar Tabla Final", "Seleccione una opción:", options, 0, False)
        if not ok or not choice:
            return

        if choice.startswith("Guardar en el sistema de archivos"):
            # Guardar en el sistema de archivos
            save_path, _ = QFileDialog.getSaveFileName(self, "Guardar Tabla Final", "", "CSV Files (*.csv)")
            if save_path:
                os.rename(self.temp_csv_path, save_path)
                QMessageBox.information(self, "Éxito", "Tabla final guardada correctamente en el sistema de archivos.")
            else:
                QMessageBox.warning(self, "Advertencia", "Guardado cancelado. El archivo temporal permanece intacto.")
        else:
            # Guardar en una concesión
            if choice.startswith("Guardar en la concesión actual"):
                concesion_id = self.selected_concesion_id
            else:
                # Permitir al usuario seleccionar una concesión
                concesiones = self.db.obtener_concesiones_no_finalizadas_con_emisor()
                if not concesiones:
                    QMessageBox.warning(self, "Advertencia", "No hay concesiones disponibles para guardar.")
                    return

                dialog = QDialog(self)
                dialog.setWindowTitle("Seleccionar Concesión")
                layout = QVBoxLayout()

                list_widget = QListWidget()
                for concesion in concesiones:
                    item = QListWidgetItem(f"{concesion['nombre_emisor']} - Folio: {concesion['folio']}")
                    item.setData(Qt.UserRole, concesion['id'])  # Almacenar el ID de la concesión
                    list_widget.addItem(item)

                layout.addWidget(list_widget)
                btn_ok = QPushButton("Aceptar")
                btn_ok.clicked.connect(dialog.accept)
                layout.addWidget(btn_ok)
                dialog.setLayout(layout)

                if dialog.exec_():
                    selected_item = list_widget.currentItem()
                    if selected_item:
                        concesion_id = selected_item.data(Qt.UserRole)
                    else:
                        QMessageBox.warning(self, "Advertencia", "No se seleccionó ninguna concesión.")
                        return
                else:
                    QMessageBox.warning(self, "Advertencia", "Selección de concesión cancelada.")
                    return

            # Guardar el archivo CSV en la base de datos
            try:
                self.db.crear_documento(concesion_id, "tabla_final.csv", "CSV", self.temp_csv_path)
                QMessageBox.information(self, "Éxito", "Tabla final guardada correctamente en la concesión.")
                self.close()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al guardar el documento en la base de datos: {str(e)}")

    def load_pdf_options(self):
        """Muestra un cuadro de diálogo para elegir entre cargar PDF de una concesión o desde archivos del usuario"""
        options = ["Cargar PDF de una concesión", "Cargar PDF desde archivos del usuario"]
        choice, ok = QInputDialog.getItem(self, "Cargar PDF", "Seleccione una opción:", options, 0, False)
        if ok and choice:
            if choice == "Cargar PDF de una concesión":
                self.load_pdf_from_concesion()
            elif choice == "Cargar PDF desde archivos del usuario":
                self.load_pdf_from_file()

    def load_pdf_from_concesion(self):
        """Carga un PDF desde una concesión existente"""
        concesiones = self.db.obtener_concesiones_no_finalizadas_con_emisor()
        if not concesiones:
            QMessageBox.warning(self, "Advertencia", "No hay concesiones disponibles con documentos vinculados.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Seleccionar Concesión")
        layout = QVBoxLayout()

        list_widget = QListWidget()
        for concesion in concesiones:
            item = QListWidgetItem(f"{concesion['nombre_emisor']} - Folio: {concesion['folio']}")
            item.setData(Qt.UserRole, concesion['id'])  # Almacenar el ID de la concesión
            list_widget.addItem(item)

        layout.addWidget(list_widget)
        btn_ok = QPushButton("Aceptar")
        btn_ok.clicked.connect(dialog.accept)
        layout.addWidget(btn_ok)
        dialog.setLayout(layout)

        if dialog.exec_():
            selected_item = list_widget.currentItem()
            if selected_item:
                concesion_id = selected_item.data(Qt.UserRole)
                documentos = self.db.obtener_documentos(concesion_id)
                if not documentos:
                    QMessageBox.warning(self, "Advertencia", "La concesión seleccionada no tiene documentos asociados.")
                    return

                # Mostrar los documentos disponibles
                doc_dialog = QDialog(self)
                doc_dialog.setWindowTitle("Seleccionar Documento")
                doc_layout = QVBoxLayout()

                doc_list_widget = QListWidget()
                for doc in documentos:
                    item = QListWidgetItem(f"{doc[2]} ({doc[3]})")
                    item.setData(Qt.UserRole, doc[0])  # Almacenar el ID del documento
                    doc_list_widget.addItem(item)

                doc_layout.addWidget(doc_list_widget)
                btn_doc_ok = QPushButton("Aceptar")
                btn_doc_ok.clicked.connect(doc_dialog.accept)
                doc_layout.addWidget(btn_doc_ok)
                doc_dialog.setLayout(doc_layout)

                if doc_dialog.exec_():
                    selected_doc = doc_list_widget.currentItem()
                    if selected_doc:
                        doc_id = selected_doc.data(Qt.UserRole)
                        documento = self.db.obtener_documento_por_id(doc_id)
                        if documento:
                            # Guardar el contenido del documento en un archivo temporal
                            temp_pdf_path = f"temp_{documento['nombre']}.pdf"
                            with open(temp_pdf_path, 'wb') as f:
                                f.write(documento['contenido'])
                            self.load_pdf_from_path(temp_pdf_path)

    def load_pdf_from_file(self):
        """Carga un PDF desde archivos del usuario"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar PDF", "", "PDF Files (*.pdf)")
        if file_path:
            self.load_pdf_from_path(file_path)

    def load_pdf_from_path(self, file_path):
        """Carga un PDF desde una ruta específica"""
        try:
            # Leer todas las tablas de todas las páginas
            self.tables = camelot.read_pdf(file_path, flavor='stream', pages='all')
            if self.tables:
                self.page_selector.clear()
                pages = sorted(set(table.page for table in self.tables))
                for page in pages:
                    self.page_selector.addItem(f"Hoja {page}")
                self.current_page = pages[0]
                self.update_table_selector()
            else:
                QMessageBox.warning(self, "Error", "No se encontraron tablas en el PDF")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al procesar PDF: {str(e)}")