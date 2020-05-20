import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

import threading
import time

from pandas import DataFrame
import datetime
import os

from crawler_api import PyMon
from kiwoom_api import *
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, LSTM, Conv2D,BatchNormalization, Dropout, MaxPooling2D, Flatten
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.backend import set_session
import tensorflow as tf
graph = tf.get_default_graph()
sess = tf.compat.v1.Session()

import collections
from environment import Environment
from agent import Agent
from visualizer import Visualizer

import requests

class Trader:
    def __init__(self, chart_data = None, value_network=None, stock_code =None, num_steps=1, min_trading_unit=1, max_trading_unit=2,
    value_network_path=None, policy_network_path=None, balance = 10000000, delayed_reward_threshold =.05):

        # 인자 확인
        assert min_trading_unit > 0
        assert max_trading_unit > 0
        assert max_trading_unit >= min_trading_unit
        assert num_steps > 0

        # 환경 설정
        self.stock_code = stock_code
        self.chart_data = chart_data
        self.environment = Environment(chart_data)
        self.training_data = None

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

        self.balance = balance

        self.value_network = self.value_network.load_model(model_path = value_network_path)
        self.policy_network = self.policy_network.load_model(model_path = policy_network_path)


       
    def build_sample(self):
        self.chart_data = chart_data
        self.environment = Environment(chart_data)
        self.training_data = None

        self.agent = Agent(self.environment,
            min_trading_unit=min_trading_unit,
            max_trading_unit=max_trading_unit,
            delayed_reward_threshold=delayed_reward_threshold)
            
        self.environment.observe()
        if len(self.training_data) > self.training_data_idx + 1:
            self.training_data_idx += 1
            self.sample = self.training_data.iloc[
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
        self.visualizer.clear([0, len(self.chart_data)])
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
            if int( str(datetime.now().hour) + str(datetime.now().minute) ) < 1531 && int(str(datetime.now().hour) + str(datetime.now().minute)) >= 900:
                break
            next_sample = self.build_sample()
            q_sample.append(next_sample)
            pred_value = self.value_network.predict(list(q_sample))
            pred_policy = self.policy_network.predict(list(q_sample))

            # 신경망 또는 탐험에 의한 행동 결정
            action, confidence, exploration = self.agent.decide_action( pred_value, pred_policy, epsilon)

            # 결정한 행동을 수행하고 즉시 보상과 지연 보상 획득
            immediate_reward, delayed_reward = self.agent.act(action, confidence)

             # 행동 결정에 따른 거래 요청
            if action == 0:
                data = {
                "accno": "8133856511"
                "qty": self.agent.max_trading_unit,
                "price": 0,
                "code": self.stock_code,
                "type": "market",
                }
                resp = requests.post(self.balance_url, json=data)
                result = resp.json()
            elif action == 1:
                data = {
                "accno": "8133856511"
                "qty": self.agent.max_trading_unit,
                "price": 0,
                "code": self.stock_code,
                "type": "market",
                }
                resp = requests.post(self.balance_url, json=data)
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
            num_epoches_digit = int(str(datetime.now().hour) + str(datetime.now().minute))
            epoch_str = str(epoch + 10).rjust(num_epoches_digit, '0')
            time_end_epoch = time.time()
            elapsed_time_epoch = time_end_epoch - time_start_epoch
            if self.learning_cnt > 0:
                self.loss /= self.learning_cnt
            logging.info("[{}][Epoch {}/{}] Epsilon:{:.4f} "
                "#Expl.:{}/{} #Buy:{} #Sell:{} #Hold:{} "
                "#Stocks:{} PV:{:,.0f} "
                "LC:{} Loss:{:.6f} ET:{:.4f}".format(
                    self.stock_code, epoch_str, num_epoches, epsilon, 
                    self.exploration_cnt, self.itr_cnt,
                    self.agent.num_buy, self.agent.num_sell, 
                    self.agent.num_hold, self.agent.num_stocks, 
                    self.agent.portfolio_value, self.learning_cnt, 
                    self.loss, elapsed_time_epoch))
        
        self.visualize(str(time_end_epoch), num_epoches, epsilon)


if __name__ == "__main__":
    balance_url = "127.0.0.1:5000/balance"
    price_url = "127.0.0.1:5000/price"
    order_url = "127.0.0.1:5000/order"
    
    # account_num = "8133856511"
    stock_code = 108230
    cash = requests.post(balance_url, data={"accno" :  "8133856511" }, None)
    balance = cash["cash"]

    # 모델 경로 준비
    value_network_path = os.path.join(settings.BASE_DIR,
                                              f'models\{value_network_name}.h5')
    policy_network_path = os.path.join(settings.BASE_DIR,
                                               'models\{}.h5'.format(policy_network_name))

     # 공통 파라미터 설정
    chart_data, training_data = data_manager.load_data(stock_code, start_date, end_date)

    min_trading_unit = max(
            int(1000000 / chart_data.iloc[-1]['current']), 1)
    max_trading_unit = max(
             int(10000000 / chart_data.iloc[-1]['current']), 1)
    common_params = {'stock_code': stock_code,
                    'delayed_reward_threshold': delayed_reward_threshold,
                    'net': net, 
                    'num_steps': num_steps,
                    'balance' : balance,
                    'output_path': output_path,
                    'min_trading_unit': min_trading_unit, 
                    'max_trading_unit': max_trading_unit,
                    'chart_data': chart_data,
                    'training_data': training_data
                    }

    
    # 거래 시작
    trader = None

    trader =Trader(**{common_params})

    

    
