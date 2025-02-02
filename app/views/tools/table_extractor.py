import sys
import camelot
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
                             QTableWidget, QTableWidgetItem, QSpinBox, QListWidget, QLabel,
                             QMessageBox, QLineEdit, QComboBox,QListWidgetItem, QDialog, QApplication)
from PyQt5.QtCore import Qt

class PdfTableExtractor(QDialog):  # Cambiamos QWidget por QDialog
    def __init__(self):
        super().__init__()
        self.tables = []
        self.current_table_index = 0
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Extractor de Tablas PDF")
        self.setGeometry(200, 200, 1000, 600)

        main_layout = QHBoxLayout()
        # Controles izquierdos
        control_layout = QVBoxLayout()
        # Botón para cargar PDF
        self.btn_load = QPushButton('Cargar PDF', self)
        self.btn_load.clicked.connect(self.load_pdf)
        control_layout.addWidget(self.btn_load)
        # Selector de tablas
        control_layout.addWidget(QLabel('Seleccionar Tabla:'))
        self.table_selector = QComboBox()
        self.table_selector.currentIndexChanged.connect(self.change_table)
        control_layout.addWidget(self.table_selector)
        # Controles de filas
        control_layout.addWidget(QLabel('Fila inicial:'))
        self.spin_start = QSpinBox()
        self.spin_start.valueChanged.connect(self.update_filtered_table)
        control_layout.addWidget(self.spin_start)
        control_layout.addWidget(QLabel('Fila final:'))
        self.spin_end = QSpinBox()
        self.spin_end.valueChanged.connect(self.update_filtered_table)
        control_layout.addWidget(self.spin_end)
        # Filas a eliminar
        control_layout.addWidget(QLabel('Filas a eliminar (ej. 7,10,11):'))
        self.exclude_rows_input = QLineEdit()
        self.exclude_rows_input.setPlaceholderText("Ejemplo: 7,10,11")
        self.exclude_rows_input.textChanged.connect(self.update_filtered_table)
        control_layout.addWidget(self.exclude_rows_input)
        # Lista de columnas
        control_layout.addWidget(QLabel('Columnas:'))
        self.column_list = QListWidget()
        self.column_list.itemChanged.connect(self.update_filtered_table)
        control_layout.addWidget(self.column_list)
        main_layout.addLayout(control_layout)
        # Tablas
        table_layout = QVBoxLayout()
        self.original_table = QTableWidget()
        self.filtered_table = QTableWidget()
        table_layout.addWidget(QLabel('Tabla Original:'))
        table_layout.addWidget(self.original_table)
        table_layout.addWidget(QLabel('Tabla Filtrada:'))
        table_layout.addWidget(self.filtered_table)
        main_layout.addLayout(table_layout)
        self.setLayout(main_layout)

    def load_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar PDF", "", "PDF Files (*.pdf)")
        if file_path:
            try:
                self.tables = camelot.read_pdf(file_path, flavor='stream', pages='all')
                if self.tables:
                    self.table_selector.clear()
                    for i in range(len(self.tables)):
                        self.table_selector.addItem(f"Tabla {i + 1}")
                    self.current_table_index = 0
                    self.show_table(self.tables[self.current_table_index])
                else:
                    QMessageBox.warning(self, "Error", "No se encontraron tablas en el PDF")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al procesar PDF: {str(e)}")

    def change_table(self, index):
        self.current_table_index = index
        self.show_table(self.tables[index])

    def show_table(self, table):
        df = table.df
        # Configurar tabla original
        self.original_table.setRowCount(df.shape[0])
        self.original_table.setColumnCount(df.shape[1])
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                self.original_table.setItem(i, j, QTableWidgetItem(df.iloc[i, j]))
        # Configurar controles
        self.spin_start.setMaximum(df.shape[0])
        self.spin_end.setMaximum(df.shape[0])
        self.spin_end.setValue(df.shape[0])
        self.column_list.clear()
        for col in range(df.shape[1]):
            item = QListWidgetItem(f"Columna {col + 1}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.column_list.addItem(item)
        self.update_filtered_table()

    def update_filtered_table(self):
        if not self.tables or self.current_table_index >= len(self.tables):
            return
        table = self.tables[self.current_table_index]
        df = table.df
        max_rows = df.shape[0]
        start_row = min(self.spin_start.value(), max_rows)
        end_row = min(self.spin_end.value(), max_rows)
        selected_columns = [i for i in range(self.column_list.count())
                            if self.column_list.item(i).checkState() == Qt.Checked]
        max_columns = df.shape[1]
        selected_columns = [col for col in selected_columns if col < max_columns]
        exclude_rows = []
        try:
            exclude_rows = [int(row.strip()) - 1 for row in self.exclude_rows_input.text().split(",") if row.strip()]
            exclude_rows = [row for row in exclude_rows if row >= 0 and row < max_rows]
        except ValueError:
            QMessageBox.warning(self, "Advertencia", "Las filas excluidas deben ser números separados por comas.")
        try:
            filtered_df = df.iloc[start_row:end_row, selected_columns]
            rows_to_keep = [i for i in range(filtered_df.shape[0]) if i + start_row not in exclude_rows]
            filtered_df = filtered_df.iloc[rows_to_keep]
            self.filtered_table.setRowCount(filtered_df.shape[0])
            self.filtered_table.setColumnCount(filtered_df.shape[1])
            for i in range(filtered_df.shape[0]):
                for j in range(filtered_df.shape[1]):
                    self.filtered_table.setItem(i, j, QTableWidgetItem(filtered_df.iloc[i, j]))
        except IndexError as e:
            QMessageBox.critical(self, "Error", f"Error al filtrar la tabla: {str(e)}")

