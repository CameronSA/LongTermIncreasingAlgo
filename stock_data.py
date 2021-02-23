import yfinance as yf
import pandas as pd
from tqdm import tqdm
import pickle
from dateutil.relativedelta import relativedelta
import time

class StockData:
    def __init__(self, backtest):
        self.backtest = backtest
        self.backtest_data = {}

    # Generates backtest data
    def generate_backtest_data(self, start_date, end_date, interval='1d'):
        pd.set_option('mode.chained_assignment', None)
        print('Generating backtest data. . .')
        time.sleep(0.01)
        tickers = self.get_snp500_stock_tickers()
        tickers.add('^GSPC')
        for ticker in tqdm(set(tickers)):
            self.backtest_data[ticker] = yf.Ticker(ticker).history(start=start_date.strftime('%Y-%m-%d'),
                                                                   end=end_date.strftime('%Y-%m-%d'),
                                                                   interval=interval)

    # Save data to a pickle file
    def save_backtest_data(self, filepath):
        with open(filepath, 'wb') as file:
            pickle.dump(self.backtest_data, file, pickle.HIGHEST_PROTOCOL)

    # Load data from a pickle file
    def load_backtest_data(self, filepath):
        pd.set_option('mode.chained_assignment', None)
        with open(filepath, 'rb') as file:
            self.backtest_data = pickle.load(file)

    # Returns OHLC data for the specified ticker over the specified date range
    def get_historical_data(self, ticker, start_date, end_date, interval='1d'):
        end_date = end_date + relativedelta(days=1)
        if self.backtest:
            data = self.backtest_data[ticker]
            return data.loc[start_date.strftime('%Y-%m-%d'):end_date.strftime('%Y-%m-%d')]
        else:
            tckr = yf.Ticker(ticker)
            return tckr.history(start=start_date.strftime('%Y-%m-%d'),
                                end=end_date.strftime('%Y-%m-%d'), interval=interval)

    # Returns the most recent OHLC data for the specified ticker from the given date
    def get_most_recent_data(self, ticker, date, interval='1d'):
        return self.get_historical_data(ticker, date, date, interval)

    # Reads tickers from a file.
    # Returns a list of tickers
    def get_snp500_stock_tickers(self):
        tickers = pd.read_csv('./Files/SNP500_listings_2020-11-22.csv')['Symbol']
        return set([item.replace(".", "-") for item in tickers])  # yfinance assumes '-' instead of '.' in tickers

