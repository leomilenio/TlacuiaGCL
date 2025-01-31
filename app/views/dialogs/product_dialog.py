from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QSpinBox, QLineEdit, QPushButton, QMessageBox

class ProductoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar Producto")
        self.setFixedSize(800, 300)  # Ancho duplicado
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        self.txt_cantidad = QSpinBox()
        self.txt_cantidad.setMinimum(1)
        self.txt_cantidad.setMaximum(9999)
        
        self.txt_descripcion = QLineEdit()
        self.txt_isbn = QLineEdit()
        self.txt_pvp = QLineEdit()
        self.txt_precio_neto = QLineEdit()
        
        form = QFormLayout()
        form.addRow("Cantidad:", self.txt_cantidad)
        form.addRow("Descripción:", self.txt_descripcion)
        form.addRow("ISBN:", self.txt_isbn)
        form.addRow("PVP Unitario:", self.txt_pvp)
        form.addRow("Precio Neto:", self.txt_precio_neto)
        
        btn_guardar = QPushButton("Guardar")
        btn_guardar.clicked.connect(self.validar_datos)
        
        layout.addLayout(form)
        layout.addWidget(btn_guardar)
        self.setLayout(layout)
    
    def validar_datos(self):
        try:
            precio_neto = float(self.txt_precio_neto.text())
            pvp = float(self.txt_pvp.text()) if self.txt_pvp.text() else 0.0
            if not self.txt_descripcion.text().strip():
                raise ValueError
            self.guardar_producto()
        except:
            QMessageBox.critical(self, "Error", "Verifica los datos ingresados")
    
    def guardar_producto(self):
        parent = self.parent()
        parent.db.crear_producto(
            parent.current_concesion_id,
            self.txt_cantidad.value(),
            self.txt_descripcion.text(),
            self.txt_isbn.text(),
            self.txt_pvp.text() or 0.0,
            float(self.txt_precio_neto.text())
        )
        self.accept()