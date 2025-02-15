import pandas as pd

# Crear un archivo Excel simulado
data_excel = {
    "descripcion": ["Libro A", "Libro B"],
    "precio": [100.00, 200.00],
    "descuento": [0.00, 10.00],
    "f_articulo": ["978-3-16-148410-0", "978-1-4028-9462-6"],
    "total": [500.00, 900.00],
    "cnt_column": [5, 10]
}
df_excel = pd.DataFrame(data_excel)
df_excel.to_excel("mock_geslib.xlsx", index=False)

# Crear un archivo CSV simulado
data_csv = {
    "ISBN": ["978-3-16-148410-0", "978-1-4028-9462-6"],
    "Cantidad": [5, 15],
    "PNT": [500.00, 250.00]
}
df_csv = pd.DataFrame(data_csv)
df_csv.to_csv("mock_factura.csv", index=False)