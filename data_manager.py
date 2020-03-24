import pandas as pd
import numpy as np

def load_chart_data(fpath):
    chart_data = pd.read_csv(fpath, thousands=",", header=None)
    chart_data.columns =['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']
    return chart_data

def preprocess(chart_data):
    prep_data = chart_data
    windows = [5, 10, 20, 60, 120]

    for window in windows:
        prep_data['close_ma{}'.format(window)] = prep_data['Close'].rolling(window).mean()
        prep_data['volume_ma{}'.format(window)] = (
            prep_data['Volume'].rolling(window).mean())
    return prep_data

def build_training_data(prep_data):
    training_data = prep_data

    training_data['open_lastclose_ratio'] = np.zeros(len(training_data))
    training_data.loc[1:, 'open_lastclose_ratio'] = \
        (training_data['Open'][1:].values - training_data['Close'][:-1].values) / \
        training_data['Close'][:-1].values
    training_data['high_close_ratio'] = \
        (training_data['High'].values - training_data['Close'].values) / \
        training_data['Close'].values
    training_data['low_close_ratio'] = \
        (training_data['Low'].values - training_data['Close'].values) / \
        training_data['Close'].values
    training_data['close_lastclose_ratio'] = np.zeros(len(training_data))
    training_data.loc[1:, 'close_lastclose_ratio'] = \
        (training_data['Close'][1:].values - training_data['Close'][:-1].values) / \
        training_data['Close'][:-1].values
    training_data['volume_lastvolume_ratio'] = np.zeros(len(training_data))
    training_data.loc[1:, 'volume_lastvolume_ratio'] = \
        (training_data['Volume'][1:].values - training_data['Volume'][:-1].values) / \
        training_data['Volume'][:-1]\
            .replace(to_replace=0, method='ffill')\
            .replace(to_replace=0, method='bfill').values

    windows = [5, 10, 20, 60, 120]
    for window in windows:
        training_data['close_ma%d_ratio' % window] = \
            (training_data['Close'] - training_data['close_ma%d' % window]) / \
            training_data['close_ma%d' % window]
        training_data['volume_ma%d_ratio' % window] = \
            (training_data['Volume'] - training_data['volume_ma%d' % window]) / \
            training_data['volume_ma%d' % window]

    return training_data