import pandas as pd
import numpy as np
import os
import settings

COLUMNS_CHART_DATA = ['date', 'open', 'high', 'low', 'close', 'volume', 'dividends', 'stock splits']

COLUMNS_TRAINING_DATA_V1 = [
    'open_lastclose_ratio', 'high_close_ratio', 'low_close_ratio',
    'close_lastclose_ratio', 'volume_lastvolume_ratio',
    'close_ma5_ratio', 'volume_ma5_ratio',
    'close_ma10_ratio', 'volume_ma10_ratio',
    'close_ma20_ratio', 'volume_ma20_ratio',
    'close_ma60_ratio', 'volume_ma60_ratio',
    'close_ma120_ratio', 'volume_ma120_ratio',
]

COLUMNS_TRAINING_DATA_V2 = [
    'per', 'pbr', 'roe',
    'open_lastclose_ratio', 'high_close_ratio', 'low_close_ratio',
    'close_lastclose_ratio', 'volume_lastvolume_ratio',
    'close_ma5_ratio', 'volume_ma5_ratio',
    'close_ma10_ratio', 'volume_ma10_ratio',
    'close_ma20_ratio', 'volume_ma20_ratio',
    'close_ma60_ratio', 'volume_ma60_ratio',
    'close_ma120_ratio', 'volume_ma120_ratio',
    'market_kospi_ma5_ratio', 'market_kospi_ma20_ratio', 
    'market_kospi_ma60_ratio', 'market_kospi_ma120_ratio', 
    'bond_k3y_ma5_ratio', 'bond_k3y_ma20_ratio', 
    'bond_k3y_ma60_ratio', 'bond_k3y_ma120_ratio'
]


def preprocess(data):
    print("default data : ", data)

    windows = [5, 10, 20, 60, 120]
    for window in windows:
        data[f'close_ma{window}'] = \
            data['close'].rolling(window).mean()
        data[f'volume_ma{window}'] = \
            data['volume'].rolling(window).mean()

    print("close, volume data : ", data)

    data['open_lastclose_ratio'] = np.zeros(len(data))
    data.loc[1:, 'open_lastclose_ratio'] = \
        (data['open'][1:].values - data['close'][:-1].values) \
        / data['close'][:-1].values
    data['high_close_ratio'] = \
        (data['high'].values - data['close'].values) \
        / data['close'].values
    data['low_close_ratio'] = \
        (data['low'].values - data['close'].values) \
        / data['close'].values
    data['close_lastclose_ratio'] = np.zeros(len(data))
    data.loc[1:, 'close_lastclose_ratio'] = \
        (data['close'][1:].values - data['close'][:-1].values) \
        / data['close'][:-1].values
    data['volume_lastvolume_ratio'] = np.zeros(len(data))
    data.loc[1:, 'volume_lastvolume_ratio'] = \
        (data['volume'][1:].values - data['volume'][:-1].values) \
        / data['volume'][:-1] \
            .replace(to_replace=0, method='ffill') \
            .replace(to_replace=0, method='bfill').values

    windows = [5, 10, 20, 60, 120]
    for window in windows:
        data['close_ma%d_ratio' % window] = \
            (data['close'] - data['close_ma%d' % window]) \
            / data['close_ma%d' % window]
        data['volume_ma%d_ratio' % window] = \
            (data['volume'] - data['volume_ma%d' % window]) \
            / data['volume_ma%d' % window]

    return data


def load_data(fpath, date_from, date_to, ver='v2'):
    header = None if ver == 'v1' else 0
    data = pd.read_csv(fpath, thousands=',', header=header, names=COLUMNS_CHART_DATA,
        converters={'date': lambda x: str(x)})

    # 데이터 전처리
    data = preprocess(data)

    # 기간 필터링
    data['date'] = data['date'].str.replace('-', '')
    data = data[(data['date'] >= date_from) & (data['date'] <= date_to)]
    data = data.dropna()

    # 차트 데이터 분리
    chart_data = data[COLUMNS_CHART_DATA]

    # 학습 데이터 분리
    training_data = None
    if ver == 'v1':
        training_data = data[COLUMNS_TRAINING_DATA_V1]
    elif ver == 'v2':
        data.loc[:, ['per', 'pbr', 'roe']] = \
            data[['per', 'pbr', 'roe']].apply(lambda x: x / 100)
        training_data = data[COLUMNS_TRAINING_DATA_V2]
        training_data = training_data.apply(np.tanh)
    else:
        raise Exception('Invalid version.')
    
    default_data_dir = os.path.join(settings.BASE_DIR, 'data/stockMarket')
    dji_data = pd.read_csv(f'{default_data_dir}/DJI.csv', thousands=',', header=header, names=COLUMNS_CHART_DATA, converters={'date':lambda x: str(x)})
    dji_data.drop(['date', 'dividends', 'stock splits'], axis='columns',inplace=True)
    dji_data.rename(columns = {'open':'dji_open', 'high':'dji_high', 'low':'dji_low', 'close':'dji_close', 'volume':'dji_volume'}, inplace=True)
    training_data = training_data.append(dji_data)

    return chart_data, training_data