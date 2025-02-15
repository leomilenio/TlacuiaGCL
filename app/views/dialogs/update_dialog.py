from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox, QTextEdit
from app.models.json_extract import extract_version_from_file
import requests
import sys
import os


class UpdateDialog(QDialog):
    def __init__(self, version_actual, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscar Actualizaciones")
        self.setGeometry(200, 200, 400, 400)
        self.url = "https://github.com/leomilenio/TlacuiaGCL/blob/Estable/app/models/dev_info.json"

        # Obtener la versión actual antes de inicializar la interfaz
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        file_path = os.path.join(base_path, 'app', 'models', 'dev_info.json')
        self.version = extract_version_from_file(file_path).get('version', 'desconocida')
        self.release_notes_actual = extract_version_from_file(file_path).get('release_notes', "Sin notas de la versión.")
        # Ahora podemos inicializar la interfaz
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        # Usar self.version_actual ya inicializado
                # Mostrar la versión actual y las notas de la versión
        self.label_status = QLabel(
            f"Tlacuia GCL - Versión actual: {self.version}\n")
        layout.addWidget(self.label_status)

        self.label_actual_release_notes = QLabel("Notas de la version actual: ")
        layout.addWidget(self.label_actual_release_notes)

        self.text_release_notes = QTextEdit()
        self.text_release_notes.setPlainText(self.release_notes_actual)
        self.text_release_notes.setReadOnly(True)  # Solo lectura
        self.text_release_notes.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.text_release_notes)

        self.btn_buscar = QPushButton("Buscar actualizaciones ahora")
        self.btn_buscar.clicked.connect(self.verificar_actualizaciones)
        layout.addWidget(self.btn_buscar)

        self.setLayout(layout)

    def verificar_actualizaciones(self):
        try:
            # URL del archivo JSON con la información de la última versión
            response = requests.get(self.url)
            data = response.json()
            
            # Extraer la información de la última versión
            latest_version = data["Tlacuia GCL"]["version"]
            download_url = data["Tlacuia GCL"]["download_url"]
            release_notes = data["Tlacuia GCL"].get("release_notes", "Sin notas de la versión.")
            
            if latest_version > self.version_actual:
                mensaje = (
                    f"Nueva versión disponible: {latest_version}\n\n"
                    f"Notas de la versión:\n{release_notes}\n\n"
                    "¿Desea descargarla ahora?"
                )
                respuesta = QMessageBox.question(
                    self,
                    "Actualización Disponible",
                    mensaje,
                    QMessageBox.Yes | QMessageBox.No
                )
                if respuesta == QMessageBox.Yes:
                    # Abrir el navegador para descargar la nueva versión
                    import webbrowser
                    webbrowser.open(download_url)
            else:
                QMessageBox.information(
                    self,
                    "No hay actualizaciones disponibles.",
                    f"La aplicación está actualizada en la versión más reciente: {self.version_actual}."
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo verificar actualizaciones: {e}")