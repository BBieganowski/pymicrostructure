"""Range of metrics to analyze market data."""

from pymicrostructure.markets.base import Market
import pandas as pd
import numpy as np
from numpy.lib.stride_tricks import as_strided
from scipy import stats
from statsmodels.tsa.stattools import adfuller
import seaborn as sns


################ LIQUIDITY METRICS ################


def quoted_spread(market: Market) -> pd.DataFrame:
    """
    Calculate the quoted spread of a market.

    The quoted spread is the difference between the best bid and best ask prices.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have an 'ob_snapshots' attribute.
        Each snapshot should be a dictionary with 'bid' and 'ask' keys.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with a 'quoted_spread' column, indexed by snapshot times.
    """
    best_bid = [
        snapshot["bid"][0]["price"] if snapshot["bid"] else None
        for snapshot in market.ob_snapshots
    ]
    best_ask = [
        snapshot["ask"][0]["price"] if snapshot["ask"] else None
        for snapshot in market.ob_snapshots
    ]
    ob_time = [snapshot["time"] for snapshot in market.ob_snapshots]

    df = pd.DataFrame({"best_bid": best_bid, "best_ask": best_ask}, index=ob_time)
    df["quoted_spread"] = df["best_ask"] - df["best_bid"]

    return df[["quoted_spread"]]


def effective_spread(
    market: Market, volume: float, relative: bool = False
) -> pd.DataFrame:
    """
    Calculate the effective spread of a market for a given order size.

    The effective spread is the difference between the execution price of a market order
    and the midpoint price, multiplied by 2 to account for round-trip costs.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have an 'ob_snapshots' attribute.
        Each snapshot should be a dictionary with 'bid' and 'ask' keys, containing lists
        of price-volume pairs.
    volume : float
        The size of the market order to simulate.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with 'effective_spread_buy' and 'effective_spread_sell' columns,
        indexed by snapshot times.
    """
    assert volume > 0, "Volume must be positive."

    def calculate_execution_price(orders, volume):
        remaining_volume = volume
        execution_price = 0
        for order in orders:
            price, size = order["price"], abs(order["volume"])
            if remaining_volume <= size:
                execution_price += price * remaining_volume
                break
            else:
                execution_price += price * size
                remaining_volume -= size
        return execution_price / volume if volume > 0 else None

    effective_spreads = []
    ob_times = []

    for snapshot in market.ob_snapshots:
        bid_orders = snapshot["bid"]
        ask_orders = snapshot["ask"]

        if not bid_orders or not ask_orders:
            effective_spreads.append((None, None))
        else:
            mid_price = (bid_orders[0]["price"] + ask_orders[0]["price"]) / 2

            buy_execution_price = calculate_execution_price(ask_orders, volume)
            sell_execution_price = calculate_execution_price(bid_orders, volume)

            if buy_execution_price and sell_execution_price:
                effective_spread_buy = 2 * abs((buy_execution_price - mid_price))
                effective_spread_sell = -2 * abs((mid_price - sell_execution_price))
                if relative:
                    effective_spread_buy /= mid_price
                    effective_spread_sell /= mid_price
                effective_spreads.append((effective_spread_buy, effective_spread_sell))
            else:
                effective_spreads.append((None, None))

        ob_times.append(snapshot["time"])

    df = pd.DataFrame(
        effective_spreads,
        columns=[
            f"effective_spread_buy_v_{volume}",
            f"effective_spread_sell_v_{volume}",
        ],
        index=ob_times,
    )

    return df


def amihud_illiquidity(market: Market, window: int = 20) -> pd.DataFrame:
    """
    Calculate the rolling window Amihud illiquidity measure (lambda) based on trade history.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have a 'trade_history' attribute.
        Each trade in the history should be a dictionary with 'price', 'volume', and 'time' keys.
    window : int, optional
        The size of the rolling window (in number of periods). Default is 20.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with an 'amihud_lambda' column, indexed by time.
    """
    # Convert trade history to DataFrame
    trades_df = pd.DataFrame(market.trade_history)
    trades_df.set_index("time", inplace=True)

    # Calculate returns
    trades_df["return"] = trades_df["price"].pct_change() * 100

    # Calculate dollar volume
    trades_df["dollar_volume"] = trades_df["price"] * trades_df["volume"]

    assert 0 not in trades_df["dollar_volume"], "Dollar volume cannot be zero."

    # Calculate Amihud measure
    trades_df["daily_amihud"] = abs(trades_df["return"]) / trades_df["dollar_volume"]

    # Calculate rolling window Amihud lambda
    trades_df["amihud_lambda"] = trades_df["daily_amihud"].rolling(window=window).mean()

    return trades_df[["amihud_lambda"]]


