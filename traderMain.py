# -*- coding: utf-8 -*-
import os
import sys
import logging
import argparse
import json
import datetime
from datetime import timedelta
import requests

import settings
from base import utils
import data_manager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError

from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5 import uic
from trader import Trader
import time

ui_path = f'{os.path.dirname(os.path.abspath(__file__))}/ui/trader_ui.ui'
form_class = uic.loadUiType(ui_path)[0]

class MainWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.sched = BackgroundScheduler()
        self.sched.start()

        self.startTradePushButton.clicked.connect(self.startPushButtonEvent)
        self.stopTradePushButton.clicked.connect(self.stopPushButtonEvent)
        self.shutdownPushButton.clicked.connect(self.shutdownPushButtonEvent)

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

    def initTrader(self):
        price_url = "http://127.0.0.1:5550/price"
        balance_url = "http://127.0.0.1:5550/balance"
        current_price_url = "http://127.0.0.1:5550/currentPrice"
        stock_code = self.inputStockCodeLineEdit.text()
        
        start_date = datetime.datetime.now() - datetime.timedelta(days=5)
        start_date = datetime.datetime.combine(start_date, datetime.time(9,0))
        end_date = datetime.datetime.combine(datetime.datetime.now(), datetime.time(16,0))

        value_network_path = os.path.join(settings.BASE_DIR,
                                                'models/a3c_lstm_value_081000_108230_006400_265520_032620.h5')
        policy_network_path = os.path.join(settings.BASE_DIR,
                                                'models/a3c_lstm_policy_081000_108230_006400_265520_032620.h5')
        
        # 공통 파라미터 설정
        
        # 키움 서버에서 차트 데이터 갱신해 저장하기
        price = requests.post(price_url, json={"code" :  stock_code, 
                                                "tick" : 1, 
                                                "start_date" : start_date.strftime("%Y%m%d%H%M%S"), 
                                                "end_date" : end_date.strftime("%Y%m%d%H%M%S")
                                                }, 
                                                headers=None)
        while not price.json():
            time.sleep(0.34)

        # 갱신된 차트 데이터 불러오기
        chart_data, training_data = data_manager.load_data(stock_code, start_date.strftime("%Y%m%d%H%M%S"), end_date.strftime("%Y%m%d%H%M%S"))

        min_trading_unit = max(
                int(1000000 / chart_data.iloc[-1]['current']), 1)
        max_trading_unit = max(
                int(10000000 / chart_data.iloc[-1]['current']), 1)
        common_params = {'gui_window':self,
                        'stock_code': stock_code,
                        'delayed_reward_threshold': 0.05,
                        'num_steps': 1,
                        'chart_data': chart_data,
                        'training_data': training_data
                        }
        # 거래 시작

        self.trader = Trader(**common_params)

    def job_trade(self):
        start_date = datetime.datetime.combine(datetime.datetime.now(), datetime.time(9,0))

        if datetime.datetime.now() >= start_date:
            self.trader.trade()

    def shutdownPushButtonEvent(self):
        exit()

    def startPushButtonEvent(self):
        self.initTrader()
        self.stockCodeLineEdit.setText(self.inputStockCodeLineEdit.text())
        self.sched.add_job(self.job_trade, 'cron', second='0', id=self.inputStockCodeLineEdit.text(), max_instances=5)
        self.logTextBrowser.append('거래 시작됨')

    def stopPushButtonEvent(self):
        self.sched.remove_all_jobs()
        self.logTextBrowser.append('거래 종료됨')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    app.exec_()
