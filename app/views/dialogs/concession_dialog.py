from PyQt5.QtWidgets import QDialog, QVBoxLayout, QGroupBox, QComboBox, QLineEdit, QDateEdit, QRadioButton, QSpinBox, QLabel, QHBoxLayout, QFileDialog, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QButtonGroup, QWidget, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QDate
from app.models.database import ConcesionesDB

class NewConcesionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = ConcesionesDB()
        self.setWindowTitle("Nueva Concesión")
        self.setFixedSize(600, 700)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # Sección 1: Datos del Emisor
        grp_emisor = QGroupBox("Datos del Emisor")
        emisor_layout = QVBoxLayout()
        
        self.txt_nombre_emisor = QLineEdit()
        self.txt_nombre_vendedor = QLineEdit()
        
        emisor_layout.addWidget(QLabel("Nombre del Emisor:"))
        emisor_layout.addWidget(self.txt_nombre_emisor)
        emisor_layout.addWidget(QLabel("Nombre del Vendedor:"))
        emisor_layout.addWidget(self.txt_nombre_vendedor)
        
        grp_emisor.setLayout(emisor_layout)
        layout.addWidget(grp_emisor)
        
        # Sección 2: Datos de la Concesión
        grp_concesion = QGroupBox("Datos de la Concesión")
        concesion_layout = QVBoxLayout()
        
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["Nota de credito", "Factura"])
        
        self.txt_folio = QLineEdit()
        
        self.date_recepcion = QDateEdit()
        self.date_recepcion.setDate(QDate.currentDate())
        
        # Toggle para fecha de vencimiento
        self.toggle_group = QButtonGroup(self)
        self.rdb_dias = QRadioButton("Definir por días")
        self.rdb_fecha = QRadioButton("Definir fecha exacta")
        self.toggle_group.addButton(self.rdb_dias)
        self.toggle_group.addButton(self.rdb_fecha)
        self.rdb_dias.setChecked(True)
        
        self.spn_dias = QSpinBox()
        self.spn_dias.setRange(1, 365)
        self.spn_dias.setValue(30)
        
        self.date_vencimiento = QDateEdit()
        self.date_vencimiento.setDate(QDate.currentDate().addDays(30))
        self.date_vencimiento.setEnabled(False)
        
        self.toggle_group.buttonClicked.connect(self.actualizar_fecha_input)
        
        concesion_layout.addWidget(QLabel("Tipo:"))
        concesion_layout.addWidget(self.cmb_tipo)
        concesion_layout.addWidget(QLabel("Folio (requerido):"))
        concesion_layout.addWidget(self.txt_folio)
        concesion_layout.addWidget(QLabel("Fecha Recepción:"))
        concesion_layout.addWidget(self.date_recepcion)
        concesion_layout.addWidget(QLabel("Fecha Vencimiento:"))
        concesion_layout.addWidget(self.rdb_dias)
        concesion_layout.addWidget(self.spn_dias)
        concesion_layout.addWidget(self.rdb_fecha)
        concesion_layout.addWidget(self.date_vencimiento)
        
        grp_concesion.setLayout(concesion_layout)
        layout.addWidget(grp_concesion)
        
        # Sección 3: Documentos
        grp_docs = QGroupBox("Documentos Adjuntos")
        docs_layout = QVBoxLayout()
        
        self.btn_seleccionar_docs = QPushButton("Seleccionar Archivos...")
        self.btn_seleccionar_docs.clicked.connect(self.seleccionar_documentos)
        self.lista_docs = QListWidget()
        
        docs_layout.addWidget(self.btn_seleccionar_docs)
        docs_layout.addWidget(self.lista_docs)
        grp_docs.setLayout(docs_layout)
        layout.addWidget(grp_docs)
        
        # Sección 4: Botones
        btn_layout = QHBoxLayout()
        self.btn_limpiar = QPushButton("Limpiar")
        self.btn_limpiar.clicked.connect(self.limpiar_formulario)
        self.btn_listo = QPushButton("Listo")
        self.btn_listo.clicked.connect(self.guardar_concesion)
        
        btn_layout.addWidget(self.btn_limpiar)
        btn_layout.addWidget(self.btn_listo)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def actualizar_fecha_input(self):
        if self.rdb_dias.isChecked():
            self.spn_dias.setEnabled(True)
            self.date_vencimiento.setEnabled(False)
        else:
            self.spn_dias.setEnabled(False)
            self.date_vencimiento.setEnabled(True)
    
    def seleccionar_documentos(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar Documentos", "", 
            "Archivos soportados (*.pdf *.xlsx *.xls)"
        )
        for file in files:
            QListWidgetItem(file, self.lista_docs)
    
    def limpiar_formulario(self):
        for widget in self.findChildren(QLineEdit):
            widget.clear()
        self.lista_docs.clear()
        self.cmb_tipo.setCurrentIndex(0)
        self.date_recepcion.setDate(QDate.currentDate())
        self.rdb_dias.setChecked(True)
        self.spn_dias.setValue(30)
    
    def guardar_concesion(self):
        if not self.txt_folio.text().strip():
            QMessageBox.critical(self, "Error", "El folio es requerido")
            return
        
        # Guardar emisor
        emisor_id = self.db.crear_emisor(
            self.txt_nombre_emisor.text(),
            self.txt_nombre_vendedor.text()
        )
        
        # Capturar la fecha de recepción seleccionada
        fecha_recepcion = self.date_recepcion.date().toString("yyyy-MM-dd")

        # Calcular fecha vencimiento
        if self.rdb_dias.isChecked():
            dias = self.spn_dias.value()
            fecha_vencimiento = None
        else:
            dias = None
            fecha_vencimiento = self.date_vencimiento.date().toString("yyyy-MM-dd")
        
        # Crear concesión
        concesion_id = self.db.crear_concesion(
            emisor_id=emisor_id,
            tipo=self.cmb_tipo.currentText(),
            folio=self.txt_folio.text(),
            fecha_recepcion=fecha_recepcion,
            fecha_vencimiento=fecha_vencimiento,
            dias_validez=dias
        )
        
        # Guardar documentos
        for i in range(self.lista_docs.count()):
            file_path = self.lista_docs.item(i).text()
            tipo = "PDF" if file_path.lower().endswith(".pdf") else "Excel"
            self.db.crear_documento(concesion_id, file_path.split("/")[-1], tipo, file_path)
        
        self.accept()

