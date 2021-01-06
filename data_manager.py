import pandas as pd
import numpy as np
import os
import settings

COLUMNS_CHART_DATA = ['date','current', 'open', 'high', 'low', 'volume']

COLUMNS_INDEX_DATA = ['KOSPI'] #KOSDAQ

def load_stock_data(stock_code, json_data = None):
    data = None
    if json_data is None:
        path = os.path.join(settings.BASE_DIR, f'data\stocks\{stock_code}.csv')
        data = pd.read_csv(path, thousands=',', header=None, names=COLUMNS_CHART_DATA,
            converters={'date': lambda x: str(x)})
    else:
        data = pd.read_json(json_data)
    
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
    #https://github.com/Crypto-toolbox/pandas-technical-indicators/blob/master/technical_indicators.py
    #MACD 데이터 계산
    short = 12
    long = 26
    sign = 9
    data['MACD'] = np.zeros(len(data))
    data['MACD'] =  data['current'].ewm(span = short, min_periods = short, adjust=False).mean() - data['current'].ewm(span = long, min_periods = long, adjust=False).mean()

    # data['MACD_sign'] = np.zeros(len(data))
    # data['MACD_sign'] = data['MACD'].ewm(span=sign, min_periods=sign, adjust=False).mean()

    data = average_directional_movement_index(data)

    # data['MACD_osc'] = np.zeros(len(data))
    # data['MACD_osc'] = data['MACD'] - data['MACD_sign']
    #DMI 데이터 계산

    return data

def load_stock_index_data():
    for index in COLUMNS_INDEX_DATA:
        path = os.path.join(settings.BASE_DIR, f'data\stockIndex\{index}.csv')
        data = pd.read_csv(path, thousands=',', header=None, names=COLUMNS_CHART_DATA,
        converters={'date': lambda x: str(x)})

        index = index + '_'
        windows = [5, 10, 20, 60, 120]
        for window in windows:
            data[f'{index}current_ma{window}'] = \
                data['current'].rolling(window).mean()
            data[f'{index}volume_ma{window}'] = \
                data['volume'].rolling(window).mean()

        data[f'{index}open_lastcurrent_ratio'] = np.zeros(len(data))
        data.loc[1:, f'{index}open_lastcurrent_ratio'] = \
            (data['open'][1:].values - data['current'][:-1].values) \
            / data['current'][:-1].values
        data[f'{index}high_current_ratio'] = \
            (data['high'].values - data['current'].values) \
            / data['current'].values
        data[f'{index}low_current_ratio'] = \
            (data['low'].values - data['current'].values) \
            / data['current'].values
        data[f'{index}current_lastcurrent_ratio'] = np.zeros(len(data))
        data.loc[1:, f'{index}current_lastcurrent_ratio'] = \
            (data['current'][1:].values - data['current'][:-1].values) \
            / data['current'][:-1].values
        data[f'{index}volume_lastvolume_ratio'] = np.zeros(len(data))
        data.loc[1:, f'{index}volume_lastvolume_ratio'] = \
            (data['volume'][1:].values - data['volume'][:-1].values) \
            / data['volume'][:-1] \
                .replace(to_replace=0, method='ffill') \
                .replace(to_replace=0, method='bfill').values

        for window in windows:
            data[f'{index}current_ma{window}_ratio'] = \
                (data['current'] - data[f'{index}current_ma{window}']) \
                / data[f'{index}current_ma{window}']
            data[f'{index}volume_ma{window}_ratio'] = \
                (data[f'volume'] - data[f'{index}volume_ma{window}']) \
                / data[f'{index}volume_ma{window}']
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

def load_data(stock_code, date_from=None, date_to=None, json_data = None):
    if json_data is None:
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
        
        training_data = load_stock_data(stock_code)
        #training_data = pd.merge(training_data, load_stock_index_data(), on='date')
        
        data_path = f'{default_training_dir}/3.custom_training_{stock_code}.csv'

        training_data.set_index(training_data['date'], inplace=True)

        training_data = training_data[(training_data['date'] >= date_from) & (training_data['date'] <= date_to)]
        training_data = training_data.dropna()

        training_data.drop(['date'], axis=1, inplace=True)
        training_data.to_csv(data_path, mode='w', header=False)
        return chart_data, training_data

    else:
        data = load_stock_data(stock_code, json_data)
        data = data.dropna()

        chart_data = data[COLUMNS_CHART_DATA]
        chart_data.reset_index(drop=True, inplace=True)

        training_data = load_stock_data(stock_code, json_data)
        training_data.set_index(training_data['date'], inplace=True)
        training_data = training_data.dropna()
        training_data.drop(['date'], axis=1, inplace=True)
        return chart_data, training_data
    

def average_directional_movement_index(df, n=14, n_ADX=14):
    """Calculate the Average Directional Movement Index for given data.
    
    :param df: pandas.DataFrame
    :param n: 
    :param n_ADX: 
    :return: pandas.DataFrame
    """
    i = 0
    UpI = []
    DoI = []
    while i + 1 <= df.index[-1]:
        UpMove = df.loc[i + 1, 'high'] - df.loc[i, 'high']
        DoMove = df.loc[i, 'low'] - df.loc[i + 1, 'low']
        if UpMove > DoMove and UpMove > 0:
            UpD = UpMove
        else:
            UpD = 0
        UpI.append(UpD)
        if DoMove > UpMove and DoMove > 0:
            DoD = DoMove
        else:
            DoD = 0
        DoI.append(DoD)
        i = i + 1
    i = 0
    TR_l = [0]
    while i < df.index[-1]:
        TR = max(df.loc[i + 1, 'high'], df.loc[i, 'current']) - min(df.loc[i + 1, 'low'], df.loc[i, 'current'])
        TR_l.append(TR)
        i = i + 1
    TR_s = pd.Series(TR_l)
    ATR = pd.Series(TR_s.ewm(span=n, min_periods=n).mean())
    UpI = pd.Series(UpI)
    DoI = pd.Series(DoI)
    PosDI = pd.Series(UpI.ewm(span=n, min_periods=n).mean() / ATR, name='PosDI_' + str(n))
    NegDI = pd.Series(DoI.ewm(span=n, min_periods=n).mean() / ATR, name='NegDI_' + str(n))
    ADX = pd.Series((abs(PosDI - NegDI) / (PosDI + NegDI)).ewm(span=n_ADX, min_periods=n_ADX).mean(),
                    name='ADX_' + str(n) + '_' + str(n_ADX))
    df = df.join(PosDI)
    df = df.join(NegDI)
    df = df.join(ADX)
    
    return df

if  __name__ == "__main__":
    load_data('006400', '20201108090000', '20201207153000')