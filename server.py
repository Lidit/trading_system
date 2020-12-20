import tornado
from tornado.web import Application, RequestHandler
from tornado.ioloop import IOLoop

import time
import datetime
from datetime import timedelta

import json
import pandas as pd

from kiwoom import Kiwoom, logger
from kiwoom_api import Kiwoom as kwm

import decorator
import os
import sys

from PyQt5.QtWidgets import QApplication

TR_REQ_TIME_INTERVAL = 0.5

STOCK_DATA_PATH = f'{os.path.dirname(os.path.abspath(__file__))}\data\stocks'
STOCK_INDEX_DATA_PATH = f'{os.path.dirname(os.path.abspath(__file__))}\data\stockIndex'

#주식 분봉 차트 조회
class PriceHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.event = None

    def wait_response(self, price):
        self.event.set()

    def getStockData(self, stock_code, tick_range, start_date, end_date):
        stock_code = stock_code
        tick_range = tick_range
        start_date = start_date
        end_date = end_date

        kw.set_input_value("종목코드", stock_code)
        kw.set_input_value("틱범위", tick_range)
        kw.set_input_value("수정주가구분", 1)
        kw.comm_rq_data("opt10080_req", "opt10080", 0, "0101")

        ohlcv = kw.ohlcv

        while kw.remained_data == True:
            logger.debug("loop")
            time.sleep(TR_REQ_TIME_INTERVAL)
            if ohlcv['date'][-1] < start_date:
                break
            print("데이터 받는중~")
            kw.set_input_value("종목코드", stock_code)
            kw.set_input_value("틱범위", tick_range)
            kw.set_input_value("수정주가구분", 1)
            kw.comm_rq_data("opt10080_req", "opt10080", 2, "0101")
            for key, val in kw.ohlcv.items():
                ohlcv[key][-1:] = val

        df = pd.DataFrame(
            ohlcv, columns=['date', 'current', 'open', 'high', 'low', 'volume'])
        df = df[df.date >= start_date]
        df = df.sort_values(by=['date'], axis=0)
        df = df.reset_index(drop=True)
        df.to_csv(f'{STOCK_DATA_PATH}/{stock_code}.csv',
                  mode='w', header=False)
        print("데이터 받기완료. 저장하기~")
        logger.debug("getStockData success")

        return df


    @tornado.gen.coroutine
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        print(data)
        code = data["code"]
        tick = data["tick"]
        start_date = data["start_date"]
        end_date = data["end_date"]
        hts.dict_stock[code] = {}
        df = PriceHandler.getStockData(self, code, tick, start_date, end_date)

        #time.sleep(0.34)
        logger.debug("Response to client:")
        logger.debug("request success")
        self.write(json.dumps(df.to_json()))

#예수금 조회
class BalanceHandler(RequestHandler):
    def post(self):
        hts.dict_callback["예수금상세현황요청"] = None
        hts.kiwoom_TR_OPW00001_예수금상세현황요청(account_num)

        while hts.dict_callback["예수금상세현황요청"] is None:
            time.sleep(0.1)

        time.sleep(TR_REQ_TIME_INTERVAL)

        hts.dict_callback["계좌수익률요청"] = None
        hts.kiwoom_TR_OPT10085_계좌수익률요청(account_num)

        while hts.dict_callback["계좌수익률요청"] is None:
            time.sleep(0.1)
            
        result = {}
        result["balance"] = int(hts.dict_callback["예수금상세현황요청"]["주문가능금액"])
        result["dict"] = hts.dict_callback["계좌수익률요청"]
        self.write(json.dumps(result))

#현재 주식 가격 조회
class CurrentPriceHandler(RequestHandler):
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        stock_code = data["stock_code"]

        hts.dict_callback["주식기본정보"] = None
        
        hts.kiwoom_TR_OPT10001_주식기본정보요청(stock_code)

        while hts.dict_callback["주식기본정보"] is None:
            time.sleep(0.1)
        
        self.write(json.dumps(hts.dict_callback["주식기본정보"]))

#주식 매매
class OrderHandler(RequestHandler):
    request_no = 0

    @tornado.gen.coroutine
    def post(self):
        """
        request data must hold the following:
        qty : pos number for buy, neg number for sell
        price : limit order price. Don't care if pre/market order.
        code : code of the stock
        type : {limit, market, premarket}
        accno : account number of this transaction
        """
        data = tornado.escape.json_decode(self.request.body)
        logger.debug("OrderHandler: incoming")
        logger.debug(data)

        # data must hold
        qty = data['qty']
        assert qty != 0
        nOrderType = 1 if qty > 0 else 2 # 1=buy, 2=sell
        qty = abs(qty)

        code = data['code']

        sHogaGb = "00"
        if data['type'] == "limit":
            sHogaGb = "00"
        elif data['type'] == "market":
            sHogaGb = "03"
        elif data['type'] == "premarket":
            sHogaGb = "61"
        else:
            assert 0, "Wrong type of order from client"

        price = 0
        if data['type'] == "limit":
            price = data['price']

        rq_name = "RQ_" + str(OrderHandler.request_no)
        OrderHandler.request_no += 1

        hts.kiwoom_SendOrder(
            rq_name,
            "8949", # dummy
            account_num,
            nOrderType,
            code,
            qty,
            price,
            sHogaGb,
            "" # original order number to cancel or correct.
        )
        logger.debug("Order sent.")
        self.write(json.dumps("주문 완료"))
        

def make_app():
    urls = [
        ("/price", PriceHandler),
        ("/balance", BalanceHandler),
        ("/currentPrice", CurrentPriceHandler),
        ("/order", OrderHandler),
    ]
    return Application(urls, debug=True, autoreload=False)

def shutdown():
    pass

app = QApplication(sys.argv)
hts = Kiwoom()
kw = kwm()
account_num = ""

if __name__ == "__main__":
    if hts.kiwoom_GetConnectState() != 0:
        logger.debug('Connection failed')
        sys.exit()
    
    logger.debug('로그인 시도')
    res = hts.kiwoom_CommConnect()

    if res.get('result') != 0:
        logger.deubg('Login failed')
        sys.exit()
    
    accounts = hts.kiwoom_GetAccList()

    for acc in accounts:
        account_num = acc
    
    logger.debug(account_num)

    port = 5550
    tornado_app = make_app()
    tornado_app.listen(port)

    logger.debug('RESTful api server started at port {}'.format(port))

    IOLoop.instance().start()