import pandas as pd
import numpy as np
import os
import settings

COLUMNS_CHART_DATA = ['date','current', 'open', 'high', 'low', 'volume']

COLUMNS_INDEX_DATA = ['KOSPI', 'KOSDAQ']

def load_stock_data(stock_code):
    path = os.path.join(settings.BASE_DIR, f'data/stocks/{stock_code}.csv')
    data = pd.read_csv(path, thousands=',', header=None, names=COLUMNS_CHART_DATA,
        converters={'date': lambda x: str(x)})

    windows = [5, 10, 20, 60, 120]
    for window in windows:
        data[f'current_ma{window}'] = \
            data['current'].rolling(window).mean()
        data[f'volume_ma{window}'] = \
            data['volume'].rolling(window).mean()
    
    data['open_lastcurrent_ratio'] = np.zeros(len(data))
    data.loc[1:, 'open_lastcurrent_ratio'] = \
        (data['open'][1:].values - data['current'][:-1].values) \
        / data['current'][:-1].values
    data['high_current_ratio'] = \
        (data['high'].values - data['current'].values) \
        / data['current'].values
    data['low_current_ratio'] = \
        (data['low'].values - data['current'].values) \
        / data['current'].values
    data['current_lastcurrent_ratio'] = np.zeros(len(data))
    data.loc[1:, 'current_lastcurrent_ratio'] = \
        (data['current'][1:].values - data['current'][:-1].values) \
        / data['current'][:-1].values
    data['volume_lastvolume_ratio'] = np.zeros(len(data))
    data.loc[1:, 'volume_lastvolume_ratio'] = \
        (data['volume'][1:].values - data['volume'][:-1].values) \
        / data['volume'][:-1] \
            .replace(to_replace=0, method='ffill') \
            .replace(to_replace=0, method='bfill').values

    for window in windows:
        data[f'current_ma{window}_ratio'] = \
            (data['current'] - data[f'current_ma{window}']) \
            / data[f'current_ma{window}']
        data[f'volume_ma{window}_ratio'] = \
            (data[f'volume'] - data[f'volume_ma{window}']) \
            / data[f'volume_ma{window}']
    return data

def load_stock_index_data():
    
    
    for index in COLUMNS_INDEX_DATA:
        path = os.path.join(settings.BASE_DIR, f'data/stockIndex/{index}.csv')
        data = pd.read_csv(path, thousands=',', header=None, names=COLUMNS_CHART_DATA,
        converters={'date': lambda x: str(x)})
        
        windows = [5, 10, 20, 60, 120]
        for window in windows:
            data[f'current_ma{window}'] = \
                data['current'].rolling(window).mean()
            data[f'volume_ma{window}'] = \
                data['volume'].rolling(window).mean()

        data['open_lastcurrent_ratio'] = np.zeros(len(data))
        data.loc[1:, 'open_lastcurrent_ratio'] = \
            (data['open'][1:].values - data['current'][:-1].values) \
            / data['current'][:-1].values
        data['high_current_ratio'] = \
            (data['high'].values - data['current'].values) \
            / data['current'].values
        data['low_current_ratio'] = \
            (data['low'].values - data['current'].values) \
            / data['current'].values
        data['current_lastcurrent_ratio'] = np.zeros(len(data))
        data.loc[1:, 'current_lastcurrent_ratio'] = \
            (data['current'][1:].values - data['current'][:-1].values) \
            / data['current'][:-1].values
        data['volume_lastvolume_ratio'] = np.zeros(len(data))
        data.loc[1:, 'volume_lastvolume_ratio'] = \
            (data['volume'][1:].values - data['volume'][:-1].values) \
            / data['volume'][:-1] \
                .replace(to_replace=0, method='ffill') \
                .replace(to_replace=0, method='bfill').values

        for window in windows:
            data[f'current_ma{window}_ratio'] = \
                (data['current'] - data[f'current_ma{window}']) \
                / data[f'current_ma{window}']
            data[f'volume_ma{window}_ratio'] = \
                (data[f'volume'] - data[f'volume_ma{window}']) \
                / data[f'volume_ma{window}']
    return data

