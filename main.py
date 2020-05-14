# -*- coding: utf-8 -*-
import os
import sys
import logging
import argparse
import json

import settings
import utils
import data_manager

from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5 import uic

ui_path = f'{os.path.dirname(os.path.abspath(__file__))}/ui/training_main.ui'
form_class = uic.loadUiType(ui_path)[0]


class MainWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.startLearningButton.clicked.connect(self.startLearning)
        self.stockCodeLineEdit.setText('010060')
        self.numEpochesLineEdit.setText('1000')
        self.balanceLineEdit.setText('10000000')
        self.lrLineEdit.setText('0.001')
        self.discountFactorLineEdit.setText('0.9')
        self.startEpsilonLineEdit.setText('1')
        self.outputNameLineEdit.setText(utils.get_time_str())

    def startLearning(self):
        self.startLearningButton.setEnabled(False)
        print(self.stockCodeLineEdit.text())
        stock_code = self.stockCodeLineEdit.text()
        num_epoches = int(self.numEpochesLineEdit.text())
        balance = int(self.balanceLineEdit.text())
        lr = float(self.lrLineEdit.text())
        discount_factor = float(self.discountFactorLineEdit.text())
        start_epsilon = float(self.startEpsilonLineEdit.text())
        output_name = self.outputNameLineEdit.text()
        rl_method = 'a2c'
        net = 'lstm'
        num_steps = 5
        delayed_reward_threshold = 0.1
        backend = 'tensorflow'
        value_network_name = ""
        policy_network_name = ""

        reuse_models = False
        learning = True
        start_date = "20200505090000"
        end_date = "20200512153000"

        os.environ['KERAS_BACKEND'] = backend

        output_path = os.path.join(settings.BASE_DIR,
                                   'output/{}_{}_{}'.format(output_name, rl_method, net))
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # 파라미터 기록
        # with open(os.path.join(output_path, 'params.json'), 'w') as f:
        #     f.write(json.dumps(vars(args)))

        # 로그 기록 설정
        file_handler = logging.FileHandler(filename=os.path.join(
            output_path, "{}.log".format(output_name)), encoding='utf-8')
        stream_handler = logging.StreamHandler(sys.stdout)
        file_handler.setLevel(logging.DEBUG)
        stream_handler.setLevel(logging.INFO)
        logging.basicConfig(format="%(message)s",
                            handlers=[file_handler, stream_handler], level=logging.DEBUG)

        # 로그, Keras Backend 설정을 먼저하고 RLTrader 모듈들을 이후에 임포트해야 함
        from agent import Agent
        from learners import DQNLearner, PolicyGradientLearner, ActorCriticLearner, A2CLearner, A3CLearner

        # 모델 경로 준비
        value_network_path = ''
        policy_network_path = ''
        if value_network_name is not "":
            value_network_path = os.path.join(settings.BASE_DIR,
                                              f'models\{value_network_name}.h5')
        else:
            value_network_path = os.path.join(
                output_path, '{}_{}_value_{}.h5'.format(
                    rl_method, net, output_name))
        if policy_network_name is not "":
            policy_network_path = os.path.join(settings.BASE_DIR,
                                               'models\{}.h5'.format(policy_network_name))
        else:
            policy_network_path = os.path.join(
                output_path, '{}_{}_policy_{}.h5'.format(
                    rl_method, net, output_name))

        list_stock_code = []
        list_chart_data = []
        list_training_data = []
        list_min_trading_unit = []
        list_max_trading_unit = []

        # for stock_code in stock_code:
        #     # 차트 데이터, 학습 데이터 준비
        chart_data, training_data = data_manager.load_data(stock_code, start_date, end_date)
        print(chart_data)
        print(training_data)
        # 최소/최대 투자 단위 설정
        min_trading_unit = max(
            int(100000 / chart_data.iloc[-1]['low']), 1)
        max_trading_unit = max(
             int(1000000 / chart_data.iloc[-1]['low']), 1)

        # # 최소/최대 투자 단위 설정
        # min_trading_unit = max(
        #     int(100000 / chart_data.iloc[-1]['close']), 1)
        # max_trading_unit = max(
        #      int(1000000 / chart_data.iloc[-1]['close']), 1)

         # 공통 파라미터 설정
        common_params = {'rl_method': rl_method,
                           'delayed_reward_threshold': delayed_reward_threshold,
                           'net': net, 'num_steps': num_steps, 'lr': lr,
                             'output_path': output_path,
                             'reuse_models': reuse_models}

        # 강화학습 시작
        learner = None

        if rl_method != 'a3c':
            common_params.update({'stock_code': stock_code,
                                    'chart_data': chart_data,
                                    'training_data': training_data,
                                    'min_trading_unit': min_trading_unit, 
                                    'max_trading_unit': max_trading_unit})

            if rl_method == 'dqn':
                learner = DQNLearner(**{**common_params,
                                        'value_network_path': value_network_path})
            elif rl_method == 'pg':
                learner = PolicyGradientLearner(**{**common_params,
                                                    'policy_network_path': policy_network_path})
            elif rl_method == 'ac':
                learner = ActorCriticLearner(**{
                    **common_params,
                    'value_network_path': value_network_path,
                    'policy_network_path': policy_network_path})
            elif rl_method == 'a2c':
                learner = A2CLearner(**{
                    **common_params,
                    'value_network_path': value_network_path,
                    'policy_network_path': policy_network_path})
            if learner is not None:
                learner.run(balance=balance,
                            num_epoches=num_epoches,
                            discount_factor=discount_factor,
                            start_epsilon=start_epsilon,
                            learning=learning)
                learner.save_models()
        else:
            list_stock_code.append(stock_code)
            list_chart_data.append(chart_data)
            list_training_data.append(training_data)
            list_min_trading_unit.append(min_trading_unit)
            list_max_trading_unit.append(max_trading_unit)

        if rl_method == 'a3c':
            learner = A3CLearner(**{
                **common_params,
                'list_stock_code': list_stock_code,
                'list_chart_data': list_chart_data,
                'list_training_data': list_training_data,
                'list_min_trading_unit': list_min_trading_unit,
                'list_max_trading_unit': list_max_trading_unit,
                'value_network_path': value_network_path,
                'policy_network_path': policy_network_path})

            learner.run(balance=balance, num_epoches=num_epoches,
                        discount_factor=discount_factor,
                        start_epsilon=start_epsilon,
                        learning=learning)
            learner.save_models()
        self.startLearningButton.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    app.exec_()
