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
        max_inventory: int,
        prevent_market_orders: bool = False,
        name: str = None,
    ):
        super().__init__(market, name)
        self.fair_price_strategy = fair_price_strategy
        self.spread_strategy = spread_strategy
        self.volume_strategy = volume_strategy
        self.max_inventory = max_inventory
        self.prevent_market_orders = prevent_market_orders

    def update(self) -> None:
        self.fair_price = self.fair_price_strategy(self)
        bid_offset, ask_offset = self.spread_strategy(self)
        bid_volume, ask_volume = self.volume_strategy(self)
        self.cancel_all_orders()

        bid_price = self.fair_price + bid_offset
        ask_price = self.fair_price + ask_offset

        # Ensure it's not filled immediately
        if self.prevent_market_orders:
            if self.market.best_ask:
                bid_price = min(bid_price, self.market.best_ask-0.01)
            if self.market.best_bid:
                ask_price = max(ask_price, self.market.best_bid+0.01)

        orders = []
        if bid_volume > 0:
            bid = LimitOrder(
                trader_id=self.trader_id,
                volume=bid_volume,
                price=bid_price
            )
            orders.append(bid)

        if ask_volume < 0:
            ask = LimitOrder(
                trader_id=self.trader_id,
                volume=ask_volume,
                price=ask_price
            )
            orders.append(ask)

        self.market.submit_order(orders)
    
