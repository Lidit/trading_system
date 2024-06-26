# -*- coding: utf-8 -*-
import os, sys
import logging
import argparse
import json
import datetime
import data_manager
import settings
import holiday

from base import utils



from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5 import uic

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stock_code', nargs='+')
    parser.add_argument('--rl_method', 
        choices=['dqn', 'pg', 'ac', 'a2c', 'a3c'], default='a2c')
    parser.add_argument('--net', 
        choices=['dnn', 'lstm', 'cnn'], default='lstm')
    parser.add_argument('--num_steps', type=int, default=1)
    parser.add_argument('--lr', type=float, default=0.01)
    parser.add_argument('--discount_factor', type=float, default=0.9)
    parser.add_argument('--start_epsilon', type=float, default=0)
    parser.add_argument('--balance', type=int, default=50000000)
    parser.add_argument('--num_epoches', type=int, default=100)
    parser.add_argument('--delayed_reward_threshold', 
        type=float, default=0.01)
    parser.add_argument('--backend', 
        choices=['tensorflow', 'plaidml'], default='tensorflow')
    parser.add_argument('--output_name', default=utils.get_time_str())
    parser.add_argument('--value_network_name')
    parser.add_argument('--policy_network_name')
    parser.add_argument('--reuse_models', action='store_true')
    parser.add_argument('--learning', action='store_true')
    parser.add_argument('--days', type=int, default=0)
    args = parser.parse_args()

    today = datetime.date.today() + datetime.timedelta(days=0)
    print(today)
    data = holiday.getHolidayInfo(today)

    if holiday.isHoliday(data, today):
        print("오늘은 휴일 입니다. 종료.")
        exit()

    tomorrow = today + datetime.timedelta(days=1)
    data = holiday.getHolidayInfo(tomorrow)
    print(data)
    
    i = 0
    if holiday.isHoliday(data, tomorrow):
        while True:
            date = today - datetime.timedelta(days=i)
            print(date)
            data = holiday.getHolidayInfo(date)
            if holiday.isHoliday(data, date):
                if i > 0:
                    i -= 1
                break
            i += 1
    print(i)
    
    start_date = datetime.datetime.now() - datetime.timedelta(days=i)
    start_date = datetime.datetime.combine(start_date, datetime.time(9,0))
    end_date = datetime.datetime.combine(datetime.datetime.now() - datetime.timedelta(days=0), datetime.time(15,30))
    print(start_date)
    print(end_date)
    parser.add_argument('--start_date', default=start_date.strftime("%Y%m%d%H%M%S"))
    parser.add_argument('--end_date', default=end_date.strftime("%Y%m%d%H%M%S"))
    args = parser.parse_args()

    # Keras Backend 설정
    if args.backend == 'tensorflow':
        os.environ['KERAS_BACKEND'] = 'tensorflow'

    # 출력 경로 설정
    output_path = os.path.join(settings.BASE_DIR, 
        'output/{}/{}_{}_{}'.format(datetime.datetime.now().strftime("%Y%m%d%H%M%S"), args.output_name, args.rl_method, args.net))
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # 파라미터 기록
    with open(os.path.join(output_path, 'params.json'), 'w') as f:
        f.write(json.dumps(vars(args)))
    
    # 로그 기록 설정
    file_handler = logging.FileHandler(filename=os.path.join(
        output_path, "{}.log".format(args.output_name)), encoding='utf-8')
    stream_handler = logging.StreamHandler(sys.stdout)
    file_handler.setLevel(logging.DEBUG)
    stream_handler.setLevel(logging.INFO)
    logging.basicConfig(format="%(message)s",
                        handlers=[file_handler, stream_handler], level=logging.DEBUG)
    
    logging.info('start_date %s' % start_date)
    logging.info('end_date %s' % end_date)

    # 로그, Keras Backend 설정을 먼저하고 RLTrader 모듈들을 이후에 임포트해야 함
    from base.agent import Agent
    from base.learners import ActorCriticLearner, A2CLearner, A3CLearner

    # 모델 경로 준비
    value_network_path = ''
    policy_network_path = ''

    if args.value_network_name is not None:
        value_network_path = os.path.join(settings.BASE_DIR, 
            f'models\{args.value_network_name}.h5')
    else:
        value_network_path = os.path.join(
            output_path, '{}_{}_value_{}.h5'.format(
                args.rl_method, args.net, args.output_name))
    
    if args.policy_network_name is not None:
        policy_network_path = os.path.join(settings.BASE_DIR, 
            'models\{}.h5'.format(args.policy_network_name))
    else:
        policy_network_path = os.path.join(
            output_path, '{}_{}_policy_{}.h5'.format(
                args.rl_method, args.net, args.output_name))

    list_stock_code = []
    list_chart_data = []
    list_training_data = []
    list_min_trading_unit = []
    list_max_trading_unit = []
    print(args.stock_code)
    for stock_code in args.stock_code:

        print(stock_code)

        # 차트 데이터, 학습 데이터 준비
        chart_data, training_data = data_manager.load_data(stock_code, date_from=args.start_date, date_to=args.end_date)
        # 최소/최대 투자 단위 설정
        min_trading_unit = max(
            int(100000 / chart_data.iloc[-1]['current']), 1)
        max_trading_unit = max(
             int(1000000 / chart_data.iloc[-1]['current']), 1)

        # # 최소/최대 투자 단위 설정
        # min_trading_unit = max(
        #     int(100000 / chart_data.iloc[-1]['close']), 1)
        # max_trading_unit = max(
        #      int(1000000 / chart_data.iloc[-1]['close']), 1)

         # 공통 파라미터 설정
        common_params = {'rl_method': args.rl_method,
                           'delayed_reward_threshold': args.delayed_reward_threshold,
                           'net': args.net, 'num_steps': args.num_steps, 'lr': args.lr,
                             'output_path': output_path,
                             'reuse_models': args.reuse_models}

        # 강화학습 시작
        learner = None

        if args.rl_method != 'a3c':
            common_params.update({'stock_code': stock_code,
                                    'chart_data': chart_data,
                                    'training_data': training_data,
                                    'min_trading_unit': min_trading_unit, 
                                    'max_trading_unit': max_trading_unit})

            if args.rl_method == 'ac':
                learner = ActorCriticLearner(**{
                    **common_params,
                    'value_network_path': value_network_path,
                    'policy_network_path': policy_network_path})
            elif args.rl_method == 'a2c':
                learner = A2CLearner(**{
                    **common_params,
                    'value_network_path': value_network_path,
                    'policy_network_path': policy_network_path})
            if learner is not None:
                learner.run(balance=args.balance,
                            num_epoches=args.num_epoches,
                            discount_factor=args.discount_factor,
                            start_epsilon=args.start_epsilon,
                            learning=args.learning)
                learner.save_models()
        else:
            list_stock_code.append(stock_code)
            list_chart_data.append(chart_data)
            list_training_data.append(training_data)
            list_min_trading_unit.append(min_trading_unit)
            list_max_trading_unit.append(max_trading_unit)

    if args.rl_method == 'a3c':
        learner = A3CLearner(**{
            **common_params,
            'list_stock_code': list_stock_code,
            'list_chart_data': list_chart_data,
            'list_training_data': list_training_data,
            'list_min_trading_unit': list_min_trading_unit,
            'list_max_trading_unit': list_max_trading_unit,
            'value_network_path': value_network_path,
            'policy_network_path': policy_network_path})

        learner.run(balance=args.balance, num_epoches=args.num_epoches,
                    discount_factor=args.discount_factor,
                    start_epsilon=args.start_epsilon,
                    learning=args.learning)
        learner.save_models()

