import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
from ta import trend
import time
from numpy.polynomial import polynomial

# Converts a date into an int by calculating the elapsed number of seconds since the start of UTC.
# Returns the converted date
def utc_time_difference(date_time):
    start = datetime(1970, 1, 1, 12, 0, 0, 0)
    elapsed_time = date_time - start
    return elapsed_time.total_seconds()


# Screens ticker OHLC data based on a set of SMA related conditions.
# Returns a dictionary of screened tickers and their OHLC data
def get_screened_tickers_data(tickers_data_dict, number_years):
    screened_tickers_data_dict = {}
    print(f'Filtering ticker OHLC data based on the {number_years * 50}, {number_years * 150},'
          f' and {number_years * 200} day SMAs. . .')
    for ticker, ticker_data in tickers_data_dict.items():
        # Calculate moving averages
        ticker_data[f'SMA{50 * number_years}'] = trend.sma_indicator(ticker_data['Close'], number_years * 50)
        ticker_data[f'SMA{150 * number_years}'] = trend.sma_indicator(ticker_data['Close'], number_years * 150)
        ticker_data[f'SMA{200 * number_years}'] = trend.sma_indicator(ticker_data['Close'], number_years * 200)

        # Add in date to int conversion
        ticker_data['Date'] = ticker_data.index
        ticker_data['UTC'] = ticker_data['Date'].apply(lambda x: utc_time_difference(x))

        # Get most recent values
        most_recent_data = ticker_data.iloc[-1]
        current_close = most_recent_data['Close']
        current_sma50 = most_recent_data[f'SMA{50 * number_years}']
        current_sma150 = most_recent_data[f'SMA{150 * number_years}']
        current_sma200 = most_recent_data[f'SMA{200 * number_years}']

        # 1) Is the current close price > the 50, 150 & 200 SMAs?
        if current_close < current_sma50 or current_close < current_sma150 or current_close < current_sma200:
            continue

        # 2) Is the 50 SMA > 150 SMA > 200 SMA?
        if current_sma50 < current_sma150 or current_sma50 < current_sma200 or current_sma150 < current_sma200:
            continue

        # 3) Has the 200 SMA been trending up for at least 1 month?
        month_ago_date = most_recent_data['Date'] - relativedelta(months=number_years)
        filtered_ticker_data = ticker_data.loc[ticker_data['Date'] >= month_ago_date]
        coefs = polynomial.polyfit(filtered_ticker_data['UTC'], filtered_ticker_data[f'SMA{200 * number_years}'], 1)
        # Make sure SMA yields a positive gradient when fit with a first order polynomial.
        # The most recent value must be greater than the oldest value.
        if coefs[1] < 0 or current_sma200 < filtered_ticker_data[f'SMA{200 * number_years}'][0]:
            continue

        # 4) Is the current price at least 30% above the annual low?
        if current_close < min(ticker_data['Low'])*1.3:
            continue

        # 5) Is the current price within 25% of the annual high?
        annual_high = max(ticker_data['High'])
        if current_close < annual_high*0.75 or current_close > annual_high*1.25:
            continue

        # If the above conditions are met, note the ticker
        screened_tickers_data_dict[ticker] = ticker_data

    return screened_tickers_data_dict


# Selects the top x% performing tickers relative to the S&P500.
# The top x% are then vetted to make sure they are all performing better than the S&P500.
# Returns a dictionary of screened tickers and their OHLC data
def get_high_rs_rated_ticker_data(stock_data, tickers, start_date, end_date, performance_quantile=30.):
    snp_data = stock_data.get_historical_data('^GSPC', start_date, end_date)
    snp_data['Percent Change'] = snp_data['Close'].pct_change()
    snp_return = (snp_data['Percent Change'] + 1).cumprod()[-1]

    returns = []
    ticker_data_dict = {}
    print('Gathering ticker OHLC data and calculating RS ratings relative to the S&P500 index. . .')
    time.sleep(0.01)
    for ticker in tqdm(tickers):
        try:
            ticker_data = stock_data.get_historical_data(ticker, start_date, end_date)
            if ticker_data.empty:
                continue

            ticker_data_dict[ticker] = ticker_data
            ticker_data['Percent Change'] = ticker_data['Close'].pct_change()
            ticker_return = (ticker_data['Percent Change'] + 1).cumprod()[-1]
            relative_ticker_return = ticker_return/snp_return
            returns.append((ticker, relative_ticker_return))
        except Exception as error:
            print(error)
            continue

    rs_data = pd.DataFrame(returns, columns=['Ticker', 'Relative Return'])
    rs_data['RS Rating'] = rs_data['Relative Return'].rank(pct=True)*100.

    print(f'Compiling OHLC for top {performance_quantile}% performing tickers relative to the S&P500. . .')
    rs_data = rs_data[rs_data['RS Rating'] >= rs_data['RS Rating'].quantile(1.-(performance_quantile/100.))]
    rs_data = rs_data[rs_data['RS Rating'] >= 1.]

    screened_tickers_data_dict = {}
    for ticker in rs_data['Ticker']:
        screened_tickers_data_dict[ticker] = ticker_data_dict[ticker]
    return screened_tickers_data_dict

