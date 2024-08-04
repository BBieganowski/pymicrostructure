from microstructpy.traders.base import Trader
from functools import partial
from typing import Tuple, Callable
import numpy as np


##### Fairprice Policies #####


def fairprice_constant(fair_price: int) -> Callable[[Trader], int]:
    """
    Constant fairprice policy at user defined price.
    """

    def func(trader: Trader) -> int:
        return fair_price

    return func


def fairprice_orderflow_sign(
    window: int, agressiveness: int
) -> Callable[[Trader], int]:
    """
    Fairprice policy based on the sign of the order flow in the last window trades.
    """

    def func(trader: Trader) -> int:
        orderflow = trader.market.get_recent_trades(window)
        orderflow = sum(
            [trade["volume"] * trade["agressor_side"] for trade in orderflow]
        )
        return trader.fair_price + agressiveness * int(np.sign(orderflow))

    return func


def fairprice_orderflow_magnitude(
    window: int, agressiveness: int
) -> Callable[[Trader], int]:
    """
    Fairprice policy based on the magnitude of the order flow in the last window trades.
    """

    def func(trader: Trader) -> int:
        trades = trader.market.get_recent_trades(window)
        orderflow = sum([trade["volume"] * trade["agressor_side"] for trade in trades])

        total_volume = sum([trade["volume"] for trade in trades])
        indicator = orderflow / total_volume if total_volume != 0 else 0
        return trader.fair_price + int(indicator * agressiveness * 3)

    return func


def fairprice_news_impact_linear(agressiveness: int) -> Callable[[Trader], int]:
    """
    Fairprice policy based on the news impact.
    """

    def func(trader: Trader) -> int:
        news = trader.market.news_history[-1]
        if news == 0:
            return trader.fair_price
        return trader.fair_price + int(news * agressiveness)

    return func


def fairprice_news_impact_exponential(
    window: int, agressiveness: int
) -> Callable[[Trader], int]:
    """
    Fairprice policy based on the news impact.
    """

    def func(trader: Trader) -> int:
        if trader.market.current_tick < window:
            return trader.fair_price
        news = sum(trader.market.news_history[-window:]) / window
        return trader.fair_price + np.exp(news * agressiveness)

    return func


##### Volume Policies #####


def volume_mm_max_allowed() -> Callable[[Trader], Tuple[int, int]]:
    """
    Fairprice policy based on the maximum volume allowed by the trader.
    """

    def func(trader: Trader) -> Tuple[int, int]:
        bid_volume = trader.max_inventory - trader.position
        ask_volume = trader.max_inventory + trader.position
        return bid_volume, -ask_volume

    return func


def volume_mm_constant(volume: int) -> Callable[[Trader], Tuple[int, int]]:
    """
    Constant volume policy at user defined volume.
    """

    def func(trader: Trader) -> Tuple[int, int]:
        max_bid = trader.max_inventory - trader.position
        max_ask = trader.max_inventory + trader.position
        return min(volume, max_bid), -min(volume, max_ask)

    return func


def volume_mm_max_fraction(
    fraction: float = 0.2,
) -> Callable[[Trader], Tuple[int, int]]:
    """
    Volume policy based on the trader's inventory.
    """

    def func(trader: Trader) -> Tuple[int, int]:
        bid_volume = int((trader.max_inventory - trader.position) * fraction)
        ask_volume = int((trader.max_inventory + trader.position) * fraction)
        return bid_volume, -ask_volume

    return func


def volume_informed_constant(volume: int) -> Callable[[Trader], int]:
    """
    Constant volume policy for informed trader at user defined volume.
    """

    def func(trader: Trader) -> int:
        fairprice = trader.price_target
        if fairprice is None:
            return 0

        if trader.market.best_bid:
            if fairprice < trader.market.best_bid:
                return -volume
        if trader.market.best_ask:
            if fairprice > trader.market.best_ask:
                return volume
        return 0

    return func


def volume_informed_twap() -> Callable[[Trader], int]:
    """
    TWAP volume policy for informed trader.
    """

    def func(trader: Trader) -> int:
        fairprice = trader.price_target
        if fairprice is None:
            return 0

        if trader.market.best_bid:
            if fairprice < trader.market.best_bid:
                volume_left = -trader.max_inventory - trader.position
                time_left = trader.market.duration - trader.market.current_tick
                return int(volume_left / time_left)
        if trader.market.best_ask:
            if fairprice > trader.market.best_ask:
                volume_left = trader.max_inventory - trader.position
                time_left = trader.market.duration - trader.market.current_tick
                return int(volume_left / time_left)

        return 0

    return func


#### Spread Policies ####


def spread_mm_constant(halfspread: int) -> Callable[[Trader], Tuple[int, int]]:
    """
    Constant spread policy at user defined halfspread.
    """

    def func(trader: Trader) -> Tuple[int, int]:
        return (-halfspread, halfspread)

    return func


def spread_mm_orderflow_imbalance(
    window: int, agressiveness: int, min_halfspread: int, inventory_risk_factor: int = 5
) -> Callable[[Trader], Tuple[int, int]]:
    """
    Spread policy based on the order flow imbalance in the last window trades.
    """

    def func(trader: Trader) -> Tuple[int, int]:
        trades = trader.market.get_recent_trades(window)
        orderflow = sum([trade["volume"] * trade["agressor_side"] for trade in trades])

        total_volume = sum([trade["volume"] for trade in trades])
        indicator = orderflow / total_volume if total_volume != 0 else 0
        bid_offset = min(int(indicator * agressiveness), -min_halfspread)
        ask_offset = max(int(indicator * agressiveness), min_halfspread)

        inventory_risk = trader.position / trader.max_inventory
        bid_offset -= int(inventory_risk * inventory_risk_factor)
        ask_offset -= int(inventory_risk * inventory_risk_factor)

        return bid_offset, ask_offset

    return func
