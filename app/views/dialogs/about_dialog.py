import sys
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout,
                             QLabel, QPushButton, QMessageBox, QTextEdit)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QUrl

from app.models.json_extract import (extract_version_from_file, extract_devContact_from_file, extract_license_from_file)

class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()

        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        file_path = os.path.join(base_path, 'app', 'models', 'dev_info.json')

        version = extract_version_from_file(file_path).get('version', 'desconocida')
        licencia = extract_license_from_file(file_path).get('licence', 'desconocida')
        devContact = extract_devContact_from_file(file_path).get('contact', 'Sin informacion')

        self.license_file_path = os.path.join(base_path, 'LICENSE.txt')

        self.setWindowTitle("Acerca de")
        self.setFixedSize(300, 350)

        layout = QVBoxLayout()

        # Logo del software
        logo_path = os.path.join(base_path, 'app', 'resources', 'media', 'TlacuiaLogo.png')  # Ruta del logo
        logo_label = QLabel(self)
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():  # Verificar si la imagen se cargó correctamente
            logo_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))  # Escalar el logo
            logo_label.setAlignment(Qt.AlignCenter)
        else:
            logo_label.setText("Logo no encontrado")  # Mensaje de error si no se encuentra el logo
        layout.addWidget(logo_label)

        title = QLabel("<h1> Tlacuia GCL </h1>")
        title.setAlignment(Qt.AlignCenter)
        title.mouseDoubleClickEvent = self.show_easter_egg

        versionValue = QLabel(f"Version - {version}")
        versionValue.setAlignment(Qt.AlignCenter)


        contactInfo = QLabel(f"Contacto - {devContact}")
        contactInfo.setAlignment(Qt.AlignCenter)

        # Licencia: al hacer clic, abre una nueva ventana con el contenido del archivo LICENSE.txt
        licenseType = QLabel(f"Licencia - {licencia}")
        licenseType.setAlignment(Qt.AlignCenter)
        licenseType.setStyleSheet("text-decoration: underline;")
        licenseType.setCursor(Qt.PointingHandCursor)  # Cambia el cursor al pasar sobre el texto
        licenseType.mousePressEvent = self.show_license_content  # Conecta el clic a una función


        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(versionValue)
        layout.addWidget(contactInfo)
        layout.addWidget(licenseType)

        layout.addWidget(close_button)
        self.setLayout(layout)
        
    def show_license_content(self, event):
        """Muestra el contenido del archivo LICENSE.txt en una nueva ventana."""
        if not os.path.exists(self.license_file_path):
            QMessageBox.warning(self, "Error", "El archivo LICENSE.txt no se encontró.")
            return

        with open(self.license_file_path, 'r', encoding='utf-8') as file:
            license_content = file.read()

        # Crear una nueva ventana para mostrar el contenido de la licencia
        license_dialog = QDialog(self)
        license_dialog.setWindowTitle("Licencia")
        license_dialog.resize(600, 400)

        layout = QVBoxLayout()

        text_edit = QTextEdit()
        text_edit.setPlainText(license_content)
        text_edit.setReadOnly(True)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(license_dialog.accept)

        layout.addWidget(text_edit)
        layout.addWidget(ok_button)

        license_dialog.setLayout(layout)
        license_dialog.exec()

    def show_easter_egg(self, event):
        QMessageBox.information(self, "Un mensaje!", "Te adoro un monton Armando!!")