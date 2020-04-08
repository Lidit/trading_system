import pandas as pd
import numpy as np
import os
import settings

COLUMNS_CHART_DATA = ['date', 'open', 'high', 'low', 'close', 'volume', 'dividends', 'stock splits']

COLUMNS_TRAINING_DATA_V1 = ['date',
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

COLUMNS_INDEX_DATA = ['DJI', 'NASDAQ', 'KOSPI', 'KOSDAQ']

def load_stock_data(ver, stock_code):
    header = None if ver == 'v1' else 0
    path = os.path.join(settings.BASE_DIR, f'data/stocks/{stock_code}.csv')
    data = pd.read_csv(path, thousands=',', header=header, names=COLUMNS_CHART_DATA,
        converters={'date': lambda x: str(x)})

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

def load_stock_index_data(ver, training_data):
    header = None if ver == 'v1' else 0
    for index in COLUMNS_INDEX_DATA:
        path = os.path.join(settings.BASE_DIR, f'data/stockIndex/{index}.csv')
        data = pd.read_csv(path, thousands=',', header=header, names=COLUMNS_CHART_DATA,
        converters={'date': lambda x: str(x)})

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
        data.drop(COLUMNS_CHART_DATA, axis='columns',inplace=True)
        training_data = training_data.append(data)
    return training_data

def load_data(stock_code, date_from, date_to, ver='v2'):
    default_training_dir = os.path.join(settings.BASE_DIR, 'data/training')
    if not os.path.isdir(default_training_dir):
            os.makedirs(default_training_dir)
    
    data = load_stock_data(ver, stock_code)

    data_path = f'{default_training_dir}/defaultData.csv'
    pd.DataFrame(data).to_csv(data_path, mode='w', header=False)

    #기간 필터링
    # data['date'] = data['date'].str.replace('-', '')
    # data = data[(data['date'] >= date_from) & (data['date'] <= date_to)]
    # data = data.dropna()

    # data_path = f'{default_training_dir}/fillterData.csv'
    # pd.DataFrame(data).to_csv(data_path, mode='w', header=False)

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
    
    data_path = f'{default_training_dir}/defaultTrainingData.csv'
    pd.DataFrame(training_data).to_csv(data_path, mode='w', header=False)

    # training_data = load_stock_index_data(ver, training_data)
    
    # data_path = f'{default_training_dir}/customTraining.csv'
    # training_data_pd = pd.DataFrame(training_data)
    # training_data_pd.to_csv(data_path, mode='w', header=False)
    return chart_data, training_data