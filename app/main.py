import sys
from PyQt5.QtWidgets import QApplication
#from app.views.main_window import MainWindow
from app.views.dialogs.welcome_window import WelcomeWindow

def main():
    app = QApplication(sys.argv)
    win = WelcomeWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()