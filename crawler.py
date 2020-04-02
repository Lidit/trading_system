import os
import errno
import settings
import yfinance as yf
import pandas as pd
import pandas_datareader as pdr


class Crawler:
    stock_type = {
        'kospi': 'stockMkt',
        'kosdaq': 'kosdaqMkt'
    }

    # 회사명으로 주식 종목 코드를 획득할 수 있도록 하는 함수
    def get_code(self, df, name):
        code = df.query("name=='{}'".format(name))['code'].to_string(index=False)

        # 위와같이 code명을 가져오면 앞에 공백이 붙어있는 상황이 발생하여 앞뒤로 sript() 하여 공백 제거
        code = code.strip()
        return code


    # download url 조합
    def get_download_stock(self, market_type=None):
        cr = Crawler()
        market_type_param = cr.stock_type[market_type]
        download_link = 'http://kind.krx.co.kr/corpgeneral/corpList.do'
        download_link = download_link + '?method=download'
        download_link = download_link + '&marketType=' + market_type_param

        df = pd.read_html(download_link, header=0)[0]
        return df

    # kospi 종목코드 목록 다운로드
    def get_download_kospi(self):
        cr = Crawler()
        df = cr.get_download_stock('kospi')
        df.종목코드 = df.종목코드.map('{:06d}.KS'.format)
        return df

    # kosdaq 종목코드 목록 다운로드
    def get_download_kosdaq(self):
        cr = Crawler()
        df = cr.get_download_stock('kosdaq')
        df.종목코드 = df.종목코드.map('{:06d}.KQ'.format)
        return df

    # 2008-12-01 ~ 2018-12-31 동안의 데이터 불러오기
    def getAllStockData(self, name):
        cr = Crawler()
        stocks = yf.Ticker(cr.get_code(code_df, str(name)))

        df = pd.DataFrame(stocks.history(start=start_date, end=end_date))
        if(df.empty):
            return print("데이터가 존재하지 않습니다.\n")
        else:
            df.to_csv(str(name)+".csv", mode='w')



    """
    		Open	High	Low	Close	Volume	Dividends	Stock Splits
    Date							
    1980-12-12	0.41	0.41	0.41	0.41	117258400	0.0		0.0
    1980-12-15	0.39	0.39	0.39	0.39	43971200	0.0		0.0
    1980-12-16	0.36	0.36	0.36	0.36	26432000	0.0		0.0
    1980-12-17	0.37	0.37	0.37	0.37	21610400	0.0		0.0
    1980-12-18	0.38	0.38	0.38	0.38	18362400	0.0		0.0
    	...		...		...		...		...		...			...		...
    2020-01-31	320.93	322.68	308.29	309.51	49897100	0.0		0.0
    2020-02-03	304.30	313.49	302.22	308.66	43496400	0.0		0.0
    2020-02-04	315.31	319.64	313.63	318.85	34154100	0.0		0.0
    2020-02-05	323.52	324.76	318.95	321.45	29706700	0.0		0.0
    2020-02-06	322.57	325.22	320.26	325.21	26227500	0.0		0.0
    """

    # 배당 정보 받아볼수 있는 코드
    # 종목객체.dividends

    """
    Date
    1987-05-11    0.00214
    1987-08-10    0.00214
    1987-11-17    0.00286
    1988-02-12    0.00286
    1988-05-16    0.00286
                   ...   
    2018-11-08    0.73000
    2019-02-08    0.73000
    2019-05-10    0.77000
    2019-08-09    0.77000
    2019-11-07    0.77000
    """

    # df["Close"].plot()
# 종목 타입에 따라 download url이 다름. 종목코드 뒤에 .KS .KQ등이 입력되어야해서 Download Link 구분 필요
stock_type = {
    'kospi': 'stockMkt',
    'kosdaq': 'kosdaqMkt'
}

crawler = Crawler()


# # kospi, kosdaq 종목코드 각각 다운로드
# kospi_df = crawler.get_download_kospi()
# kosdaq_df = crawler.get_download_kosdaq()

# # data frame merge
# code_df = pd.concat([kospi_df, kosdaq_df])

# # data frame정리
# code_df = code_df[['회사명', '종목코드']]

# # data frame title 변경 '회사명' = name, 종목코드 = 'code'
# code_df = code_df.rename(columns={'회사명': 'name', '종목코드': 'code'})

# code_df

# code = crawler.get_code(code_df, '삼성전자')
# Ticker(종목코드) 객체를 생성합니다.
# ex) samsung = yf.Ticker(code)
# dji = yf.Ticker("^DJI")

# 회사 정보 불러오기
# 종목정보.info

# 지정 기간의 주가 데이터를 불러옴.
# 종목객체.history(period='max')
# samsung_data = pd.DataFrame(samsung.history(period="1mo"))
# samsung_data.to_csv("test.csv", mode='w')

# for i in code_df.name:
#     getAllStockData(i)

# print(samsung.history(period="1mo"))
# dji.history(period="1mo")


