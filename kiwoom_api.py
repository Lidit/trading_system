import sys
import time

from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self.create_kiwoom_instance()
        self.set_signal_slots()

    def create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def set_signal_slots(self):
        self.OnEventConnect.connect(self.on_event_connect)
        self.OnReceiveTrData.connect(self.on_receive_tr_data)

    def on_event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")

        self.login_event_loop.exit()

    def receiveRealData(self, code, realType, realData):
        """
        실시간 데이터 수신 이벤트
        실시간 데이터를 수신할 때 마다 호출되며,
        setRealReg() 메서드로 등록한 실시간 데이터도 이 이벤트 메서드에 전달됩니다.
        getCommRealData() 메서드를 이용해서 실시간 데이터를 얻을 수 있습니다.
        :param code: string - 종목코드
        :param realType: string - 실시간 타입(KOA의 실시간 목록 참조)
        :param realData: string - 실시간 데이터 전문
        """

        try:
            self.log.debug("[receiveRealData]")
            self.log.debug("({})".format(realType))

            if realType not in RealType.REALTYPE:
                return

            data = []

            if code != "":
                data.append(code)
                codeOrNot = code
            else:
                codeOrNot = realType

            for fid in sorted(RealType.REALTYPE[realType].keys()):
                value = self.getCommRealData(codeOrNot, fid)
                data.append(value)

            # TODO: DB에 저장
            self.log.debug(data)

        except Exception as e:
            self.log.error('{}'.format(e))
    
    def on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        self.ohlcv = None

        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10080_req":
            self.opt10080(rqname, trcode)
        
        elif rqname == "opt10081_req":
            self.opt10081(rqname, trcode)

        elif rqname == "opt20005_req":
            self.opt20005(rqname, trcode)

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

    def comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString", code,
                               real_type, field_name, index, item_name)
        return ret.strip()
    
    #분봉 가져오기
    def opt10080(self, rqname, trcode):
        data_cnt = self.get_repeat_cnt(trcode, rqname)
        self.ohlcv = {'date':[], 'current':[], 'open':[], 'high':[], 'low':[], 'volume':[]}
        
        for i in range(data_cnt):
            date = self.comm_get_data(trcode, "", rqname, i, "체결시간")
            current = abs(int(self.comm_get_data(trcode, "", rqname, i, "현재가")))
            open = abs(int(self.comm_get_data(trcode, "", rqname, i, "시가")))
            high = abs(int(self.comm_get_data(trcode, "", rqname, i, "고가")))
            low = abs(int(self.comm_get_data(trcode, "", rqname, i, "저가")))
            volume = self.comm_get_data(trcode, "", rqname, i, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['current'].append(current)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['volume'].append(int(volume))

    #일봉 가져오기
    def opt10081(self, rqname, trcode):
        data_cnt = self.get_repeat_cnt(trcode, rqname)
        self.ohlcv = {'date':[], 'open':[], 'high':[], 'low':[], 'close':[], 'volume':[]}

        for i in range(data_cnt):
            date = self.comm_get_data(trcode, "", rqname, i, "일자")
            open = self.comm_get_data(trcode, "", rqname, i, "시가")
            high = self.comm_get_data(trcode, "", rqname, i, "고가")
            low = self.comm_get_data(trcode, "", rqname, i, "저가")
            close = self.comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self.comm_get_data(trcode, "", rqname, i, "거래량")
            # dividends = self._comm_get_data(trcode, "", rqname, i, "배당금")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))
            # self.ohlcv['dividends'].append(int(dividends))

    #증시 데이터 분봉 가져오기
    def opt20005(self, rqname, trcode):
        data_cnt = self.get_repeat_cnt(trcode, rqname)
        self.ohlcv = {'date':[], 'current':[], 'open':[], 'high':[], 'low':[], 'volume':[]}

        for i in range(data_cnt):
            date = self.comm_get_data(trcode, "", rqname, i, "체결시간")
            current = abs(int(self.comm_get_data(trcode, "", rqname, i, "현재가")))
            open = abs(int(self.comm_get_data(trcode, "", rqname, i, "시가")))
            high = abs(int(self.comm_get_data(trcode, "", rqname, i, "고가")))
            low = abs(int(self.comm_get_data(trcode, "", rqname, i, "저가")))
            volume = self.comm_get_data(trcode, "", rqname, i, "거래량")
            
            self.ohlcv['date'].append(date)
            self.ohlcv['current'].append(current)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['volume'].append(int(volume))

class RealType(object):

    REALTYPE = {
        '주식시세': {
            10: '현재가',
            11: '전일대비',
            12: '등락율',
            27: '최우선매도호가',
            28: '최우선매수호가',
            13: '누적거래량',
            14: '누적거래대금',
            16: '시가',
            17: '고가',
            18: '저가',
            25: '전일대비기호',
            26: '전일거래량대비',
            29: '거래대금증감',
            30: '거일거래량대비',
            31: '거래회전율',
            32: '거래비용',
            311: '시가총액(억)'
        },

        '주식체결': {
            20: '체결시간(HHMMSS)',
            10: '체결가',
            11: '전일대비',
            12: '등락율',
            27: '최우선매도호가',
            28: '최우선매수호가',
            15: '체결량',
            13: '누적체결량',
            14: '누적거래대금',
            16: '시가',
            17: '고가',
            18: '저가',
            25: '전일대비기호',
            26: '전일거래량대비',
            29: '거래대금증감',
            30: '전일거래량대비',
            31: '거래회전율',
            32: '거래비용',
            228: '체결강도',
            311: '시가총액(억)',
            290: '장구분',
            691: 'KO접근도'
        },

        '주식호가잔량': {
            21: '호가시간',
            41: '매도호가1',
            61: '매도호가수량1',
            81: '매도호가직전대비1',
            51: '매수호가1',
            71: '매수호가수량1',
            91: '매수호가직전대비1',
            42: '매도호가2',
            62: '매도호가수량2',
            82: '매도호가직전대비2',
            52: '매수호가2',
            72: '매수호가수량2',
            92: '매수호가직전대비2',
            43: '매도호가3',
            63: '매도호가수량3',
            83: '매도호가직전대비3',
            53: '매수호가3',
            73: '매수호가수량3',
            93: '매수호가직전대비3',
            44: '매도호가4',
            64: '매도호가수량4',
            84: '매도호가직전대비4',
            54: '매수호가4',
            74: '매수호가수량4',
            94: '매수호가직전대비4',
            45: '매도호가5',
            65: '매도호가수량5',
            85: '매도호가직전대비5',
            55: '매수호가5',
            75: '매수호가수량5',
            95: '매수호가직전대비5',
            46: '매도호가6',
            66: '매도호가수량6',
            86: '매도호가직전대비6',
            56: '매수호가6',
            76: '매수호가수량6',
            96: '매수호가직전대비6',
            47: '매도호가7',
            67: '매도호가수량7',
            87: '매도호가직전대비7',
            57: '매수호가7',
            77: '매수호가수량7',
            97: '매수호가직전대비7',
            48: '매도호가8',
            68: '매도호가수량8',
            88: '매도호가직전대비8',
            58: '매수호가8',
            78: '매수호가수량8',
            98: '매수호가직전대비8',
            49: '매도호가9',
            69: '매도호가수량9',
            89: '매도호가직전대비9',
            59: '매수호가9',
            79: '매수호가수량9',
            99: '매수호가직전대비9',
            50: '매도호가10',
            70: '매도호가수량10',
            90: '매도호가직전대비10',
            60: '매수호가10',
            80: '매수호가수량10',
            100: '매수호가직전대비10',
            121: '매도호가총잔량',
            122: '매도호가총잔량직전대비',
            125: '매수호가총잔량',
            126: '매수호가총잔량직전대비',
            23: '예상체결가',
            24: '예상체결수량',
            128: '순매수잔량(총매수잔량-총매도잔량)',
            129: '매수비율',
            138: '순매도잔량(총매도잔량-총매수잔량)',
            139: '매도비율',
            200: '예상체결가전일종가대비',
            201: '예상체결가전일종가대비등락율',
            238: '예상체결가전일종가대비기호',
            291: '예상체결가',
            292: '예상체결량',
            293: '예상체결가전일대비기호',
            294: '예상체결가전일대비',
            295: '예상체결가전일대비등락율',
            13: '누적거래량',
            299: '전일거래량대비예상체결률',
            215: '장운영구분'
        },

        '장시작시간': {
            215: '장운영구분(0:장시작전, 2:장종료전, 3:장시작, 4,8:장종료, 9:장마감)',
            20: '시간(HHMMSS)',
            214: '장시작예상잔여시간'
        },

        '업종지수': {
            20: '체결시간',
            10: '현재가',
            11: '전일대비',
            12: '등락율',
            15: '거래량',
            13: '누적거래량',
            14: '누적거래대금',
            16: '시가',
            17: '고가',
            18: '저가',
            25: '전일대비기호',
            26: '전일거래량대비(계약,주)'
        },

        '업종등락': {
            20: '체결시간',
            252: '상승종목수',
            251: '상한종목수',
            253: '보합종목수',
            255: '하락종목수',
            254: '하한종목수',
            13: '누적거래량',
            14: '누적거래대금',
            10: '현재가',
            11: '전일대비',
            12: '등락율',
            256: '거래형성종목수',
            257: '거래형성비율',
            25: '전일대비기호'
        },

        '주문체결': {
            9201: '계좌번호',
            9203: '주문번호',
            9205: '관리자사번',
            9001: '종목코드',
            912: '주문분류(jj:주식주문)',
            913: '주문상태(10:원주문, 11:정정주문, 12:취소주문, 20:주문확인, 21:정정확인, 22:취소확인, 90,92:주문거부)',
            302: '종목명',
            900: '주문수량',
            901: '주문가격',
            902: '미체결수량',
            903: '체결누계금액',
            904: '원주문번호',
            905: '주문구분(+:현금매수, -:현금매도)',
            906: '매매구분(보통, 시장가등)',
            907: '매도수구분(1:매도, 2:매수)',
            908: '체결시간(HHMMSS)',
            909: '체결번호',
            910: '체결가',
            911: '체결량',
            10: '체결가',
            27: '최우선매도호가',
            28: '최우선매수호가',
            914: '단위체결가',
            915: '단위체결량',
            938: '당일매매수수료',
            939: '당일매매세금'
        },

        '잔고': {
            9201: '계좌번호',
            9001: '종목코드',
            302: '종목명',
            10: '현재가',
            930: '보유수량',
            931: '매입단가',
            932: '총매입가',
            933: '주문가능수량',
            945: '당일순매수량',
            946: '매도매수구분',
            950: '당일총매도손익',
            951: '예수금',
            27: '최우선매도호가',
            28: '최우선매수호가',
            307: '기준가',
            8019: '손익율'
        },

        '주식시간외호가': {
            21: '호가시간(HHMMSS)',
            131: '시간외매도호가총잔량',
            132: '시간외매도호가총잔량직전대비',
            135: '시간외매수호가총잔량',
            136: '시간외매수호가총잔량직전대비'
        }
    }
