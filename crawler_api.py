import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
import pandas as pd
import argparse
from pandas import DataFrame
import csv
from PyQt5 import uic

TR_REQ_TIME_INTERVAL = 0.2

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")

        self.login_event_loop.exit()

    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString", code,
                               real_type, field_name, index, item_name)
        return ret.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)
        
        elif rqname == "opt10080_req":
            self._opt10080(rqname, trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _opt10081(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")
            # dividends = self._comm_get_data(trcode, "", rqname, i, "배당금")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            # self.ohlcv['dividends'].append(int(dividends))
            self.ohlcv['volume'].append(int(volume))

    def _opt10080(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "체결시간")
            current = abs(int(self._comm_get_data(trcode, "", rqname, i, "현재가")))
            open = abs(int(self._comm_get_data(trcode, "", rqname, i, "시가")))
            high = abs(int(self._comm_get_data(trcode, "", rqname, i, "고가")))
            low = abs(int(self._comm_get_data(trcode, "", rqname, i, "저가")))
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")

            print(f'체결 시간 {date} 현재가 {current} 시가 {open} 고가 {high} 저가 {low} 거래량 {volume}')
            

MARKET_KOSPI   = 0
MARKET_KOSDAQ  = 10

class PyMon:
    def __init__(self):
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()
        self.get_code_list()
        self.index_data = list()

    def get_code_list(self):
        self.kospi_codes = self.kiwoom.get_code_list_by_market(MARKET_KOSPI)
        self.kosdaq_codes = self.kiwoom.get_code_list_by_market(MARKET_KOSDAQ)

    def get_ohlcv(self, code, start):
        self.kiwoom.ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.set_input_value("기준일자", start)
        self.kiwoom.set_input_value("수정주가구분", 1)
        self.kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")
        time.sleep(0.2)

        df = DataFrame(self.kiwoom.ohlcv, columns=['open', 'high', 'low', 'close', 'volume'],
                       index=self.kiwoom.ohlcv['date'])
        return df

    def get_ohlcv_minute(self, code, tick):
        self.kiwoom.ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.set_input_value("틱범위", tick)
        self.kiwoom.set_input_value("수정주가구분", 1)
        self.kiwoom.comm_rq_data("opt10080_req", "opt10080", 0, "0102")
        time.sleep(0.2)
        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.set_input_value("틱범위", tick)
        self.kiwoom.set_input_value("수정주가구분", 1)
        self.kiwoom.comm_rq_data("opt10080_req", "opt10080", 2, "0102")
        df = DataFrame(self.kiwoom.ohlcv, columns=['open', 'high', 'low', 'close', 'volume'],
                       index=self.kiwoom.ohlcv['date'])
        return df


    def run(self, stock_code, start_date, end_date):
        df = self.get_ohlcv(stock_code, end_date)
        df.to_csv(f'data/stocks/{stock_code}.csv', mode='a', header=False)
        self.index_data = df.index.tolist()
        print(df)
        return self.index_data[-1]


ui_path = os.path.dirname(os.path.abspath(__file__))
ui_path = f'{ui_path}/ui/crawler.ui'
form_class = uic.loadUiType(ui_path)[0]

class WindowClass(QMainWindow, form_class) :
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.getStockDataButton.clicked.connect(self.getStockData)

    def getStockData(self) :
        app = QApplication(sys.argv)
        pymon = PyMon()
        stock_code = self.stockCodePlainTextEdit.toPlainText()
        # start_date = self.startDatePlainTextEdit.toPlainText()
        # end_date = self.endDatePlainTextEdit.toPlainText()
        pymon.get_ohlcv_minute(stock_code, 1)
        #pymon.run(str(stock_code), str(start_date), str(end_date))

    #     f = open(f'data/stocks/{stock_code}.csv','r')
    #     rdr = csv.reader(f)

    #     while pymon.run(str(stock_code), str(start_date), str(end_date)) > start_date:
    #         end_date = str(int(pymon.index_data[-1]) -1)


    # # csv 정렬후 다시저장
    #     f = open(f'data/stocks/{stock_code}.csv','r')
    #     rdr = csv.reader(f)

    #     stock_data = list()

    #     for line in rdr:
    #         stock_data.append(line)

    #     f.close()

    #     stock_data.sort()

    #     filter_index = 0
    #     for i in stock_data[0:-1]:
    #         if int(i[0]) < int(start_date) :
    #             # print(i)
    #             del stock_data[stock_data.index(i)]
    #         # filter_index += 1

    #     f = open(f'data/stocks/{stock_code}.csv','w', newline='')
    #     wr = csv.writer(f)
    #     wr.writerows(stock_data)
    #     f.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    myWindow = WindowClass()
    myWindow.show()

    app.exec_()
    