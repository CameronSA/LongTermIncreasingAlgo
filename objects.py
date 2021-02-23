class AlgorithmResults:
    def __init__(self, time_elapsed, bank_open, bank_close, portfolio_value_open, portfolio_value_close,
                 owned_tickers_open, owned_tickers_close):
        self.time_elapsed = time_elapsed
        self.bank_open = bank_open
        self.bank_close = bank_close
        self.portfolio_value_open = portfolio_value_open
        self.portfolio_value_close = portfolio_value_close
        self.owned_tickers_open = owned_tickers_open
        self.owned_tickers_close = owned_tickers_close
        self.sold_tickers = owned_tickers_close - owned_tickers_open
        self.equity_open = bank_close + portfolio_value_close
        self.equity_close = bank_open + portfolio_value_open


class TickerResults:
    def __init__(self, ticker, ohlc_stop_loss_data):
        self.ticker = ticker
        self.ohlc_stop_loss_data = ohlc_stop_loss_data
