import os
import mplfinance as fplt


# Plots OHLC with 50*x, 150*x and 200*x SMAs, where x is the number of years.
def plot_ohlc_with_sma(fig_name, title, ohlc_data, number_years, is_snp=False):
    sma50_title = f'SMA{50 * number_years}'
    sma150_title = f'SMA{150 * number_years}'
    sma200_title = f'SMA{200 * number_years}'

    sma50 = 50*number_years
    sma150 = 150*number_years
    sma200 = 200*number_years

    ohlc_data_trimmed = ohlc_data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()

    mc = fplt.make_marketcolors(
        up='tab:blue', down='tab:red',
        wick={'up': 'blue', 'down': 'red'},
        volume='lawngreen',
    )

    s = fplt.make_mpf_style(base_mpl_style="seaborn", marketcolors=mc, mavcolors=["green", "blue", "red"])

    fig, axes = fplt.plot(
        ohlc_data_trimmed,
        type="candle",
        title=title,
        ylabel='Price ($)',
        mav=(sma50, sma150, sma200),
        figscale=1,
        style=s,
        returnfig=True,
    )

    axes[0].legend((sma50_title, sma150_title, sma200_title), loc='upper left')

    if is_snp:
        png_dir = "./Plots/S&P500/png"
        svg_dir = "./Plots/S&P500/svg"
    else:
        png_dir = "./Plots/StockPrice/png"
        svg_dir = "./Plots/StockPrice/svg"
    os.makedirs(png_dir, exist_ok=True)
    os.makedirs(svg_dir, exist_ok=True)
    fig.savefig(f"{png_dir}/{fig_name}.png")
    fig.savefig(f"{svg_dir}/{fig_name}.svg")