def kyle_lambda(market: Market, window: int = 20) -> pd.DataFrame:
    """
    Calculate the rolling window Kyle's Lambda based on trade history.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have a 'trade_history' attribute.
        Each trade in the history should be a dictionary with 'price', 'volume', 'aggressor_side', and 'time' keys.
    window : int, optional
        The size of the rolling window (in number of periods). Default is 20.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with a 'kyle_lambda' column, indexed by time.
    """
    # Convert trade history to DataFrame
    trades_df = pd.DataFrame(market.trade_history)
    trades_df.set_index("time", inplace=True)

    # Calculate price changes
    trades_df["price_change"] = trades_df["price"].diff()

    # Calculate signed volume (order flow)
    trades_df["signed_volume"] = trades_df["volume"] * trades_df["aggressor_side"]
    trades_df.dropna(inplace=True)

    def rolling_regression(x, y, window=100):
        slope = [np.nan] * window
        for i in range(window, len(x)):
            slope.append(np.polyfit(x[i - window : i], y[i - window : i], 1)[0])
        return slope

    trades_df["kyle_lambda"] = rolling_regression(
        trades_df["price_change"], trades_df["signed_volume"]
    )

    # Function to calculate Kyle's Lambda for a window
    return trades_df[["kyle_lambda"]]


################ INEFFICIENCY METRICS ##################


def returns_autocorrelation(market: Market, window: int = 20) -> pd.DataFrame:
    """
    Calculate the rolling window auto-correlation of returns based on trade history.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have a 'trade_history' attribute.
        Each trade in the history should be a dictionary with 'price', 'time', and 'aggressor_side' keys.
    window : int, optional
        The size of the rolling window (in number of periods). Default is 20.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with a 'returns_autocorr' column, indexed by time.
    """
    # Convert trade history to DataFrame
    trades_df = pd.DataFrame(market.trade_history)
    trades_df.set_index("time", inplace=True)

    # Calculate returns
    trades_df["return"] = trades_df["price"].pct_change()

    # Calculate rolling window auto-correlation
    trades_df["returns_autocorr"] = (
        trades_df["return"].rolling(window=window).corr(trades_df["return"].shift(1))
    )

    return trades_df[["returns_autocorr"]]


def variance_ratio_test(market: Market, k: int = 5, window: int = 100) -> pd.DataFrame:
    """
    Perform a rolling Variance Ratio test on price series.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have a 'trade_history' attribute.
        Each trade in the history should be a dictionary with 'price' and 'time' keys.
    k : int, optional
        The number of periods to use for the k-period return. Default is 5.
    window : int, optional
        The size of the rolling window. Default is 100.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with 'vr_statistic' and 'p_value' columns, indexed by time.
    """
    # Convert trade history to DataFrame
    trades_df = pd.DataFrame(market.trade_history)
    trades_df.set_index("time", inplace=True)

    # Calculate log returns
    trades_df["log_return"] = np.log(trades_df["price"]).diff()

    def calculate_vr(returns):
        if len(returns) < window:
            return pd.Series({"vr_statistic": np.nan, "p_value": np.nan})

        # Calculate 1-period and k-period variances
        var_1 = np.var(returns)
        var_k = np.var(returns.rolling(k).sum()) / k

        # Calculate Variance Ratio
        vr = var_k / var_1

        # Calculate test statistic
        m = len(returns)
        phi = (2 * (2 * k - 1) * (k - 1)) / (3 * k * m)
        vr_statistic = (vr - 1) / np.sqrt(phi)

        return vr_statistic

    # Perform rolling Variance Ratio test
    trades_df.dropna(inplace=True)
    trades_df["vr_statistic"] = (
        trades_df["log_return"].rolling(window).apply(calculate_vr)
    )

    return trades_df[["vr_statistic"]]


