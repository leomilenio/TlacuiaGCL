import os
import re
import sys
import camelot
import pdfplumber
import ollama
import json
import requests
import pandas as pd
import subprocess
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
                             QTableWidget, QTableWidgetItem, QSpinBox, QListWidget, QLabel,
                             QMessageBox, QLineEdit, QComboBox, QListWidgetItem, QDialog, QInputDialog,
                             QTextEdit, QProgressDialog)
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
        self.is_load_pdf_enabled = True 
        self.db = ConcesionesDB()
        self.initUI()

        # Verificar si Ollama y Mistral están instalados
        if self.check_ollama_and_mistral_installed():
            self.btn_choose_method.setEnabled(True)  # Habilitar el botón
        else:
            self.btn_choose_method.setEnabled(False)  # Deshabilitar el botón
            QMessageBox.warning(self, "Advertencia", "Ollama o Mistral no están instalados. Por favor, instale Mistral y Ollama para utilizar esta funcion.")

    def initUI(self):
        self.setWindowTitle("Extractor de Tablas PDF")
        self.setGeometry(200, 200, 1200, 800)  # Ventana más grande

        main_layout = QHBoxLayout()
        
        # Controles izquierdos (Filtrado)
        control_layout = QVBoxLayout()
        
        # Botón para elegir el método de extracción
        self.btn_choose_method = QPushButton('Ocupar otro método de extracción (Experimental)', self)
        self.btn_choose_method.clicked.connect(self.choose_extraction_method)
        control_layout.addWidget(self.btn_choose_method)

        # Botón para cargar PDF
        self.btn_load = QPushButton('Cargar PDF', self)
        self.btn_load.clicked.connect(self.load_pdf_options)
        self.update_load_pdf_button_state()  # Actualizar estado inicial del botón
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

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.destroyed.connect(self.eliminar_archivos_temporales)

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

    def set_load_pdf_enabled(self, enabled):
        """
        Habilita o deshabilita el botón "Cargar PDF".
        :param enabled: Booleano que indica si el botón debe estar habilitado.
        """
        self.is_load_pdf_enabled = enabled
        self.update_load_pdf_button_state()

    def update_load_pdf_button_state(self):
        """
        Actualiza el estado del botón "Cargar PDF" según el valor de is_load_pdf_enabled.
        """
        self.btn_load.setEnabled(self.is_load_pdf_enabled)

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
                self.eliminar_archivos_temporales()
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
            
    def eliminar_archivos_temporales(self):
        """Elimina los archivos temporales generados durante la ejecución"""
        temp_files = [self.temp_csv_path,
                      *[f for f in os.listdir('.') if re.match(r'tem_.*\.pdf\.pdf$', f)]
                      ] 
         # Agregar aquí otros archivos temporales si los hay
        for file in temp_files:
            if os.path.exists(file):
                try:
                    os.remove(file)
                    print(f"Archivo temporal eliminado: {file}")
                except Exception as e:
                    print(f"No se pudo eliminar el archivo temporal {file}: {str(e)}")

    # Implementacion de prueba, analisis mediante LLM
    def load_pdf_for_llm(self):
        """Muestra un cuadro de diálogo para elegir entre cargar PDF de una concesión o desde archivos del usuario."""
        options = ["Cargar PDF de una concesión", "Cargar PDF desde archivos del usuario"]
        choice, ok = QInputDialog.getItem(self, "Cargar PDF", "Seleccione una opción:", options, 0, False)
        if ok and choice:
            if choice == "Cargar PDF de una concesión":
                self.load_pdf_from_concesion_for_llm()
            elif choice == "Cargar PDF desde archivos del usuario":
                self.load_pdf_from_file_for_llm()

    def load_pdf_from_file_for_llm(self):
        """Carga un PDF desde archivos del usuario para procesarlo con LLM."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar PDF", "", "PDF Files (*.pdf)")
        if file_path:
            self.process_pdf_with_llm(file_path)

    def choose_extraction_method(self):
        """Permite al usuario elegir entre Camelot y LLM, mostrando una advertencia previa."""
        # Mostrar advertencia sobre la naturaleza experimental de la utilidad
        advertencia = QMessageBox.warning(
            self,
            "Advertencia",
            "Esta utilidad sigue en etapa experimental, verifique el manual para "
            "verificar que su ordenador cumple con los requisitos mínimos. "
            "Considere que el LLM (MISTRAL) podría no realizar la tarea correctamente.",
            QMessageBox.Ok | QMessageBox.Cancel
        )
        
        # Si el usuario cancela, detener el proceso
        if advertencia == QMessageBox.Cancel:
            return

        # Continuar con el flujo normal si el usuario acepta
        options = ["Camelot", "LLM: Mistral"]
        choice, ok = QInputDialog.getItem(
            self, 
            "Elegir Método de Extracción", 
            "Seleccione un método:", 
            options, 
            0, 
            False
        )
        
        if ok and choice:
            self.extraction_method = choice
            if choice == "Camelot":
                self.load_pdf_options()  # Flujo actual
            elif choice == "LLM: Mistral":
                self.load_pdf_for_llm()  # Nuevo flujo para LLM

    def extract_text_from_pdf(file_path):
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
        return text


    def preprocess_for_llm(self, text):
        print("Texto en preprocesamiento:")
        print(text)

        # Dividir el texto en bloques separados por líneas vacías
        blocks = [block.strip() for block in text.split("\n\n") if block.strip()]

        # Identificar el bloque que contiene la tabla de productos
        table_block = None
        for block in blocks:
            if "Cant Cve.Prod.SA|Cve.Producto|Cve.Prod.Cliente|Título" in block:
                table_block = block
                break

        if not table_block:
            raise ValueError("No se encontró la tabla de productos en el texto.")

        # Procesar cada fila de la tabla
        product_rows = []
        lines = table_block.split("\n")
        for line in lines[1:]:  # Ignorar la primera línea (encabezado)
            if not line.strip():  # Detenerse si encontramos una línea vacía
                break

            # Dividir la línea en columnas usando el separador "|"
            columns = [col.strip() for col in line.split("|") if col.strip()]

            # Extraer los campos relevantes
            cantidad = re.findall(r"\d+", columns[0])[0]  # Extraer solo números de la cantidad
            isbn = columns[1]
            titulo = columns[3]
            imp_neto = columns[-1].replace(",", "")  # Eliminar comas

            # Guardar en un diccionario
            product_rows.append({
                "cantidad": int(cantidad),
                "isbn": isbn,
                "titulo": titulo,
                "importe_neto": float(imp_neto)
            })

        return product_rows

    def process_pdf_with_llm(self, file_path):
        try:
            
            progress_dialog = QProgressDialog("Mistral está procesando el documento ingresado...", "Cancelar", 0, 0, self)
            progress_dialog.setWindowTitle("Procesando...")
            progress_dialog.setWindowModality(Qt.WindowModal)  # Bloquear interacción con otras ventanas
            progress_dialog.setMinimumDuration(0)  # Mostrar inmediatamente
            progress_dialog.show()

            # Paso 1: Extraer tablas con Camelot
            tables = camelot.read_pdf(file_path, flavor='stream', pages='all')
            combined_text = ""
            for table in tables:
                df = table.df
                # Convertir DataFrame a texto estructurado
                combined_text += df.to_csv(sep="|", index=False)
                print(combined_text)
            
            # Paso 2: Preprocesar texto para LLM
            processed_text = self.preprocess_for_llm(combined_text)
            print("Texto preprocesado:")
            print(processed_text)
            text_chunks = self.split_text_into_chunks(processed_text)
            
            extracted_data = []
            raw_response = []

            try:
                for chunk in text_chunks:
                    # Paso 3: Analizar con LLM
                    response = ollama.chat(
                        model="mistral:latest",
                        messages=[
                            {
                                "role": "user",
                                "content": (
                                    "ANALIZA ESTA TABLA DE PRODUCTOS Y GENERA UN JSON CON EL SIGUIENTE FORMATO:\n"
                                    "{\n"
                                    "  \"Conceptos\": [\n"
                                    "    {\n"
                                    "      \"Cantidad\": int,\n"
                                    "      \"ISBN\": \"###-###-###-####-#\",\n"
                                    "      \"TituloLibro\": \"texto\",\n"
                                    "      \"PrecioUnitario\": float,\n"
                                    "      \"ImporteNeto\": float\n"
                                    "    }\n"
                                    "  ]\n"
                                    "}\n\n"
                                    "REGLAS ABSOLUTAS DE EXTRACCIÓN:\n"
                                    "1. Validar ISBN (13 dígitos, formatear como ###-###-###-####-#).\n"
                                    "2. Verificar que ImporteNeto = Cantidad * PrecioUnitario.\n"
                                    "3. Si faltan datos, OMITIR la fila completamente.\n\n"
                                    f"TEXTO A PROCESAR:\n{chunk}"
                                )
                            }
                        ],
                        options={
                            "temperature": 0.0,  # Minimizar aleatoriedad
                            "max_tokens": 4096,  # Limitar longitud máxima
                            "stop": ["\n}"]      # Forzar finalización al cerrar JSON
                        }
                    )
                    raw_response.append(response["message"]["content"])
                    extracted_data.extend(self.parse_llm_response(response))
            except requests.exceptions.RequestException as e:
                QMessageBox.critical(self, "Error", f"Error al comunicarse con el modelo LLM: {str(e)}")
                return
            raw_response = "\n".join(raw_response)

            progress_dialog.cancel()

            self.preview_llm_data(extracted_data, raw_response, file_path)  # Pasar ambos argumentos
            
        except Exception as e:
            if 'progress_dialog' in locals():
                progress_dialog.cancel()
            QMessageBox.critical(self, "Error", f"Error al procesar el PDF con LLM: {str(e)}")

    def validate_extracted_data(self, data):
        validated_data = []
        for item in data:
            # Validar ISBN
            isbn = item.get("ISBN", "")
            if not re.match(r"^\d{3}-\d-\d{2}-\d{6}-\d$", isbn):
                continue
            
            # Validar relación matemática
            cantidad = float(item.get("Cantidad", 0))
            precio_unitario = float(item.get("PrecioUnitario", 0))
            importe_neto = float(item.get("ImporteNeto", 0))
            if abs(importe_neto - (cantidad * precio_unitario)) > 0.01:
                continue
            
            validated_data.append(item)
        
        return validated_data

    def load_pdf_from_concesion_for_llm(self):
        """Carga un PDF desde una concesión existente para procesarlo con LLM."""
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
                            temp_pdf_path = f"temp_{documento['nombre']}.pdf"
                            with open(temp_pdf_path, 'wb') as f:
                                f.write(documento['contenido'])
                            self.process_pdf_with_llm(temp_pdf_path)


    def preview_llm_data(self, extracted_data, raw_response, file_path):
        """Muestra una previsualización de los datos extraídos por el LLM."""
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Previsualización de Datos Extraídos")
        layout = QVBoxLayout()
        
        # Mostrar datos procesados
        processed_label = QLabel("Datos Procesados:")
        layout.addWidget(processed_label)
        table_widget = QTableWidget()
        
        if isinstance(extracted_data, list) and len(extracted_data) > 0:
            headers = ["Cantidad", "ISBN", "TituloLibro", "PrecioUnitario", "ImporteNeto"]
            table_widget.setRowCount(len(extracted_data))
            table_widget.setColumnCount(len(headers))
            table_widget.setHorizontalHeaderLabels(headers)
            
            for row_idx, row_data in enumerate(extracted_data):
                for col_idx, key in enumerate(headers):
                    item = QTableWidgetItem(str(row_data.get(key, "")))
                    table_widget.setItem(row_idx, col_idx, item)
        else:
            label = QLabel("No se encontraron datos válidos para previsualizar.")
            layout.addWidget(label)
        
        layout.addWidget(table_widget)
        
        # Mostrar respuesta sin procesar
        raw_label = QLabel("Respuesta Sin Procesar del LLM:")
        layout.addWidget(raw_label)
        raw_text_edit = QTextEdit()
        raw_text_edit.setPlainText(raw_response)
        raw_text_edit.setReadOnly(True)
        layout.addWidget(raw_text_edit)

        # Botones de acción
        btn_layout = QHBoxLayout()

        btn_save = QPushButton("Guardar Respuesta")
        btn_save.clicked.connect(lambda: self.save_results(raw_response, preview_dialog))

        btn_discard = QPushButton("Descartar Respuesta")
        btn_discard.clicked.connect(preview_dialog.reject)

        btn_retry = QPushButton("Volver a Procesar")
        btn_retry.clicked.connect(lambda: self.retry_processing(file_path, preview_dialog))

        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_discard)
        btn_layout.addWidget(btn_retry)

        layout.addLayout(btn_layout)
        preview_dialog.setLayout(layout)
        preview_dialog.exec_()

    def retry_processing(self, file_path, dialog):
        """
        Vuelve a procesar el análisis del PDF con LLM.
        :param file_path: Ruta del archivo PDF original.
        :param dialog: Diálogo actual para cerrarlo antes de reiniciar el proceso.
        """
        dialog.reject()  # Cerrar el diálogo actual
        self.process_pdf_with_llm(file_path)  # Volver a procesar el PDF


    def parse_llm_response(self, response):
        """
        Analiza la respuesta del modelo LLM y extrae los datos relevantes.
        """
        try:
            # Verificar si la respuesta contiene datos válidos
            if not response or "message" not in response or "content" not in response["message"]:
                raise ValueError("La respuesta del modelo está vacía o no tiene el formato esperado.")
            
            # Obtener el contenido de la respuesta
            content = response["message"]["content"].strip()
            
            # Verificar si el contenido está vacío
            if not content:
                raise ValueError("La respuesta del modelo está vacía.")
            
            # Intentar analizar el contenido como JSON
            try:
                parsed_data = json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"Error al analizar la respuesta JSON: {e}")
            
            # Validar que el JSON tenga la estructura esperada
            if "Conceptos" not in parsed_data or not isinstance(parsed_data["Conceptos"], list):
                raise ValueError("La respuesta del modelo no contiene la clave 'Conceptos' o no es una lista.")
            
            # Validar cada elemento en la lista de Conceptos
            validated_data = self.validate_extracted_data(parsed_data["Conceptos"])
            
            return validated_data
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al analizar la respuesta del modelo: {str(e)}")
            return []
        
    def split_text_into_chunks(self, text, max_length=2000):
        """
        Divide el texto en fragmentos más pequeños para evitar exceder el límite de tokens del modelo LLM.
        :param text: Texto completo a dividir.
        :param max_length: Longitud máxima de cada fragmento (en caracteres).
        :return: Lista de fragmentos de texto.
        """
        words = text.split()
        chunks = []
        current_chunk = []

        for word in words:
            # Verificar si agregar la siguiente palabra excede el límite
            if sum(len(w) + 1 for w in current_chunk) + len(word) <= max_length:
                current_chunk.append(word)
            else:
                # Guardar el fragmento actual y comenzar uno nuevo
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]

        # Agregar el último fragmento
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
    
    def save_results(self, raw_response, dialog):
        """
        Guarda la respuesta del LLM en un archivo .txt.
        :param raw_response: Respuesta sin procesar del LLM.
        :param dialog: Diálogo actual para cerrarlo después de guardar.
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Respuesta", "", "Text Files (*.txt)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(raw_response)
                QMessageBox.information(self, "Éxito", "Respuesta guardada correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar la respuesta: {str(e)}")
        dialog.accept()

    import subprocess

    def check_ollama_and_mistral_installed(self):
        """
        Verifica si Ollama y Mistral están instalados en el sistema.
        :return: Booleano indicando si ambos están instalados.
        """
        try:
            print("Se ha ejecutado el metodo check_ollama_and_mistral")
            # Verificar si Ollama está instalado
            subprocess.run(["ollama", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Verificar si Mistral está disponible a través de Ollama
            result = subprocess.run(["ollama", "list"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if "mistral" not in result.stdout.lower():
                return False
            
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False