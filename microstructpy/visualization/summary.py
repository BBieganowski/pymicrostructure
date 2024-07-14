from microstructpy.markets.base import Market
from microstructpy.traders.base import Trader
from microstructpy.metrics.trader_metrics import (
    position_history,
    profit_history,
)
import matplotlib.pyplot as plt

from typing import List


def participant_comparison(participants: List[Trader]):
    fig, axs = plt.subplots(2, len(participants))
    # adjust size
    fig.set_size_inches(15, 10)

    for i, participant in enumerate(participants):
        trader_type = type(participant).__name__
        pos_ts, pos_hist = position_history(participant)
        pnl_ts, pnl_hist = profit_history(participant)

        axs[0, i].plot(pos_ts, pos_hist)
        axs[0, i].set_title(f"{trader_type} {participant.trader_id} Position")
        axs[0, i].set_xlabel("Trade Number")

        axs[1, i].plot(pnl_ts, pnl_hist)
        axs[1, i].set_title(f"{trader_type} {participant.trader_id} Profit")
        axs[1, i].set_xlabel("Trade Number")
    plt.show()


def price_path(market: Market):
    """
    Visualize the price path of a market.

    Parameters
    ----------
    market : Market
        The market to visualize.

    Returns
    -------
    None
    """
    prices = [trade["price"] for trade in market.trade_history]
    agressor_side = [trade["agressor_side"] for trade in market.trade_history]
    time = [trade["time"] for trade in market.trade_history]

    best_bid = [
        snapshot["bid"][0]["price"] if snapshot["bid"] else None
        for snapshot in market.ob_snapshots
    ]
    best_ask = [
        snapshot["ask"][0]["price"] if snapshot["ask"] else None
        for snapshot in market.ob_snapshots
    ]
    ob_time = [snapshot["time"] for snapshot in market.ob_snapshots]

    plt.plot(ob_time, best_bid, label="Best Bid", color="green")
    plt.plot(ob_time, best_ask, label="Best Ask", color="red")

    # plt.scatter(time, prices, c=agressor_side, cmap="RdYlGn_r", label="Trades")

    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.title("Price Path")
    plt.legend()
    plt.show()
