import os
import errno
import settings
import yfinance as yf
import pandas as pd
import pandas_datareader as pdr
import argparse

class Crawler:
    stock_type = {
        'kospi': 'stockMkt',
        'kosdaq': 'kosdaqMkt'
    }

    stock_index = {
        'DJI': '^DJI',
        'NASDAQ': '^IXIC',
        'KOSPI': '^KS11',
        'KOSDAQ': '^KQ11',
        'dollarExRate': 'KRW=X',
        'yuanExRate': 'CNYKRW=X',
        'yenExRate': 'JPYKRW=X',
        'WTI': 'CL=F',
        'SSI': '000001.SS',
        'HSI': '^HSI',
        'SCI': '399106.SZ',
        'gold': 'GC=F'
    }

    def __init__(self):
        self.kospi_df = self.get_download_kospi()
        self.kosdaq_df = self.get_download_kosdaq()
        
        self.code_df = pd.concat([self.kospi_df, self.kosdaq_df])
        self.code_df = self.code_df[['회사명', '종목코드']]
        self.code_df = self.code_df.rename(columns={'회사명': 'name', '종목코드': 'code'})

    # 회사명으로 주식 종목 코드를 획득할 수 있도록 하는 함수
    def get_code(self, df, name):
        code = df.query("name=='{}'".format(name))[
                        'code'].to_string(index=False)

        # 위와같이 code명을 가져오면 앞에 공백이 붙어있는 상황이 발생하여 앞뒤로 sript() 하여 공백 제거
        code = code.strip()
        return code

    # download url 조합
    def get_download_stock(self, market_type=None):
        market_type_param = self.stock_type[market_type]
        download_link = 'http://kind.krx.co.kr/corpgeneral/corpList.do'
        download_link = download_link + '?method=download'
        download_link = download_link + '&marketType=' + market_type_param

        df = pd.read_html(download_link, header=0)[0]
        return df

    # kospi 종목코드 목록 다운로드
    def get_download_kospi(self):
        df = self.get_download_stock('kospi')
        df.종목코드 = df.종목코드.map('{:06d}.KS'.format)
        return df

    # kosdaq 종목코드 목록 다운로드
    def get_download_kosdaq(self):
        df = self.get_download_stock('kosdaq')
        df.종목코드 = df.종목코드.map('{:06d}.KQ'.format)
        return df

    # 종목 데이터 가져오기
    def getStockData(self, name, start_date, end_date):
        data_code = crawler.get_code(self.code_df, name)
        data = yf.Ticker(data_code)

        if data_code.find(".KS"):
            data_code = data_code.strip(".KS")
        elif data_code.find(".KQ"):
            data_code = data_code.strip(".KQ")
        
        default_stock_dir = os.path.join(settings.BASE_DIR, 'data/stocks')
        if not os.path.isdir(default_stock_dir):
            os.makedirs(default_stock_dir)
        
        data_df = pd.DataFrame(data.history(start=start_date, end=end_date))
        data_df.drop(['Dividends', 'Stock Splits'],1, inplace=True)
        data_path = f'{default_stock_dir}/{data_code}.csv'
        data_df.to_csv(data_path, mode='w', header=False)

    #주가 데이터 가져오기
    def getStockIndexData(self, start_date, end_date):
        default_stock_index_dir = os.path.join(settings.BASE_DIR, 'data/stockIndex')
        if not os.path.isdir(default_stock_index_dir):
            os.makedirs(default_stock_index_dir)
        for key, value in self.stock_index.items() :
            ticker = yf.Ticker(value)
            dataFrame = pd.DataFrame(ticker.history(start=start_date, end=end_date))
            dataFrame.drop(['Dividends', 'Stock Splits'], 1, inplace=True)
            path = f'{default_stock_index_dir}/{key}.csv'
            dataFrame.to_csv(path, mode='w', header=False)

if __name__ == '__main__' :
    parse = argparse.ArgumentParser()
    parse.add_argument('--stock_name')
    parse.add_argument('--start_date', default='2008-12-01')
    parse.add_argument('--end_date', default='2018-12-31')
    parse.add_argument('--stock_index', default='T')
    args = parse.parse_args()

    crawler = Crawler()

    if args.stock_index == 'T':
        crawler.getStockIndexData(args.start_date, args.end_date)

    crawler.getStockData(args.stock_name, args.start_date, args.end_date)