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

#일진 다이아 081000
#톱텍 108230
#삼성sdi 006400
#ap 시스템 265520
#유비케어 032620

class MainWindow(QMainWindow, form_class) :
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.kiwoom = Kiwoom()

        self.kiwoom.comm_connect()

        self.return_status_msg = ''

        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeOut)
        
        self.getStockDataButton.clicked.connect(self.getStockData)

        start_date = datetime.datetime.now() - datetime.timedelta(days=30)
        start_date = datetime.datetime.combine(start_date, datetime.time(9,0))
        end_date = datetime.datetime.combine(datetime.datetime.now(), datetime.time(16,0))
        self.startDateDateEdit.setDate(start_date)
        self.endDateDateEdit.setDate(end_date)

    def timeOut(self):
        current_time = QTime.currentTime()

        text_time = current_time.toString("hh:mm:ss")
        time_msg = f'현재시간 : {text_time}'

        state =self.kiwoom.get_connect_state()

        if state == 1:
            state_msg = "서버 연결 중"
        else:
            state_msg = "서버 연결 끊김"

        if self.return_status_msg == '':
            statusbar_msg = f'{state_msg} | {time_msg}'
        else:
            statusbar_msg = f'{state_msg} | {time_msg} | {self.return_status_msg}'
        
        self.statusbar.showMessage(statusbar_msg)

    @decorators.call_printer
    def getStockData(self) :
        self.getStockDataButton.setEnabled(False)
        stock_code = self.stockCodeLineEdit.text()
        tick_unit = self.tickTypeComboBox.currentText()
        tick_range = 1
        base_date = datetime.datetime.today().strftime("%Y%m%d%H%M%S")

        start_datetime = datetime.datetime.fromordinal(self.startDateDateEdit.date().toPyDate().toordinal())
        start_dateitme = start_datetime.replace(hour=9, minute=0, second=0)
        start_date = start_dateitme.strftime("%Y%m%d%H%M%S")

        end_datetime = datetime.datetime.fromordinal(self.endDateDateEdit.date().toPyDate().toordinal())
        end_dateitme = end_datetime.replace(hour=16, minute=0, second=0)
        end_date = end_dateitme.strftime("%Y%m%d%H%M%S")

        if tick_unit == "분봉":
            self.kiwoom.set_input_value("종목코드", stock_code)
            self.kiwoom.set_input_value("틱범위", tick_range)
            self.kiwoom.set_input_value("수정주가구분", 1)
            self.kiwoom.comm_rq_data("opt10080_req", "opt10080", 0, "0101")

            ohlcv = self.kiwoom.ohlcv

            while self.kiwoom.remained_data == True:
                time.sleep(TR_REQ_TIME_INTERVAL)
                if ohlcv['date'][-1] < start_date:
                    break
                self.return_stats_msg = "분봉 받는중..."
                self.kiwoom.set_input_value("종목코드", stock_code)
                self.kiwoom.set_input_value("틱범위", tick_range)
                self.kiwoom.set_input_value("수정주가구분", 1)
                self.kiwoom.comm_rq_data("opt10080_req", "opt10080", 2, "0101")
                for key, val in self.kiwoom.ohlcv.items():
                    ohlcv[key][-1:] = val
            
            df = pd.DataFrame(ohlcv, columns=['date','current', 'open', 'high', 'low', 'volume'])
            df = df[df.date >= start_date]
            df = df.sort_values(by=['date'], axis=0)
            df = df.reset_index(drop=True)
            df.to_csv(f'{STOCK_DATA_PATH}/{stock_code}.csv', mode='w', header=False)
            
        elif tick_unit == "일봉":
            self.kiwoom.set_input_value("종목코드", stock_code)
            self.kiwoom.set_input_value("기준일자", base_date)
            self.kiwoom.set_input_value("수정주가구분", 1)
            self.kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")
            ohlcv = self.kiwoom.ohlcv

            while self.kiwoom.remained_data == True:
                time.sleep(TR_REQ_TIME_INTERVAL)
                self.kiwoom.set_input_value("종목코드", stock_code)
                self.kiwoom.set_input_value("기준일자", base_date)
                self.kiwoom.set_input_value("수정주가구분", 1)
                self.kiwoom.comm_rq_data("opt10081_req", "opt10081", 2, "0101")
                for key, val in self.kiwoom.ohlcv.items():
                    ohlcv[key][-1:] = val

            df = pd.DataFrame(ohlcv, columns=['open', 'high', 'low', 'close', 'volume'], index=ohlcv['date'])
            df.to_csv(f'{STOCK_DATA_PATH}/{stock_code}.csv', mode='w')
        
        if self.checkBox.isChecked():
            self.kiwoom.set_input_value("업종코드", "001")
            self.kiwoom.set_input_value("틱범위", "1")
            self.kiwoom.comm_rq_data("opt20005_req", "opt20005", 0, "0101")

            while self.kiwoom.remained_data == True:
                time.sleep(TR_REQ_TIME_INTERVAL)
                if ohlcv['date'][-1] < start_date:
                    break
                self.return_stats_msg = "코스피 분봉 받는중..."
                self.kiwoom.set_input_value("업종코드", "001")
                self.kiwoom.set_input_value("틱범위", "1")
                self.kiwoom.comm_rq_data("opt20005_req", "opt20005", 2, "0101")

            df = pd.DataFrame(ohlcv, columns=['date','current', 'open', 'high', 'low', 'volume'])
            df = df[df.date >= start_date]
            df = df.sort_values(by=['date'], axis=0)
            df = df.reset_index(drop=True)
            df.to_csv(f'{STOCK_INDEX_DATA_PATH}/KOSPI.csv', mode='w', header=False)

            self.kiwoom.set_input_value("업종코드", "101")
            self.kiwoom.set_input_value("틱범위", "1")
            self.kiwoom.comm_rq_data("opt20005_req", "opt20005", 0,"0101")

            while self.kiwoom.remained_data == True:
                time.sleep(TR_REQ_TIME_INTERVAL)
                if ohlcv['date'][-1] < start_date:
                    break
                self.return_stats_msg = "코스닥 분봉 받는중..."
                self.kiwoom.set_input_value("업종코드", "101")
                self.kiwoom.set_input_value("틱범위", "1")
                self.kiwoom.comm_rq_data("opt20005_req", "opt20005", 2, "0101")

            df = pd.DataFrame(ohlcv, columns=['date','current', 'open', 'high', 'low', 'volume'])
            df = df[df.date >= start_date]
            df = df.sort_values(by=['date'], axis=0)
            df = df.reset_index(drop=True)
            df.to_csv(f'{STOCK_INDEX_DATA_PATH}/KOSDAQ.csv', mode='w', header=False)
        self.getStockDataButton.setEnabled(True)
        
        
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    app.exec_()
    
