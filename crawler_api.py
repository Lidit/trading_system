import sys
import os
import time
import datetime
import pandas as pd
import csv
from pandas import DataFrame

from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5 import uic

from kiwoom_api import Kiwoom            
import decorators

MARKET_KOSPI   = 0
MARKET_KOSDAQ  = 10

TR_REQ_TIME_INTERVAL = 0.2

STOCK_DATA_PATH = f'{os.path.dirname(os.path.abspath(__file__))}/data/stocks'
STOCK_INDEX_DATA_PATH = f'{os.path.dirname(os.path.abspath(__file__))}/data/stockIndex'

ui_path = f'{os.path.dirname(os.path.abspath(__file__))}/ui/crawler.ui'
form_class = uic.loadUiType(ui_path)[0]

class MainWindow(QMainWindow, form_class) :
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    app.exec_()
    
