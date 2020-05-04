import sys
import os
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

ui_path = f'{os.path.dirname(os.path.abspath(__file__))}/ui/crawler.ui'
form_class = uic.loadUiType(ui_path)[0]

class MainWindow(QMainWindow, form_class) :
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.kiwoom = Kiwoom()

        self.kiwoom.comm_connect()

        self.return_stats_msg = ''

        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeOut)

        self.getStockDataButton.clicked.connect(self.getStockData)

    def timeOut(self):
        current_time = QTime.currentTime()

        text_time = current_time.toString("hh:mm:ss")
        time_msg = f'현재시간 : {text_time}'

        state =self.kiwoom.get_connect_state()

        if state == 1:
            state_msg = "서버 연결 중"
        else:
            state_msg = "서버 연결 끊김"
        
        if self.return_stats_msg == '':
            statusbar_msg = f'{state_msg} | {time_msg}'
        else:
            statusbar_msg = f'{state_msg} | {time_msg} | {self.return_stats_msg}'
        
        self.statusbar.showMessage(statusbar_msg)

    @decorators.return_status_msg_setter
    def getStockData(self) :
        stock_code = self.stockCodePlainTextEdit.toPlainText()
        tick_unit = ''
        tick_range = 1
        base_date = datetime.datetime.today().strftime("%Y%m%d")

        if tick_unit == "분봉":
            self.kiwoom.set_input_value("종목코드", stock_code)
            self.kiwoom.set_input_value("틱범위", tick_range)
            self.kiwoom.set_input_value("수정주가구분", 1)
            self.kiwoom.comm_rq_data("opt10080_req", "opt10080", 0, "0101")

            ohlcv = self.kiwoom.ohlcv

            while self.kiwoom.remained_data == True:
                self.kiwoom.set_input_value("종목코드", stock_code)
                self.kiwoom.set_input_value("틱범위", tick_range)
                self.kiwoom.set_input_value("수정주가구분", 1)
                self.kiwoom.comm_rq_data("opt10080_req", "opt10080", 2, "0101")
                for key, val in self.kiwoom.ohlcv.items():
                    ohlcv[key][-1:] = val
            
            df = pd.DataFrame(ohlcv, columns=['current', 'open', 'high', 'low', 'volume'], index=ohlcv['date'])
            
        elif tick_unit == "일봉":
            self.kiwoom.set_input_value("종목코드", stock_code)
            self.kiwoom.set_input_value("기준일자", base_date)
            self.kiwoom.set_input_value("수정주가구분", 1)
            self.kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")
            ohlcv = self.kiwoom.ohlcv

            while self.kiwoom.remained_data == True:
                self.kiwoom.set_input_value("종목코드", stock_code)
                self.kiwoom.set_input_value("기준일자", base_date)
                self.kiwoom.set_input_value("수정주가구분", 1)
                self.kiwoom.comm_rq_data("opt10081_req", "opt10081", 2, "0101")
                for key, val in self.kiwoom.ohlcv.items():
                    ohlcv[key][-1:] = val

            df = pd.DataFrame(ohlcv, columns=['open', 'high', 'low', 'close', 'volume', index=ohlcv['date'])
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    app.exec_()
    
