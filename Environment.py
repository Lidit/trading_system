class Environment:
    PRICE_IDX = 2  # 종가의 위치 (현재가의 위치)

    def __init__(self, chart_data=None):
        self.chart_data = chart_data
        self.observation = None
        self.idx = -1

    def reset(self):
        self.observation = None
        self.idx = -1

    def observe(self):
        if len(self.chart_data) > self.idx + 1:
            self.idx += 1
            self.observation = self.chart_data.iloc[self.idx]
            # self.observation = self.chart_data.iloc[]
            return self.observation
        return None

    def get_price(self):
        if self.observation is not None:
            return self.observation[self.PRICE_IDX]
        return None

    def set_chart_data(self, chart_data):
        self.chart_data = chart_data

class RealTimeEnvironment():
    PRICE_IDX = 2 # 실시간 가격의 위치

    def __init__(self, chart_data = None):
        self.chart_data = chart_data
        self.observation = None
        self.idx = -1
    
    def reset(self):
        self.observation = None
    
    def observe(self):
        self.observation = self.chart_data.iloc[-1]

        return self.observation
    
    def get_price(self):
        if self.observation is not None:
            return self.observation[self.PRICE_IDX]
        return None

    def set_chart_data(self, chart_data):
        self.chart_data = chart_data
    