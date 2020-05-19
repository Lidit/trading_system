#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The server program that provides RESTful API
"""

import tornado
from tornado.web import Application, RequestHandler
from tornado.ioloop import IOLoop

import json
import pandas as pd
import sys
import time
import datetime
from datetime import timedelta
import data_manager
from kiwoom import Kiwoom, logger
import settings
import pandas as pd

from kiwoom_api import Kiwoom as kwm
import decorator
import os
from PyQt5.QtWidgets import QApplication

SLEEP_TIME = 0.34
TR_REQ_TIME_INTERVAL = 0.2

STOCK_DATA_PATH = f'{os.path.dirname(os.path.abspath(__file__))}/data/stocks'
STOCK_INDEX_DATA_PATH = f'{os.path.dirname(os.path.abspath(__file__))}/data/stockIndex'

# @decorators.call_printer


class PriceHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.event = None
        self.kw = kwm()
    
    def wait_response(self, price):
        self.event.set()
    
    def getStockData(self, stock_code) :
    
        stock_code = stock_code
        # tick_unit = "분봉"
        tick_range = 1
        # base_date = datetime.datetime.today().strftime("%Y%m%d%H%M%S")

        # start_datetime = datetime.datetime.fromordinal(self.startDateDateEdit.date().toPyDate().toordinal())
        # end_dateitme = time.localtime(time.time())
        
        # end_date = time.localtime(time.time())


        # end_date = time.strftime("%Y%m%d%H%M00",time.localtime(time.time()) )
        # start_datetime = end_date - timedelta(days=5)
        # start_date = time.strftime("%Y%m%d%H%M00", start_datetime)

        # end_datetime = datetime.datetime.fromordinal(self.endDateDateEdit.date().toPyDate().toordinal())

        start_date = "20200512090000"
        end_date = "20200519160000"


        self.kw.set_input_value("종목코드", stock_code)
        self.kw.set_input_value("틱범위", tick_range)
        self.kw.set_input_value("수정주가구분", 1)
        self.kw.comm_rq_data("opt10080_req", "opt10080", 0, "0101")

        ohlcv = self.kw.ohlcv

        while self.kw.remained_data == True:
            time.sleep(TR_REQ_TIME_INTERVAL)
            if ohlcv['date'][-1] < start_date:
                break
            self.return_stats_msg = "분봉 받는중..."
            self.kw.set_input_value("종목코드", stock_code)
            self.kw.set_input_value("틱범위", tick_range)
            self.kw.set_input_value("수정주가구분", 1)
            self.kw.comm_rq_data("opt10080_req", "opt10080", 2, "0101")
            for key, val in self.kw.ohlcv.items():
                ohlcv[key][-1:] = val

        df = pd.DataFrame(ohlcv, columns=['date','current', 'open', 'high', 'low', 'volume'])
        df = df[df.date >= start_date]
        df = df.sort_values(by=['date'], axis=0)
        df = df.reset_index(drop=True)
        df.to_csv(f'{STOCK_DATA_PATH}/{stock_code}.csv', mode='w', header=False)



    def post(self):
        """
        request data must contain
        "code": symbol (aka code) of the stock
        """
        data = tornado.escape.json_decode(self.request.body)

        code = data["code"]
        hts.dict_stock[code] = {}
        data_lenth = 750
        # Make request
        # result = hts.kiwoom_TR_OPT10080_주식분봉차트조회(code, 1, 0, data_lenth, 0)

        # Wait for response
        # while not hts.result['result']:
        #     time.sleep(SLEEP_TIME)

        # odata = {
        #     "date": int(result["체결시간"]),
        #     "current" : int(result["현재가"]),
        #     "open" : int(result["시가"]),
        #     "high" : int(result["고가"]),
        #     "low" : int(result["저가"]),
        #     "volume": int(result["거래량"])
        # }
        # chart_data = {'date':[], 'current':[], 'open':[], 'high':[], 'low':[], 'volume':[]}
        # print(hts.result["result"])

        # for key ,line in hts.result.items():


        #     for line in info.items():
        #         chart_data["date"].append(int(line["체결시간"]))
        #         chart_data["current"].append(int(line["현재가"]))
        #         chart_data["open"].append(int(line["시가"]))
        #         chart_data["high"].append(int(line["고가"]))
        #         chart_data["low"].append(int(line["저가"]))
        #         chart_data["volume"].append(int(line["거래량"]))
            # print(hts.result)
        
       
        # print(chart_data)

        path = os.path.join(settings.BASE_DIR, f'data/stocks/{code}.csv')
        PriceHandler.getStockData(self, code)
        chart = pd.read_csv(path, thousands=',', header=None, names=data_manager.COLUMNS_CHART_DATA,
        converters={'date': lambda x: str(x)})

        chart_data = chart.to_json(chart.json, orient = "table")

        logger.debug("Response to client:")
        logger.debug(str(chart_data))
        self.write(json.dumps(chart_data))


class OrderHandler(RequestHandler):
    request_no = 0

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
            data['accno'],
            nOrderType,
            code,
            qty,
            price,
            sHogaGb,
            "" # original order number to cancel or correct.
        )
        logger.debug("Order sent.")


class BalanceHandler(RequestHandler):
    def post(self):
        """
        Request data must contain
        accno : account number the transaction will happen
        """
        data = tornado.escape.json_decode(self.request.body)
        logger.debug("BalanceHandler: incoming")
        logger.debug(data)

        hts.int_주문가능금액 = None
        result = hts.kiwoom_TR_OPW00001_예수금상세현황요청(data["accno"])
        while not hts.int_주문가능금액:
            time.sleep(SLEEP_TIME)
        cash = hts.int_주문가능금액

        hts.dict_holding = None
        hts.kiwoom_TR_OPT10085_계좌수익률요청(data["accno"])
        while hts.dict_holding is None:
            time.sleep(SLEEP_TIME)

        result = {}
        for code, info in hts.dict_holding.items():
            result[code] = int(info["보유수량"])
        result["cash"] = cash

        logger.debug("Response to client:")
        logger.debug(str(result))
        self.write(json.dumps(result))
    


def make_app():
    urls = [
        ("/price", PriceHandler),
        ("/order", OrderHandler),
        ("/balance", BalanceHandler),
    ]
    # Autoreload seems troublesome.
    return Application(urls, debug=True, autoreload=False)


def shutdown():
    # It seems there's no logout so... nothing here.
    pass


#
# Shared variables
#
app = QApplication(sys.argv)
hts = Kiwoom()

if __name__ == "__main__":
    # login
    if hts.kiwoom_GetConnectState() != 0:
        logger.debug('Connection failed')
        sys.exit()

    logger.debug('로그인 시도')
    res = hts.kiwoom_CommConnect()
    if res.get('result') != 0:
        logger.debug('Login failed')
        sys.exit()

    # To see list of your accounts...
    if True:
        accounts = hts.kiwoom_GetAccList()
        logger.debug("Your accounts:")
        for acc in accounts:
            logger.debug(acc)

    port = 5000
    tornado_app = make_app()
    tornado_app.listen(port)
    #tornado.autoreload.add_reload_hook(shutdown)
    logger.debug('RESTful api server started at port {}'.format(port))

    #try:
    #    IOLoop.instance().start()
    #except KeyboardInterrupt:
    #    shutdown()
    # Nothing to do for shutdown so... commenting out.

    IOLoop.instance().start()
