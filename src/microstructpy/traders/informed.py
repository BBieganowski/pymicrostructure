"""Informed traders that know the future price of a security."""

from microstructpy.traders.base import Trader
from microstructpy.orders.market import MarketOrder
from microstructpy.orders.limit import LimitOrder
from microstructpy.markets.continous import ContinousDoubleAuction
from typing import Tuple, Callable

import numpy as np


class BaseInformedTrader(Trader):
    def __init__(
        self,
        market: ContinousDoubleAuction,
        price_strategy: Callable,
        volume_strategy: Callable,
        include_in_results=True,
        name: str = None,
        max_inventory: int = 1000
    ) -> None:
        super().__init__(market, name, include_in_results)
        self.max_inventory = max_inventory
        self.price_strategy  = price_strategy
        self.price_target = None
        self.volume_strategy = volume_strategy
    
    def update(self) -> None:
        self.price_target = self.price_strategy(self)
        volume = self.volume_strategy(self)
        self.cancel_all_orders()
        if volume != 0:
            order = LimitOrder(
                trader_id=self.trader_id,
                volume=volume,
                price=self.price_target
            )
            self.market.submit_order(order)