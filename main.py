from logic_helpers import *
from datetime import timedelta
from plotting import *
from finance_management import FinanceManagement
from stock_data import StockData
import math

# Gets a list of tickers for trading by comparing S&P500 tickers to the S&P500 index
# and filtering based on 3 different SMAs.
# Returns a list of tickers suitable for trading
def get_tickers_for_trading(stock_data, number_years, assumed_current_date, plot_results=False):
    print('Getting list of S&P500 tickers. . .')
    snp500_tickers = stock_data.get_snp500_stock_tickers()
    print('Acquired list of tickers')
    end_date = assumed_current_date
    start_date = end_date - relativedelta(years=number_years)
    start_date_string = start_date.strftime('%Y-%m-%d')
    end_date_string = end_date.strftime('%Y-%m-%d')

    print(f'Screening ticker OHLC data over the last {number_years} years from {end_date_string}. . .')
    performant_tickers_data_dict = get_high_rs_rated_ticker_data(stock_data, snp500_tickers, start_date, end_date)
    screened_tickers_data_dict = get_screened_tickers_data(performant_tickers_data_dict, number_years)

    # Plot a subset for sanity checks:
    if plot_results:
        print("Plotting subset. . .")
        plot_ohlc_with_sma(f'snp500_price', f'S&P500: {start_date_string} - {end_date_string}',
                           stock_data.get_historical_data('^GSPC', start_date, end_date), number_years,
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


# Update stop losses on currently owned tickers, or sell if a stop loss has been hit
def manage_owned_tickers(stock_data, financial_management , trailing_stop_loss_fraction):
    print("Updating stop losses. . .")
    tickers = financial_management.get_owned_tickers()
    for ticker in tickers:
        financial_management.update_stop_loss_or_sell(stock_data, ticker, trailing_stop_loss_fraction)


# Handle ticker orders - buy the ones that require buying and apply initial stop losses
def handle_ticker_orders(financial_management, tickers, initial_stop_loss_fraction):
    bank = financial_management.bank * 0.5

    # Find tickers that are not already owned
    owned_tickers = financial_management.get_owned_tickers()
    tickers_to_buy = list(set(tickers) - set(owned_tickers))

    if bank <= 0:
        print('No money left!')
        return

    print(f"Buying stock for {len(tickers_to_buy)} tickers. . .")
    if len(tickers_to_buy) > 0:
        # Divide bank up by number of required investments, submit buy orders and stop losses
        investment_per_ticker = math.floor(bank*100.0/float(len(tickers_to_buy)))/100.0
        for ticker in tickers_to_buy:
            financial_management.submit_buy_order(ticker, investment_per_ticker, initial_stop_loss_fraction)


# The main function
def main():
    start_time = time.time()
    assumed_current_date = datetime.today() - relativedelta(days=2)
    #assumed_current_date = datetime(day=23, month=3, year=2020)  # pandemic low
    #assumed_current_date = datetime(day=23, month=5, year=2020)
    number_years = 1
    initial_stop_loss_fraction = 0.9
    trailing_stop_loss_fraction = 0.8

    # Define stock data and financial management classes
    stock_data = StockData(backtest=False)
    # stock_data.generate_backtest_data(assumed_current_date - relativedelta(years=1), assumed_current_date)
    # filepath = './Files/backtest_data.pkl'
    # stock_data.save_backtest_data(filepath)
    # stock_data.load_backtest_data(filepath)
    financial_management = FinanceManagement(stock_data, assumed_current_date)

    # Get a list of tickers that are suitable for trading
    tickers = get_tickers_for_trading(stock_data, number_years, assumed_current_date)

    # Manage owned tickers by updating stop losses or selling any stock that has hit the stop losses
    manage_owned_tickers(stock_data, financial_management, trailing_stop_loss_fraction)

    # Buy any tickers if required
    handle_ticker_orders(financial_management, tickers, initial_stop_loss_fraction)

    # Save the amendments
    financial_management.save_investment_records()

    # Calculate elapsed time
    end_time = time.time()
    elapsed_seconds = end_time - start_time
    print(f'Time elapsed: {timedelta(seconds=elapsed_seconds)}')


# Application entry point
if __name__ == "__main__":
    main()
