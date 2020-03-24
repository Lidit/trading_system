import logging
import os
import settings
import data_manager
from policy_learner import PolicyLearner
from crawler import Crawler
import pandas as pd

stock_code = '006400' # 삼성SDI

# 로그 기록
log_dir = os.path.join(settings.BASE_DIR, 'logs/%s' % stock_code)
timestr =settings.get_time_str()
file_handler = logging.FileHandler(filename=os.path.join(log_dir, "%s_%s.log" % (stock_code, timestr)), encoding="utf-8")
stream_handler = logging.StreamHandler()
file_handler.setLevel(logging.DEBUG)
stream_handler.setLevel(logging.INFO)
logging.basicConfig(format="%(message)s", handlers=[file_handler,stream_handler], level=logging.DEBUG)

if __name__ == '__main__':
    # # stock_code = '005930' # 일단 삼성전자--
    
    # cr = Crawler()
    #
    # # kospi, kosdaq 종목코드 각각 다운로드
    # kospi_df = cr.get_download_kospi()
    # kosdaq_df = cr.get_download_kosdaq()
    #
    # # data frame merge
    # code_df = pd.concat([kospi_df, kosdaq_df])
    #
    # # data frame정리
    # code_df = code_df[['회사명', '종목코드']]
    #
    # # data frame title 변경 '회사명' = name, 종목코드 = 'code'
    # code_df = code_df.rename(columns={'회사명': 'name', '종목코드': 'code'})
    #
    # # 사용 예시
    # # stock_code = cr.get_code(code_df,'회사명')
    # stock_name = '삼성SDI'
    # stock_code = cr.get_code(code_df, stock_name)

    # 데이터 준비
    chart_data = data_manager.load_chart_data(os.path.join(settings.BASE_DIR, 'data/{}.csv'.format(stock_code)))
    prep_data = data_manager.preprocess(chart_data)
    training_data = data_manager.build_training_data(prep_data)

    # 기간 필터링
    training_data = training_data[(training_data['Date'] >= '2008-12-01') & (training_data['Date'] <= '2018-12-31')]
    training_data = training_data.dropna()

    # 차트 데이터 분리
    features_chart_data = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    chart_data = training_data[features_chart_data]

    # 학습 데이터 분리
    features_training_data = [
        'open_lastclose_ratio', 'high_close_ratio', 'low_close_ratio',
        'close_lastclose_ratio', 'volume_lastvolume_ratio',
        'close_ma5_ratio', 'volume_ma5_ratio',
        'close_ma10_ratio', 'volume_ma10_ratio',
        'close_ma20_ratio', 'volume_ma20_ratio',
        'close_ma60_ratio', 'volume_ma60_ratio',
        'close_ma120_ratio', 'volume_ma120_ratio'
    ]
    training_data = training_data[features_training_data]

    # 강화학습 시작
    policy_learner = PolicyLearner(
        stock_code=stock_code, chart_data=chart_data, training_data=training_data,
        min_trading_unit=1, max_trading_unit=2, delayed_reward_threshold=.2, lr=.001)
    policy_learner.fit(balance=10000000, num_epoches=1000, discount_factor=0, start_epsilon=.5)

    # 정책 신경망을 파일로 저장
    model_dir = os.path.join(settings.BASE_DIR, 'models/%s' % stock_code)
    model_path = os.path.join(model_dir, 'model_%d.h5' % timestr)
    policy_learner.policy_network.save_model(model_path)