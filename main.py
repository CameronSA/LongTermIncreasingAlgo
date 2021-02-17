import pandas as pd
import yfinance as yf
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
from ta import trend
import numpy as np
from numpy.polynomial import polynomial
import warnings
# warnings.simplefilter('ignore', np.RankWarning)

# Converts a date into an int by calculating the elapsed number of seconds since the start of UTC
def utc_time_difference(time):
    start = datetime(1970, 1, 1, 12, 0, 0, 0)
    elapsed_time = time - start
    return elapsed_time.total_seconds()

def get_historical_data(ticker, start_date, end_date, interval='1d'):
    tckr = yf.Ticker(ticker)
    return tckr.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), interval=interval)

# Reads tickers from a file
def getSNP500StockTickers():
    tickers = pd.read_csv('./Files/SNP500_listings_2020-11-22.csv')['Symbol']
    return set([item.replace(".", "-") for item in tickers])  # yfinance assumes '-' instead of '.' in tickers

def screenTickers(tickers, start_date, end_date, number_years):
    screened_tickers = []
    for ticker in tqdm(tickers):
        ticker_data = get_historical_data(ticker, start_date, end_date)

        # Calculate moving averages
        ticker_data[f'SMA{50 * number_years}'] = trend.sma_indicator(ticker_data['Close'], number_years * 50)
        ticker_data[f'SMA{150 * number_years}'] = trend.sma_indicator(ticker_data['Close'], number_years * 150)
        ticker_data[f'SMA{200 * number_years}'] = trend.sma_indicator(ticker_data['Close'], number_years * 200)

        # Add in date to int conversion
        ticker_data['Date'] = ticker_data.index
        ticker_data['UTC'] = ticker_data['Date'].apply(lambda x: utc_time_difference(x))

        most_recent_data = ticker_data.iloc[-1]
        current_close = most_recent_data['Close']
        current_sma50 = most_recent_data[f'SMA{50 * number_years}']
        current_sma150 = most_recent_data[f'SMA{150 * number_years}']
        current_sma200 = most_recent_data[f'SMA{200 * number_years}']

        # 1) Is the current close price greater than the 150 & 200 SMAs?
        if current_close < current_sma150 or current_close < current_sma200:
            continue

        # 2) Is the 150 SMA greater than the 200 SMA?
        if current_sma150 < current_sma200:
            continue

        # 3) Has the 200 SMA been trending up for at least 1 month?
        month_ago_date = most_recent_data['Date'] - relativedelta(months=number_years)
        filtered_ticker_data = ticker_data.loc[ticker_data['Date'] >= month_ago_date]
        coefs = polynomial.polyfit(filtered_ticker_data['UTC'], filtered_ticker_data[f'SMA{200 * number_years}'], 1)
        if coefs[1] < 0:
            continue

        # 4) Is the 50 SMA greater than the 150 SMA and the 200 SMA?
        if current_sma50 < current_sma150 or current_sma50 < current_sma200:
            continue

        # 5) Is the current price greater than the 50 SMA?
        if current_close < current_sma50:
            continue

        # 6) Is the current price at least 30% above the annual low?
        if current_close < min(ticker_data['Low'])*1.3:
            continue

        # 7) Is the current price within 25% of the annual high?
        annual_high = max(ticker_data['High'])
        if current_close < annual_high*0.75 or current_close > annual_high*1.25:
            continue

        # 8) Is the IBD RS-Rating greater than 70?
        #TODO condition

        # If the above conditions are met, note the ticker
        screened_tickers.append(ticker)

    return screened_tickers

def main():
    print('Getting list of tickers. . .')
    number_years = 1
    snp500_tickers = getSNP500StockTickers()
    end_date = datetime.today()
    start_date = end_date - relativedelta(years=number_years)

    print(f'Processing ticker data over the last {number_years} years. . .')
    screened_tickers = screenTickers(snp500_tickers, start_date, end_date, number_years)
    # for ticker in sorted(screened_tickers):
    #     print(ticker)
    print(f'total tickers: {len(snp500_tickers)}')
    print(f'shortlisted tickers: {len(screened_tickers)}')


if __name__ == "__main__":
    main()