import os
from datetime import datetime
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from PyQt5.QtWidgets import (QMessageBox, QFileDialog)
from app.models.json_extract import extract_version_from_file


class Reporte:
    def __init__(self, app_name="Tlacuia GCL", margins=(50, 50, 50, 50), orientation="vertical"):
        """
        Inicializa la clase Reporte.
        :param app_name: Nombre de la aplicación.
        :param margins: Tupla con los márgenes (izquierdo, derecho, superior, inferior).
        :param orientation: Orientación del reporte ("vertical" o "horizontal").
        """
        self.app_name = app_name
        self.margins = margins  # Márgenes: izquierdo, derecho, superior, inferior
        self.orientation = orientation  # Orientación del reporte
        # Extraer la versión desde el archivo JSON
        current_file_path = os.path.abspath(__file__)  # Ruta absoluta del archivo actual
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))  # Subir tres niveles hasta /TlacuiaGCL
        
        # Construir la ruta al archivo JSON
        file_path = os.path.join(base_path, 'app', 'models', 'dev_info.json')
        
        # Directorio donde se encuentra report_generator.py
        utils_dir = os.path.dirname(current_file_path)
        # Ruta a la carpeta 'fonts' dentro de 'utils'
        fonts_dir = os.path.join(utils_dir, 'fonts')


        # Registrar las variantes de la fuente usando rutas absolutas
        pdfmetrics.registerFont(TTFont('OfficeCodePro-Regular', os.path.join(fonts_dir, 'OfficeCodePro-Regular.ttf')))
        pdfmetrics.registerFont(TTFont('OfficeCodePro-Italic', os.path.join(fonts_dir, 'OfficeCodePro-RegularItalic.ttf')))
        pdfmetrics.registerFont(TTFont('OfficeCodePro-Bold', os.path.join(fonts_dir, 'OfficeCodePro-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('OfficeCodePro-BoldItalic', os.path.join(fonts_dir, 'OfficeCodePro-BoldItalic.ttf')))
        pdfmetrics.registerFont(TTFont('OfficeCodePro-Light', os.path.join(fonts_dir, 'OfficeCodePro-Light.ttf')))
        pdfmetrics.registerFont(TTFont('OfficeCodePro-LightItalic', os.path.join(fonts_dir, 'OfficeCodePro-LightItalic.ttf')))
        pdfmetrics.registerFont(TTFont('OfficeCodePro-Medium', os.path.join(fonts_dir, 'OfficeCodePro-Medium.ttf')))
        pdfmetrics.registerFont(TTFont('OfficeCodePro-MediumItalic', os.path.join(fonts_dir, 'OfficeCodePro-MediumItalic.ttf')))

        # Registrar la familia de fuentes
        pdfmetrics.registerFontFamily('OfficeCodePro',
            normal='OfficeCodePro-Regular',
            bold='OfficeCodePro-Bold',
            italic='OfficeCodePro-Italic',
            boldItalic='OfficeCodePro-BoldItalic'
        )

        print(f"Ruta generada para dev_info.json: {file_path}")
        if not os.path.exists(file_path):
            print(f"El archivo no existe en la ruta: {file_path}")
        else:
            print("El archivo existe.")
        try:
            metadata = extract_version_from_file(file_path)
            self.version = metadata.get('version', 'desconocida')
        except Exception as e:
            print(f"Error al leer el archivo JSON: {str(e)}")
            self.version = "version desconocida"

    def generar_pdf(self, filename=None, titulo_reporte="", elementos=None, advertencias=None, save_dialog=False):
        """
        Genera un PDF con los resultados del análisis.
        :param filename: Ruta donde se guardará el archivo PDF. Si es None y save_dialog es True, se abrirá un cuadro de diálogo.
        :param titulo_reporte: Título del reporte.
        :param elementos: Lista de elementos del cuerpo del documento (tablas, texto, imágenes).
        :param advertencias: Texto opcional para el pie de página.
        :param save_dialog: Booleano que indica si se debe abrir un cuadro de diálogo para seleccionar la ubicación y nombre del archivo.
        """
        try:
            if save_dialog:
                filename, _ = QFileDialog.getSaveFileName(
                    None, "Guardar PDF", "", "PDF (*.pdf)"
                )
                if not filename:
                    QMessageBox.warning(None, "Cancelado", "La operación fue cancelada por el usuario.")
                    return

            # Determinar el tamaño de página según la orientación
            if self.orientation == "horizontal":
                pagesize = landscape(letter)
            else:
                pagesize = letter
            c = canvas.Canvas(filename, pagesize=pagesize)
            width, height = pagesize
            left_margin, right_margin, top_margin, bottom_margin = self.margins

            # Inicializar posición vertical y contador de páginas
            y = height - top_margin
            page_number = 1

            # Encabezado
            y = self._dibujar_encabezado(c, width, height)

            # Título del reporte
            y -= 10
            c.setFont("OfficeCodePro-Bold", 14)
            c.drawString(left_margin, y, titulo_reporte)
            y -= 20

            # Dibujar elementos del cuerpo
            for idx, elemento in enumerate(elementos or []):
                print(f"--- Procesando elemento {idx+1} de {len(elementos)} ---")
                tipo = elemento.get("tipo")
                if tipo == "tabla":
                    y, page_number = self._dibujar_tabla(
                        c, y, elemento["datos"], elemento["columnas"], width, height, bottom_margin, page_number
                    )
                elif tipo == "texto":
                    y = self._dibujar_texto(c, y, elemento["contenido"], width, bottom_margin)
                elif tipo == "imagen":
                    y = self._dibujar_imagen(c, y, elemento["ruta"], elemento["ancho"], elemento["alto"], width, bottom_margin)

                # Manejo de paginación
                if y < bottom_margin:
                    print(f"Paginación detectada: y={y}, bottom_margin={bottom_margin}")
                    self._dibujar_pie_de_pagina(c, width, bottom_margin, page_number)
                    c.showPage()
                    page_number += 1
                    y = height - top_margin
                    self._dibujar_encabezado(c, width, height)

            # Dibujar el pie de página en la última página
            self._dibujar_pie_de_pagina(c, width, bottom_margin, page_number)

            # Guardar el PDF
            c.save()
            QMessageBox.information(None, "Éxito", "PDF generado correctamente.")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"No se pudo generar el PDF: {str(e)}")

    def _dibujar_pie_de_pagina(self, c, width, bottom_margin, page_number):
        try:
            print(f"Se ha llamado a _dibujar_pie_de_pagina con la pag. {page_number}")
            c.setFont("OfficeCodePro-Regular", 8)
            c.drawCentredString(width / 2, bottom_margin - 10, f"Página {page_number}")
        except Exception as e: 
            print(f"Ocurrio un error en dibujar pie de pagina: {e}")


    def _dibujar_encabezado(self, c, width, height):
        """
        Dibuja el encabezado del reporte.
        :param c: Objeto Canvas de ReportLab.
        :param width: Ancho de la página.
        :param height: Altura de la página.
        :return: Posición vertical actualizada después del encabezado.
        """
        _, _, top_margin, _ = self.margins
        y = height - top_margin
        c.setFont("OfficeCodePro-Bold", 12)
        c.drawString(50, y, f"{self.app_name} {self.version}")
        y -= 15
        c.setFont("OfficeCodePro-Regular", 10)
        c.drawString(50, y, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        return y - 20

    def _dibujar_tabla(self, c, y, datos, columnas, width, height, bottom_margin, page_number):
        """
        Dibuja una tabla en el PDF con soporte para paginación.
        :param c: Objeto Canvas de ReportLab.
        :param y: Posición vertical actual.
        :param datos: Lista de diccionarios con los datos de la tabla.
        :param columnas: Lista de nombres de columnas.
        :param width: Ancho de la página.
        :param bottom_margin: Margen inferior.
        :param page_number: Número de página actual.
        :return: Posición vertical actualizada después de la tabla.
        """
        left_margin, right_margin, top_margin, _ = self.margins  # Extraer márgenes
        x_offset = left_margin

        # Función auxiliar para dibujar encabezados
        def dibujar_encabezados(y):
            nonlocal x_offset
            x_offset = left_margin
            c.setFont("OfficeCodePro-Bold", 10)
            for columna in columnas:
                c.drawString(x_offset, y, columna)
                x_offset += 100
            return y - 20  # Espacio adicional después de los encabezados

        # Dibujar encabezados iniciales
        y = dibujar_encabezados(y)

        # Iterar sobre las filas de datos
        fila_index = 0
        while fila_index < len(datos):
            fila = datos[fila_index]

            # Verificar si hay espacio suficiente para dibujar una fila
            if y < bottom_margin:
                print(f"Paginación detectada: y={y}, bottom_margin={bottom_margin}")
                # Dibujar el pie de página antes de crear una nueva página
                self._dibujar_pie_de_pagina(c, width, bottom_margin, page_number)
                c.showPage()  # Crear una nueva página
                page_number += 1  # Incrementar el contador de páginas
                y = height - top_margin  # Reiniciar posición vertical
                y = self._dibujar_encabezado(c, width, height)  # Dibujar encabezado de página
                y -= 20  # Dejar espacio entre el encabezado de la página y la tabla
                y = dibujar_encabezados(y)  # Dibujar encabezados de la tabla

            # Dibujar los datos de la fila
            x_offset = left_margin
            c.setFont("OfficeCodePro-Regular", 10)
            for columna in columnas:
                valor = fila.get(columna, "")
                if isinstance(valor, str) and len(valor) > 30:
                    line1 = valor[:30]
                    line2 = valor[30:]
                    c.drawString(x_offset, y, line1)
                    y -= 10
                    c.drawString(x_offset, y, line2)
                else:
                    c.drawString(x_offset, y, str(valor))
                x_offset += 100

            y -= 20  # Reducir la posición vertical después de dibujar una fila
            fila_index += 1

        return y, page_number  # Devolver la posición vertical actualizada y el número de página

    def _dibujar_texto(self, c, y, contenido, width, bottom_margin):
        """
        Dibuja un bloque de texto en el PDF.
        :param c: Objeto Canvas de ReportLab.
        :param y: Posición vertical actual.
        :param contenido: Texto a dibujar.
        :param width: Ancho de la página.
        :param bottom_margin: Margen inferior.
        :return: Posición vertical actualizada después del texto.
        """
        left_margin, right_margin, _, _ = self.margins
        max_chars = width - left_margin - right_margin
        lineas = self._dividir_texto_en_lineas(contenido, max_chars)
        c.setFont("OfficeCodePro-Regular", 10)

        for linea in lineas:
            c.drawString(left_margin, y, linea)
            y -= 15

            # Manejo de paginación
            if y < bottom_margin:
                return y  # Dejar que el llamador maneje la paginación

        return y

    def _dibujar_imagen(self, c, y, ruta, ancho, alto, width, bottom_margin):
        """
        Dibuja una imagen en el PDF.
        :param c: Objeto Canvas de ReportLab.
        :param y: Posición vertical actual.
        :param ruta: Ruta de la imagen.
        :param ancho: Ancho de la imagen.
        :param alto: Alto de la imagen.
        :param width: Ancho de la página.
        :param bottom_margin: Margen inferior.
        :return: Posición vertical actualizada después de la imagen.
        """
        left_margin, _, _, _ = self.margins
        c.drawImage(ruta, left_margin, y - alto, width=ancho, height=alto)
        y -= alto + 10  # Espacio adicional debajo de la imagen

        # Manejo de paginación
        if y < bottom_margin:
            return y  # Dejar que el llamador maneje la paginación

        return y

    def _dividir_texto_en_lineas(self, texto, max_chars):
        """
        Divide un texto en líneas de longitud máxima especificada.
        :param texto: Texto a dividir.
        :param max_chars: Máximo número de caracteres por línea.
        :return: Lista de líneas.
        """
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