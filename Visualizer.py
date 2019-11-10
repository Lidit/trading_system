import numpy as np
import matplotlib.pyplot as plt
from mpl_finance import candlestick_ohlc


class Visualizer:

    def __init__(self):
        self.fig = None
        self.axes = None

    def prepare(self, chart_data):
        self.fig, self.axes = plt.subplots(nrows=4, ncols=1, facecolor='w', shares=True)
        for ax in self.axes:
            ax.get_xaxis().get_major_formatter().set_scientific(False)
            ax.get_yaxis().get_major_formatter().set_scientific(False)

        self.axes[0].set_ylabel('Env')

        x = np.arange(len(chart_data))
        volume = np.array(chart_data)[:, -1].tolist()
        self.axes[0].bar(x, volume, color='b', alpha=0.3)

        ax = self.axes[0].twinx()
        ohlc = np.hstack((x.reshpae(-1, 1), np.array(chart_data)[:, 1:-1]))

        candlestick_ohlc(ax, ohlc, colorup='r', colordown='b')

    def plot(self, epoch_str=None, num_epoches=None, epsilon=None, action_list=None, actions=None, num_stocks=None,
             outvals=None, exps=None, learning=None, initial_balance=None, pvs=None):
        x = np.arrange(len(actions))
        actions = np.array(actions)
        outvals = np.array(outvals)
        pvs_base = np.zeros(len(actions)) + initial_balance

        colors = ['r', 'b']

        for actiontype, color in zip(action_list, colors):
            for i in x[actions == actiontype]:
                self.axes[1].axvline(i, color=color, alpha=0.1)
            self.axes[1].plot(x, num_stocks, '-k')

        for exp_idx in exps:
            self.axes[2].axvline(exp_idx, color='y')
        for idx, outval in zip(x, outvals):
            color = 'white'
            if outval.argmax() == 0:
                color = 'r'
            elif outval.argmax() == 1:
                color = 'b'
            self.axes[2].axvline(idx, color=color, alpha=0.1)
        styles = ['.r', '.b']
        for action, style in zip(action_list, styles):
            self.axes[2].plot(x, outvals[:, action], style)

        self.axes[3].axhline(initial_balance, linestyle='-', color='gray')
        self.axes[3].fill_between(x, pvs, pvs_base, where=pvs > pvs_base, facecolor='r', alpha=0.1)
        self.axes[3].fill_between(x, pvs, pvs_base, where=pvs < pvs_base, facecolor='b', alpha=0.1)

        self.axes[3].plot(x, pvs, '-k')

        for learning_idx, delayed_reward in learning:
            if delayed_reward > 0:
                self.axes[3].axvline(learning_idx, color='r', alpha=0.1)
            else:
                self.axes[3].axvline(learning_idx, color='b', alpha=0.1)

        self.fig.suptitle('Epoch %s/%s (e=%.2f)' % (epoch_str, num_epoches, epsilon))

        plt.tight_layout()
        plt.subplots_adjust(top=.9)

    def clear(self, xlim):
        for ax in self.axes[1:]:
            ax.cla()
            ax.relim()
            ax.autoscale()

            self.axes[1].set_ylabel('Agent')
            self.axes[2].set_ylabel('PG')
            self.axes[3].set_ylabel('PV')
            for ax in self.axes:
                ax.set_xlim(xlim)
                ax.get_xaxis().get_major_formatter().set_scientific(False)
                ax.get_yaxis().get_major_formatter().set_scientific(False)
                ax.ticklabel_format(useOffset=False)

    def sav(self, path):
        plt.savefig(path)