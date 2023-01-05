import yfinance as yf
import pandas_datareader as web

import pandas as pd
from datetime import datetime


def get_current_rate():
    rate = web.get_quote_yahoo("JPY=X")[
        ["shortName", "price", "regularMarketTime", "bid", "ask"]
    ].iloc[0]

    columns = ["Name", "Side", "Open", "High", "Low", "Close"]
    # spread = rate['ask'] - rate['bid']
    name = rate["shortName"]
    bid = rate["bid"]
    ask = rate["ask"]
    price = rate["price"]
    ts = datetime.fromtimestamp(rate["regularMarketTime"])

    return pd.DataFrame(
        data=[
            [name, "bid", price, price, price, price],
            [name, "bid", price, price, price, price],
        ],
        index=[ts, ts],
        columns=columns,
    )


def get_history_rate():
    usd_jpy = yf.Ticker("USDJPY=X")
    return usd_jpy.history(
        period="1d", interval="1m", start="2022-12-20", end="2022-12-21"
    )
