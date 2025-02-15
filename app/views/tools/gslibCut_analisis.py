from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QTableWidget, QTableWidgetItem, QMessageBox, 
                            QFileDialog, QComboBox, QInputDialog, QRadioButton, 
                            QButtonGroup, QStackedWidget, QWidget)
from PyQt5.QtCore import Qt
from app.models.database import ConcesionesDB
from app.utils.report_generator import Reporte
import pandas as pd
import io
import re

class AnalizadorCorteGeslib(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = ConcesionesDB()  # Usamos tu clase de base de datos
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Cargador de Documentos")
        self.setMinimumSize(1000, 600)

        # Layout principal: QHBoxLayout
        main_layout = QVBoxLayout()  # Cambiamos a QVBoxLayout para contener los paneles y el botón
        self.setLayout(main_layout)

        # Contenedor horizontal para los dos paneles principales
        panels_layout = QHBoxLayout()

        # Panel Izquierdo - Reporte GESLib
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Cargar archivo de Reporte de GESLib"))
        self.btn_cargar_geslib = QPushButton("Seleccionar Excel")
        self.btn_cargar_geslib.clicked.connect(self.cargar_excel)
        left_panel.addWidget(self.btn_cargar_geslib)
        self.tabla_geslib = QTableWidget()
        left_panel.addWidget(self.tabla_geslib)

        # Panel Derecho - Factura CSV
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Cargar archivo de factura CSV"))

        # Selector de origen CSV
        self.csv_source_group = QButtonGroup()
        self.rb_csv_file = QRadioButton("Desde archivo")
        self.rb_csv_db = QRadioButton("Desde base de datos")
        self.csv_source_group.addButton(self.rb_csv_file)
        self.csv_source_group.addButton(self.rb_csv_db)

        # Seleccionar 'Desde archivo' por defecto
        self.rb_csv_file.setChecked(True)

        source_layout = QHBoxLayout()
        source_layout.addWidget(self.rb_csv_file)
        source_layout.addWidget(self.rb_csv_db)
        right_panel.addLayout(source_layout)

        # Stack para diferentes fuentes
        self.csv_stack = QStackedWidget()

        # Widget para cargar archivo
        self.file_widget = QWidget()
        file_layout = QVBoxLayout()
        self.btn_cargar_csv = QPushButton("Seleccionar CSV")
        self.btn_cargar_csv.clicked.connect(self.cargar_csv)  # Conectar al método controlador
        file_layout.addWidget(self.btn_cargar_csv)
        self.file_widget.setLayout(file_layout)

        # Widget para cargar desde DB
        self.db_widget = QWidget()
        db_layout = QVBoxLayout()
        self.list_concesiones = QComboBox()
        self.list_concesiones.currentIndexChanged.connect(self.cargar_documentos_db)
        db_layout.addWidget(QLabel("Concesiones activas:"))
        db_layout.addWidget(self.list_concesiones)
        self.list_documentos = QComboBox()
        db_layout.addWidget(QLabel("Documentos disponibles:"))
        db_layout.addWidget(self.list_documentos)
        self.btn_cargar_db = QPushButton("Cargar desde DB")
        self.btn_cargar_db.clicked.connect(self.cargar_csv_db)
        db_layout.addWidget(self.btn_cargar_db)
        self.db_widget.setLayout(db_layout)

        # Añadir widgets al QStackedWidget
        self.csv_stack.addWidget(self.file_widget)
        self.csv_stack.addWidget(self.db_widget)

        # Establecer el widget inicial
        self.csv_stack.setCurrentWidget(self.file_widget)

        right_panel.addWidget(self.csv_stack)

        self.tabla_csv = QTableWidget()
        right_panel.addWidget(self.tabla_csv)

        # Agregar los dos paneles principales al layout horizontal
        panels_layout.addLayout(left_panel, stretch=40)
        panels_layout.addLayout(right_panel, stretch=60)

        # Agregar el layout de los paneles al layout principal
        main_layout.addLayout(panels_layout)

        # Layout para el botón "Comparar tablas"
        button_layout = QHBoxLayout()
        self.btn_comparar = QPushButton("Comparar tablas")
        self.btn_comparar.clicked.connect(self.comparar_tablas)
        self.btn_comparar.setStyleSheet("font-size: 14px; padding: 10px;")  # Estilo opcional
        button_layout.addWidget(self.btn_comparar, alignment=Qt.AlignCenter)  # Centrar el botón

        # Agregar el layout del botón al layout principal
        main_layout.addLayout(button_layout)

        # Conectar los botones de radio al cambio de widget en el QStackedWidget
        self.rb_csv_file.toggled.connect(lambda: self.csv_stack.setCurrentIndex(0))
        self.rb_csv_db.toggled.connect(lambda: self.csv_stack.setCurrentIndex(1))

        # Cargar concesiones activas
        self.cargar_concesiones_activas()

    def cargar_concesiones_activas(self):
        concesiones = self.db.obtener_concesiones_no_finalizadas_con_emisor()
        self.list_concesiones.clear()
        for concesion in concesiones:
            self.list_concesiones.addItem(
                f"{concesion['nombre_emisor']} - Folio: {concesion['folio']}", 
                concesion['id']
            )

    def cargar_documentos_db(self):
        concesion_id = self.list_concesiones.currentData()
        documentos = self.db.obtener_documentos(concesion_id)
        self.list_documentos.clear()
        for doc in documentos:
            if doc[3] == 'CSV':  # Índice 3 = tipo de documento
                self.list_documentos.addItem(doc[2], doc[0])  # Índice 2 = nombre

    def cargar_csv(self):
        if self.rb_csv_file.isChecked():
            self.cargar_csv_file()
        elif self.rb_csv_db.isChecked():
            self.cargar_csv_db()
        else:
            QMessageBox.warning(self, "Opción no seleccionada", "Por favor, selecciona una opción para cargar el CSV.")

    def cargar_csv_db(self):
        doc_id = self.list_documentos.currentData()
        documento = self.db.obtener_documento_por_id(doc_id)
        if documento:
            df = pd.read_csv(io.BytesIO(documento['contenido']))
            self.procesar_csv(df)
        else:
            QMessageBox.warning(self, "Error", "Documento no encontrado")

    def cargar_csv_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Seleccionar factura CSV", "", "CSV Files (*.csv)")
        if filepath:
            try:
                df = pd.read_csv(filepath)
                self.procesar_csv(df)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al leer archivo CSV: {str(e)}")

    def cargar_excel(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Seleccionar reporte GESLib", "", "Excel Files (*.xlsx *.xls)")
        if filepath:
            try:
                df = pd.read_excel(filepath)
                if not self.validar_encabezados(df.columns):
                    QMessageBox.warning(self, "Error", "El archivo no es un reporte GESLib válido")
                    return
                
                # Añadir columnas con 'cnt'
                cnt_columns = [col for col in df.columns if 'cnt' in col.lower()]
                df = df[['descripcion', 'precio', 'descuento', 'f_articulo', 'total'] + cnt_columns]
                
                # Limpiar ISBNs
                df['f_articulo'] = df['f_articulo'].apply(self.limpiar_isbn)
                
                self.mostrar_dataframe(self.tabla_geslib, df)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al leer archivo Excel: {str(e)}")


    def procesar_csv(self, df):
        # Crear el diálogo para selección de columnas
        dialog = QDialog(self)
        dialog.setWindowTitle("Previsualización y selección de columnas")
        dialog.setMinimumSize(600, 400)  # Tamaño de la ventana

        # Layout principal: QHBoxLayout para dividir en tercios
        main_layout = QHBoxLayout()
        dialog.setLayout(main_layout)

        # Primer tercio: Selección de columnas
        selection_layout = QVBoxLayout()

        # Función auxiliar para crear pares de QLabel y QComboBox
        def create_label_combo_pair(label_text, combo_box):
            pair_layout = QHBoxLayout()
            label = QLabel(label_text)
            pair_layout.addWidget(label)
            pair_layout.addWidget(combo_box)
            return pair_layout

        # Columna ISBN
        self.combo_isbn = QComboBox()
        self.combo_isbn.addItems(df.columns)
        selection_layout.addLayout(create_label_combo_pair("Ubique Columna ISBN:", self.combo_isbn))

        # Columna Cantidad
        self.combo_cantidad = QComboBox()
        self.combo_cantidad.addItems(df.columns)
        selection_layout.addLayout(create_label_combo_pair("Ubique Columna Cantidad:", self.combo_cantidad))

        # Columna Precio
        self.combo_precio = QComboBox()
        self.combo_precio.addItems(df.columns)
        selection_layout.addLayout(create_label_combo_pair("Ubique Columna PNT:", self.combo_precio))

        # Botón Aceptar
        btn_aceptar = QPushButton("Aceptar")
        btn_aceptar.clicked.connect(lambda: self.filtrar_csv(df, dialog))
        selection_layout.addWidget(btn_aceptar)

        # Advertencia del significado de PNT
        advertencia_label = QLabel("*PNT: Producto Neto Total")
        advertencia_label.setStyleSheet("font-style: italic; color: gray;")  # Estilo itálico y color gris
        selection_layout.addWidget(advertencia_label)

        # Agregar el layout de selección al primer tercio
        main_layout.addLayout(selection_layout, stretch=1)

        # Dos tercios restantes: Tabla de previsualización
        preview_layout = QVBoxLayout()

        # Crear una tabla para previsualizar el CSV
        preview_table = QTableWidget()
        preview_table.setRowCount(min(10, df.shape[0]))  # Mostrar máximo 10 filas
        preview_table.setColumnCount(df.shape[1])
        preview_table.setHorizontalHeaderLabels(df.columns)

        # Llenar la tabla con datos del DataFrame
        for i in range(min(10, df.shape[0])):
            for j in range(df.shape[1]):
                preview_table.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))

        preview_layout.addWidget(QLabel("Previsualización del archivo CSV:"))
        preview_layout.addWidget(preview_table)

        # Agregar el layout de previsualización a los dos tercios restantes
        main_layout.addLayout(preview_layout, stretch=2)

        # Mostrar el diálogo
        dialog.exec_()

    def filtrar_csv(self, df, dialog):
        col_isbn = self.combo_isbn.currentText()
        col_cantidad = self.combo_cantidad.currentText()

        # Validar ISBNs
        df['isbn_valid'] = df[col_isbn].apply(lambda x: self.validar_isbn(self.limpiar_isbn(str(x))))
        df_filtrado = df[df['isbn_valid']].copy()
        df_filtrado.drop(columns=['isbn_valid'], inplace=True)

        # Procesar la columna "cantidad"
        df_filtrado[col_cantidad] = df_filtrado[col_cantidad].apply(self.procesar_cantidad)

        # Eliminar filas con cantidad inválida (None)
        df_filtrado = df_filtrado[df_filtrado[col_cantidad].notna()]

        if len(df_filtrado) == 0:
            QMessageBox.warning(self, "Advertencia", "No se encontraron registros válidos después de procesar la columna 'cantidad'.")
            return

        # Mostrar el DataFrame filtrado en la tabla
        self.mostrar_dataframe(self.tabla_csv, df_filtrado)
        dialog.close()

    def validar_encabezados(self, columns):
        required = ['descripcion', 'precio', 'descuento', 'f_articulo', 'total']
        return all(col in columns for col in required)

    def limpiar_isbn(self, isbn):
        return re.sub(r'[^0-9X]', '', str(isbn).upper())

    def validar_isbn(self, isbn):
        return len(isbn) in (10, 13) and (isbn[:-1].isdigit() or (len(isbn) == 10 and isbn[-1] in ('X', 'x')))

    def mostrar_dataframe(self, tabla, df):
        tabla.setRowCount(df.shape[0])
        tabla.setColumnCount(df.shape[1])
        tabla.setHorizontalHeaderLabels(df.columns)
        
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                tabla.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))

    def comparar_tablas(self):
        """
        Compara las tablas cargadas y genera un análisis de congruencia.
        """
        # Verificar si las tablas están cargadas
        if self.tabla_geslib.rowCount() == 0 or self.tabla_csv.rowCount() == 0:
            QMessageBox.warning(
                self,
                "Tablas no cargadas",
                "Ambas tablas deben estar cargadas para realizar la comparación. Por favor, cargue los datos en ambas tablas."
            )
            return

        # Obtener los DataFrames de las tablas cargadas
        try:
            self.df_geslib = self.obtener_dataframe_desde_tabla(self.tabla_geslib)
            self.df_csv = self.obtener_dataframe_desde_tabla(self.tabla_csv)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron obtener los datos de las tablas: {str(e)}")
            return

        # Crear el DataFrame df_TotalAnalisis
        df_TotalAnalisis = self.generar_analisis_congruencia(self.df_geslib, self.df_csv)

        # Mostrar el resultado en una nueva ventana
        self.mostrar_resultado(df_TotalAnalisis)

    def obtener_dataframe_desde_tabla(self, tabla):
        """
        Convierte una QTableWidget en un DataFrame de pandas.
        """
        rows = tabla.rowCount()
        cols = tabla.columnCount()
        headers = [tabla.horizontalHeaderItem(i).text() for i in range(cols)]
        data = []
        for row in range(rows):
            data.append([tabla.item(row, col).text() for col in range(cols)])
        return pd.DataFrame(data, columns=headers)

    def generar_analisis_congruencia(self, df_geslib, df_csv):
        """
        Genera un análisis de congruencia entre los datos del reporte GESLib y la factura CSV.
        """
        # Datos del Reporte (Excel)
        report_isbn_col = self.df_geslib['f_articulo']
        report_pnt_col = self.df_geslib['total']

        # Si hay múltiples columnas con "cnt", pedir al usuario que seleccione una
        cnt_columns = [col for col in self.df_geslib.columns if 'cnt' in col.lower()]
        if len(cnt_columns) > 1:
            cnt_column, ok = QInputDialog.getItem(self, "Seleccionar columna", "Seleccione la columna de cantidad:", cnt_columns, 0, False)
            if not ok:
                return
        else:
            cnt_column = cnt_columns[0]
        report_cantidad_col = self.df_geslib[cnt_column]

        # Datos de la Factura (CSV)
        factura_isbn_col = self.df_csv[self.combo_isbn.currentText()]
        factura_cantidad_col = self.df_csv[self.combo_cantidad.currentText()]
        factura_pnt_col = self.df_csv[self.combo_precio.currentText()]

        # Obtener todos los ISBN únicos
        all_isbns = set(report_isbn_col).union(set(factura_isbn_col))

        # Procesar cada ISBN
        df_TotalAnalisis = pd.DataFrame(columns=[
            "ISBN",
            "Congruencia del ISBN",
            "Aparición en Reporte",
            "Aparición en Factura",
            "Congruencia de cantidad",
            "Congruencia de PNT",
            "Notas"
        ])

        for isbn in all_isbns:
            report_appears = 1 if isbn in report_isbn_col.values else 0
            factura_appears = 1 if isbn in factura_isbn_col.values else 0
            congruencia_isbn = 1 if report_appears and factura_appears else 0

            # Obtener cantidades y PNT
            report_cantidad = self.limpiar_y_formatear_numero(report_cantidad_col[report_isbn_col == isbn].values[0]) if report_appears else None
            factura_cantidad = self.limpiar_y_formatear_numero(factura_cantidad_col[factura_isbn_col == isbn].values[0]) if factura_appears else None
            report_pnt = self.limpiar_y_formatear_numero(report_pnt_col[report_isbn_col == isbn].values[0]) if report_appears else None
            factura_pnt = self.limpiar_y_formatear_numero(factura_pnt_col[factura_isbn_col == isbn].values[0]) if factura_appears else None

            # Congruencia de cantidad y PNT
            congruencia_cantidad = 1 if report_cantidad == factura_cantidad else 0
            congruencia_pnt = 1 if report_pnt == factura_pnt else 0

            # Generar notas
            notas = []
            if congruencia_isbn and congruencia_cantidad and congruencia_pnt:
                notas.append("La congruencia es correcta")
            else:
                if not congruencia_isbn:
                    if not report_appears:
                        notas.append("El ISBN no aparece en el reporte")
                    if not factura_appears:
                        notas.append("El ISBN no aparece en la factura")
                if not congruencia_cantidad:
                    notas.append(f"Existe una diferencia en cantidad: CR = {report_cantidad} ; CF = {factura_cantidad}")
                if not congruencia_pnt:
                    notas.append(f"Existe una diferencia de PNT: PNR = {report_pnt} ; PNF = {factura_pnt}")

            # Concatenar todas las notas con "; "
            notas_concatenadas = "; ".join(notas)

            # Agregar fila al DataFrame
            new_row = {
                "ISBN": isbn,
                "Congruencia del ISBN": congruencia_isbn,
                "Aparición en Reporte": report_appears,
                "Aparición en Factura": factura_appears,
                "Congruencia de cantidad": congruencia_cantidad,
                "Congruencia de PNT": congruencia_pnt,
                "Notas": notas_concatenadas
            }
            df_TotalAnalisis = pd.concat([df_TotalAnalisis, pd.DataFrame([new_row])], ignore_index=True)

        return df_TotalAnalisis

    def mostrar_resultado(self, df):
        """
        Muestra los resultados de la comparación en una nueva ventana.
        """
        result_dialog = QDialog(self)
        result_dialog.setWindowTitle("Reporte de Incongruencias")
        result_dialog.setMinimumSize(1200, 600)

        layout = QVBoxLayout()
        result_dialog.setLayout(layout)

        table = QTableWidget()
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns)

        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                table.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))

        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        layout.addWidget(table)

        btn_generar_reporte = QPushButton("Generar Reporte")
        btn_generar_reporte.clicked.connect(lambda: self.generar_reporte(df))
        layout.addWidget(btn_generar_reporte)

        result_dialog.exec_()

    def generar_reporte(self, df):
        """
        Genera un reporte según el tipo de congruencia detectada.
        """
        if df[["Congruencia del ISBN", "Aparición en Reporte", "Aparición en Factura", 
            "Congruencia de cantidad", "Congruencia de PNT"]].all().all():
            self.generar_reporte_tipo_1()
        elif df["Congruencia del ISBN"].all():
            self.generar_reporte_tipo_2(df)
        else:
            self.generar_reporte_tipo_3(df)

    def mostrar_resultado(self, df):
        # Crear la ventana de resultados
        result_dialog = QDialog(self)
        result_dialog.setWindowTitle("Reporte de Incongruencias")
        result_dialog.setMinimumSize(1200, 600)  # Nuevas dimensiones: 1200x600

        # Layout principal
        layout = QVBoxLayout()
        result_dialog.setLayout(layout)

        # Crear la tabla
        table = QTableWidget()
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels([
            "ISBN",
            "Congruencia del ISBN",
            "Aparición en Reporte",
            "Aparición en Factura",
            "Congruencia de cantidad",
            "Congruencia de PNT",
            "Notas"
        ])

        # Llenar la tabla con los datos del DataFrame
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                table.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))

        # Ajustar el ancho de las columnas según el contenido más largo
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        layout.addWidget(table)

        btn_generar_reporte = QPushButton("Generar Reporte")
        btn_generar_reporte.clicked.connect(lambda: self.generar_reporte(df))
        layout.addWidget(btn_generar_reporte)

        # Mostrar la ventana
        result_dialog.exec_()

    def limpiar_y_formatear_numero(self, valor):
        """
        Limpia y formatea un valor numérico para asegurar un formato estándar.
        Ejemplo: 000000.0000
        """
        try:
            # Eliminar caracteres no numéricos excepto el punto decimal
            valor_limpio = re.sub(r'[^0-9.]', '', str(valor))
            
            # Convertir a float
            numero = float(valor_limpio)
            
            print(f"Se ejecuto limpiar y formatear numero en {valor_limpio}, se obtuvo {numero}")

            # Formatear con 4 decimales
            return f"{numero:.4f}"
        except ValueError:
            # Si no se puede convertir, registrar el error y devolver un valor predeterminado
            print(f"Error al limpiar y formatear el valor: '{valor}'")
            return "0.0000"
        
    def procesar_cantidad(self, valor):
        """
        Procesa el valor de la columna "cantidad" para asegurar que tenga el formato correcto.
        - Si el valor es un número entero, lo devuelve como entero.
        - Si el valor contiene varios números separados por espacios, extrae el primer número.
        - Si el valor no es válido, muestra una advertencia y devuelve None.
        """
        try:
            # Dividir el valor por espacios
            partes = str(valor).strip().split()
            
            if not partes:  # Verificar si la lista está vacía
                QMessageBox.warning(
                    self,
                    "Advertencia",
                    f"El valor '{valor}' en la columna 'cantidad' está vacío."
                )
                return None
            
            # Verificar si hay múltiples partes
            if len(partes) > 1:
                # Mostrar advertencia al usuario sobre el uso del primer número
                QMessageBox.information(
                    self,
                    "Advertencia",
                    f"Se encontró un valor con múltiples números: '{valor}'. "
                    f"Se usará solo el primer número: {partes[0]}"
                )
            
            # Convertir el primer elemento a entero
            return int(partes[0])
        
        except ValueError:
            # Si no se puede convertir a entero, mostrar advertencia
            QMessageBox.warning(
                self,
                "Error",
                f"El valor '{valor}' en la columna 'cantidad' no es un número válido."
            )
            return None
        
    def generar_reporte_tipo_1(self):
        try:
            # Verificar si la columna 'cnt' existe
            cnt_columns = [col for col in self.df_geslib.columns if 'cnt' in col.lower()]
            if not cnt_columns:
                print("Columnas disponibles en df_geslib:")
                print(self.df_geslib.head())
                raise KeyError("No se encontró ninguna columna de cantidad ('cnt') en el reporte.")

            # Usar la primera columna 'cnt' disponible
            cnt_column = cnt_columns[0]
            cantidad_total = self.df_geslib[cnt_column]
            cantidad_total = pd.to_numeric(cantidad_total, errors = 'coerce')
            cantidad_total = cantidad_total.sum()
            print(f"cantidad_total: {cantidad_total}")

            # Calcular precio neto total
            precio_neto_total = self.df_geslib['total']
            precio_neto_total = pd.to_numeric(precio_neto_total, errors= 'coerce')
            precio_neto_total = precio_neto_total.sum()
            print(f"precio_neto_total: {precio_neto_total}")
            precio_neto_total_formateado = f"${precio_neto_total:,.2f}"

            # Preparar datos para la tabla
            datos_tabla = []
            for _, row in self.df_geslib.iterrows():
                datos_tabla.append({
                    "ISBN": row['f_articulo'],
                    "CANTIDAD": row[cnt_column],
                    "PRECIO NETO": row['total']
                })

            # Definir elementos del cuerpo del reporte
            elementos = [
                {"tipo": "texto", "contenido": "**El reporte y la factura analizados tienen los mismos datos**"},
                {"tipo": "tabla", "datos": datos_tabla, "columnas": ["ISBN", "CANTIDAD", "PRECIO NETO"]},
                {"tipo": "texto", "contenido": f"Cantidad Total: {cantidad_total} | Precio Neto Total: {precio_neto_total_formateado}"}
            ]

            # Generar el PDF
            titulo_reporte = "Resultados de congruencia"
            reporte = Reporte()
            filename = "reporte_congruencia_completa.pdf"
            reporte.generar_pdf(filename, titulo_reporte, elementos, save_dialog=True)

        except KeyError as e:
            QMessageBox.warning(self, "Error", f"Error al generar el reporte: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error inesperado: {str(e)}")

    def generar_reporte_tipo_2(self, df_total_analisis):
        # Filtrar registros con incongruencias
        df_incongruencias = df_total_analisis[
            (df_total_analisis["Congruencia de cantidad"] == 0) |
            (df_total_analisis["Congruencia de PNT"] == 0)
        ]

        # Preparar datos para la tabla
        datos_tabla = []
        for _, row in df_incongruencias.iterrows():
            datos_tabla.append({
                "ISBN": row["ISBN"],
                "C. CANTIDAD": "Congruente" if row["Congruencia de cantidad"] == 1 else "Incongruente",
                "C. PNT": "Congruente" if row["Congruencia de PNT"] == 1 else "Incongruente",
                "NOTAS": row["Notas"]
            })

        # Definir elementos del cuerpo del reporte
        elementos = [
            {"tipo": "tabla", "datos": datos_tabla, "columnas": ["ISBN", "C. CANTIDAD", "C. PNT", "NOTAS"]}
        ]

        # Generar el PDF
        titulo_reporte = "Resultados de congruencia: Incongruencias numéricas existentes"
        reporte = Reporte()
        filename = "reporte_incongruencias_numericas.pdf"
        reporte.generar_pdf(filename, titulo_reporte, elementos, save_dialog=True)
    
    def generar_reporte_tipo_3(self, df_total_analisis):
        # Filtrar registros con Congruencia del ISBN == 1
        #df_congruentes = df_total_analisis[df_total_analisis["Congruencia del ISBN"] == 1]

        # Preparar datos para la tabla
        datos_tabla = []
        df_congruentes = df_total_analisis
        for _, row in df_congruentes.iterrows():
            s_reporte = "OK" if row["Aparición en Reporte"] == 1 else "N/A"
            s_factura = "OK" if row["Aparición en Factura"] == 1 else "N/A"
            cantidad = "-" if s_reporte == "N/A" or s_factura == "N/A" else \
                ("Congruente" if row["Congruencia de cantidad"] == 1 else "Incongruente")
            precio_neto = "-" if s_reporte == "N/A" or s_factura == "N/A" else \
                ("Congruente" if row["Congruencia de PNT"] == 1 else "Incongruente")

            datos_tabla.append({
                "ISBN": row["ISBN"],
                "S. REPORTE": s_reporte,
                "S. FACTURA": s_factura,
                "CANTIDAD": cantidad,
                "PRECIO NETO": precio_neto,
                "NOTAS": row["Notas"]
            })

        # Definir elementos del cuerpo del reporte
        elementos = [
            {"tipo": "tabla", "datos": datos_tabla, "columnas": ["ISBN", "S. REPORTE", "S. FACTURA", "CANTIDAD", "PRECIO NETO", "NOTAS"]}
        ]

        # Generar el PDF
        titulo_reporte = "Resultados de congruencia: Múltiples incongruencias existentes"
        reporte = Reporte(margins=(50, 50, 70, 50), orientation="horizontal")  # Márgenes ajustados para hoja horizontal
        filename = "reporte_multiples_incongruencias.pdf"
        reporte.generar_pdf(filename, titulo_reporte, elementos, save_dialog=True)