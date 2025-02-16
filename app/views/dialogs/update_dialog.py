from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox, QTextEdit
from PyQt5.QtGui import QFontDatabase
import requests
import json
import os
from packaging.version import parse, InvalidVersion
from app.models.json_extract import extract_version_from_file


class UpdateDialog(QDialog):
    def __init__(self, version_actual, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscar Actualizaciones")
        self.setGeometry(200, 200, 500, 300)
        self.url = "https://raw.githubusercontent.com/leomilenio/TlacuiaGCL/master/app/models/dev_info.json"
        
        # Obtener la versión actual antes de inicializar la interfaz
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        file_path = os.path.join(base_path, 'app', 'models', 'dev_info.json')
        self.version_actual = extract_version_from_file(file_path).get('version', 'desconocida')
        self.release_notes_actual = extract_version_from_file(file_path).get('release_notes', "Sin notas de la versión.")
        
        # Cargar la fuente TTF desde los recursos
        baseFont_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        font_path = os.path.join(baseFont_path, 'utils', 'fonts', 'OfficeCodePro-Regular.ttf')
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            print(font_id)
            if font_id != -1:
                print("update_dialog: Se cargo la fuente correctamente")
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                print(font_families)
                self.custom_font_family = font_families[0]  # Usar la primera familia cargada
            else:
                print("Error al cargar la fuente.")
                self.custom_font_family = "Arial"  # Fuente de respaldo
        else:
            print(f"No se encontró la fuente en {font_path}")
            self.custom_font_family = "Arial"  # Fuente de respaldo
        
        # Ahora podemos inicializar la interfaz
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        # Mostrar la versión actual y las notas de la versión
        self.label_status = QLabel(
            f"Versión actual detectada: {self.version_actual}\n")
        layout.addWidget(self.label_status)
        self.label_actual_release_notes = QLabel("Notas de la versión actual: ")
        layout.addWidget(self.label_actual_release_notes)
        
        # Configurar el QTextEdit con la fuente cargada
        self.text_release_notes = QTextEdit()
        self.text_release_notes.setPlainText(self.release_notes_actual)
        self.text_release_notes.setReadOnly(True)  # Solo lectura
        self.text_release_notes.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid #ccc;
                font-family: '{self.custom_font_family}';
                font-size: 12px;
            }}
        """)
        layout.addWidget(self.text_release_notes)
        
        # Botón para buscar actualizaciones
        self.btn_buscar = QPushButton("Buscar actualizaciones ahora")
        self.btn_buscar.clicked.connect(self.verificar_actualizaciones)
        self.btn_buscar.setEnabled(True)  # Habilitar el botón
        layout.addWidget(self.btn_buscar)
        
        # Nota temporal
        self.temp_note = QLabel("En desarrollo: Botón habilitado")
        layout.addWidget(self.temp_note)
        
        self.setLayout(layout)

    def verificar_actualizaciones(self):
        try:
            # Descargar el archivo JSON con la información de la última versión
            response = requests.get(self.url)
            response.raise_for_status()  # Lanzar una excepción si hay un error HTTP
            data = response.json()

            # Extraer la información de la última versión
            latest_version_str = data["Tlacuia GCL"]["version"]
            download_url = data["Tlacuia GCL"]["download_url"]
            release_notes = data["Tlacuia GCL"].get("release_notes", "Sin notas de la versión.")

            # Validar el formato de la versión
            try:
                latest_version = parse(latest_version_str)
                current_version = parse(self.version_actual)
            except InvalidVersion:
                raise ValueError("La versión en el JSON tiene un formato inválido.")

            # Comparar versiones
            if latest_version > current_version:
                mensaje = (
                    f"Nueva versión disponible: {latest_version_str}\n\n"
                    f"Notas de la nueva versión:\n{release_notes}\n\n"
                    "¿Desea descargarla ahora?"
                )
                respuesta = QMessageBox.question(
                    self,
                    "Actualización Disponible",
                    mensaje,
                    QMessageBox.Yes | QMessageBox.No
                )
                if respuesta == QMessageBox.Yes:
                    import webbrowser
                    webbrowser.open(download_url)
            else:
                QMessageBox.information(
                    self,
                    "No hay actualizaciones disponibles.",
                    f"La aplicación está actualizada en la versión más reciente: {self.version_actual}."
                )
        except ValueError as ve:
            # Capturar errores de formato de versión
            QMessageBox.critical(self, "Error", str(ve))
        except Exception as e:
            # Capturar otros errores
            QMessageBox.critical(self, "Error", f"No se pudo verificar actualizaciones: {str(e)} \n Respuesta: {response}")