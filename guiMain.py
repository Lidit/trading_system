import sys
import os
from crawler_api import *
from PyQt5.QtWidgets import *
from PyQt5 import uic

ui_path = os.path.dirname(os.path.abspath(__file__))
ui_path = f'{ui_path}/ui/training_main.ui'
print(ui_path)
form_class = uic.loadUiType(ui_path)[0]

class WindowClass(QMainWindow, form_class) :
    def __init__(self):
        super().__init__()
        self.setupUi(self)

if __name__ == '__main__' :

    app = QApplication(sys.argv)

    myWindow = WindowClass()
    myWindow.show()

    app.exec_()