from microstructpy.markets.base import Market
import pandas as pd
import numpy as np


################ MICROSTRUCTURE METRICS ################


def roll_spread_estimator(
    market: Market, window_size: int = 100, relative: bool = False
) -> pd.DataFrame:
    """
    Estimate the rolling spread of a market based on its trade history.

    This function calculates the rolling spread using a covariance-based method
    on the price changes over a specified window size.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have a 'trade_history' attribute.
        Each trade in the history should be a dictionary with 'price' and 'time' keys.
    window_size : int, optional (default=100)
        The size of the rolling window for spread estimation.
    relative : bool, optional (default=False)
        If True, calculate relative price changes instead of absolute changes.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with a 'roll_spread' column, indexed by trade times.

    Notes:
    ------
    The roll spread is estimated as:
    roll_spread = mult * sqrt(-cov(delta_price_t, delta_price_t-1))
    where mult is 200 for relative changes and 2 for absolute changes.
    """
    trade_data = [
        {"price": trade["price"], "time": trade["time"]}
        for trade in market.trade_history
    ]

    df = pd.DataFrame(trade_data)
    df.set_index("time", inplace=True)

    if relative:
        df["price_delta"] = df["price"].pct_change()
    else:
        df["price_delta"] = df["price"].diff()

    df["price_delta_l1"] = df["price_delta"].shift(1)
    df.dropna(inplace=True)
    df["rolling_cov"] = (
        df["price_delta"].rolling(window=window_size).cov(df["price_delta_l1"])
    )

    mult = 200 if relative else 2
    df["roll_spread"] = mult * np.sqrt(-df["rolling_cov"].clip(upper=0))

    return df[["roll_spread"]]
