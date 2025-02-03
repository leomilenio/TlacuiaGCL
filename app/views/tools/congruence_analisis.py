from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QLabel, 
                             QComboBox, QTableWidget, QTableWidgetItem,
                             QListWidgetItem, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from app.models.database import ConcesionesDB
from app.models.json_extract import extract_version_from_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
import pandas as pd
import requests
import os
import re
import io

class AnalizadorCongruencias(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = ConcesionesDB()  # Instancia de la base de datos
        self.documentos_seleccionados = []  # Lista de documentos seleccionados
        self.tabla_1_data = None
        self.tabla_2_data = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Analizador de Congruencias")
        self.setGeometry(200, 200, 1000, 800)  # Ventana más grande

        layout = QVBoxLayout()

        # Etiqueta de instrucciones
        layout.addWidget(QLabel("Seleccione dos documentos CSV de una concesión activa."))

        # Paso 1: Seleccionar concesión
        self.concesion_list = QListWidget()
        self.concesion_list.itemClicked.connect(self.cargar_documentos_csv)
        layout.addWidget(QLabel("Concesiones Activas:"))
        layout.addWidget(self.concesion_list)

        # Paso 2: Seleccionar documentos
        self.documento_list = QListWidget()
        self.documento_list.setSelectionMode(QListWidget.MultiSelection)
        self.documento_list.itemSelectionChanged.connect(self.seleccionar_documentos)
        layout.addWidget(QLabel("Documentos Disponibles (CSV):"))
        layout.addWidget(self.documento_list)

        # Paso 3: Mostrar tablas seleccionadas
        self.tabla_1_widget = QTableWidget()
        self.tabla_2_widget = QTableWidget()

        layout.addWidget(QLabel("Tabla 1:"))
        layout.addWidget(self.tabla_1_widget)
        layout.addWidget(QLabel("Tabla 2:"))
        layout.addWidget(self.tabla_2_widget)

        # Paso 4: Seleccionar columnas con ISBN
        self.columna_selector_1 = QComboBox()
        self.columna_selector_2 = QComboBox()
        layout.addWidget(QLabel("Columna con ISBN (Tabla 1):"))
        layout.addWidget(self.columna_selector_1)
        layout.addWidget(QLabel("Columna con ISBN (Tabla 2):"))
        layout.addWidget(self.columna_selector_2)

        # Botón para iniciar análisis
        btn_analizar = QPushButton("Analizar Congruencias")
        btn_analizar.clicked.connect(self.analizar_congruencias)
        layout.addWidget(btn_analizar)

        # Resultados
        self.result_table = QTableWidget()
        layout.addWidget(QLabel("Resultados:"))
        layout.addWidget(self.result_table)

        self.setLayout(layout)

        # Cargar concesiones activas
        self.cargar_concesiones_activas()

    def cargar_concesiones_activas(self):
        """Carga las concesiones activas con documentos vinculados."""
        concesiones = self.db.obtener_concesiones_no_finalizadas_con_emisor()
        for concesion in concesiones:
            item = QListWidgetItem(f"{concesion['nombre_emisor']} - Folio: {concesion['folio']}")
            item.setData(Qt.UserRole, concesion['id'])
            self.concesion_list.addItem(item)

    def cargar_documentos_csv(self, item):
        """Carga los documentos asociados a la concesión seleccionada, filtrando solo CSV."""
        concesion_id = item.data(Qt.UserRole)
        documentos = self.db.obtener_documentos(concesion_id)
        self.documento_list.clear()
        for doc in documentos:
            if doc[3] == 'CSV':  # Filtrar solo documentos CSV
                item = QListWidgetItem(f"{doc[2]} ({doc[3]})")
                item.setData(Qt.UserRole, doc[0])
                self.documento_list.addItem(item)

    def seleccionar_documentos(self):
        """Guarda los documentos seleccionados y muestra sus tablas."""
        selected_items = self.documento_list.selectedItems()
        if len(selected_items) == 2:
            self.documentos_seleccionados = [item.data(Qt.UserRole) for item in selected_items]
            QMessageBox.information(self, "Éxito", "Documentos seleccionados correctamente.")
            self.cargar_tablas_seleccionadas()
        else:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar exactamente dos documentos.")

    def cargar_tablas_seleccionadas(self):
        """Carga y muestra las tablas de los documentos seleccionados."""
        self.tabla_1_data = self.leer_csv_desde_documento(self.documentos_seleccionados[0])
        self.tabla_2_data = self.leer_csv_desde_documento(self.documentos_seleccionados[1])

        self.mostrar_tabla(self.tabla_1_widget, self.tabla_1_data)
        self.mostrar_tabla(self.tabla_2_widget, self.tabla_2_data)

        # Configurar selectores de columna
        self.columna_selector_1.clear()
        self.columna_selector_1.addItems(self.tabla_1_data.columns)
        self.columna_selector_2.clear()
        self.columna_selector_2.addItems(self.tabla_2_data.columns)

    def leer_csv_desde_documento(self, doc_id):
        """Lee un archivo CSV desde un documento en la base de datos."""
        documento = self.db.obtener_documento_por_id(doc_id)
        contenido = documento['contenido']
        return pd.read_csv(io.BytesIO(contenido))

    def mostrar_tabla(self, tabla_widget, data):
        """Muestra una tabla en un QTableWidget."""
        tabla_widget.setRowCount(data.shape[0])
        tabla_widget.setColumnCount(data.shape[1])
        tabla_widget.setHorizontalHeaderLabels(data.columns)
        tabla_widget.setEditTriggers(QTableWidget.NoEditTriggers)  # No editable

        for row in range(data.shape[0]):
            for col in range(data.shape[1]):
                item = QTableWidgetItem(str(data.iat[row, col]))
                tabla_widget.setItem(row, col, item)

    def analizar_congruencias(self):
        """Analiza las congruencias entre los documentos seleccionados."""
        if len(self.documentos_seleccionados) != 2:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar dos documentos para analizar.")
            return

        # Obtener columnas seleccionadas
        columna_1 = self.columna_selector_1.currentText()
        columna_2 = self.columna_selector_2.currentText()

        # Extraer ISBNs
        isbn_list_1 = self.extraer_isbn(self.tabla_1_data[columna_1])
        isbn_list_2 = self.extraer_isbn(self.tabla_2_data[columna_2])

        # Comparar ISBNs
        resultados = self.comparar_isbn(isbn_list_1, isbn_list_2)

        # Mostrar resultados en la tabla
        self.mostrar_resultados(resultados)

        # Generar PDF
        self.generar_pdf(resultados)

    def extraer_isbn(self, columna):
        """Extrae números ISBN válidos de una columna."""
        isbn_list = []
        for value in columna:
            isbn = self.limpiar_isbn(str(value))
            if isbn and self.validar_isbn(isbn):
                isbn_list.append(isbn)
        return isbn_list

    def limpiar_isbn(self, texto):
        """Limpia un número ISBN eliminando guiones y otros caracteres no numéricos."""
        return re.sub(r'[^0-9X]', '', texto.upper())

    def validar_isbn(self, isbn):
        """Valida si un número ISBN tiene 10 o 13 dígitos."""
        return len(isbn) in (10, 13)

    def comparar_isbn(self, isbn_list_1, isbn_list_2):
        """Compara dos listas de ISBN y devuelve los resultados."""
        resultados = []
        for isbn in set(isbn_list_1 + isbn_list_2):
            en_tabla_1 = isbn in isbn_list_1
            en_tabla_2 = isbn in isbn_list_2
            estado = "Congruente" if en_tabla_1 and en_tabla_2 else "No congruente"
            resultados.append({
                "ISBN": isbn,
                "Tabla 1": "Sí" if en_tabla_1 else "No",
                "Tabla 2": "Sí" if en_tabla_2 else "No",
                "Estado": estado
            })
        return resultados

    def mostrar_resultados(self, resultados):
        """Muestra los resultados en una tabla."""
        self.result_table.setRowCount(len(resultados))
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["ISBN", "Tabla 1", "Tabla 2", "Estado"])

        for row, resultado in enumerate(resultados):
            self.result_table.setItem(row, 0, QTableWidgetItem(resultado["ISBN"]))
            self.result_table.setItem(row, 1, QTableWidgetItem(resultado["Tabla 1"]))
            self.result_table.setItem(row, 2, QTableWidgetItem(resultado["Tabla 2"]))
            estado_item = QTableWidgetItem(resultado["Estado"])
            if resultado["Estado"] == "No congruente":
                estado_item.setBackground(QColor("red"))
            self.result_table.setItem(row, 3, estado_item)

    def generar_pdf(self, resultados):
        """Genera un PDF con los resultados del análisis."""
        reply = QMessageBox.question(
        self,
        "Buscar Títulos",
        "¿Desea intentar buscar los títulos correspondientes a los ISBN?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
        )

            # Buscar títulos si el usuario selecciona "Sí"
        if reply == QMessageBox.Yes:
            for resultado in resultados:
                isbn = resultado["ISBN"]
                titulo = self.buscar_titulo_por_isbn(isbn)
                resultado["Titulo"] = titulo
        else:
            for resultado in resultados:
                resultado["Titulo"] = ""

            
        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF", "", "PDF (*.pdf)")

        if not filename:
            return

        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        file_path = os.path.join(base_path, 'models', 'dev_info.json')

        metadata_version = extract_version_from_file(file_path)
        version = metadata_version.get('version', 'desconocida')

        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        y = height - 50

        # Encabezado
        y = height - 25
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"Tlacuia GCL {version}")
        y -= 15
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Reporte de Análisis de Congruencias")
        y -= 15

        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        y -= 30

        # Columnas
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, "ISBN")
        c.drawString(150, y, "T1")
        c.drawString(250, y, "T2")
        c.drawString(350, y, "Estado")
        c.drawString(450, y, "Título")
        y -= 20

        # Datos
        c.setFont("Helvetica", 10)
        for resultado in resultados:
            c.drawString(50, y, resultado["ISBN"])
            c.drawString(150, y, resultado["Tabla 1"])
            c.drawString(250, y, resultado["Tabla 2"])
            c.drawString(350, y, resultado["Estado"])

            # Ajustar el título para que ocupe hasta 2 líneas
            titulo = resultado["Titulo"]
            if titulo:
                if len(titulo) > 30:  # Dividir el título si es demasiado largo
                    line1 = titulo[:30]
                    line2 = titulo[30:]
                    c.drawString(450, y, line1)
                    y -= 10
                    c.drawString(450, y, line2)
                else:
                    c.drawString(450, y, titulo)
            else:
                c.drawString(450, y, "")  # Dejar celda vacía si no hay título


            y -= 20

            if y < 50:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica-Bold", 10)
                c.drawString(50, y, "ISBN")
                c.drawString(150, y, "T1")
                c.drawString(250, y, "T2")
                c.drawString(350, y, "Estado")
                c.drawString(450, y, "Título")
                y -= 20
                c.setFont("Helvetica", 10)

        # Advertencia sobre el uso de la API de Google Books
        c.setFont("Helvetica-Oblique", 8)
        advertencia = (
            "* Nota: Este reporte utiliza la API de Google Books y Open Library para identificar "
            "los títulos correspondientes a los ISBN. Los resultados pueden contener "
            "errores debido a limitaciones en la precisión de la API."
        )
        advertencia_lines = self.dividir_texto_en_lineas(advertencia, 100)  # Dividir en líneas de máximo 100 caracteres
        y -= 20
        for line in advertencia_lines:
            c.drawCentredString(width / 2, y, line)  # Centrar el texto horizontalmente
            y -= 10

        c.save()

        QMessageBox.information(self, "Éxito", "PDF generado correctamente.")

    def dividir_texto_en_lineas(self, texto, max_chars):
        """Divide un texto en líneas de longitud máxima especificada."""
        palabras = texto.split()
        lineas = []
        linea_actual = ""
        for palabra in palabras:
            if len(linea_actual) + len(palabra) + 1 <= max_chars:
                linea_actual += (" " + palabra if linea_actual else palabra)
            else:
                lineas.append(linea_actual)
                linea_actual = palabra
        if linea_actual:
            lineas.append(linea_actual)
        return lineas


    def buscar_titulo_por_isbn(self, isbn):
        """Busca el título de un libro usando múltiples APIs gratuitas."""
        # Intentar con Google Books primero
        google_books_title = self.buscar_titulo_por_isbn_google_books(isbn)
        if google_books_title != "Título no encontrado":
            return google_books_title

        # Si Google Books no encuentra el título, intentar con Open Library
        open_library_title = self.buscar_titulo_por_isbn_open_library(isbn)
        if open_library_title != "Título no encontrado":
            return open_library_title

        # Si ninguna API encuentra el título, devolver "Título no encontrado"
        return "Título no encontrado"

    def buscar_titulo_por_isbn_google_books(self, isbn):
        """Busca el título de un libro usando la API de Google Books."""
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("items"):
                    return data["items"][0]["volumeInfo"].get("title", "Título no encontrado")
            return "Título no encontrado"
        except Exception as e:
            print(f"Error al buscar título para ISBN {isbn} en Google Books: {str(e)}")
            return "Título no encontrado"

    def buscar_titulo_por_isbn_open_library(self, isbn):
        """Busca el título de un libro usando la API de Open Library."""
        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                key = f"ISBN:{isbn}"
                if key in data and "title" in data[key]:
                    return data[key]["title"]
            return "Título no encontrado"
        except Exception as e:
            print(f"Error al buscar título para ISBN {isbn} en Open Library: {str(e)}")
            return "Título no encontrado"