class ConcesionItem(QWidget):
    def __init__(self, emisor, folio, status):
        super().__init__()
        self.setFixedHeight(60)
        
        layout = QHBoxLayout()
        
        # Etiquetas con los datos
        self.lbl_emisor = QLabel(emisor)
        self.lbl_folio = QLabel(f"Folio: {folio}")
        self.lbl_status = QLabel(status)
        
        # Formato visual
        self.lbl_emisor.setFixedWidth(150)
        self.lbl_emisor.setStyleSheet("font-weight: bold;")
        self.lbl_folio.setStyleSheet("color: white;")
        
        # Color según estado
        colores = {
                "Valido": "#4CAF50",
                "Vence pronto": "#FFC107",
                "Vencida": "#F44336",
                "Pendiente": "#999999"
        }
        self.lbl_status.setStyleSheet(f"""
            background-color: {colores.get(status, "#999")};
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
        """)
        
        # Espaciadores para alineaciones específicas
        left_spacer = QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        right_spacer = QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        layout.addWidget(self.lbl_emisor)       # Alineado a la izquierda
        layout.addItem(left_spacer)
        layout.addWidget(self.lbl_folio, 0, alignment= Qt.AlignCenter)  # Centrado
        layout.addItem(right_spacer)
        layout.addWidget(self.lbl_status, 0, alignment= Qt.AlignRight)  # Alineado a la derecha
        
        self.setLayout(layout)

class EditConcesionDialog(NewConcesionDialog):
    def __init__(self, concesion_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Concesión")
        self.concesion_id = concesion_data[0]
        self.cargar_datos_iniciales(concesion_data)
    
    def cargar_datos_iniciales(self, data):
        """Carga los datos existentes en el formulario"""
        # Obtener datos del emisor
        emisor = self.db.cursor.execute(
            "SELECT * FROM grantingEmisor WHERE id = ?", 
            (data[1],)
        ).fetchone()
        
        self.txt_nombre_emisor.setText(emisor[1])
        self.txt_nombre_vendedor.setText(emisor[2])
        
        # Cargar datos de la concesión
        self.cmb_tipo.setCurrentText(data[2])
        self.txt_folio.setText(data[3])
        self.date_recepcion.setDate(QDate.fromString(data[4], "yyyy-MM-dd"))
        
        # Configurar fecha de vencimiento
        if "dias" in data[5]:  # Asumiendo que tienes este dato
            self.rdb_dias.setChecked(True)
            self.spn_dias.setValue(int(data[5].split(" ")[0]))
        else:
            self.rdb_fecha.setChecked(True)
            self.date_vencimiento.setDate(QDate.fromString(data[5], "yyyy-MM-dd"))
    
    def guardar_concesion(self):
        """Actualiza los datos en lugar de crear nuevos"""
        # Actualizar emisor
        self.db.cursor.execute('''
            UPDATE grantingEmisor SET 
                nombre_emisor = ?,
                nombre_vendedor = ?
            WHERE id = (SELECT emisor_id FROM Concesiones WHERE id = ?)
        ''', (
            self.txt_nombre_emisor.text(),
            self.txt_nombre_vendedor.text(),
            self.concesion_id
        ))
        
        # Resto de la lógica de actualización similar a guardar_concesion...
        # (Implementar según estructura de tu base de datos)
        
        self.db.conn.commit()
        self.accept()