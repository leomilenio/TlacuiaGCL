import os
from PyQt5.QtWidgets import (QMainWindow, QListWidget, QListWidgetItem, QWidget, 
                            QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, 
                            QPushButton, QFileDialog, QMessageBox,QHBoxLayout, QSizePolicy,
                            QDialog)
from PyQt5.QtCore import Qt, QSize, QDate
from app.models.database import ConcesionesDB
from app.views.dialogs import (ProductoDialog, NewConcesionDialog, 
                              AlertDialog, FinConcesionDialog)
from app.views.dialogs.concession_dialog import (EditConcesionDialog, ConcesionItem)
from datetime import datetime


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = ConcesionesDB()
        self.current_concesion_id = None  # Almacenará el ID de la concesión seleccionada
        
        self.initUI()
        self.cargar_concesiones()

        if os.path.exists('concesiones.db'):
            self.mostrar_alerta_concesiones()
        
    def initUI(self):
        self.setGeometry(100, 100, 1300, 600)  # Aumentamos el tamaño de la ventana
        self.setWindowTitle("Tlacuia - Gestor de Concesiones para Librerias")
        
        main_widget = QWidget()
        main_layout = QHBoxLayout()  # Cambiamos a layout horizontal
        
        # ========== LISTADO ==========
        list_widget = QWidget()
        list_layout = QVBoxLayout()
        
        # Cabecera
        header = QWidget()
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Tlacuia - DB", styleSheet="font-weight: bold;"))
        header_layout.addStretch(50)
        
        currentDate = QDate.currentDate().toString("dd/MM/yyyy")
        date_label = QLabel(f"Fecha: {currentDate}", styleSheet="font-weight: bold;")
        header_layout.addWidget(date_label)

        self.btn_alerta = QPushButton("Ver Alertas")
        self.btn_alerta.setStyleSheet(
            """
            QPushButton{
                background-color: #BEA231;
                color: white; 
                padding: 8px;
                border-radius: 5px; 
                font-weight: bold; 
            }

            QPushButton: hover {
                background-color: #FFA000;
            }
            """
        )
        self.btn_alerta.setFixedSize(100, 30)
        self.btn_alerta.clicked.connect(self.mostrar_alerta_concesiones)
        header_layout.addWidget(self.btn_alerta)

        self.btn_nuevo = QPushButton("+")
        self.btn_nuevo.setStyleSheet(
            """
            QPushButton{
                background-color: #386F53;
                color: white; 
                padding: 8px;
                border-radius: 5px; 
                font-weight: bold; 
            }

            QPushButton: hover {
                background-color: #FFA000;
            }
            """
        )
        self.btn_nuevo.setFixedSize(50, 30)
        self.btn_nuevo.clicked.connect(self.mostrar_nueva_concesion)
        header_layout.addWidget(self.btn_nuevo)
        

        header.setLayout(header_layout)
        list_layout.addWidget(header)
        
        # Lista
        self.lista = QListWidget()
        self.lista.setStyleSheet("""
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
        self.lista.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lista.itemSelectionChanged.connect(self.mostrar_detalles_concesion)
        list_layout.addWidget(self.lista)
        
        list_widget.setLayout(list_layout)
        main_layout.addWidget(list_widget)
        
        # ========== PANEL DE DETALLES ==========
        self.details_widget = QWidget()
        details_layout = QVBoxLayout()
        
        # Información de la concesión
        self.lbl_titulo = QLabel("Detalles de la Concesión")
        self.lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #13678A;")
        details_layout.addWidget(self.lbl_titulo)
        
        # Campos de información
        self.lbl_emisor = QLabel("Emisor: ")
        self.lbl_folio = QLabel("Folio: ")
        self.lbl_tipo = QLabel("Tipo: ")
        self.lbl_fecha_recepcion = QLabel("Fecha Recepción: ")
        self.lbl_fecha_vencimiento = QLabel("Fecha Vencimiento: ")
        self.lbl_estado = QLabel("Estado: ")
        
        for lbl in [self.lbl_emisor, self.lbl_folio, self.lbl_tipo, 
                   self.lbl_fecha_recepcion, self.lbl_fecha_vencimiento, self.lbl_estado]:
            lbl.setStyleSheet("font-size: 14px; margin: 5px;")
            details_layout.addWidget(lbl)
        
                # En MainWindow.initUI(), añade estos elementos:
        self.tabla_productos = QTableWidget()
        self.tabla_productos.setColumnCount(6)
        self.tabla_productos.setHorizontalHeaderLabels([
            "Cantidad", "Descripción", "ISBN", "PVP Unitario", 
            "Precio Neto", "Precio Total"
        ])

        self.tabla_productos.horizontalHeader().setStretchLastSection(True)
        self.tabla_productos.setColumnWidth(0, 80)   # Cantidad
        self.tabla_productos.setColumnWidth(1, 250)  # Descripción
        self.tabla_productos.setColumnWidth(2, 150)  # ISBN
        self.tabla_productos.setColumnWidth(3, 120)  # PVP
        self.tabla_productos.setColumnWidth(4, 120)  # Precio Neto
        self.tabla_productos.setColumnWidth(5, 120)  # Precio Total

        # Documentos adjuntos
        details_layout.addWidget(QLabel("Documentos Adjuntos:", styleSheet="font-weight: bold; margin-top: 15px;"))
        self.lista_documentos = QListWidget()
        self.lista_documentos.setStyleSheet("background: #012030; border-radius: 5px;")
        details_layout.addWidget(self.lista_documentos)
        


        # Botones de acción
        btn_layout = QHBoxLayout()
        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setStyleSheet("background: #4CAF50; color: white; padding: 8px;")
        self.btn_editar.clicked.connect(self.editar_concesion)
        
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setStyleSheet("background: #F44336; color: white; padding: 8px;")
        self.btn_eliminar.clicked.connect(self.eliminar_concesion)
        
        self.btn_agregar_doc = QPushButton("Añadir Documento")
        self.btn_agregar_doc.clicked.connect(self.agregar_documento)
        
        btn_layout.addWidget(self.btn_editar)
        btn_layout.addWidget(self.btn_eliminar)
        btn_layout.addWidget(self.btn_agregar_doc)

        # En el layout de detalles, después de documentos:
        details_layout.addWidget(QLabel("Productos:", styleSheet="font-weight: bold;"))
        details_layout.addWidget(self.tabla_productos)

        self.lbl_finalizada = QLabel("CONCESIÓN FINALIZADA")
        self.lbl_finalizada.setStyleSheet("""
            color: #FF0000;
            font-weight: bold;
            font-size: 16px;
            padding: 8px;
            border: 2px solid #FF0000;
            border-radius: 5px;
        """)
        self.lbl_finalizada.hide()
        details_layout.insertWidget(6, self.lbl_finalizada) 

        # Añade un nuevo botón en btn_layout:
        self.btn_agregar_producto = QPushButton("Agregar Producto")
        self.btn_agregar_producto.clicked.connect(self.agregar_producto)
        btn_layout.addWidget(self.btn_agregar_producto)

        details_layout.addLayout(btn_layout)
        
        self.details_widget.setLayout(details_layout)
        main_layout.addWidget(self.details_widget)
        
        self.btn_fin_concesion = QPushButton("Fin de Concesión")
        self.btn_fin_concesion.clicked.connect(self.manejar_fin_concesion) 
        btn_layout.addWidget(self.btn_fin_concesion)


        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def manejar_exportar_pdf(self):
            if not self.current_concesion_id:
                return
            
            concesion = self.db.obtener_concesion_por_id(self.current_concesion_id)
            
            if not concesion['finalizada']:
                QMessageBox.warning(self, "Error", "La concesión debe estar finalizada")
                return
            
            reportes = self.db.obtener_reportes_por_concesion(self.current_concesion_id)
            
            if not reportes:
                QMessageBox.information(self, "Información", "No hay reportes generados")
                return
            
            # Diálogo para seleccionar reporte
            dialog = QDialog(self)
            layout = QVBoxLayout()
            
            lista = QListWidget()
            for reporte in reportes:
                item = QListWidgetItem(f"{reporte[1]} - {reporte[2]}")
                item.setData(Qt.UserRole, reporte[0])
                lista.addItem(item)
            
            btn_exportar = QPushButton("Exportar")
            btn_exportar.clicked.connect(lambda: self.exportar_pdf_seleccionado(lista.currentItem(), dialog))
            
            layout.addWidget(QLabel("Seleccione un reporte para exportar:"))
            layout.addWidget(lista)
            layout.addWidget(btn_exportar)
            dialog.setLayout(layout)
            dialog.exec_()
    
    def exportar_pdf_seleccionado(self, item, dialog):
        if not item:
            return
        
        reporte_id = item.data(Qt.UserRole)
        contenido = self.db.obtener_contenido_reporte(reporte_id)
        
        filename, _ = QFileDialog.getSaveFileName(
        self, "Guardar PDF", item.text().split(" - ")[0], "PDF (*.pdf)")
        
        if filename:
            with open(filename, 'wb') as f:
                f.write(contenido)
            QMessageBox.information(self, "Éxito", "PDF exportado correctamente")
            dialog.close()


    def manejar_fin_concesion(self):
        concesion = self.db.obtener_concesion_por_id(self.current_concesion_id)
        
        if concesion['finalizada']:
            self.manejar_exportar_pdf()
        else:
            self.mostrar_fin_concesion_dialogo()

    def mostrar_fin_concesion_dialogo(self):
        productos = self.db.obtener_productos_por_concesion(self.current_concesion_id)
        if productos:
            dialog = FinConcesionDialog(productos, self)
            if dialog.exec_():
                self.db.marcar_concesion_como_finalizada(self.current_concesion_id)
                self.actualizar_ui_finalizada()

    def actualizar_ui_finalizada(self):
        self.lbl_finalizada.show()
        self.btn_fin_concesion.setText("Generar PDF")
        self.btn_agregar_producto.setEnabled(False)
        self.btn_agregar_doc.setEnabled(False)


    def generar_pdf_existente(self):
        productos = self.db.obtener_productos_por_concesion(self.current_concesion_id)
        if productos:
            dialog = FinConcesionDialog(productos, self, solo_lectura=True)
            dialog.generar_pdf()

    def mostrar_fin_concesion(self):
        if not self.current_concesion_id:
            return
        
        productos = self.db.obtener_productos_por_concesion(self.current_concesion_id)
        if productos:
            dialog = FinConcesionDialog(productos, self)
            dialog.exec_()

    def agregar_producto(self):
        if not self.current_concesion_id:
            QMessageBox.warning(self, "Error", "Selecciona una concesión primero")
            return
        dialog = ProductoDialog(self)
        if dialog.exec_():
            self.actualizar_productos()

    def actualizar_productos(self):
        self.tabla_productos.setRowCount(0)
        if not self.current_concesion_id:
            return
            
        productos = self.db.obtener_productos_por_concesion(self.current_concesion_id)
        for prod in productos:
            row = self.tabla_productos.rowCount()
            self.tabla_productos.insertRow(row)
            
            # Formatear valores numéricos
            pvp = prod['pvp_unitario'] or 0.0
            neto = prod['precio_neto'] or 0.0
            total = prod['precio_total'] or 0.0
            
            items = [
                QTableWidgetItem(str(prod['cantidad'])),
                QTableWidgetItem(prod['descripcion']),
                QTableWidgetItem(prod['isbn'] or "N/A"),
                QTableWidgetItem(f"${pvp:.2f}"),
                QTableWidgetItem(f"${neto:.2f}"),
                QTableWidgetItem(f"${total:.2f}")
            ]
            
            # Alinear numéricos a la derecha
            for i in [0, 3, 4, 5]:
                items[i].setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
            for col, item in enumerate(items):
                self.tabla_productos.setItem(row, col, item)

    def mostrar_nueva_concesion(self):
        dialog = NewConcesionDialog(self)
        if dialog.exec_():
            self.cargar_concesiones()

    def mostrar_alerta_concesiones(self):
        concesiones = self.db.obtener_concesiones()
        concesiones_proximas = []
        
        for concesion in concesiones:
            if concesion['status'] == 'Vence pronto':
                dias_restantes = (datetime.strptime(concesion['fecha_vencimiento'], '%Y-%m-%d').date() - datetime.now().date()).days
                concesiones_proximas.append({
                    'emisor': self.obtener_nombre_emisor(concesion['emisor_id']),
                    'folio': concesion['folio'],
                    'dias_restantes': dias_restantes
                })
        
        if concesiones_proximas or not concesiones:
            dialog = AlertDialog(concesiones_proximas, self)
            dialog.exec_()

    def mostrar_detalles_concesion(self):
        selected = self.lista.currentItem()
        if not selected:
            return
            
        # Obtener ID desde el item seleccionado
        concesion_id = selected.data(Qt.UserRole)
        concesion = self.db.obtener_concesion_por_id(concesion_id)
        
        if not concesion:
            QMessageBox.warning(self, "Error", "Concesión no encontrada")
            return
        
        self.current_concesion_id = concesion['id']
        
        # Actualizar labels...
        self.lbl_emisor.setText(f"Emisor: {self.obtener_nombre_emisor(concesion['emisor_id'])}")
        self.lbl_folio.setText(f"Folio: {concesion['folio']}")
        self.lbl_tipo.setText(f"Tipo: {concesion['tipo']}")
        self.lbl_fecha_recepcion.setText(f"Fecha Recepción: {concesion['fecha_recepcion']}")
        self.lbl_fecha_vencimiento.setText(f"Fecha Vencimiento: {concesion['fecha_vencimiento']}")
        self.lbl_estado.setText(f"Estado: {concesion['status']}")
        
        self.actualizar_documentos()
        self.actualizar_productos()

        finalizada = concesion.get('finalizada', 0)
        if finalizada:
            self.actualizar_ui_finalizada()
        else:
            self.lbl_finalizada.hide()
            self.btn_fin_concesion.setText("Fin de Concesión")
            self.btn_agregar_producto.setEnabled(True)
            self.btn_agregar_doc.setEnabled(True)

        
    def cargar_concesiones(self):
        self.lista.clear()
        concesiones = self.db.obtener_concesiones()
        
        for concesion in concesiones:
            item = QListWidgetItem(self.lista)
            item.setData(Qt.UserRole, concesion['id'])  # Almacenar ID
            item.setSizeHint(QSize(0, 60))  # Altura del item
            
            # Crear widget personalizado
            widget = ConcesionItem(
                emisor=self.obtener_nombre_emisor(concesion['emisor_id']),
                folio=concesion['folio'],
                status=concesion['status']
            )
            
            self.lista.addItem(item)
            self.lista.setItemWidget(item, widget)
    
    def obtener_nombre_emisor(self, emisor_id):
        # Consultar nombre del emisor desde la base de datos
        self.db.cursor.execute('SELECT nombre_emisor FROM grantingEmisor WHERE id = ?', (emisor_id,))
        result = self.db.cursor.fetchone()
        return result[0] if result else "Desconocido"

    def actualizar_documentos(self):
        """Actualiza la lista de documentos de la concesión actual"""
        self.lista_documentos.clear()
        if self.current_concesion_id:
            documentos = self.db.obtener_documentos(self.current_concesion_id)
            for doc in documentos:
                QListWidgetItem(f"{doc[2]} ({doc[3]})", self.lista_documentos)
    
    def editar_concesion(self):
        """Abre diálogo para editar la concesión seleccionada"""
        if not self.current_concesion_id:
            return
            
        # Obtener datos actuales
        concesion_data = self.db.cursor.execute(
            "SELECT * FROM Concesiones WHERE id = ?", 
            (self.current_concesion_id,)
        ).fetchone()
        
        dialog = EditConcesionDialog(concesion_data, self)
        if dialog.exec_():
            self.cargar_concesiones()
            self.mostrar_detalles_concesion()
    
    def agregar_documento(self):
        """Añade nuevo documento a la concesión actual"""
        if not self.current_concesion_id:
            return
            
        file, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Documento", "", 
            "Archivos soportados (*.pdf *.xlsx *.xls)"
        )
        if file:
            tipo = "PDF" if file.lower().endswith(".pdf") else "Excel"
            self.db.crear_documento(self.current_concesion_id, os.path.basename(file), tipo, file)
            self.actualizar_documentos()
    
    def eliminar_concesion(self):
        """Elimina la concesión seleccionada"""
        if not self.current_concesion_id:
            return
            
        confirm = QMessageBox.question(
            self, "Confirmar Eliminación", 
            "¿Estás seguro de eliminar esta concesión y todos sus documentos?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.db.cursor.execute("DELETE FROM Concesiones WHERE id = ?", (self.current_concesion_id,))
            self.db.conn.commit()
            self.cargar_concesiones()
            self.current_concesion_id = None
            self.lista_documentos.clear()
            self.tabla_productos.setRowCount(0)
