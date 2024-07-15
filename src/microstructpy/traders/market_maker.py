"""Module for market maker traders."""

from microstructpy.traders.base import Trader
from microstructpy.orders.limit import LimitOrder
from microstructpy.markets.base import Market
from typing import Tuple, Callable
from functools import partial
import numpy as np


class BaseMarketMaker(Trader):
    def __init__(
        self,
        market: Market,
        fair_price_strategy: Callable,
        spread_strategy: Callable,
        volume_strategy: Callable,
        initial_fair_price: int,
        max_inventory: int,
        name: str = None,
    ):
        super().__init__(market, name)
        self.fair_price_strategy = fair_price_strategy
        self.spread_strategy = spread_strategy
        self.volume_strategy = volume_strategy
        self.fair_price = initial_fair_price
        self.max_inventory = max_inventory

    def update(self) -> None:
        self.fair_price        = self.fair_price_strategy(self)
        bid_offset, ask_offset = self.spread_strategy(self)
        bid_volume, ask_volume = self.volume_strategy(self)

        self.cancel_all_orders()

        orders = []
        if bid_volume > 0:
            bid = LimitOrder(
                trader_id=self.trader_id,
                volume=bid_volume,
                price=self.fair_price + bid_offset,
            )
            orders.append(bid)

        if ask_volume < 0:
            ask = LimitOrder(
                trader_id=self.trader_id,
                volume=ask_volume,
                price=self.fair_price + ask_offset,
            )
            orders.append(ask)

        self.market.submit_order(orders)


class ConstantMarketMaker(BaseMarketMaker):
    def __init__(
        self,
        market: Market,
        price: int,
        max_inventory: int,
        spread: int,
        name: str = None,
    ):
        super().__init__(
            market,
            partial(fairprice_constant, price=price),
            partial(spread_fixed, halfspread=spread),
            partial(volume_max_fraction, max_frac=1),
            price,
            max_inventory,
            name,
        )


def fairprice_constant(trader: BaseMarketMaker, price: int = 100) -> int:
    return price


def fairprice_of_sign(trader: BaseMarketMaker, window_size: int = 5) -> int:
    trades = trader.market.get_recent_trades(window_size)
    of = (
        1
        if sum([trade["volume"] * trade["agressor_side"] for trade in trades]) > 0
        else -1
    )
    return trader.fair_price + of


def volume_max_fraction(trader: BaseMarketMaker, max_frac: float = 0.5) -> Tuple[int, int]:
    max_bid = trader.max_inventory - trader.position
    max_ask = -trader.max_inventory - trader.position
    max_size = int(trader.max_inventory * max_frac)
    bid_volume = min(max_bid, max_size)
    ask_volume = max(max_ask, -max_size)
    return bid_volume, ask_volume


def spread_fixed(trader: BaseMarketMaker, halfspread: int = 2) -> int:
    return (-halfspread, halfspread)


def spread_position_linear(
    trader: BaseMarketMaker, neutral_halfspread: int
) -> Tuple[int, int]:
    normalized_position = trader.position / trader.max_inventory
    bid_offset = int(-neutral_halfspread - neutral_halfspread * normalized_position)
    ask_offset = int(neutral_halfspread - neutral_halfspread * normalized_position)
    return (bid_offset, ask_offset)
