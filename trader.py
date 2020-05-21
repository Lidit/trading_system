import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

import threading
import time

from pandas import DataFrame
import datetime
import os
import settings
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

from networks import LSTMNetwork

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
from environment import Environment
from agent import Agent
from visualizer import Visualizer
import data_manager

import requests

class Trader:
    def __init__(self, chart_data = None, training_data=None, stock_code =None, num_steps=1, min_trading_unit=1, max_trading_unit=2,
    value_network_path=None, policy_network_path=None, balance = 9986883, delayed_reward_threshold =.05):

        # 인자 확인
        assert min_trading_unit > 0
        assert max_trading_unit > 0
        assert max_trading_unit >= min_trading_unit
        assert num_steps > 0
        self.balance_url = "http://127.0.0.1:5550/balance"
        self.price_url = "http://127.0.0.1:5550/price"
        self.order_url = "http://127.0.0.1:5550/order"

        # 환경 설정
        self.training_data_idx = -1
        self.stock_code = stock_code
        self.chart_data = chart_data
        self.environment = Environment(chart_data)
        self.environment.observe()
        # print(self.environment.observe())
        self.training_data = training_data
        # print(self.environment.get_price())
        self.agent = Agent(self.environment,
            min_trading_unit=min_trading_unit,
            max_trading_unit=max_trading_unit,
            delayed_reward_threshold=delayed_reward_threshold)

        self.visualizer = Visualizer()

        # 메모리
        self.memory_sample = []
        self.memory_action = []
        self.memory_reward = []
        self.memory_value = []
        self.memory_policy = []
        self.memory_pv = []
        self.memory_num_stocks = []
        self.memory_exp_idx = []
        self.memory_learning_idx = []

        self.balance = 9986883
        self.agent.set_balance(self.balance)
        self.agent.reset()
        print(self.agent.portfolio_value)
        print(self.agent.balance)
        print(self.agent.initial_balance)
        # self.agent.set_balance(balance)

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
        chart_data, training_data = data_manager.load_data(stock_code, "20200512090000", "20200520135000")
        self.environment = Environment(chart_data)
        self.environment.observe()

        self.agent = Agent(self.environment,
            min_trading_unit=min_trading_unit,
            max_trading_unit=max_trading_unit,
            delayed_reward_threshold=0.05)
        self.balance = 9986883
        self.agent.set_balance(self.balance)
        self.agent.reset()
        # self.agent.environment.observe()
        
        if len(training_data) > self.training_data_idx + 1:
            self.training_data_idx += 1
            self.sample = training_data.iloc[
                self.training_data_idx].tolist()
            self.sample.extend(self.agent.get_states())
            return self.sample
        return None
        
   


    def reset(self):
        self.sample = None
        self.training_data_idx = -1
        # 환경 초기화
        self.environment.reset()
        # 에이전트 초기화
        self.agent.reset()
        # 가시화 초기화
        # self.visualizer.clear([0, len(self.chart_data)])
        # 메모리 초기화
        self.memory_sample = []
        self.memory_action = []
        self.memory_reward = []
        self.memory_value = []
        self.memory_policy = []
        self.memory_pv = []
        self.memory_num_stocks = []
        self.memory_exp_idx = []
        self.memory_learning_idx = []


    def trade(self):

        q_sample = collections.deque(maxlen=1)
        
        self.reset()
        
        
        while True:
            # self.reset()
            time_start_epoch = time.time()
            next_sample = self.build_sample()
            q_sample.append(next_sample)
            pred_value = self.value_network.predict(list(q_sample))
            pred_policy = self.policy_network.predict(list(q_sample))

            # 신경망 또는 탐험에 의한 행동 결정
            action, confidence, exploration = self.agent.decide_action( pred_value, pred_policy, 0)

            # 결정한 행동을 수행하고 즉시 보상과 지연 보상 획득
            immediate_reward, delayed_reward = self.agent.act(action, confidence)

             # 행동 결정에 따른 거래 요청
            if action == 0:
                data = {
                "accno": "8133856511",
                "qty": self.agent.max_trading_unit,
                "price": 0,
                "code": self.stock_code,
                "type": "market",
                }
                resp = requests.post(self.order_url, data=data)
                result = resp.json()
            elif action == 1:
                data = {
                "accno": "8133856511",
                "qty": self.agent.max_trading_unit,
                "price": 0,
                "code": self.stock_code,
                "type": "market",
                }
                resp = requests.post(self.order_url, data=data)
                result = resp.json()

            # 행동 및 행동에 대한 결과를 기억
            self.memory_sample.append(list(q_sample))
            self.memory_action.append(action)
            self.memory_reward.append(immediate_reward)
            if self.value_network is not None:
                self.memory_value.append(pred_value)
            if self.policy_network is not None:
                self.memory_policy.append(pred_policy)
            self.memory_pv.append(self.agent.portfolio_value)
            self.memory_num_stocks.append(self.agent.num_stocks)
            if exploration:
                self.memory_exp_idx.append(self.training_data_idx)

            # 지연 보상 발생된 경우 미니 배치 학습
            # if learning and (delayed_reward != 0):
            #     self.fit(delayed_reward, discount_factor)
        # 거래 정보 로그 기록
            # num_epoches_digit = int(str(datetime.now().hour) + str(datetime.now().minute))
            # epoch_str = str(10).rjust(num_epoches_digit, '0')
            # time_end_epoch = time.time()
            # elapsed_time_epoch = time_end_epoch - time_start_epoch
            # if self.learning_cnt > 0:
            #     self.loss /= self.learning_cnt
            # logging.info("[{}][Epoch {}/{}] Epsilon:{:.4f} "
            #     "#Expl.:{}/{} #Buy:{} #Sell:{} #Hold:{} "
            #     "#Stocks:{} PV:{:,.0f} "
            #     "LC:{} Loss:{:.6f} ET:{:.4f}".format(
            #         self.stock_code, epoch_str, num_epoches, epsilon, 
            #         self.exploration_cnt, self.itr_cnt,
            #         self.agent.num_buy, self.agent.num_sell, 
            #         self.agent.num_hold, self.agent.num_stocks, 
            #         self.agent.portfolio_value, self.learning_cnt, 
            #         self.loss, elapsed_time_epoch))
        
        # self.visualize(str(time_end_epoch), num_epoches, epsilon)


