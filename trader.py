import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

import time

from pandas import DataFrame
import datetime

from crawler_api import PyMon
from kiwoom_api import *
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, LSTM, Conv2D,BatchNormalization, Dropout, MaxPooling2D, Flatten
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.backend import set_session
import tensorflow as tf
graph = tf.get_default_graph()
sess = tf.compat.v1.Session()

class Trader:
    def __init__(self, value_network=None, stock_code =None, min_trading_unit=1, max_trading_unit=2
    net, value_network_path=None, policy_network_path=None, balance = 10000000):
        os.environ['KERAS_BACKEND'] = backend
        # 로그, Keras Backend 설정을 먼저하고 RLTrader 모듈들을 이후에 임포트해야 함
        from agent import Agent
        from learners import DQNLearner, PolicyGradientLearner, ActorCriticLearner, A2CLearner, A3CLearner
        
        self.environment = Environment(chart_data)

        self.agent = Agent(self.environment,
                    min_trading_unit=min_trading_unit,
                    max_trading_unit=max_trading_unit,
                    delayed_reward_threshold=delayed_reward_threshold)

        self.balance = balance

        self.value_network_path = value_network_path
        self.policy_network_path = policy_network_path

        self.value_network = load_model(model_path=self.value_network_path)
        self.policy_network = load_model(model_path=self.policy_network_path)

    def build_sample(self):
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

    def trade():
        q_sample = collections.deque(maxlen=1)
        self.reset()
        while( int(str(datetime.now().hour) + str(datetime.now().minute)) < 1531 ):        
            next_sample = self.build_sample()
            q_sample.append(next_sample)
            pred_value = self.value_network.predict(list(q_sample))