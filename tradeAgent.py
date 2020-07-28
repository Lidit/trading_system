import numpy as np
from base import *


class TradeAgent:
    # 에이전트 상태가 구성하는 값 개수
    STATE_DIM = 2  # 주식 보유 비율, 포트폴리오 가치 비율

    # 매매 수수료 및 세금
    TRADING_CHARGE = 0.0035  # 거래 수수료 (일반적으로 0.015%)
    TRADING_TAX = 0.0025  # 거래세 (실제 0.25%)

    # 행동
    ACTION_BUY = 0  # 매수
    ACTION_SELL = 1  # 매도
    ACTION_HOLD = 2  # 홀딩

    # 인공 신경망에서 확률을 구할 행동들
    ACTIONS = [ACTION_BUY, ACTION_SELL]
    NUM_ACTIONS = len(ACTIONS)  # 인공 신경망에서 고려할 출력값의 개수

    def __init__(
        self, environment, gui_window, stock_code, balance, stock_dick):
        self.gui_window = gui_window
        
        
        self.printLog('에이전트 초기화 및 설정')
        # Environment 객체
        # 현재 주식 가격을 가져오기 위해 환경 참조
        self.environment = environment

        # Agent 클래스의 속성
        self.initial_balance = balance  # 초기 자본금
        self.balance = balance  # 현재 현금 잔고

        if stock_code in stock_dick:
            current_value = abs(stock_dick[stock_code]["현재가"])
            self.num_stocks = stock_dick[stock_code]["보유수량"]
            self.base_portfolio_value = (current_value * self.num_stocks) + self.balance
            self.portfolio_value = self.base_portfolio_value
        else:
            self.num_stocks = 0
            self.base_portfolio_value = self.balance
            self.portfolio_value = self.base_portfolio_value

        self.max_buy_limit = self.balance / 2
        self.unit_limit = self.max_buy_limit * 0.1
        

        # Agent 클래스의 상태
        self.ratio_hold = 0  # 주식 보유 비율
        self.ratio_portfolio_value = 0  # 포트폴리오 가치 비율

    def set_balance(self, balance):
        self.balance = balance
    
    def set_num_stocks(self, num_stocks):
        self.num_stocks = num_stocks
    
    def set_portfolio_value(self, portfolio_value):
        self.portfolio_value = portfolio_value

    def get_states(self):
        # self.environment.observe()
        self.printLog(f'"현재 evironment에서 인식하는 가격: " {self.environment.get_price()}')
        self.printLog(f'"현재 포트폴리오 가치: " {self.portfolio_value}')

        self.ratio_hold = self.num_stocks / int(
            self.portfolio_value / self.environment.get_price())
        self.ratio_portfolio_value = (
            self.portfolio_value / self.base_portfolio_value
        )
        return (
            self.ratio_hold,
            self.ratio_portfolio_value
        )

    def decide_action(self, pred_value, pred_policy, epsilon):
        confidence = 0.

        pred = pred_policy
        if pred is None:
            pred = pred_value

        if pred is None:
            # 예측 값이 없을 경우 탐험
            epsilon = 1
        else:
            # 값이 모두 같은 경우 탐험
            maxpred = np.max(pred)
            if (pred == maxpred).all():
                epsilon = 1

        # 탐험 결정
        if np.random.rand() < epsilon:
            exploration = True
            action = np.random.randint(self.NUM_ACTIONS - 1) + 1
        else:
            exploration = False
            action = np.argmax(pred)

        confidence = .5

        if pred_policy is not None:
            confidence = pred[action]
        elif pred_value is not None:
            confidence = utils.sigmoid(pred[action])

        return action, confidence, exploration

    def validate_action(self, action):
        if action == TradeAgent.ACTION_BUY:
            # 적어도 1주를 살 수 있는지 확인
            value = self.environment.get_price() * (1 + self.TRADING_CHARGE) * (1 + self.TRADING_TAX)
            if self.balance < value or (self.balance - value) < self.max_buy_limit:
                return False

        elif action == TradeAgent.ACTION_SELL:
            # 주식 잔고가 있는지 확인 
            if self.num_stocks <= 0:
                return False
        return True

    def decide_buy_unit(self, confidence):
        if self.balance < self.initial_balance - self.max_buy_limit:
            return 0
        count = 0
        value = self.environment.get_price() * (1 + self.TRADING_CHARGE) * (1 + self.TRADING_TAX)

        while value < self.unit_limit and self.balance > value:
            count = count + 1
            value = self.environment.get_price() * count * (1 + self.TRADING_CHARGE) * (1 + self.TRADING_TAX)

        if count > 0:
            count = count - 1
        
        self.printLog(f'매수 수량 : {count}')
        return count 


    def decide_sell_unit(self, confidence):
        if self.num_stocks < 1:
            self.printLog(f'매도 수량 : 0')
            return 0
        
        sell_count = self.num_stocks / 2
        
        if sell_count >= 1:
            self.printLog(f'매도 수량 : {sell_count}')
            return sell_count
        else:
            self.printLog(f'매도 수량 : 1')
            return 1

    def printLog(self, log):
        if self.gui_window is not None:
            self.gui_window.logTextBrowser.append(f'{log}')