def hurst_exponent(
    market: Market, window: int = 100, max_lag: int = 20
) -> pd.DataFrame:
    """
    Calculate the rolling Hurst exponent for a price series.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have a 'trade_history' attribute.
        Each trade in the history should be a dictionary with 'price' and 'time' keys.
    window : int, optional
        The size of the rolling window. Default is 100.
    max_lag : int, optional
        The maximum lag to consider in the R/S calculation. Default is 20.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with a 'hurst_exponent' column, indexed by time.
    """
    # Convert trade history to DataFrame
    trades_df = pd.DataFrame(market.trade_history)
    trades_df.set_index("time", inplace=True)

    # Calculate log returns
    trades_df["log_return"] = np.log(trades_df["price"]).diff()

    def calculate_hurst(returns):
        returns = returns.dropna().values  # Convert to numpy array and drop NaNs
        if len(returns) < window:
            return np.nan

        # Calculate the array of the variances of the lagged differences
        tau = [np.arange(1, lag + 1) for lag in range(2, max_lag)]

        # Calculate the cumulative sum of log returns
        cum_sum = returns.cumsum()

        def r_s(lag):
            # Use list comprehension instead of stride tricks
            series = [cum_sum[lag:] - cum_sum[:-lag]]

            # Calculate the R/S statistic
            r = np.max(series) - np.min(series)
            s = np.std(np.diff(series))
            return r / s if s != 0 else np.nan

        r_s_values = [r_s(t) for t in range(2, max_lag)]

        # Calculate the Hurst exponent
        hurst = np.polyfit(np.log(range(2, max_lag)), np.log(r_s_values), 1)[0]

        return hurst

    # Calculate rolling Hurst exponent
    trades_df["hurst_exponent"] = (
        trades_df["log_return"].rolling(window=window).apply(calculate_hurst)
    )

    return trades_df[["hurst_exponent"]]


def rolling_adf_test(
    market: Market, window: int = 100, alpha: float = 0.05
) -> pd.DataFrame:
    """
    Perform a rolling Augmented Dickey-Fuller test on price series.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have a 'trade_history' attribute.
        Each trade in the history should be a dictionary with 'price' and 'time' keys.
    window : int, optional
        The size of the rolling window. Default is 100.
    alpha : float, optional
        The significance level for the test. Default is 0.05.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with 'adf_statistic', 'p_value', and 'is_stationary' columns, indexed by time.
    """
    # Convert trade history to DataFrame
    trades_df = pd.DataFrame(market.trade_history)
    trades_df.set_index("time", inplace=True)

    def perform_adf_test(prices):
        if len(prices) < window:
            return pd.Series(
                {"adf_statistic": np.nan, "p_value": np.nan, "is_stationary": np.nan}
            )

        result = adfuller(prices, autolag="AIC")
        adf_statistic, p_value = result[0], result[1]

        return adf_statistic

    # Perform rolling ADF test
    trades_df["adf_statistic"] = (
        trades_df["price"].rolling(window).apply(perform_adf_test)
    )

    return trades_df[["adf_statistic"]]


################ ORDER FLOW METRICS ####################


def rolling_cancellation_rate(market: Market, window: int = 100) -> pd.DataFrame:
    """
    Calculate the rolling window cancellation rate based on order history.

    The cancellation rate is the number of canceled orders divided by the total number of orders.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have a 'cancellations' and 'order_history' attribute.
        Each order in the history should be a dictionary with 'status' and 'time' keys.
    window : int, optional
        The size of the rolling window. Default is 100.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with a 'cancellation_rate' column, indexed by time.
    """
    # Convert order history to DataFrame
    cancellations = market.cancellations
    cancellations = [(abs(x.volume), x.time) for x in cancellations]
    cancellations_df = pd.DataFrame(cancellations, columns=["volume", "time"])
    cancellations_df.set_index("time", inplace=True)
    # aggregate on time
    cancellations_df = cancellations_df.groupby("time").sum()
    return cancellations_df


def order_flow_imbalance(market: Market, window: int = 100) -> pd.DataFrame:
    """
    Calculate the rolling window order flow imbalance based on trade history.

    The order flow imbalance is the ratio of buy volume to total volume.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have a 'trade_history' attribute.
        Each trade in the history should be a dictionary with 'volume' and 'aggressor_side' keys.
    window : int, optional
        The size of the rolling window. Default is 100.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with an 'order_flow_imbalance' column, indexed by time.
    """
    # Convert trade history to DataFrame
    trades_df = pd.DataFrame(market.trade_history)
    trades_df.set_index("time", inplace=True)

    # Calculate order flow imbalance
    trades_df["order_flow_imbalance"] = (
        trades_df["volume"] * trades_df["aggressor_side"]
    )

    # Calculate rolling window order flow imbalance
    trades_df["order_flow_imbalance"] = (
        trades_df["order_flow_imbalance"].rolling(window=window).mean()
    )

    return trades_df[["order_flow_imbalance"]]


