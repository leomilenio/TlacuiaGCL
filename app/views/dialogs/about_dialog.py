import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QDialog, QVBoxLayout,
                             QLabel, QPushButton, QAction)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt

from app.models.json_extract import (extract_version_from_file, extract_devContact_from_file, extract_license_from_file)

class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()

        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        file_path = os.path.join(base_path, 'models', 'dev_info.json')

        version = extract_version_from_file(file_path).get('version', 'desconocida')
        licencia = extract_license_from_file(file_path).get('licence', 'desconocida')
        devContact = extract_devContact_from_file(file_path).get('contact', 'Sin informacion')

        self.setWindowTitle("Acerca de")
        self.setFixedSize(300, 200)

        layout = QVBoxLayout()

        title = QLabel("<h2> Tlacuia GCL </h2>")
        title.setAlignment(Qt.AlignCenter)

        versionValue = QLabel(f"Version - {version}")
        versionValue.setAlignment(Qt.AlignCenter)


        contactInfo = QLabel(f"Contacto - {devContact}")
        contactInfo.setAlignment(Qt.AlignCenter)

        licenseType = QLabel(f"Licencia - {licencia}")
        licenseType.setAlignment(Qt.AlignCenter)

        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(versionValue)
        layout.addWidget(contactInfo)
        layout.addWidget(licenseType)

        layout.addWidget(close_button)
        self.setLayout(layout)
        