# def load_stock_index_data(training_data, date_from, date_to):
#     for index in COLUMNS_INDEX_DATA:
#         columns = []
#         columns.append('date')
#         for i in range(1, len(COLUMNS_CHART_DATA)):
#             columns.append(f'{index}_{COLUMNS_CHART_DATA[i]}')

#         path = os.path.join(settings.BASE_DIR, f'data/stockIndex/{index}.csv')
#         data = pd.read_csv(path, thousands=',', header=None, names=COLUMNS_CHART_DATA,
#         converters={'date': lambda x: str(x)})
#         index = index + '_'
#         windows = [5, 10, 20, 60, 120]
#         for window in windows:
#             data[f'{index}current_ma{window}'] = \
#                 data[f'{index}current'].rolling(window).mean()
#             data[f'{index}volume_ma{window}'] = \
#                 data[f'{index}volume'].rolling(window).mean()

#         data[f'{index}open_lastcurrent_ratio'] = np.zeros(len(data))
#         data.loc[1:, f'{index}open_lastcurrent_ratio'] = \
#             (data['open'][1:].values - data['current'][:-1].values) \
#             / data['current'][:-1].values
#         data[f'{index}high_current_ratio'] = \
#             (data['high'].values - data['current'].values) \
#             / data['current'].values
#         data[f'{index}low_current_ratio'] = \
#             (data['low'].values - data['current'].values) \
#             / data['current'].values
#         data[f'{index}current_lastcurrent_ratio'] = np.zeros(len(data))
#         data.loc[1:, f'{index}current_lastcurrent_ratio'] = \
#             (data['current'][1:].values - data['current'][:-1].values) \
#             / data['current'][:-1].values
#         data[f'{index}volume_lastvolume_ratio'] = np.zeros(len(data))
#         data.loc[1:, f'{index}volume_lastvolume_ratio'] = \
#             (data[f'{index}volume'][1:].values - data[f'{index}volume'][:-1].values) \
#             / data[f'{index}volume'][:-1] \
#                 .replace(to_replace=0, method='ffill') \
#                 .replace(to_replace=0, method='bfill').values
        
#         for window in windows:
#             data[f'{index}current_ma{window}_ratio'] = \
#                 (data['current'] - data[f'{index}current_ma{window}']) \
#                 / data[f'{index}current_ma{window}']
#             data[f'{index}volume_ma{window}_ratio'] = \
#                 (data[f'{index}volume'] - data[f'{index}volume_ma{window}']) \
#                 / data[f'{index}volume_ma{window}']
#         training_data = pd.merge(training_data, data, on='date')
#     return training_data

def load_data(stock_code, date_from, date_to):
    default_training_dir = os.path.join(settings.BASE_DIR, 'data/training')
    if not os.path.isdir(default_training_dir):
            os.makedirs(default_training_dir)
    
    data = load_stock_data(stock_code)

    data = data[(data['date'] >= date_from) & (data['date'] <= date_to)]
    data = data.dropna()
    data_path = f'{default_training_dir}/1.default_{stock_code}.csv'
    pd.DataFrame(data).to_csv(data_path, mode='w', header=False)
    # 차트 데이터 분리
    chart_data = data[COLUMNS_CHART_DATA]
    chart_data.reset_index(drop=True, inplace=True)
    
    training_data = load_stock_index_data()
    data_path = f'{default_training_dir}/3.custom_training_{stock_code}.csv'
    training_data.set_index(training_data['date'], inplace=True)
    training_data.drop(['date'], axis=1, inplace=True)
    training_data.to_csv(data_path, mode='w', header=False)
    return chart_data, training_data


if  __name__ == "__main__":
    load_data('032620', '20200507090000', '20200512153000')