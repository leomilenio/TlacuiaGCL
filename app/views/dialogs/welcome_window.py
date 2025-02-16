from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QListWidget, QListWidgetItem, QMessageBox, QStyledItemDelegate
from PyQt5.QtCore import Qt, QMargins
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont
from datetime import datetime
from app.views.main_window import MainWindow
from app.models.json_extract import (extract_version_from_file)
from app.models.database import ConcesionesDB
from app.views.dialogs.update_dialog import UpdateDialog
from app.views.dialogs.about_dialog import AboutDialog
import os

# Delegado personalizado para dibujar los elementos con bordes redondeados
class CustomItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        # Obtener el texto del elemento
        text = index.data(Qt.DisplayRole)
        status = index.data(Qt.UserRole)  # Usaremos UserRole para almacenar el estado

        # Configurar el color de fondo según el estado
        if status == 'Valido':
            background_color = QColor(178, 219, 142, 244)  # Verde con 30% de transparencia
        elif status == 'Vence pronto':
            background_color = QColor(245, 229, 121, 244)  # Amarillo con 30% de transparencia
        elif status == 'Vencido':
            background_color = QColor(223, 206, 107, 244)  # Rojo con 30% de transparencia
        else:
            background_color = QColor(255, 255, 255, 200)  # Blanco con 30% de transparencia

        # Dibujar el rectángulo con bordes redondeados
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Margen interno (10 píxeles)
        margin = 5
        rect = option.rect.adjusted(margin, margin, -margin, -margin)

        # Dibujar el fondo
        painter.setBrush(QBrush(background_color))
        painter.setPen(QPen(Qt.NoPen))  # Sin borde externo
        painter.drawRoundedRect(rect, 10, 10)  # Bordes redondeados con radio 10

        # Separar el texto en tres partes: emisor, folio, días restantes
        parts = text.split(" | ")
        emisor = parts[0]
        folio = parts[1]
        dias_restantes = parts[2]

        # Fuente en negrita
        font = QFont()
        font.setBold(True)
        painter.setFont(font)

        # Margen interno para el texto
        text_margin = 5
        text_rect = rect.adjusted(text_margin, text_margin, -text_margin, -text_margin)

        # Alinear el texto: emisor a la izquierda, folio al centro, días restantes a la derecha
        painter.setPen(Qt.black)  # Color del texto
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, emisor)
        painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignVCenter, folio)
        painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, dias_restantes)

        painter.restore()

    def sizeHint(self, option, index):
            # Ajustar el tamaño del elemento para incluir márgenes
            size = super().sizeHint(option, index)
            margins = QMargins(10, 10, 10, 10)  # Márgenes de 10 píxeles en cada lado
            return size.grownBy(margins)  # Aplicar los márgenes


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
        btn_iniciar_gestor = QPushButton("Gestor de Concesiones")
        btn_iniciar_gestor.setStyleSheet("background-color: #386F53; color: white; border-radius: 10px; padding: 25px;")
        btn_iniciar_gestor.clicked.connect(self.iniciar_gestor_concesiones)
        left_vbox.addWidget(btn_iniciar_gestor)

        # Botón 2: Asistente de bodega
        btn_asistente_bodega = QPushButton("Asistente de Bodega")
        btn_asistente_bodega.setStyleSheet("background-color: #386F53; color: white; border-radius: 10px; padding: 25px;")
        btn_asistente_bodega.clicked.connect(self.asistente_bodega)
        left_vbox.addWidget(btn_asistente_bodega)

        # Añadir espacio vacío para centrar los botones
        left_vbox.addStretch()

        # Botón 3: Buscar actualizaciones
        btn_buscar_actualizaciones = QPushButton("Buscar Actualizaciones")
        btn_buscar_actualizaciones.setStyleSheet("background-color: #1E90FF; color: white; border-radius: 10px; padding: 10px;")
        btn_buscar_actualizaciones.clicked.connect(self.mostrar_dialogo_actualizaciones)
        left_vbox.addWidget(btn_buscar_actualizaciones)

        # Boton 4: Acerca de
        btn_about = QPushButton("Acerca de")
        btn_about.setStyleSheet("background-color: #1E90FF; color: white; border-radius: 10px; padding: 10px;")
        btn_about.clicked.connect(self.mostrar_acercaDe)
        left_vbox.addWidget(btn_about)
        # Columna derecha (VBox): Lista de concesiones activas y próximas a vencer
        right_vbox = QVBoxLayout()
        right_vbox.addWidget(QLabel("Concesiones Activas y Próximas a Finalizar:", styleSheet="font-size: 18px; font-weight: bold;"))

        # Lista de concesiones
        self.lista_concesiones = QListWidget()
        self.lista_concesiones.setStyleSheet("""
            QListWidget {
                border: none;
                border-radius: 10px;
                background: #012030; /* Fondo oscuro */
            }
            QListWidget::item {
                margin: 5px; /* Espaciado entre elementos */
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

            # Asignar el estado como UserRole
            item.setData(Qt.UserRole, concesion['status'])

            self.lista_concesiones.addItem(item)

        # Aplicar el delegado personalizado
        self.lista_concesiones.setItemDelegate(CustomItemDelegate(self.lista_concesiones))

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
    
    def mostrar_acercaDe(self):
        dialog = AboutDialog()
        dialog.exec()