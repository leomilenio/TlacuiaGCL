import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from app.views.dialogs.welcome_window import WelcomeWindow

def resource_path(relative_path):
    """ Obtener la ruta absoluta al recurso icono,para desarrollo como para ejecutables 
    empaquetados """
    try:
        # PyInstaller crea un directorio temporal y almacena los recursos en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def main():
    app = QApplication(sys.argv)

    # Ruta del archivo de ícono
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(base_path, 'app', 'resources', 'icons', 'icon.ico')

    # Establecer el ícono global para toda la aplicación
    app.setWindowIcon(QIcon(icon_path))

    # Crear y mostrar la ventana principal
    win = WelcomeWindow()
    win.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()