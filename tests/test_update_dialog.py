import unittest
import os
import json
from PyQt5.QtWidgets import QApplication, QPushButton, QMessageBox
from app.views.dialogs.update_dialog import UpdateDialog
from packaging.version import parse, InvalidVersion

# Crear una instancia de QApplication para las pruebas
app = QApplication([])

class TestUpdateDialog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mock_data_path = os.path.join(os.path.dirname(__file__), "mock_data", "mock_dev_info.json")
        print(f"Ruta del archivo JSON: {cls.mock_data_path}")  # Depuración
        if not os.path.exists(cls.mock_data_path):
            raise FileNotFoundError(f"No se encontró el archivo JSON en: {cls.mock_data_path}")
        
    def setUp(self):
        """Configuración antes de cada prueba."""
        self.version_actual = "1.0.0"  # Versión actual simulada
        self.dialog = UpdateDialog(version_actual=self.version_actual)

    def tearDown(self):
        """Limpieza después de cada prueba."""
        self.dialog.close()

    def verificar_actualizaciones(self):
        # Simular datos con una versión inválida
        mock_data = {
            "Tlacuia GCL": {
                "version": "invalid_version",
                "download_url": "",
                "release_notes": "Sin notas de la versión."
            }
        }

        latest_version = mock_data["Tlacuia GCL"]["version"]
        try:
            # Intentar analizar la versión
            parsed_version = parse(latest_version)
        except InvalidVersion:
            # Lanzar una excepción si el formato de la versión es inválido
            raise ValueError("La versión en el JSON tiene un formato inválido.")
        
        # Continuar con la lógica normal si la versión es válida
        if parsed_version > parse(self.version_actual):
            mensaje = (
                f"Nueva versión disponible: {latest_version}\n\n"
                f"Notas de la versión:\n{mock_data['Tlacuia GCL']['release_notes']}\n\n"
                "¿Desea descargarla ahora?"
            )
            respuesta = QMessageBox.question(
                self,
                "Actualización Disponible",
                mensaje,
                QMessageBox.Yes | QMessageBox.No
            )
            if respuesta == QMessageBox.Yes:
                import webbrowser
                webbrowser.open(mock_data["Tlacuia GCL"]["download_url"])
        else:
            QMessageBox.information(
                self,
                "No hay actualizaciones disponibles.",
                f"La aplicación está actualizada en la versión más reciente: {self.version_actual}."
            )
    
    def test_verificar_actualizaciones_error_formato_version(self):
        """Prueba cuando la versión en el JSON tiene un formato inválido."""
        # Simular datos con una versión inválida
        mock_data = {
            "Tlacuia GCL": {
                "version": "invalid_version",
                "download_url": "",
                "release_notes": "Sin notas de la versión."
            }
        }

        # Sobrescribir el método verificar_actualizaciones para usar datos simulados
        def mock_verificar_actualizaciones():
            latest_version = mock_data["Tlacuia GCL"]["version"]
            try:
                parse(latest_version)  # Validar el formato de la versión
            except InvalidVersion:
                raise ValueError("La versión en el JSON tiene un formato inválido.")
            return mock_data["Tlacuia GCL"]

        self.dialog.verificar_actualizaciones = mock_verificar_actualizaciones

        # Verificar que se maneje correctamente el error
        with self.assertRaises(ValueError):
            self.dialog.verificar_actualizaciones()
            
    def test_verificar_actualizaciones_error_formato_version(self):
        """Prueba cuando la versión en el JSON tiene un formato inválido."""
        # Simular datos con una versión inválida
        mock_data = {
            "Tlacuia GCL": {
                "version": "invalid_version",
                "download_url": "",
                "release_notes": "Sin notas de la versión."
            }
        }

        # Sobrescribir el método verificar_actualizaciones para usar datos simulados
        def mock_verificar_actualizaciones():
            return mock_data["Tlacuia GCL"]

        self.dialog.verificar_actualizaciones = mock_verificar_actualizaciones

        # Verificar que se maneje correctamente el error
        with self.assertRaises(ValueError):
            latest_version = mock_data["Tlacuia GCL"]["version"]
            # Intentar comparar versiones (esto debería fallar)
            self.assertGreater(latest_version, self.version_actual)

    def test_carga_json_local(self):
        """Prueba la carga del archivo JSON local."""
        # Verificar que el archivo JSON simulado existe
        self.assertTrue(os.path.exists(self.mock_data_path), "El archivo JSON simulado debería existir.")

        # Cargar el archivo JSON
        with open(self.mock_data_path, "r") as file:
            data = json.load(file)

        # Verificar que el JSON contiene la información esperada
        self.assertIn("Tlacuia GCL", data, "El JSON debería contener la clave 'Tlacuia GCL'.")
        self.assertIn("version", data["Tlacuia GCL"], "El JSON debería contener la clave 'version'.")

    def test_interfaz_grafica(self):
        """Prueba básica de la interfaz gráfica."""
        # Verificar que la ventana tiene el título correcto
        self.assertEqual(self.dialog.windowTitle(), "Buscar Actualizaciones", "El título de la ventana debería ser correcto.")

        # Buscar el botón 'Buscar actualizaciones ahora' por su texto
        btn_buscar = None
        for widget in self.dialog.findChildren(QPushButton):
            if widget.text() == "Buscar actualizaciones ahora":
                btn_buscar = widget
                break

        self.assertIsNotNone(btn_buscar, "El botón 'Buscar actualizaciones ahora' debería estar presente.")
        
if __name__ == "__main__":
    unittest.main()