# Data 폴더 생성
default_data_dir = os.path.join(settings.BASE_DIR, 'data/stockMarket')
if not os.path.isdir(default_data_dir):
    os.makedirs(default_data_dir)

start_date = "2008-12-01"
end_date = "2018-12-31"

# 여기서 부터 시장지표
# 4대지수
DJI = yf.Ticker("^DJI")
DJI_df = pd.DataFrame(DJI.history(start=start_date, end=end_date))
DJI_path = f'{default_data_dir}/DJI.csv'
DJI_df.to_csv(DJI_path, mode='w', header=False)

NASDAQ = yf.Ticker("^IXIC")
NASDAQ_df = pd.DataFrame(NASDAQ.history(start=start_date, end=end_date))
NASDAQ_path = f'{default_data_dir}/NASDAQ.csv'
NASDAQ_df.to_csv(NASDAQ_path, mode='w')

KOSPI = yf.Ticker("^KS11")
KOSPI_df = pd.DataFrame(KOSPI.history(start=start_date, end=end_date))
KOSPI_path = f'{default_data_dir}/KOSPI.csv'
KOSPI_df.to_csv(KOSPI_path, mode='w')

KOSDAQ = yf.Ticker("^KQ11")
KOSDAQ_df = pd.DataFrame(KOSDAQ.history(start=start_date, end=end_date))
KOSDAQ_path = f'{default_data_dir}/KOSDAQ.csv'
KOSDAQ_df.to_csv(KOSDAQ_path, mode='w')

# 환율
dollarExRate = yf.Ticker("KRW=X")
dollarExRate_df = pd.DataFrame(dollarExRate.history(start=start_date, end=end_date))
dollarExRate_path = f'{default_data_dir}/dollarExRate.csv'
dollarExRate_df.to_csv(dollarExRate_path, mode='w')

yuanExRate = yf.Ticker("CNYKRW=X")
yuanExRate_df = pd.DataFrame(yuanExRate.history(start=start_date, end=end_date))
yuanExRate_path = f'{default_data_dir}/yuanExRate.csv'
yuanExRate_df.to_csv(yuanExRate_path, mode='w')

yenExRate = yf.Ticker("JPYKRW=X")
yenExRate_df = pd.DataFrame(yenExRate.history(start=start_date, end=end_date))
yenExRate_path = f'{default_data_dir}/yenExRate.csv'
# for i in YenExRate_df.all:
#     YenExRate_df.
yenExRate_df.to_csv(yenExRate_path, mode='w')

# 유가
WTI = yf.Ticker("CL=F")
WTI_df = pd.DataFrame(WTI.history(start=start_date, end=end_date))
WTI_path = f'{default_data_dir}/WTI.csv'
WTI_df.to_csv(WTI_path, mode='w')

# dubai = yf.Ticker("")

# 중국 지수
SSI = yf.Ticker("000001.SS")  # 상해 종합 지수
SSI_df = pd.DataFrame(SSI.history(start=start_date, end=end_date))
SSI_path = f'{default_data_dir}/SSI.csv'
SSI_df.to_csv(SSI_path, mode='w')

HSI = yf.Ticker("^HSI")  # 항셍 종합 지수 (홍콩)
HSI_df = pd.DataFrame(HSI.history(start=start_date, end=end_date))
HSI_path = f'{default_data_dir}/HSI.csv'
HSI_df.to_csv(HSI_path, mode='w')

SCI = yf.Ticker("399106.SZ")  # 선전 종합 지수
SCI_df = pd.DataFrame(SCI.history(start=start_date, end=end_date))
SCI_path = f'{default_data_dir}/SCI.csv'
SCI_df.to_csv(SCI_path, mode='w')

# ect.
gold = yf.Ticker("GC=F")  # 금 가격 기준(트로이온스/달러)
gold_df = pd.DataFrame(gold.history(start=start_date, end=end_date))
gold_path = f'{default_data_dir}/gold.csv'
gold_df.to_csv(gold_path, mode='w')

# kospi, kosdaq 종목코드 각각 다운로드
kospi_df = crawler.get_download_kospi()
kosdaq_df = crawler.get_download_kosdaq()

# data frame merge
code_df = pd.concat([kospi_df, kosdaq_df])
# data frame정리
code_df = code_df[['회사명', '종목코드']]
# data frame title 변경 '회사명' = name, 종목코드 = 'code'
code_df = code_df.rename(columns={'회사명': 'name', '종목코드': 'code'})

data_code = crawler.get_code(code_df, "삼성SDI")
data = yf.Ticker(data_code)
if data_code.find(".KS"):
    data_code = data_code.strip(".KS")
elif data_code.find(".KQ"):
    data_code = data_code.strip(".KQ")
data_df = pd.DataFrame(data.history(start=start_date, end=end_date))
data_path = f'{default_data_dir}/{data_code}.csv'
data_df.to_csv(data_path, mode='w', header=False)