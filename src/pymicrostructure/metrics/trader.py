"""Metric for analyzing trader performance."""

import pandas as pd
import numpy as np
from pymicrostructure.traders.base import Trader
from typing import List, Tuple, Dict
import math


def position_history(trader: Trader) -> Tuple[List[int], List[int]]:
    """
    Calculate the position history of a trader.

    Args:
        trader (Trader): The trader object.

    Returns:
        Tuple[List[int], List[int]]: A tuple containing two lists:
            - List of timestamps
            - List of positions at each timestamp
    """
    position = 0
    position_history = [0]
    position_timestamps = [0]

    final_timestamp = trader.market.last_submission_time
    trade_index = 0
    filled_trades = trader.filled_trades

    for timestamp in range(1, final_timestamp + 1):
        while (
            trade_index < len(filled_trades)
            and filled_trades[trade_index]["time"] == timestamp
        ):
            position += filled_trades[trade_index]["volume"]
            trade_index += 1

        position_history.append(position)
        position_timestamps.append(timestamp)

    return position_timestamps, position_history


def profit_history(trader: Trader) -> Tuple[List[int], List[float]]:
    """
    Calculate the profit history of a trader.

    Args:
        trader (Trader): The trader object.

    Returns:
        Tuple[List[int], List[float]]: A tuple containing two lists:
            - List of timestamps
            - List of cumulative profits at each timestamp
    """
    realized_profit = 0
    position = 0
    profit = [0]
    profit_timestamps = [0]

    final_timestamp = trader.market.last_submission_time
    trade_history = trader.filled_trades
    trade_index = 0
    midprices = dict(trader.market.midprices)

    for timestamp in range(1, final_timestamp + 1):
        while (
            trade_index < len(trade_history)
            and trade_history[trade_index]["time"] == timestamp
        ):
            trade = trade_history[trade_index]
            realized_profit -= trade["volume"] * trade["price"]
            position += trade["volume"]
            trade_index += 1

        midprice = midprices.get(timestamp, midprices[timestamp - 1])
        total_profit = realized_profit + position * midprice
        profit.append(total_profit)
        profit_timestamps.append(timestamp)

    return profit_timestamps, profit


def calculate_trader_metrics(trader: Trader) -> Dict[str, float]:
    """
    Calculate various performance metrics for a trader.

    Args:
        trader (Trader): The trader object.

    Returns:
        Dict[str, float]: A dictionary of calculated metrics.
    """
    pos_timestamps, pos_hist = position_history(trader)
    profit_timestamps, profit_hist = profit_history(trader)

    profit_series = pd.Series(profit_hist)
    profit_diff = profit_series.diff()

    filled_trades = trader.filled_trades
    total_volume = sum(abs(trade["volume"]) for trade in filled_trades)

    aggressor_volume = sum(
        abs(trade["volume"])
        for trade in filled_trades
        if trade["volume"] * trade["aggressor_side"] > 0
    )
    passive_volume = total_volume - aggressor_volume

    return {
        "final_profit": profit_hist[-1],
        "final_position": pos_hist[-1],
        "profit_per_state": profit_diff.mean(),
        "std_profit_per_state": profit_diff.std(),
        "information_ratio": (
            profit_diff.mean() / profit_diff.std() if profit_diff.std() != 0 else 0
        ),
        "total_trades": len(filled_trades),
        "volume_traded": total_volume,
        "profit_per_volume": profit_hist[-1] / total_volume if total_volume != 0 else 0,
        "average_trade_size": total_volume / len(filled_trades) if filled_trades else 0,
        "fill_rate": (
            total_volume / sum(abs(order.volume) for order in trader.orders)
            if trader.orders
            else 0
        ),
        "time_in_market": sum(1 for pos in pos_hist if pos != 0) / len(pos_hist),
        "mean_position": np.mean(pos_hist),
        "mean_abs_position": np.mean(np.abs(pos_hist)),
        "volume_as_aggressor": aggressor_volume,
        "volume_as_passive": passive_volume,
        "aggressor_ratio": aggressor_volume / total_volume if total_volume != 0 else 0,
    }


