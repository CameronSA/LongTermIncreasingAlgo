from logic_helpers import *
import math

class FinanceManagement:

    # Initialises class by reading past investment records and the bank
    def __init__(self, stock_data, assumed_current_date, initial_stop_loss_fraction, trailing_stop_loss_fraction,
                 starting_bank=10000, broker_fee_fraction=0.05):
        self.initial_stop_loss_fraction = initial_stop_loss_fraction
        self.trailing_stop_loss_fraction = trailing_stop_loss_fraction
        self.broker_fee_fraction = broker_fee_fraction
        self.current_date = assumed_current_date
        self.__investment_records_filename = './Files/investment_records.csv'
        self.__bank_filename = './Files/bank.csv'
        self.__bank_log_filename = './Files/bank_log.csv'
        self.bank_log_columns = ["Date", "Ticker", "Action", "Price", "Balance"]
        self.bank_log = pd.DataFrame(columns=self.bank_log_columns)
        self.investment_records_columns = ["Date", "Ticker", "Status", "Buy_Price", "Buy_Amount",
                                           "Individual_Buy_Price", "Stop_Loss"]
        try:
            self.investment_records = pd.read_csv(self.__investment_records_filename)
        except Exception as e:
            print(e)
            self.investment_records = pd.DataFrame(columns=self.investment_records_columns)

        try:
            with open(self.__bank_filename, 'r') as file:
                self.bank = float(file.read().replace('\n', ''))
        except Exception as e:
            print(e)
            self.bank = starting_bank
            with open(self.__bank_filename, 'w') as file:
                file.write(str(starting_bank))

        self.__complete_orders(stock_data)

    # For every order that has been submitted but not completed, complete the order and update the bank
    def __complete_orders(self, stock_data):
        if not self.investment_records.empty:
            indices_to_drop = []
            for index, row in self.investment_records.iterrows():
                # Complete buy orders
                if datetime.strptime(row['Date'], "%Y-%m-%d") < self.current_date:
                    recent_data = stock_data.get_historical_data(row['Ticker'], self.current_date-relativedelta(days=3),
                                                                 self.current_date)
                    if row['Status'] == "Buy_Order":
                        if not recent_data.empty:
                            ticker_price = float(recent_data.iloc[-1]['Close'])
                            buy_price = math.floor(float(row['Buy_Price'])*100.0)/100.0
                            self.investment_records.loc[index, 'Buy_Amount'] = buy_price/ticker_price
                            self.investment_records.loc[index, 'Individual_Buy_Price'] = math.floor(100.0*ticker_price)/100.0
                            self.investment_records.loc[index, 'Status'] = 'Owned'
                            self.investment_records.loc[index, 'Stop_Loss'] = \
                                math.floor(100.0*self.initial_stop_loss_fraction*ticker_price)/100.0
                            self.bank = math.floor(100.0*(self.bank - buy_price - (buy_price*self.broker_fee_fraction)))/100.0
                            bank_record = pd.DataFrame([[self.current_date.strftime('%Y-%m-%d'),
                                                         row['Ticker'],
                                                         "BUY",
                                                         math.floor(-100.0*(buy_price - (
                                                                 buy_price*self.broker_fee_fraction)))/100.0,
                                                         self.bank]], columns=self.bank_log_columns)
                            self.bank_log = self.bank_log.append(bank_record)
                    # Complete sell orders
                    if row['Status'] == "Sell_Order":
                        if not recent_data.empty:
                            ticker_price = float(recent_data.iloc[-1]['Open'])
                            sell_price = math.floor(100.0*float(row['Buy_Amount'])*ticker_price)/100.0
                            self.bank = math.floor(100.0*(self.bank + sell_price - (sell_price*self.broker_fee_fraction)))/100.0
                            bank_record = pd.DataFrame([[self.current_date.strftime('%Y-%m-%d'),
                                                         row['Ticker'],
                                                         "SELL",
                                                         math.floor(100.0 * (sell_price - (
                                                                     sell_price * self.broker_fee_fraction))) / 100.0,
                                                         self.bank]], columns=self.bank_log_columns)
                            self.bank_log = self.bank_log.append(bank_record, ignore_index=True)
                            indices_to_drop.append(index)
                    # Removes sold stock from original dataframe
            for index in indices_to_drop:
                self.investment_records.drop(index, inplace=True)

    # From the given list of tickers, find the ones that are currently owned.
    # Returns a list of owned tickers
    def get_owned_tickers(self):
        if not self.investment_records.empty:
            return set(self.investment_records['Ticker'])
        else:
            return []

    # Buys stocks for the given ticker equal to the value of the given price minus broker fees
    def submit_buy_order(self, ticker, price):
        price = math.floor(100.0*price)/100.0
        df_to_add = pd.DataFrame([[self.current_date.strftime('%Y-%m-%d'), ticker, "Buy_Order", price, -1, -1, -1]],
                                 columns=self.investment_records_columns)

        if ticker in self.investment_records['Ticker']:
            print(f"Record for {ticker} already exists!")
        else:
            self.investment_records = self.investment_records.append(df_to_add, ignore_index=True)

    # Sells all stocks for the given ticker
    def submit_sell_order(self, ticker):
        self.investment_records.loc[(self.investment_records["Ticker"] == ticker) &
                                    (self.investment_records["Status"] == "Owned"), "Status"] = "Sell_Order"

    # Updates the stop loss for the given ticker, or sells if it has been hit
    def update_stop_loss_or_sell(self, stock_data, ticker):
        for index, row in self.investment_records.iterrows():
            if row['Ticker'] == ticker and row['Status'] == 'Owned':
                stop_loss = float(row['Stop_Loss'])
                # Yesterday's closing price
                recent_data = stock_data.get_historical_data(row['Ticker'], self.current_date - relativedelta(days=1),
                                                             self.current_date)
                ticker_price = float(recent_data.iloc[-1]['Close'])
                if not recent_data.empty:
                    if ticker_price <= stop_loss:
                        print(f'Submitting sell order for {ticker}')
                        self.submit_sell_order(ticker)
                    elif stop_loss < ticker_price*self.trailing_stop_loss_fraction:
                        self.investment_records.loc[index, 'Stop_Loss'] = \
                            math.floor(100.0*ticker_price*self.trailing_stop_loss_fraction)/100.0

    # Saves the investment records to csv
    def save_investment_records(self):
        self.investment_records.to_csv(self.__investment_records_filename, index=False)
        with open(self.__bank_filename, 'w') as file:
            file.write(str(self.bank))
        self.bank_log.to_csv(self.__bank_log_filename, index=False)
        print('Investment records saved')

    # Gets the portfolio value.
    # Returns the number of tickers owned and the total value of stock held
    def get_portfolio_value(self, stock_data):
        held_df = self.investment_records[self.investment_records["Status"] == "Owned"].copy()
        held_df['Stock_Value'] = -1

        for index, row in held_df.iterrows():
            stock_value = float(stock_data.get_historical_data(row['Ticker'], self.current_date - relativedelta(days=3),
                                                               self.current_date).iloc[-1]['Close'])*row['Buy_Amount']
            held_df.loc[index, 'Stock_Value'] = stock_value

        portfolio_value = sum(held_df['Stock_Value'])
        return len(held_df), portfolio_value


