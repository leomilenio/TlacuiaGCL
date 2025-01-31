from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt

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