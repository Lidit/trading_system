import pandas as pd
import numpy as np
import os
import settings

COLUMNS_CHART_DATA = ['date', 'open', 'high', 'low', 'close', 'volume']
REMOVE_COLUMNS_CHART_DATA = [ 'open', 'high', 'low', 'close', 'volume']

COLUMNS_TRAINING_DATA = ['date',
    'open_lastclose_ratio', 'high_close_ratio', 'low_close_ratio',
    'close_lastclose_ratio', 'volume_lastvolume_ratio',
    'close_ma5_ratio', 'volume_ma5_ratio',
    'close_ma10_ratio', 'volume_ma10_ratio',
    'close_ma20_ratio', 'volume_ma20_ratio',
    'close_ma60_ratio', 'volume_ma60_ratio',
    'close_ma120_ratio', 'volume_ma120_ratio',
]

COLUMNS_INDEX_DATA = ['DJI', 'NASDAQ', 'KOSPI']

def load_stock_data(stock_code):
    path = os.path.join(settings.BASE_DIR, f'data/stocks/{stock_code}.csv')
    data = pd.read_csv(path, thousands=',', header=None, names=COLUMNS_CHART_DATA,
        converters={'date': lambda x: str(x)})
    data['date'] = data['date'].str.replace('-', '')

    windows = [5, 10, 20, 60, 120]
    for window in windows:
        data[f'close_ma{window}'] = \
            data['close'].rolling(window).mean()
        data[f'volume_ma{window}'] = \
            data['volume'].rolling(window).mean()
    
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

    for window in windows:
        data[f'close_ma{window}_ratio'] = \
            (data['close'] - data[f'close_ma{window}']) \
            / data[f'close_ma{window}']
        data[f'volume_ma{window}_ratio'] = \
            (data[f'volume'] - data[f'volume_ma{window}']) \
            / data[f'volume_ma{window}']
    return data

def load_stock_index_data(training_data):
    for index in COLUMNS_INDEX_DATA:
        path = os.path.join(settings.BASE_DIR, f'data/stockIndex/{index}.csv')
        data = pd.read_csv(path, thousands=',', header=None, names=COLUMNS_CHART_DATA,
        converters={'date': lambda x: str(x)})
        data['date'] = data['date'].str.replace('-', '')
        
        index = index + '_'
        windows = [5, 10, 20, 60, 120]
        for window in windows:
            data[f'{index}close_ma{window}'] = \
                data['close'].rolling(window).mean()
            data[f'{index}volume_ma{window}'] = \
                data['volume'].rolling(window).mean()

        data[f'{index}open_lastclose_ratio'] = np.zeros(len(data))
        data.loc[1:, f'{index}open_lastclose_ratio'] = \
            (data['open'][1:].values - data['close'][:-1].values) \
            / data['close'][:-1].values
        data[f'{index}high_close_ratio'] = \
            (data['high'].values - data['close'].values) \
            / data['close'].values
        data[f'{index}low_close_ratio'] = \
            (data['low'].values - data['close'].values) \
            / data['close'].values
        data[f'{index}close_lastclose_ratio'] = np.zeros(len(data))
        data.loc[1:, f'{index}close_lastclose_ratio'] = \
            (data['close'][1:].values - data['close'][:-1].values) \
            / data['close'][:-1].values
        data[f'{index}volume_lastvolume_ratio'] = np.zeros(len(data))
        data.loc[1:, f'{index}volume_lastvolume_ratio'] = \
            (data['volume'][1:].values - data['volume'][:-1].values) \
            / data['volume'][:-1] \
                .replace(to_replace=0, method='ffill') \
                .replace(to_replace=0, method='bfill').values
        
        for window in windows:
            data[f'{index}close_ma{window}_ratio'] = \
                (data['close'] - data[f'{index}close_ma{window}']) \
                / data[f'{index}close_ma{window}']
            data[f'{index}volume_ma{window}_ratio'] = \
                (data[f'volume'] - data[f'{index}volume_ma{window}']) \
                / data[f'{index}volume_ma{window}']
        training_data = pd.merge(training_data, data, on='date')
    return training_data

def load_data(stock_code, date_from, date_to):
    default_training_dir = os.path.join(settings.BASE_DIR, 'data/training')
    if not os.path.isdir(default_training_dir):
            os.makedirs(default_training_dir)
    
    data = load_stock_data(stock_code)
    data_path = f'{default_training_dir}/1.default_{stock_code}.csv'
    pd.DataFrame(data).to_csv(data_path, mode='w', header=False)
    # 차트 데이터 분리
    chart_data = data[COLUMNS_CHART_DATA]
    
    # 학습 데이터 분리
    training_data = None
    training_data = data[COLUMNS_TRAINING_DATA]

    data_path = f'{default_training_dir}/2.default_training_{stock_code}.csv'
    pd.DataFrame(training_data).to_csv(data_path, mode='w', header=False)

    training_data = load_stock_index_data(training_data)
    
    data_path = f'{default_training_dir}/3.custom_training_{stock_code}.csv'
    training_data.to_csv(data_path, mode='w', header=False)
    training_data.set_index(training_data['date'], inplace=True)
    return chart_data, training_data