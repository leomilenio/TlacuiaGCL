import os
import sys
from app.models.json_extract import extract_version_from_file
from app.utils.report_generator import Reporte
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QPushButton, QMessageBox, QFileDialog, QSpinBox, QTableWidgetItem 
from datetime import datetime

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
        """
        Genera un PDF utilizando la clase Reporte.
        """
        # Obtener la ruta para guardar el archivo PDF
        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF", "", "PDF (*.pdf)"
        )

        if filename:
            try:
                # Crear una instancia de la clase Reporte
                reporte = Reporte(app_name="Tlacuia GCL", margins=(50, 50, 50, 50), orientation="vertical")

                # Datos para el encabezado y el cuerpo del reporte
                titulo_reporte = "Reporte Final de Concesión"
                elementos = []

                # Construir los datos de la tabla
                columnas = ["Producto", "Disponible", "Vendido", "Devolver", "A Pagar"]
                datos_tabla = []
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

                    # Agregar fila a los datos de la tabla
                    datos_tabla.append({
                        "Producto": prod['descripcion'],
                        "Disponible": str(prod['cantidad']),
                        "Vendido": str(vendido),
                        "Devolver": str(devolver),
                        "A Pagar": f"${monto:.2f}"
                    })

                # Agregar la tabla al cuerpo del reporte
                elementos.append({
                    "tipo": "tabla",
                    "datos": datos_tabla,
                    "columnas": columnas
                })

                # Agregar los totales como texto
                totales_texto = (
                    f"Total a Pagar: ${total_pagar:.2f}\n"
                    f"Total a Devolver: {total_devolver} unidades"
                )
                elementos.append({
                    "tipo": "texto",
                    "contenido": totales_texto
                })

                # Generar el PDF usando la clase Reporte
                reporte.generar_pdf(filename, titulo_reporte, elementos)

                # Guardar el PDF en la base de datos
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

            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo generar el PDF: {str(e)}")