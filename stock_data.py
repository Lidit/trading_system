import os
import argparse
import datetime
import time
import sys
from kiwoom_api import Kiwoom
import pandas as pd

from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *

MARKET_KOSPI = 0
MARKET_KOSDAQ = 10

TR_REQ_TIME_INTERVAL = 0.5

STOCK_DATA_PATH = f'{os.path.dirname(os.path.abspath(__file__))}/data/stocks'
STOCK_INDEX_DATA_PATH = f'{os.path.dirname(os.path.abspath(__file__))}/data/stockIndex'

if __name__ == "__main__":
    app = QApplication(sys.argv)
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=15)
    parser.add_argument('--stock_code', nargs='+')
    args = parser.parse_args()
    print(args)

    kiwoom = Kiwoom()
    kiwoom.comm_connect()

    tick_range = 1
    start_date = datetime.datetime.now() - datetime.timedelta(days=args.days)
    start_date = datetime.datetime.combine(start_date, datetime.time(9, 0))
    start_date = start_date.strftime("%Y%m%d%H%M%S")

    end_date = datetime.datetime.combine(
        datetime.datetime.now(), datetime.time(16, 0))
    end_date = end_date.strftime("%Y%m%d%H%M%S")
    print("종목 분봉 받는중...")
    for code in args.stock_code:
        print(code)
        kiwoom.set_input_value("종목코드", code)
        kiwoom.set_input_value("틱범위", tick_range)
        kiwoom.set_input_value("수정주가구분", 1)
        kiwoom.comm_rq_data("opt10080_req", "opt10080", 0, "0101")

        ohlcv = kiwoom.ohlcv

        while kiwoom.remained_data == True:
            time.sleep(TR_REQ_TIME_INTERVAL)
            if ohlcv['date'][-1] < start_date:
                break

            kiwoom.set_input_value("종목코드", code)
            kiwoom.set_input_value("틱범위", tick_range)
            kiwoom.set_input_value("수정주가구분", 1)
            kiwoom.comm_rq_data("opt10080_req", "opt10080", 2, "0101")
            for key, val in kiwoom.ohlcv.items():
                ohlcv[key][-1:] = val

        df = pd.DataFrame(
            ohlcv, columns=['date', 'current', 'open', 'high', 'low', 'volume'])
        df = df[df.date >= start_date]
        df = df.sort_values(by=['date'], axis=0)
        df = df.reset_index(drop=True)
        df.to_csv(f'{STOCK_DATA_PATH}/{code}.csv', mode='w', header=False)

    kiwoom.set_input_value("업종코드", "001")
    kiwoom.set_input_value("틱범위", "1")
    kiwoom.comm_rq_data("opt20005_req", "opt20005", 0, "0101")

    print("코스피 분봉 받는중...")
    while kiwoom.remained_data == True:
        time.sleep(TR_REQ_TIME_INTERVAL)
        if ohlcv['date'][-1] < start_date:
            break
        kiwoom.set_input_value("업종코드", "001")
        kiwoom.set_input_value("틱범위", "1")
        kiwoom.comm_rq_data("opt20005_req", "opt20005", 2, "0101")

    df = pd.DataFrame(
            ohlcv, columns=['date', 'current', 'open', 'high', 'low', 'volume'])
    df = df[df.date >= start_date]
    df = df.sort_values(by=['date'], axis=0)
    df = df.reset_index(drop=True)
    df.to_csv(f'{STOCK_INDEX_DATA_PATH}/KOSPI.csv', mode='w', header=False)

    kiwoom.set_input_value("업종코드", "101")
    kiwoom.set_input_value("틱범위", "1")
    kiwoom.comm_rq_data("opt20005_req", "opt20005", 0, "0101")
    print("코스닥 분봉 받는중...")
    while kiwoom.remained_data == True:
        time.sleep(TR_REQ_TIME_INTERVAL)
        if ohlcv['date'][-1] < start_date:
            break

        kiwoom.set_input_value("업종코드", "101")
        kiwoom.set_input_value("틱범위", "1")
        kiwoom.comm_rq_data("opt20005_req", "opt20005", 2, "0101")

    df = pd.DataFrame(
        ohlcv, columns=['date', 'current', 'open', 'high', 'low', 'volume'])
    df = df[df.date >= start_date]
    df = df.sort_values(by=['date'], axis=0)
    df = df.reset_index(drop=True)
    df.to_csv(f'{STOCK_INDEX_DATA_PATH}/KOSDAQ.csv', mode='w', header=False)
    print("차트 조회 종료")
    app.exit()
    sys.exit()
    exit(app.exec_())
