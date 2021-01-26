import datetime
from typing import Dict, List
import requests
import urllib.parse as urlparse
import xml.etree.ElementTree as ET
import json
import xmltodict

# 특일정보 공공 API
# https://www.data.go.kr/data/15012690/openapi.do
URL = "http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getHoliDeInfo"
SERVICEKEY = "CUxrX061gY3U3xkollqvEg1RH6R5KP6JNmxwwPflL4s%2B0adSAxjMLOvnZQxJFDr9YPJ4Oop2uFdUul%2FFUa7hBA%3D%3D"


def getHolidayInfo(date):
    params = {'solYear': date.year,
              'solMonth': date.month}
    params = urlparse.urlencode(params)
    request_query = URL + '?' + \
        params + '&' + 'serviceKey' + '=' + SERVICEKEY

    response = requests.get(url=request_query)
    jsonString = json.dumps(xmltodict.parse(response.text), indent=4)
    dict = json.loads(jsonString)
    return dict['response']['body']


def isHoliday(data, today):
    weekday = today.weekday()

    if data['totalCount'] == '0':
        return weekday == 5 or weekday == 6

    holiday = ''
    items = data['items']['item']

    if type(items) == list:
        for item in items:
            holiday = datetime.datetime.strptime(
                item['locdate'], '%Y%m%d').date()

            if ((holiday == today) and items['isHoliday'] == 'Y') or weekday == 5 or weekday == 6:
                return True

    else:
        holiday = datetime.datetime.strptime(
            items['locdate'], '%Y%m%d').date()

    if ((holiday == today) and items['isHoliday'] == 'Y') or weekday == 5 or weekday == 6:
        return True

    return False


if __name__ == '__main__':
    today = datetime.date.today() + datetime.timedelta(days=-120)
    print(today)
    tomorrow = today + datetime.timedelta(days=1)
    data = getHolidayInfo(tomorrow)
    print(data)

    i = 0
    if isHoliday(data, tomorrow):
        while True:
            date = today - datetime.timedelta(days=i)
            print(date)
            data = getHolidayInfo(date)
            if isHoliday(data, date):
                if i > 0:
                    i -= 1
                break
            i += 1
    print(i)