def trade_sign_autocorrelation(market: Market, window: int = 100) -> pd.DataFrame:
    """
    Calculate the rolling window auto-correlation of trade signs based on trade history.

    The trade sign is the sign of the trade price change.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have a 'trade_history' attribute.
        Each trade in the history should be a dictionary with 'price', 'time', and 'aggressor_side' keys.
    window : int, optional
        The size of the rolling window. Default is 100.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with a 'trade_sign_autocorr' column, indexed by time.
    """
    # Convert trade history to DataFrame
    trades_df = pd.DataFrame(market.trade_history)
    trades_df.set_index("time", inplace=True)

    # Calculate trade signs
    trades_df["trade_sign"] = np.sign(trades_df["aggressor_side"])

    # Calculate rolling window auto-correlation
    trades_df["trade_sign_autocorr"] = (
        trades_df["trade_sign"]
        .rolling(window=window)
        .corr(trades_df["trade_sign"].shift(1))
    )

    return trades_df[["trade_sign_autocorr"]]


################ ORDER BOOK METRICS ####################


def order_book_depth(market: Market, window: int = 100) -> pd.DataFrame:
    """
    Calculate the rolling window order book depth based on order book snapshots.

    The order book depth is the total volume at the best bid and best ask prices.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have an 'ob_snapshots' attribute.
        Each snapshot should be a dictionary with 'bid' and 'ask' keys, containing lists
        of price-volume pairs.
    window : int, optional
        The size of the rolling window. Default is 100.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with 'bid_depth' and 'ask_depth' columns, indexed by time.
    """
    # Extract bid and ask depths from order book snapshots
    bid_depth = [
        sum(order["volume"] for order in snapshot["bid"]) if snapshot["bid"] else 0
        for snapshot in market.ob_snapshots
    ]
    ask_depth = [
        sum(order["volume"] for order in snapshot["ask"]) if snapshot["ask"] else 0
        for snapshot in market.ob_snapshots
    ]
    ob_time = [snapshot["time"] for snapshot in market.ob_snapshots]

    df = pd.DataFrame({"bid_depth": bid_depth, "ask_depth": ask_depth}, index=ob_time)
    df["bid_depth"] = df["bid_depth"].rolling(window=window).mean()
    df["ask_depth"] = df["ask_depth"].rolling(window=window).mean()
    df["depth_difference"] = df["ask_depth"] + df["bid_depth"]

    return df[["bid_depth", "ask_depth", "depth_difference"]]


def order_book_heatmap(market: Market, frequency: int = 10) -> pd.DataFrame:
    """
    Create a heatmap of order book volumes over time.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have an 'ob_snapshots' attribute.
        Each snapshot should be a dictionary with 'bid' and 'ask' keys, containing lists
        of price-volume pairs.
    frequency : int, optional
        The frequency of snapshots to include in the heatmap. Default is 10.
        This parameter can be used to reduce the computation time of the heatmap.
        At a cost of less resolution.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with order book volumes indexed by time and price level.
    """
    df = pd.DataFrame()
    for i in market.ob_snapshots[::10]:
        timestamp = i["time"]
        bid_prices = np.array([b["price"] for b in i["bid"]])
        bid_volumes = np.array([b["volume"] for b in i["bid"]])
        bid_volumes = np.cumsum(bid_volumes)

        ask_prices = np.array([a["price"] for a in i["ask"]])
        ask_volumes = np.array([a["volume"] for a in i["ask"]])
        ask_volumes = np.cumsum(ask_volumes)

        cols = np.append(bid_prices, ask_prices)
        data = np.append(bid_volumes, ask_volumes)

        df_slice = pd.DataFrame(index=[timestamp], columns=cols, data=[data])
        df = pd.concat([df, df_slice])
    df = df[df.columns.sort_values()]
    bids = df[df > 0].bfill(axis=1).fillna(0)
    asks = df[df < 0].ffill(axis=1).abs().fillna(0)
    return (bids + asks).T[::-1]


