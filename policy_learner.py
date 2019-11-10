import os
import locale
import logging
import time
import datetime
import numpy as np
import settings
from Environment import Environment
from Agent import Agent
from PolicyNetwork import PolicyNetwork
from Visualizer import Visualizer

logger = logging.getLooger(__name__)

class PolicyLearner:

    def __init__(self, stock_code, chart_data, training_data=None, min_trading_unit=1, max_trading_unit=2, delayed_reward_threshold=.05, lr=0.01):
        self.stock_code = stock_code
        self.chart_data = chart_data
        self.environment = Environment(chart_data)

        self.agent = Agent(self.environment, min_trading_unit=min_trading_unit, max_trading_unit=max_trading_unit, delayed_reward_threshold=delayed_reward_threshold)
        self.training_data = training_data
        self.sample = None
        self.training_data_idx = -1

        self.num_features = self.training_data.shape[1] + self.agent.STATE_DIM
        self.policy_network = PolicyNetwork(input_dim=self.num_features, output_dim=self.agent.NUM_ACTIONS, lr=lr)
        self.visualizer = Visualizer()

    def reset(self):
        self.sample = None
        self.training_data_idx = -1

    def fit(self, num_epoches=1000, max_memory=60, balance=10000000, discount_factor=0, start_epsilon=0.5, learning = True):
        logger.info("LR: {lr}, DF: {discount_factor}, "
                    "TU:[{min_trading_unit}, {max_trading_unit}], "
                    "DRT: {delayed_reward_threshold}".format(lr = self.policy_network.lr,
                                                             discount_factor = discount_factor,
                                                             min_trading_unit = self.agent.min_trading_unit,
                                                             max_trading_unit = self.agent.max_trading_unit,
                                                             delayed_reward_threshold = self.agent.delayed_Reward_Threshold))
        self.visualizer.prepare(self.environment.chart_data)

        epoch_summary_dir = os.path.join(
            settings.BASE_DIR, 'epoch_summary/%s/epoch_summary_%s' % (
                self.stock_code, settings.timestr))
        if not os.path.isdir(epoch_summary_dir):
            os.makedirs(epoch_summary_dir)

        self.agent.set_balance(balance)

        max_portfolio_value = 0
        epoch_win_cnt = 0

        for epoch in range(num_epoches):
            loss = 0.
            itr_cnt = 0
            win_cnt = 0
            exploration_cnt = 0
            batch_size = 0
            pos_learning_cnt = 0
            neg_learning_cnt = 0

            memory_sample = []
            memory_action = []
            memory_reward = []
            memory_prob = []
            memory_pv = []
            memory_num_stocks = []
            memory_exp_idx = []
            memory_learning_idx = []

            self.environment.reset()
            self.agent.reset()
            self.policy_network.reset()
            self.reset()

            self.visualizer.clear([0, len(self.chart_data)])

            if learning:
                epsilon = start_epsilon * (1. - float(epoch) / (num_epoches - 1))
            else:
                epsilon = 0

            while True:
                next_sample = self._build_sample()
                if next_sample is None:
                    break
                action, confidence, exploration = self.agent.decide_action(
                    self.policy_network, self.sample, epsilon)

                immediate_reward, delayed_reward = self.agent.act(action, confidence)

                memory_sample.append(next_sample)
                memory_action.append(action)
                memory_reward.append(immediate_reward)
                memory_pv.append(self.agent.portfolio_value)
                memory_num_stocks.append(self.agent.num_stocks)
                memory = [(
                    memory_sample[i],
                    memory_action[i],
                    memory_reward[i])
                    for i in list(range(len(memory_action)))[-max_memory:]
                ]
                if exploration:
                    memory_exp_idx.append(itr_cnt)
                    memory_prob.append([np.nan] * Agent.NUM_ACTIONS)
                else:
                    memory_prob.append(self.policy_network.prob)

                batch_size += 1
                itr_cnt += 1
                exploration_cnt += 1 if exploration else 0
                win_cnt += 1 if delayed_reward > 0 else 0

                if delayed_reward == 0 and batch_size >= max_memory:
                    delayed_reward = immediate_reward
                    self.agent.base_portfolio_value = self.agent.portfolio_value
                if learning and delayed_reward != 0:
                    batch_size = min(batch_size, max_memory)
                    x, y = self._get_batch(
                        memory, batch_size, discount_factor, delayed_reward)
                    if len(x) > 0:
                        if delayed_reward > 0:
                            pos_learning_cnt += 1
                        else:
                            neg_learning_cnt += 1

                        loss += self.policy_network.train_on_batch(x, y)
                        memory_learning_idx.append([itr_cnt, delayed_reward])
                    batch_size = 0

            num_epoches_digit = len(str(num_epoches))
            epoch_str = str(epoch + 1).rjust(num_epoches_digit, '0')

            self.visualizer.plot(
                epoch_str=epoch_str, num_epoches=num_epoches, epsilon=epsilon,
                action_list=Agent.ACTIONS, actions=memory_action,
                num_stocks=memory_num_stocks, outvals=memory_prob,
                exps=memory_exp_idx, learning=memory_learning_idx,
                initial_balance=self.agent.initial_balance, pvs=memory_pv
            )
            self.visualizer.save(os.path.join(
                epoch_summary_dir, 'epoch_summary_%s_%s.png' % (
                    settings.timestr, epoch_str)))

            if pos_learning_cnt + neg_learning_cnt > 0:
                loss /= pos_learning_cnt + neg_learning_cnt
            logging.info("[Epoch %s/%s]\tEpsilon:%.4f\t#Expl.:%d/%d\t"
                         "#Buy:%d\t#Sell:%d\t#Hold:%d\t"
                         "#Stocks:%d\tPV:%s\t"
                         "POS:%s\tNEG:%s\tLoss:%10.6f" % (
                             epoch_str, num_epoches, epsilon, exploration_cnt, itr_cnt,
                             self.agent.num_buy, self.agent.num_sell, self.agent.num_hold,
                             self.agent.num_stocks,
                             locale.currency(self.agent.portfolio_value, grouping=True),
                             pos_learning_cnt, neg_learning_cnt, loss))

            max_portfolio_value = max(
                max_portfolio_value, self.agent.portfolio_value)
            if self.agent.portfolio_value > self.agent.initial_balance:
                epoch_win_cnt += 1

        logging.info("Max PV: %s, \t # Win: %d" % (
            locale.currency(max_portfolio_value, grouping=True), epoch_win_cnt))

    def _get_batch(self, memory, batch_size, discount_factor, delayed_reward):
        x = np.zeros((batch_size, 1, self.num_features))
        y = np.full((batch_size, self.agent.NUM_ACTIONS), 0.5)

        for i, (sample, action, reward) in enumerate(
                reversed(memory[-batch_size:])):
            x[i] = np.array(sample).reshape((-1, 1, self.num_features))
            y[i, action] = (delayed_reward + 1) / 2
            if discount_factor > 0:
                y[i, action] *= discount_factor ** i
        return x, y

    def _build_sample(self):
        self.environment.observe()
        if len(self.training_data) > self.training_data_idx + 1:
            self.training_data_idx += 1
            self.sample = self.training_data.iloc[self.training_data_idx].tolist()
            self.sample.extend(self.agent.get_states())
            return self.sample
        return None

    def trade(self, model_path=None, balance=2000000):
        if model_path is None:
            return
        self.policy_network.load_model(model_path=model_path)
        self.fit(balance=balance, num_epoches=1, learning=False)