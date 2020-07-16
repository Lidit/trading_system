# coding=utf-8

import datetime

def call_printer(original_func):
    """original 함수 call 시, 현재 시간과 함수 명을 출력하는 데코레이터"""

    def wrapper(self):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        self.return_status_msg = '[{:.22s}] func `{}` 시작됨'.format(timestamp, original_func.__name__)
        ret = original_func(self)
        
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.return_status_msg = '`{}` 완료됨[{}]'.format(original_func.__name__, timestamp)
        return ret

    return wrapper


def return_status_msg_setter(original_func):
    """
    original 함수 exit 후, QMainWindow 인스턴스의 statusbar에 표시할 문자열을 수정하는 데코레이터
    이 데코레이터는 QMainWindow 클래스의 메소드에만 사용하여야 함
    """

    def wrapper(self):
        ret = original_func(self)

        timestamp = datetime.datetime.now().strftime('%H:%M:%S')

        # args[0]는 인스턴스 (즉, self)를 의미한다.
        self.return_status_msg = '`{}` 완료됨[{}]'.format(original_func.__name__, timestamp)
        return ret

    return wrapper