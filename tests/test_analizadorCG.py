import unittest
import pandas as pd
from PyQt5.QtWidgets import QApplication
from app.views.tools.gslibCut_analisis import AnalizadorCorteGeslib

# Crear una aplicación Qt para evitar errores al inicializar QDialog
app = QApplication([])

class TestGenerarReportes(unittest.TestCase):
    def setUp(self):
        """Inicializa el analizador y configura los DataFrames de prueba."""
        self.analizador = AnalizadorCorteGeslib()

    def test_generar_reporte_tipo_1(self):
        """
        Prueba la generación del reporte tipo 1:
        - Todos los ISBN son congruentes.
        - Todas las cantidades y precios netos son congruentes.
        """
        # Función auxiliar para generar df_geslib con 50 elementos
        def generar_df_geslib(num_elementos):
            data = {
                "f_articulo": [f"978013468599{i}" for i in range(1, num_elementos + 1)],
                "total": [float(i * 10) for i in range(1, num_elementos + 1)],  # Precios crecientes
                "cnt_column": [i for i in range(1, num_elementos + 1)]          # Cantidades crecientes
            }
            return pd.DataFrame(data)

        # Función auxiliar para generar df_TotalAnalisis con 50 elementos
        def generar_df_total_analisis(num_elementos):
            data = {
                "ISBN": [f"978013468599{i}" for i in range(1, num_elementos + 1)],
                "Congruencia del ISBN": [1] * num_elementos,
                "Aparición en Reporte": [1] * num_elementos,
                "Aparición en Factura": [1] * num_elementos,
                "Congruencia de cantidad": [1] * num_elementos,
                "Congruencia de PNT": [1] * num_elementos,
                "Notas": [f"Nota para ISBN {i}: La congruencia es correcta" for i in range(1, num_elementos + 1)]
            }
            return pd.DataFrame(data)

        # Generar los DataFrames de prueba con 50 elementos
        self.analizador.df_geslib = generar_df_geslib(50)
        df_total_analisis = generar_df_total_analisis(50)

        # Generar el reporte tipo 1
        self.analizador.generar_reporte(df_total_analisis)

    def test_generar_reporte_tipo_2(self):
        """
        Prueba la generación del reporte tipo 2:
        - Todos los ISBN son congruentes.
        - Hay incongruencias en cantidades o precios netos.
        """
        # DataFrame de prueba para df_TotalAnalisis
        data_total_analisis = {
            "ISBN": ["9780134685991", "9780262033848"],
            "Congruencia del ISBN": [1, 1],
            "Aparición en Reporte": [1, 1],
            "Aparición en Factura": [1, 1],
            "Congruencia de cantidad": [0, 1],  # Incongruencia en cantidad
            "Congruencia de PNT": [1, 0],      # Incongruencia en precio neto
            "Notas": [
                "Existe una diferencia en cantidad: CR = 1 ; CF = 2",
                "Existe una diferencia de PNT: PNR = 100.0 ; PNF = 200.0"
            ]
        }
        df_total_analisis = pd.DataFrame(data_total_analisis)

        # Generar el reporte tipo 2
        self.analizador.generar_reporte(df_total_analisis)

    def test_generar_reporte_tipo_3(self):
        """
        Prueba la generación del reporte tipo 3:
        - Algunos ISBN no son congruentes.
        - Hay múltiples incongruencias (cantidad, precio neto, aparición).
        - Se prueban dos casos: un DataFrame con 30 elementos y otro con 50.
        """
        # Función auxiliar para generar un DataFrame de prueba
        def generar_df_prueba(num_elementos):
            data = {
                "ISBN": [f"978013468599{i}" for i in range(1, num_elementos + 1)],
                "Congruencia del ISBN": [1 if i % 2 == 0 else 0 for i in range(1, num_elementos + 1)],
                "Aparición en Reporte": [1 if i % 3 != 0 else 0 for i in range(1, num_elementos + 1)],
                "Aparición en Factura": [1 if i % 4 != 0 else 0 for i in range(1, num_elementos + 1)],
                "Congruencia de cantidad": [1 if i % 5 == 0 else 0 for i in range(1, num_elementos + 1)],
                "Congruencia de PNT": [1 if i % 6 == 0 else 0 for i in range(1, num_elementos + 1)],
                "Notas": [
                    f"Nota para ISBN {i}: Esta es una prueba de congruencia"
                    for i in range(1, num_elementos + 1)
                ]
            }
            return pd.DataFrame(data)

        # Generar DataFrames de prueba
        df_30 = generar_df_prueba(30)
        print(f"Tamaño del DataFrame (50 elementos): {len(df_30)}") 
        # Caso 2: Probar con un DataFrame de 50 elementos
        df_50 = generar_df_prueba(50)
        print(f"Tamaño del DataFrame (50 elementos): {len(df_50)}")  # Debería imprimir 50

        # Caso 1: Probar con un DataFrame de 30 elementos
        print("Generando reporte tipo 3 para 30 elementos...")
        self.analizador.generar_reporte(df_30)

        # Caso 2: Probar con un DataFrame de 50 elementos
        print("Generando reporte tipo 3 para 50 elementos...")
        self.analizador.generar_reporte(df_50)


if __name__ == "__main__":
    unittest.main()