from logic_helpers import *
from datetime import timedelta
from plotting import *


# Gets a list of tickers for trading by comparing S&P500 tickers to the S&P500 index
# and filtering based on 3 different SMAs.
# Returns a list of tickers suitable for trading
def get_tickers_for_trading(number_years, assumed_current_date, plot_results=False):
    print('Getting list of S&P500 tickers. . .')
    snp500_tickers = get_snp500_stock_tickers()
    print('Acquired list of tickers')
    end_date = assumed_current_date
    start_date = end_date - relativedelta(years=number_years)
    start_date_string = start_date.strftime('%Y-%m-%d')
    end_date_string = end_date.strftime('%Y-%m-%d')

    print(f'Screening ticker OHLC data over the last {number_years} years from {end_date_string}. . .')
    performant_tickers_data_dict = get_high_rs_rated_ticker_data(snp500_tickers, start_date, end_date)
    screened_tickers_data_dict = get_screened_tickers_data(performant_tickers_data_dict, number_years)

    # Plot a subset for sanity checks:
    if plot_results:
        print("Plotting subset. . .")
        plot_ohlc_with_sma(f'snp500_price', f'S&P500: {start_date_string} - {end_date_string}',
                           get_historical_data('^GSPC', start_date, end_date), number_years,
                           is_snp=True, clear_old_plots=True)
        i = 0
        divisor = 10
        total = len(screened_tickers_data_dict.keys())
        if total <= 10:
            divisor = 1
        elif total <= 50:
            divisor = 5
        for ticker, ticker_data in screened_tickers_data_dict.items():
            if i % divisor == 0:
                plot_ohlc_with_sma(f'subset_{i}', f'{ticker}: {start_date_string} - {end_date_string}', ticker_data, number_years)
            i += 1

    print('Ticker OHLC data screening complete')
    print(f'Total tickers: {len(snp500_tickers)}')
    print(f'Tickers outperforming S&P500: {len(performant_tickers_data_dict.keys())}')
    print(f'Shortlisted tickers for trading: {len(screened_tickers_data_dict.keys())}')
    return screened_tickers_data_dict.keys()


# The main function
def main():
    start_time = time.time()
    #assumed_current_date = datetime.today()
    #assumed_current_date = datetime(day=23, month=3, year=2020)  # pandemic low
    assumed_current_date = datetime(day=23, month=5, year=2020)
    number_years = 1

    # Get a list of tickers that are suitable for trading
    tickers = get_tickers_for_trading(number_years, assumed_current_date, plot_results=True)

    # Calculate elapsed time
    end_time = time.time()
    elapsed_seconds = end_time - start_time
    print(f'Time elapsed: {timedelta(seconds=elapsed_seconds)}')


# Application entry point
if __name__ == "__main__":
    main()