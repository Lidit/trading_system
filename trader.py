import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

import threading
import time

from pandas import DataFrame

import os
import settings
import datetime
from datetime import timedelta

backend = 'tensorflow'
os.environ['KERAS_BACKEND'] = backend
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, LSTM, Conv2D, \
        BatchNormalization, Dropout, MaxPooling2D, Flatten
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.backend import set_session
import tensorflow as tf
graph = tf.get_default_graph()
sess = tf.compat.v1.Session()

from base.networks import LSTMNetwork

# from crawler_api import PyMon
from kiwoom_api import *
# from tensorflow.keras.models import Model
# from tensorflow.keras.layers import Input, Dense, LSTM, Conv2D,BatchNormalization, Dropout, MaxPooling2D, Flatten
# from tensorflow.keras.optimizers import SGD
# from tensorflow.keras.backend import set_session
# import tensorflow as tf
# graph = tf.get_default_graph()
# sess = tf.compat.v1.Session()

import collections
from base.environment import Environment, RealTimeEnvironment
from tradeAgent import TradeAgent
from base.visualizer import Visualizer
import data_manager

import requests
import json

import logging
from logging import FileHandler

#accno 8136846611 한지민
#accno 8141007211

formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')

# 로그 파일 핸들러
now = datetime.datetime.now().isoformat()[:10]
logf = now + ".log"
logf = os.path.join("traderLogs", logf)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
fh_log = FileHandler(os.path.join(BASE_DIR, logf), encoding='utf-8')
fh_log.setLevel(logging.DEBUG)
fh_log.setFormatter(formatter)

# stdout handler
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(formatter)

# 로거 생성 및 핸들러 등록
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh_log)
logger.addHandler(stdout_handler)