def participants_report(participants: List[Trader]) -> pd.DataFrame:
    """
    Generate a performance report for multiple traders.

    Args:
        participants (List[Trader]): A list of trader objects.

    Returns:
        pd.DataFrame: A DataFrame containing performance metrics for all traders.
    """
    metrics = {
        f"{trader.__class__.__name__}_{trader.trader_id}": calculate_trader_metrics(
            trader
        )
        for trader in participants
        if trader.include_in_results
    }
    return pd.DataFrame(metrics).round(2)


def final_profit(trader: Trader) -> float:
    """Get the final profit of a trader."""
    return profit_history(trader)[1][-1]


def final_position(trader: Trader) -> int:
    """Get the final position of a trader."""
    return position_history(trader)[1][-1]


def profit_per_state(trader: Trader) -> float:
    """Calculate the average profit per state for a trader."""
    return pd.Series(profit_history(trader)[1]).diff().mean()


def std_profit_per_state(trader: Trader) -> float:
    """Calculate the standard deviation of profit per state for a trader."""
    return pd.Series(profit_history(trader)[1]).diff().std()


def information_ratio(trader: Trader) -> float:
    """Calculate the information ratio for a trader."""
    std = std_profit_per_state(trader)
    return profit_per_state(trader) / std if std != 0 else 0


def total_trades(trader: Trader) -> int:
    """Get the total number of trades for a trader."""
    return len(trader.filled_trades)


def volume_traded(trader: Trader) -> float:
    """Calculate the total volume traded by a trader."""
    return sum(abs(trade["volume"]) for trade in trader.filled_trades)


def profit_per_volume(trader: Trader) -> float:
    """Calculate the profit per unit volume for a trader."""
    vol = volume_traded(trader)
    return final_profit(trader) / vol if vol != 0 else 0


def average_trade_size(trader: Trader) -> float:
    """Calculate the average trade size for a trader."""
    trades = total_trades(trader)
    return volume_traded(trader) / trades if trades != 0 else 0


def fill_rate(trader: Trader) -> float:
    """Calculate the fill rate for a trader."""
    volume_submitted = sum(abs(x.volume) for x in trader.orders)
    return volume_traded(trader) / volume_submitted if volume_submitted != 0 else 0


def time_in_market(trader: Trader) -> float:
    """Calculate the proportion of time the trader held a non-zero position."""
    pos_hist = position_history(trader)[1]
    return sum(1 for x in pos_hist if x != 0) / len(pos_hist)


def mean_position(trader: Trader) -> float:
    """Calculate the mean position of a trader."""
    return np.mean(position_history(trader)[1])


def mean_abs_position(trader: Trader) -> float:
    """Calculate the mean absolute position of a trader."""
    return np.mean(np.abs(position_history(trader)[1]))


def volume_as_aggressor(trader: Trader) -> float:
    """Calculate the volume traded as an aggressor."""
    return sum(
        abs(trade["volume"])
        for trade in trader.filled_trades
        if trade["volume"] * trade["aggressor_side"] > 0
    )


def volume_as_passive(trader: Trader) -> float:
    """Calculate the volume traded as a passive participant."""
    return sum(
        abs(trade["volume"])
        for trade in trader.filled_trades
        if trade["volume"] * trade["aggressor_side"] < 0
    )


def aggressor_ratio(trader: Trader) -> float:
    """Calculate the ratio of aggressive to total volume."""
    total_vol = volume_traded(trader)
    return volume_as_aggressor(trader) / total_vol if total_vol != 0 else 0


def trader_report(trader: Trader) -> Dict[str, float]:
    """Generate a comprehensive report for a single trader."""
    return calculate_trader_metrics(trader)
