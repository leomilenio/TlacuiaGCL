import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QPushButton, QMessageBox, QFileDialog, QSpinBox, QTableWidgetItem 


class FinConcesionDialog(QDialog):
    def __init__(self, productos, parent=None, solo_lectura=False):
        super().__init__(parent)
        self.solo_lectura = solo_lectura
        self.setWindowTitle("Fin de Concesión")
        self.setFixedSize(500, 600)  # Ancho duplicado
        self.productos = productos
        self.initUI()
        

        if solo_lectura:
            self.setWindowTitle("PDF Existente - Concesión Finalizada")
            for row in range(self.tabla.rowCount()):
                spin = self.tabla.cellWidget(row, 2)
                spin.setEnabled(False)
            self.btn_generar.setText("Exportar PDF Nuevo")

    
    def initUI(self):
        layout = QVBoxLayout()
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels([
            "Producto", "Cantidad Disponible", "Cantidad Vendida"
        ])
        
        for prod in self.productos:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            self.tabla.setItem(row, 0, QTableWidgetItem(prod['descripcion']))
            self.tabla.setItem(row, 1, QTableWidgetItem(str(prod['cantidad'])))
            spin = QSpinBox()
            spin.setMaximum(prod['cantidad'])
            self.tabla.setCellWidget(row, 2, spin)
        
        btn_generar = QPushButton("Generar PDF")
        btn_generar.clicked.connect(self.generar_pdf)
        
        layout.addWidget(self.tabla)
        layout.addWidget(btn_generar)
        self.setLayout(layout)
    
    def generar_pdf(self):    
        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF", "", "PDF (*.pdf)")
        
        if filename:
            c = canvas.Canvas(filename, pagesize=letter)
            width, height = letter
            
            # Encabezado
            y = height - 50
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y, "Reporte Final de Concesión")
            y -= 30
            
            # Columnas
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y, "Producto")
            c.drawString(250, y, "Disponible")
            c.drawString(350, y, "Vendido")
            c.drawString(450, y, "Devolver")  # Nueva columna
            c.drawString(550, y, "A Pagar")
            y -= 20
            
            # Datos
            c.setFont("Helvetica", 10)
            total_pagar = 0
            total_devolver = 0
            
            for row in range(self.tabla.rowCount()):
                prod = self.productos[row]
                spin = self.tabla.cellWidget(row, 2)
                vendido = spin.value()
                
                # Cálculos
                devolver = prod['cantidad'] - vendido
                monto = vendido * prod['precio_neto']
                
                # Acumular totales
                total_pagar += monto
                total_devolver += devolver
                
                # Dibujar fila
                c.drawString(50, y, prod['descripcion'])
                c.drawString(250, y, str(prod['cantidad']))
                c.drawString(350, y, str(vendido))
                c.drawString(450, y, str(devolver))  # Nueva columna
                c.drawString(550, y, f"${monto:.2f}")
                y -= 20
                
                if y < 100:
                    c.showPage()
                    y = height - 50
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(50, y, "Producto")
                    c.drawString(250, y, "Disponible")
                    c.drawString(350, y, "Vendido")
                    c.drawString(450, y, "Devolver")
                    c.drawString(550, y, "Monto a Pagar")
                    y -= 30
                    c.setFont("Helvetica", 10)
            
            # Totales
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, f"Total a Pagar: ${total_pagar:.2f}")
            c.drawString(50, y - 20, f"Total a Devolver: {total_devolver} unidades")
            
            c.save()

            with open(filename, 'rb') as f:
                contenido = f.read()

            nombre_archivo = os.path.basename(filename)
            self.parent().db.crear_reporte_pdf(
                self.parent().current_concesion_id,
                nombre_archivo,
                contenido
            )

            QMessageBox.information(self, "Éxito", "PDF generado correctamente y almacenado en la base de datos")
            self.accept()