class Trader:
    def __init__(self, gui_window = None, chart_data = None, training_data=None, stock_code =None, num_steps=1,
    value_network_path=None, policy_network_path=None, delayed_reward_threshold =.05):

        self.balance_url = "http://127.0.0.1:5550/balance"
        self.price_url = "http://127.0.0.1:5550/price"
        self.order_url = "http://127.0.0.1:5550/order"

        # 환경 설정
        self.gui_window = gui_window
        self.training_data_idx = -1
        self.stock_code = stock_code
        self.chart_data = chart_data
        self.environment = RealTimeEnvironment(chart_data)
        self.environment.observe() 
        self.training_data = training_data 

        self.printLog('초기 잔고 및 주식 정보 갱신')
        cash = requests.post(self.balance_url, json={}, headers=None )
        time.sleep(0.5)
        cash = cash.json()
        balance = cash["balance"]
        stock_dict = cash["dict"]


        self.agent = TradeAgent(self.environment, gui_window, stock_code, balance, stock_dict)
        
        self.gui_window.depositLineEdit.setText(f'{balance}')
        self.gui_window.currentStockLineEdit.setText(f'{self.environment.get_price()}')
        self.gui_window.volumeLineEdit.setText(f'{self.environment.get_value()}')

        self.num_features = self.agent.STATE_DIM
        if self.training_data is not None:
            self.num_features += self.training_data.shape[1]
        
        self.value_network = LSTMNetwork(
                input_dim=self.num_features, 
                output_dim=self.agent.NUM_ACTIONS, 
               lr=.001, num_steps=1, 
                shared_network=None, 
                activation='linear', loss='mse')
        self.value_network.load_model(model_path = value_network_path)

        self.policy_network = LSTMNetwork(
                input_dim=self.num_features, 
                output_dim=self.agent.NUM_ACTIONS, 
               lr=.001, num_steps=1, 
                shared_network=None, 
                activation='sigmoid', loss='binary_crossentropy')
        self.policy_network.load_model(model_path = policy_network_path)

       
    def build_sample(self):
        # self.chart_data = chart_data
        
        start_date = datetime.datetime.now() - datetime.timedelta(days=5)
        start_date = datetime.datetime.combine(start_date, datetime.time(9,0))
        end_date = datetime.datetime.combine(datetime.datetime.now(), datetime.time(16,0))

        # 샘플한번 만들때마다 차트 데이터 갱신
        price = requests.post(self.price_url, json={"code" :  self.stock_code, 
                                                "tick" : 1, 
                                                "start_date" : start_date.strftime("%Y%m%d%H%M%S"), 
                                                "end_date" : end_date.strftime("%Y%m%d%H%M%S")
                                                }, 
                                                headers=None)
        time.sleep(0.5)

        while not price.json():
            time.sleep(0.1)

        self.printLog('차트 정보 갱신')

        chart_data, training_data = data_manager.load_data(self.stock_code, start_date.strftime("%Y%m%d%H%M%S"), end_date.strftime("%Y%m%d%H%M%S"))
        self.chart_data = chart_data
        self.environment.set_chart_data(self.chart_data)
        self.agent.environment.set_chart_data(self.chart_data)
        self.environment.observe()

        self.agent.environment.set_chart_data(self.chart_data)
        
        self.sample = training_data.iloc[-1].tolist()
        self.sample.extend(self.agent.get_states())
        return self.sample

    def reset(self):
        self.sample = None
        self.training_data_idx = -1

    def trade(self):
        self.printLog(f'정보 업데이트 및 AI 판단 : {datetime.datetime.now().strftime("%Y%m%d%H%M%S")}')

        q_sample = collections.deque(maxlen=1)

        next_sample = self.build_sample()
        q_sample.append(next_sample)
        pred_value = self.value_network.predict(list(q_sample)[-1])
        pred_policy = self.policy_network.predict(list(q_sample)[-1])

        # 신경망 또는 탐험에 의한 행동 결정
        action, confidence, exploration = self.agent.decide_action( pred_value, pred_policy, 0)
        
        self.printLog(f'행동 : {action}')
        self.printLog(f'confidence : {confidence}')
        self.printLog(f'exploration : {exploration}')

        if not self.agent.validate_action(action):
            action = TradeAgent.ACTION_HOLD
        
        self.printLog(f'검증된 행동 : {action}')
        self.printLog(f'예수금 : {self.agent.balance}')
        self.printLog(f'보유 주식 수 : {self.agent.num_stocks}')
        
        # 행동 결정에 따른 거래 요청
        if action == 0:
            self.printLog("매수")
            data = {
            "qty": self.agent.decide_buy_unit(confidence),
            "price": 0,
            "code": self.stock_code,
            "type": "market",
            }
            resp = requests.post(self.order_url, data=json.dumps(data))
            time.sleep(0.5)
            # data = resp.json()
                
        elif action == 1:
            self.printLog("매도")
            data = {
            "qty": -(self.agent.decide_sell_unit(confidence)), 
            "price": 0,
            "code": self.stock_code,
            "type": "market"
            }
            resp = requests.post(self.order_url, data=json.dumps(data))
            time.sleep(0.5)

        elif action == 2:
            self.printLog("관망")

        cash = requests.post(self.balance_url, json={}, headers=None )
        time.sleep(0.5)
        cash = cash.json()
        balance = cash['balance']
        stockDict = cash["dict"]
        
        self.agent.set_balance(balance)
        if self.stock_code in stockDict:
            self.agent.set_num_stocks(stockDict[self.stock_code]["보유수량"])
        else:
            self.agent.set_num_stocks(0)

        self.printLog(f'예수금 : {self.agent.balance}')
        self.printLog(f'보유 주식 수 : {self.agent.num_stocks}')
        
        self.gui_window.depositLineEdit.setText(f'{balance}')
        self.gui_window.currentStockLineEdit.setText(f'{self.environment.get_price()}')
        self.gui_window.volumeLineEdit.setText(f'{self.environment.get_value()}')

        self.printLog('')

    def printLog(self, log):
        logger.debug(log)
        self.gui_window.logTextBrowser.append(f'{log}')