import sys
import time

from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *

TR_REQ_TIME_INTERVAL = 0.2

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._on_event_connect)
        self.OnReceiveTrData.connect(self._on_receive_tr_data)

    def _on_event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")

        self.login_event_loop.exit()
    
    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        self.ohlcv = None

        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10080_req":
            self._opt10080(rqname, trcode)
        
        elif rqname == "opt10081_req":
            self._opt10081(rqname, trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    #market의 모든 종목 코드를 가져옴
    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    #종목코드를 종목이름으로 반환
    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    #서버와의 연결 상태를 반환
    def get_connect_state(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret

    def get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def get_server_gubun(self):
        """
        실투자 환경인지 모의투자 환경인지 구분하는 메소드
        실투자, 모의투자에 따라 데이터 형식이 달라지는 경우가 있다. 대표적으로 opw00018 데이터의 소수점
        """
        ret = self.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "")
        return ret

    def get_login_info(self, tag):
        """
        계좌 정보 및 로그인 사용자 정보를 얻어오는 메소드
        """
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString", code,
                               real_type, field_name, index, item_name)
        return ret.strip()
    
    #분봉 가져오기
    def _opt10080(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)
        self.ohlcv = {'date':[], 'current':[], 'open':[], 'high':[], 'low':[], 'volume':[]}
        
        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "체결시간")
            current = abs(int(self._comm_get_data(trcode, "", rqname, i, "현재가")))
            open = abs(int(self._comm_get_data(trcode, "", rqname, i, "시가")))
            high = abs(int(self._comm_get_data(trcode, "", rqname, i, "고가")))
            low = abs(int(self._comm_get_data(trcode, "", rqname, i, "저가")))
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['current'].append(current)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['volume'].append(int(volume))

            # 체결 시간 20200422101400 현재가 37750 시가 37800 고가 37800 저가 37750 거래량 2816
            # 체결 시간 20200422101300 현재가 37800 시가 37800 고가 37800 저가 37800 거래량 138
            # 체결 시간 20200422101200 현재가 37850 시가 37800 고가 37850 저가 37800 거래량 104
            # 체결 시간 20200422101100 현재가 37800 시가 37800 고가 37850 저가 37800 거래량 109
            # 체결 시간 20200422101000 현재가 37850 시가 37800 고가 37850 저가 37800 거래량 15
            # 체결 시간 20200422100900 현재가 37800 시가 37900 고가 37900 저가 37800 거래량 467
            # 체결 시간 20200422100800 현재가 37850 시가 37900 고가 37900 저가 37850 거래량 71
            # 체결 시간 20200422100700 현재가 37850 시가 37850 고가 37850 저가 37850 거래량 10
            # 체결 시간 20200422100600 현재가 37900 시가 37900 고가 37900 저가 37900 거래량 20

    #일봉 가져오기
    def _opt10081(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)
        self.ohlcv = {'date':[], 'open':[], 'high':[], 'low':[], 'close':[], 'volume':[]}

        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")
            # dividends = self._comm_get_data(trcode, "", rqname, i, "배당금")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))
            # self.ohlcv['dividends'].append(int(dividends))