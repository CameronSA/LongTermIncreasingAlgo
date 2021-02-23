from logic_helpers import *
from datetime import timedelta
from plotting import *
from finance_management import FinanceManagement
from stock_data import StockData
import math
from objects import *
import traceback


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
def manage_owned_tickers(stock_data, financial_management):
    print("Updating stop losses. . .")
    tickers = financial_management.get_owned_tickers()
    for ticker in tickers:
        financial_management.update_stop_loss_or_sell(stock_data, ticker)


# Handle ticker orders - buy the ones that require buying and apply initial stop losses
def handle_ticker_orders(financial_management, tickers):
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
            financial_management.submit_buy_order(ticker, investment_per_ticker)


# Runs the main algorithm.
# assumed_current_date: The assumed current date
# initial_stop_loss_fraction: The initial stop loss fraction
# trailing_stop_loss_fraction: The trailing stop loss fraction
# number_years: The number of years worth of OHLC data over which to perform the stock selection
# stock_data: The stock data class. This abstracts away the API so fake data can be used
# financial_management: The financial management class. This abstracts away
# the buying/selling/stop losses so they can be simulated
def run_algorithm(assumed_current_date, number_years, stock_data, financial_management):
    assumed_current_date_string = assumed_current_date.strftime('%Y-%m-%d')
    start_time = time.time()
    bank_open = financial_management.bank
    owned_tickers_open, portfolio_value_open = financial_management.get_portfolio_value(stock_data)

    # Get a list of tickers that are suitable for trading
    tickers = get_tickers_for_trading(stock_data, number_years, assumed_current_date)

    # Manage owned tickers by updating stop losses or selling any stock that has hit the stop losses
    manage_owned_tickers(stock_data, financial_management)

    # Buy any tickers if required
    handle_ticker_orders(financial_management, tickers)

    # Calculate elapsed time
    end_time = time.time()
    elapsed_seconds = end_time - start_time
    owned_tickers_close, portfolio_value_close = financial_management.get_portfolio_value(stock_data)
    results = AlgorithmResults(timedelta(seconds=elapsed_seconds),
                               bank_open,
                               financial_management.bank,
                               portfolio_value_open,
                               portfolio_value_close,
                               owned_tickers_open,
                               owned_tickers_close)

    print(f'Time elapsed for {assumed_current_date_string}: {timedelta(seconds=elapsed_seconds)}')
    return results


# The backtesting function. Simulates running the algorithm over extended periods of time. Must allow at least a year
def backtest(start_date, end_date, number_years, initial_stop_loss_fraction,
             trailing_stop_loss_fraction, regenerate_data=True):

    results_df_columns = ['bank_open', 'bank_close', 'portfolio_open', 'portfolio_close', 'held_tickers_open',
                          'held_tickers_close', 'sold_tickers', 'equity_open', 'equity_close']
    overall_results_df = pd.DataFrame(columns=results_df_columns)
    start_time = time.time()

    # Initialise stock data class
    stock_data = StockData(backtest=True)
    filepath = './Files/backtest_data.pkl'
    if regenerate_data:
        stock_data.generate_backtest_data(start_date, end_date)
        stock_data.save_backtest_data(filepath)
    stock_data.load_backtest_data(filepath)

    try:
        for i in range(int((end_date-(start_date + relativedelta(years=number_years))).days)):
            assumed_current_date = start_date + relativedelta(years=number_years, days=i)
            assumed_current_date_string = assumed_current_date.strftime('%y-%m-%d')
            print(f"Started for date: {assumed_current_date_string}. . .")

            # Don't run the algorithm beyond the generated data
            if assumed_current_date > end_date:
                break

            # Initialise financial management class
            financial_management = FinanceManagement(stock_data, assumed_current_date,
                                                     initial_stop_loss_fraction, trailing_stop_loss_fraction)

            # Run the algorithm
            results = run_algorithm(assumed_current_date, number_years, stock_data, financial_management)

            results_df = pd.DataFrame([[results.bank_open, results.bank_close, results.portfolio_value_open,
                                        results.portfolio_value_close, results.owned_tickers_open,
                                        results.owned_tickers_close, results.sold_tickers, results.equity_open,
                                        results.equity_close]], columns=results_df_columns)

            # Log the results
            overall_results_df = overall_results_df.append(results_df)

            # Save the trade records
            financial_management.save_investment_records()
            print()
    except Exception as e:
        traceback.print_exc()
        print(f"ERROR encountered: {e}")
        print("Saving last known results before exception. . .")

    # Save the results
    start_date_string = start_date.strftime('%Y-%m-%d')
    end_date_string = end_date.strftime('%Y-%m-%d')
    filepath = f'./Files/backtesting_results_{start_date_string}_to_{end_date_string}.csv'
    overall_results_df.to_csv(filepath, index=False)
    end_time = time.time()
    time_elapsed = timedelta(seconds=(end_time - start_time))
    print(f"Backtesting complete. Time elapsed: {time_elapsed}")


# Application entry point
if __name__ == "__main__":
    #run_algorithm()
    backtest(start_date=datetime.today()-relativedelta(years=2),
             end_date=datetime.today(),
             number_years=1,
             initial_stop_loss_fraction=0.9,
             trailing_stop_loss_fraction=0.8,
             regenerate_data=False)