################ PRICE DYNAMICS METRICS ####################


def vwap(market: Market, window: int = 100) -> pd.DataFrame:
    """
    Calculate the rolling window volume-weighted average price (VWAP) based on trade history.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have a 'trade_history' attribute.
        Each trade in the history should be a dictionary with 'price', 'volume', and 'time' keys.
    window : int, optional
        The size of the rolling window. Default is 100.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with a 'vwap' column, indexed by time.
    """
    # Convert trade history to DataFrame
    trades_df = pd.DataFrame(market.trade_history)
    trades_df.set_index("time", inplace=True)

    # Calculate VWAP
    trades_df["dollar_volume"] = trades_df["price"] * trades_df["volume"]
    trades_df["cumulative_dollar_volume"] = (
        trades_df["dollar_volume"].rolling(window=window).sum()
    )
    trades_df["cumulative_volume"] = trades_df["volume"].rolling(window=window).sum()
    trades_df["vwap"] = (
        trades_df["cumulative_dollar_volume"] / trades_df["cumulative_volume"]
    )

    return trades_df[["vwap"]]


def trade_midprice_deviation(market: Market, window: int = 100) -> pd.DataFrame:
    """
    Calculate the rolling window deviation of trade prices from the midprice based on trade history.

    The midprice is the average of the best bid and best ask prices.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have an 'ob_snapshots' and 'trade_history' attribute.
        Each snapshot should be a dictionary with 'bid' and 'ask' keys, containing lists of price-volume pairs.
        Each trade in the history should be a dictionary with 'price' and 'time' keys.
    window : int, optional
        The size of the rolling window. Default is 100.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with a 'trade_midprice_deviation' column, indexed by time.
    """
    # Extract midprices from order book snapshots
    midprices = [
        (
            (snapshot["bid"][0]["price"] + snapshot["ask"][0]["price"]) / 2
            if snapshot["bid"] and snapshot["ask"]
            else None
        )
        for snapshot in market.ob_snapshots
    ]
    ob_time = [snapshot["time"] for snapshot in market.ob_snapshots]

    # Convert trade history to DataFrame
    trades_df = pd.DataFrame(market.trade_history)
    trades_df.set_index("time", inplace=True)

    ob_midprices = pd.DataFrame(midprices, index=ob_time, columns=["midprice"])
    summary = trades_df.join(ob_midprices, how="outer")
    summary.dropna(inplace=True)
    # Calculate deviation from midprice
    summary["trade_midprice_deviation"] = abs(summary["price"] - summary["midprice"])
    summary["trade_midprice_deviation"] = (
        summary["trade_midprice_deviation"].rolling(window=window).mean()
    )

    return summary[["trade_midprice_deviation"]]


def realized_volatility(market: Market, window: int = 100) -> pd.DataFrame:
    """
    Calculate the rolling window realized volatility based on trade history.

    Realized volatility is the standard deviation of price returns over a given window.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have a 'trade_history' attribute.
        Each trade in the history should be a dictionary with 'price' and 'time' keys.
    window : int, optional
        The size of the rolling window. Default is 100.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with a 'realized_volatility' column, indexed by time.
    """
    # Convert trade history to DataFrame
    trades_df = pd.DataFrame(market.trade_history)
    trades_df.set_index("time", inplace=True)

    # Calculate log returns
    trades_df["log_return"] = np.log(trades_df["price"]).diff()

    # Calculate rolling window realized volatility
    trades_df["realized_volatility"] = (
        trades_df["log_return"].rolling(window=window).std()
    )

    return trades_df[["realized_volatility"]]


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


################ OTHER METRICS METRICS ################


def news_goodness(market: Market, window: int = 20) -> pd.DataFrame:
    """
    Calculate the rolling window news goodness based on trade history.

    The news goodness is the ratio of the number of trades with positive news to the total number of trades.

    Parameters:
    -----------
    market : Market
        An object representing the market, which must have a 'trade_history' attribute.
        Each trade in the history should be a dictionary with 'price', 'time', and 'news' keys.
    window : int, optional
        The size of the rolling window. Default is 100.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with a 'news_goodness' column, indexed by time.
    """
    # Convert trade history to DataFrame
    news_history = pd.DataFrame(market.news_history)
    return news_history
