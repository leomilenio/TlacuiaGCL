from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QListWidget, QListWidgetItem, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from datetime import datetime
from app.views.main_window import MainWindow
from app.models.json_extract import (extract_version_from_file)
from app.models.database import ConcesionesDB
from app.views.dialogs.update_dialog import UpdateDialog
import os

class WelcomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = ConcesionesDB()  # Base de datos para acceder a las concesiones
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Tlacuia - Gestor de Concesiones para Librerías")
        self.setGeometry(100, 100, 900, 600)  # Dimensiones de la ventana


        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        file_path = os.path.join(base_path, 'app', 'models', 'dev_info.json')

        self.version = extract_version_from_file(file_path).get('version', 'desconocida')

        # Layout principal (HBox)
        main_layout = QHBoxLayout()

        # Columna izquierda (VBox)
        left_vbox = QVBoxLayout()
        left_vbox.addWidget(QLabel("Tlacuia", styleSheet="font-size: 24px; font-weight: bold;"))
        left_vbox.addWidget(QLabel("Gestor de Concesiones para Librerias", styleSheet="font-size: 14px; font-weight: bold;"))
        left_vbox.addWidget(QLabel(f"Versión: {self.version}", styleSheet="font-size: 12px;"))

        # Botón 1: Iniciar gestor de concesiones
        btn_iniciar_gestor = QPushButton("Iniciar Gestor de Concesiones")
        btn_iniciar_gestor.setStyleSheet("background-color: #386F53; color: white; padding: 25px;")
        btn_iniciar_gestor.clicked.connect(self.iniciar_gestor_concesiones)
        left_vbox.addWidget(btn_iniciar_gestor)

        # Botón 2: Asistente de bodega
        btn_asistente_bodega = QPushButton("Asistente de Bodega")
        btn_asistente_bodega.setStyleSheet("background-color: #386F53; color: white; padding: 25px;")
        btn_asistente_bodega.clicked.connect(self.asistente_bodega)
        left_vbox.addWidget(btn_asistente_bodega)

        # Añadir espacio vacío para centrar los botones
        left_vbox.addStretch()

        # Botón 3: Buscar actualizaciones
        btn_buscar_actualizaciones = QPushButton("Buscar Actualizaciones")
        btn_buscar_actualizaciones.setStyleSheet("background-color: #1E90FF; color: white; padding: 10px;")
        btn_buscar_actualizaciones.clicked.connect(self.mostrar_dialogo_actualizaciones)
        left_vbox.addWidget(btn_buscar_actualizaciones)

        # Columna derecha (VBox): Lista de concesiones activas y próximas a vencer
        right_vbox = QVBoxLayout()
        right_vbox.addWidget(QLabel("Concesiones Activas y Próximas a Finalizar:", styleSheet="font-size: 18px; font-weight: bold;"))

        # Lista de concesiones
        self.lista_concesiones = QListWidget()
        self.lista_concesiones.setStyleSheet("""
            QListWidget {
                border: none;
                background: #012030;
            }
            QListWidget::item {
                border-bottom: 1px solid #ddd;
            }
            QListWidget::item:hover {
                background: #4F8FAA;
            }
            QListWidget::item:selected {
                background: #13678A;
                color: white;
            }
        """)
        self.actualizar_lista_concesiones()  # Cargar las concesiones
        right_vbox.addWidget(self.lista_concesiones)

        # Añadir las columnas al layout principal
        main_layout.addLayout(left_vbox, stretch=1)
        main_layout.addLayout(right_vbox, stretch=2)

        # Widget principal
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def actualizar_lista_concesiones(self):
        self.lista_concesiones.clear()
        concesiones = self.db.obtener_concesiones()

        for concesion in concesiones:
            if concesion['status'] == 'Vencido':
                continue  # No mostrar concesiones vencidas

            emisor = self.obtener_nombre_emisor(concesion['emisor_id'])
            folio = concesion['folio']
            fecha_vencimiento = datetime.strptime(concesion['fecha_vencimiento'], '%Y-%m-%d').date()
            dias_restantes = (fecha_vencimiento - datetime.now().date()).days

            item_text = f"{emisor} | {folio} | {dias_restantes} días restantes"
            item = QListWidgetItem(item_text)

            # Colorear según el estado
            if concesion['status'] == 'Valido':
                item.setBackground(QColor(0, 255, 0, 50))  # Verde
            elif concesion['status'] == 'Vence pronto':
                item.setBackground(QColor(255, 255, 0, 50))  # Amarillo
            elif dias_restantes == 0:
                item.setBackground(QColor(255, 0, 0, 50))  # Rojo

            self.lista_concesiones.addItem(item)

    def obtener_nombre_emisor(self, emisor_id):
        """Obtiene el nombre del emisor desde la base de datos."""
        self.db.cursor.execute('SELECT nombre_emisor FROM grantingEmisor WHERE id = ?', (emisor_id,))
        result = self.db.cursor.fetchone()
        return result[0] if result else "Desconocido"

    def iniciar_gestor_concesiones(self):
        """Cierra la ventana de bienvenida y abre el MainWindow."""
        self.close()
        self.main_window = MainWindow()
        self.main_window.show()

    def asistente_bodega(self):
        """Lógica para abrir el asistente de bodega."""
        QMessageBox.information(self, "Información", "Funcionalidad del Asistente de Bodega aún no implementada.")

    def mostrar_dialogo_actualizaciones(self):
        """Muestra el diálogo de búsqueda de actualizaciones."""
        dialog = UpdateDialog(self.version, self)
        dialog.exec_()