if __name__ == "__main__":

    
    balance_url = "http://127.0.0.1:5550/balance"
    # account_num = "8133856511"
    stock_code = 108230
    keys = {'k1': 'v1', 'k2': 'v2'}
    cash = requests.post(balance_url, json={"accno" :  "8133856511" }, headers=None )
    time.sleep(0.2)
    cash = cash.json()
    balance = cash['cash']

    # 모델 경로 준비
    # value_network_path = os.path.join(settings.BASE_DIR,
    #                                           f'models\{value_network_name}.h5')
    # policy_network_path = os.path.join(settings.BASE_DIR,
    #                                            'models\{}.h5'.format(policy_network_name))

    value_network_path = os.path.join(settings.BASE_DIR,
                                              'models/a2c_lstm_value_20200513043216.h5')
    policy_network_path = os.path.join(settings.BASE_DIR,
                                               'models/a2c_lstm_policy_20200513043216.h5')


     # 공통 파라미터 설정
    chart_data, training_data = data_manager.load_data(stock_code, "20200512090000", "20200520135000")
    
    # print(chart_data)
    # print(training_data)
    
    min_trading_unit = max(
            int(1000000 / chart_data.iloc[-1]['current']), 1)
    max_trading_unit = max(
             int(10000000 / chart_data.iloc[-1]['current']), 1)
    common_params = {'stock_code': stock_code,
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

    

    
