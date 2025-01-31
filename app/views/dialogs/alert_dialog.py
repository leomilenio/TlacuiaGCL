from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton, QListWidgetItem

class AlertDialog(QDialog):
    def __init__(self, concesiones, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Alerta de Concesiones")
        self.setFixedSize(600, 400)
        self.initUI(concesiones)
        
    def initUI(self, concesiones):
        layout = QVBoxLayout()
        
        if concesiones:
            alert_label = QLabel("¡Tus siguientes concesiones están próximas a finalizar! ")
            alert_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFC107;")
            alert_label.setWordWrap(True)
            layout.addWidget(alert_label)
            
            self.lista_concesiones = QListWidget()
            self.lista_concesiones.setStyleSheet("background: #012030; border-radius: 5px;")
            
            for concesion in concesiones:
                item = QListWidgetItem(f"Emisor: {concesion['emisor']}, Folio: {concesion['folio']}, Días restantes: {concesion['dias_restantes']}")
                self.lista_concesiones.addItem(item)
            
            layout.addWidget(self.lista_concesiones)
        else:
            no_alert_label = QLabel("No tienes concesiones próximas a finalizar")
            no_alert_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
            layout.addWidget(no_alert_label)
        
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)
        
        self.setLayout(layout)
