from logic_helpers import *
from datetime import timedelta

# Gets a list of tickers for trading by comparing S&P500 tickers to the S&P500 index
# and filtering based on 3 different SMAs.
# Returns a list of tickers suitable for trading
def get_tickers_for_trading(number_years):
    print('Getting list of S&P500 tickers. . .')
    snp500_tickers = get_snp500_stock_tickers()
    print('Acquired list of tickers')
    end_date = datetime.today()
    start_date = end_date - relativedelta(years=number_years)

    print(f'Screening ticker OHLC data over the last {number_years} years. . .')
    performant_tickers_data_dict = get_high_rs_rated_ticker_data(snp500_tickers, start_date, end_date)
    screened_tickers = screen_tickers(performant_tickers_data_dict, number_years)
    print('Ticker OHLC data screening complete')
    # for ticker in sorted(screened_tickers):
    #     print(ticker)
    print(f'total tickers: {len(snp500_tickers)}')
    print(f'tickers outperforming S&P500: {len(performant_tickers_data_dict.keys())}')
    print(f'shortlisted tickers for trading: {len(screened_tickers)}')
    return screened_tickers


# The main function
def main():
    start_time = time.time()

    # Get list of tickers suitable for trading
    tickers = get_tickers_for_trading(1)

    # Calculate elapsed time
    end_time = time.time()
    elapsed_seconds = end_time - start_time
    print(f'Time elapsed: {timedelta(seconds=elapsed_seconds)}')


# Application entry point
if __name__ == "__main__":
    main()