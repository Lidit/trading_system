# def start(self):
#         self.task.setThread(self.a, state = 'learning', stock_code = self.gui.stockCodeLineEdit.text())
#         self.task.start()

#     def a(self):
#         for i in range(10000):
#             print(i)


# -*- coding: utf-8 -*-
import os
import sys
import logging
import argparse
import json
import datetime
from datetime import timedelta

import settings
import utils
import data_manager

from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5 import uic
from trader import *

class TaskThread(QThread):
    def __init__(self, parent = None):
        QThread.__init__(self,parent)

    def setThread(self, func, **kwargs):
        self.func = func
        self.stock_code = kwargs.get('stock_code')
        # if 'state' in kwargs:
        #     stock_code = kwargs.get('stock_code')
        #     print(f'stock code : {stock_code}')
        # for key, value in kwargs.items():
        #     print(f'{key} : {value}')
    
    def stopThread(self):
        print("exit")
        exit()
    
    def run(self):
        self.func(self.stock_code)

ui_path = f'{os.path.dirname(os.path.abspath(__file__))}/ui/trader_ui.ui'
form_class = uic.loadUiType(ui_path)[0]

class MainWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        #depositLineEdit
        #availableLineEdit
        #stockCodeLineEdit
        #currentStockLineEdit
        #volumeLineEdit
        #inputStockCodeLineEdit

        #startTradePushButton
        #stopTradePushButton
        #shutdownPushButton

        #logTextBrowser

        # self.startTradeButton.clicked.connect(self.startTrade)
        # self.stopTradeButton.clicked.connect(self.stopTrade)
        # self.requestDataButton.clicked.connect(self.requestData)
        # self.exitButton.clicked.connect(self.exitEvent)
        self.data_url = "http://127.0.0.1:5550/data"

    def exitEvent(self):
        exit()

    def stopTrade(self):
        self.tradeThread.stopThread()
        self.tradeLogTextBrowser.append(f'trade 종료')

    def startTrade(self):
        self.tradeLogTextBrowser.append(f'trade 시작')
        self.tradeThread = TaskThread()
        self.tradeThread.setThread(self.startTradeThread, stock_code=self.stockCodeLineEdit.text())
        self.tradeThread.start()

    def startTradeThread(self, stock_code):
        price_url = "http://127.0.0.1:5550/price"
        balance_url = "http://127.0.0.1:5550/balance"
        # account_num = "8133856511"
        stock_code = stock_code #265520
        # keys = {'k1': 'v1', 'k2': 'v2'}

        
        # 초기 현금잔고 init
        cash = requests.post(balance_url, json={"accno" :  "8133856511" }, headers=None )
        time.sleep(0.34)
        cash = cash.json()
        balance = cash['cash']

        # 모델 경로 준비
        # value_network_path = os.path.join(settings.BASE_DIR,
        #                                           f'models\{value_network_name}.h5')
        # policy_network_path = os.path.join(settings.BASE_DIR,
        #                                            'models\{}.h5'.format(policy_network_name))

        value_network_path = os.path.join(settings.BASE_DIR,
                                                'models/a2c_lstm_value_20200526052844.h5')
        policy_network_path = os.path.join(settings.BASE_DIR,
                                                'models/a2c_lstm_policy_20200526052844.h5')

        
        # 공통 파라미터 설정
        
        # 키움 서버에서 차트 데이터 갱신해 저장하기
        price = requests.post(price_url, json={"code" :  stock_code }, headers=None )
        while not price.json():
            time.sleep(0.34)
        print(price.json())

        # 갱신된 차트 데이터 불러오기
        # chart_data, training_data 매일매일 일자 갱신 수동으로 할필요없게 수정 부탁함
        chart_data, training_data = data_manager.load_data(stock_code, "20200528090000", "20200528163000")
        
        # print(chart_data)
        # print(training_data)
    

        min_trading_unit = max(
                int(1000000 / chart_data.iloc[-1]['current']), 1)
        max_trading_unit = max(
                int(10000000 / chart_data.iloc[-1]['current']), 1)
        common_params = {'gui_window':self,
                        'stock_code': stock_code,
                        'delayed_reward_threshold': 0.05,
                        'num_steps': 1,
                        'balance' : balance,
                        # 'output_path': os.path.join(settings.BASE_DIR,
                        #                'output/tradetest'),
                        'min_trading_unit': min_trading_unit, 
                        'max_trading_unit': max_trading_unit,
                        'chart_data': chart_data,
                        'training_data': training_data
                        }

        
        # 거래 시작

        trader = Trader(**common_params)
        trader.trade()
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    app.exec_()
