from logic_helpers import *

class FinanceManagement:

    # Initialises class by reading past investment records and the bank
    def __init__(self, assumed_current_date, starting_bank=1000, broker_fee_fraction=0.05):
        self.broker_fee_fraction = broker_fee_fraction
        self.current_date = assumed_current_date
        self.__investment_records_filename = './Files/investment_records.csv'
        self.__bank_filename = './Files/bank.csv'
        try:
            self.investment_records = pd.read_csv(self.__investment_records_filename)
        except Exception as e:
            print(e)
            self.investment_records = pd.DataFrame()

        try:
            with open(self.__bank_filename,'r') as file:
                self.bank = float(file.read().replace('\n', ''))
        except Exception as e:
            print(e)
            self.bank = starting_bank
            with open(self.__bank_filename,'w') as file:
                file.write(str(starting_bank))

        self.__complete_orders()

    # For every order that has been submitted but not completed, complete the order
    # and calculate the number of stocks bought (taking into account broker fees).
    def __complete_orders(self):
        if not self.investment_records.empty:
            for index, row in self.investment_records.iterrows():
                if row['Status'] == "Buy_Order":
                    ticker_price = float(get_historical_data(row['Ticker'],
                                                             self.current_date-relativedelta(days=1),
                                                             self.current_date).iloc[-1]['Open'])
                    buy_price = float(row['Buy_Price'])
                    self.investment_records.loc[index, 'Buy_Amount'] = buy_price/ticker_price
                    self.investment_records.loc[index, 'Individual_Buy_Price'] = ticker_price
                # complete sell orders here


    # From the given list of tickers, find the ones that are currently owned.
    # Returns a list of owned tickers
    def get_owned_tickers(self):
        if not self.investment_records.empty:
            return set(self.investment_records['Tickers'])

    # Buys stocks for the given ticker equal to the value of the given price minus broker fees
    def submit_buy_order(self, ticker, price):
        price = price - (price*self.broker_fee_fraction)
        df_to_add = pd.DataFrame([[ticker, "Buy_Order", price, -1, -1]],
                                 columns=["Ticker", "Status", "Buy_Price", "Buy_Amount", "Individual_Buy_Price"])
        self.investment_records.append(df_to_add, ignore_index=True)

    # Saves the investment records to csv
    def save_investment_records(self):
        self.investment_records.to_csv(self.__investment_records_filename, index=False)

