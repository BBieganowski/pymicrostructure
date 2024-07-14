import pandas as pd
import numpy as np
from microstructpy.traders.base import Trader

def position_history(trader):
    position = 0
    position_history = [0]  # Start with initial position of 0
    position_timestamps = [0]  # Start with timestamp 0

    final_timestamp = trader.market.last_submission_time
    trade_index = 0

    for timestamp in range(1, final_timestamp + 1):
        # Process any trades at this timestamp
        while (
            trade_index < len(trader.filled_trades)
            and trader.filled_trades[trade_index]["time"] == timestamp
        ):
            trade = trader.filled_trades[trade_index]
            position += trade["volume"]
            trade_index += 1

        # Append the current position to the history
        position_history.append(position)
        position_timestamps.append(timestamp)

    return position_timestamps, position_history


def profit_history(trader):
    realized_profit = 0
    unrealized_profit = 0
    position = 0

    profit = [0]
    profit_timestamps = [0]

    final_timestamp = trader.market.last_submission_time
    trade_history = trader.filled_trades.copy()

    for timestamp in range(final_timestamp + 1):
        # Process trades at this timestamp
        while trade_history and trade_history[0]["time"] == timestamp:
            trade = trade_history.pop(0)
            volume = trade["volume"]
            price = trade["price"]

            # Calculate realized profit
            realized_profit -= volume * price
            position += volume

        # Mark position to market
        midprice = [x[1] for x in trader.market.midprices if x[0] == timestamp][0]

        # Calculate unrealized profit
        unrealized_profit = position * midprice

        # Calculate total profit
        total_profit = realized_profit + unrealized_profit

        profit.append(total_profit)
        profit_timestamps.append(timestamp)

    return profit_timestamps, profit


def final_profit(trader):
    return profit_history(trader)[1][-1]

def final_position(trader):
    return position_history(trader)[1][-1]

def profit_per_state(trader):
    profit = profit_history(trader)[1]
    return pd.Series(profit).diff().mean()

def std_profit_per_state(trader):
    profit = profit_history(trader)[1]
    return pd.Series(profit).diff().std()

def information_ratio(trader):
    std = std_profit_per_state(trader)
    if std == 0:
        return 0
    return profit_per_state(trader) / std

def total_trades(trader):
    return len(trader.filled_trades)

def volume_traded(trader):
    return sum([abs(trade["volume"]) for trade in trader.filled_trades])

def profit_per_volume(trader):
    volume = volume_traded(trader)
    if volume == 0:
        return 0
    return final_profit(trader) /volume

def average_trade_size(trader):
    trade_n = total_trades(trader)
    if trade_n == 0:
        return 0
    return volume_traded(trader) / trade_n

def fill_rate(trader):
    volume_submitted = sum([abs(x.quantity) for x in trader.orders])
    volume_filled = volume_traded(trader)
    if volume_submitted == 0:
        return 0
    return volume_filled / volume_submitted

def time_in_market(trader):
    pos_hist = position_history(trader)[1]
    nonzeros = [x for x in pos_hist if x != 0]
    return len(nonzeros) / len(pos_hist)

def mean_position(trader):
    return np.mean(position_history(trader)[1])

def mean_abs_position(trader):
    return np.mean([abs(x) for x in position_history(trader)[1]])

def volume_as_agressor(trader):
    trades = trader.filled_trades
    agressor_volume = 0
    for trade in trades:
        if trade['volume']*trade['agressor_side'] > 0:
            agressor_volume += abs(trade['volume'])
    return agressor_volume

def volume_as_passive(trader):
    trades = trader.filled_trades
    passive_volume = 0
    for trade in trades:
        if trade['volume']*trade['agressor_side'] < 0:
            passive_volume += abs(trade['volume'])
    return passive_volume

def agressor_ratio(trader):
    agressor = volume_as_agressor(trader)
    passive = volume_as_passive(trader)
    if agressor + passive == 0:
        return 0
    return agressor / (agressor + passive)


def trader_report(trader):
    metrics = {
        "final_profit": final_profit(trader),
        "final_position": final_position(trader),
        "profit_per_state": profit_per_state(trader),
        "std_profit_per_state": std_profit_per_state(trader),
        "information_ratio": information_ratio(trader),
        "total_trades": total_trades(trader),
        "volume_traded": volume_traded(trader),
        "profit_per_volume": profit_per_volume(trader),
        "average_trade_size": average_trade_size(trader),
        "fill_rate": fill_rate(trader),
        "time_in_market": time_in_market(trader),
        "mean_position": mean_position(trader),
        "mean_abs_position": mean_abs_position(trader),
        "volume_as_agressor": volume_as_agressor(trader),
        "volume_as_passive": volume_as_passive(trader),
        "agressor_ratio": agressor_ratio(trader),
    }
    return metrics

def participants_report(participants):
    metrics = {}
    for trader in participants:
        name = f"{trader.__class__.__name__}_{trader.trader_id}"
        metrics[name] = trader_report(trader)
    df = pd.DataFrame(metrics).round(2)
    return df