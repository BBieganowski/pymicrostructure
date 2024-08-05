"""Informed traders that have an opinion on the future price of a security."""

from microstructpy.traders.base import Trader
from microstructpy.orders.market import MarketOrder
from microstructpy.orders.limit import LimitOrder
from microstructpy.markets.continuous import ContinuousDoubleAuction
from typing import Tuple, Callable
from microstructpy.traders.strategy import *

import numpy as np


class BaseInformedTrader(Trader):
    def __init__(
        self,
        market: ContinuousDoubleAuction,
        fair_price_strategy: Callable,
        volume_strategy: Callable,
        max_inventory: int = 1000,
        name: str = None,
        include_in_results: bool = True,
    ) -> None:
        super().__init__(market, name, include_in_results)
        self.fair_price_strategy = fair_price_strategy
        self.volume_strategy = volume_strategy
        self.max_inventory = max_inventory

    def update(self) -> None:
        self.fair_price = self.fair_price_strategy(self)
        volume = self.volume_strategy(self)

        if self.market.best_bid:
            if self.market.best_bid > self.fair_price:
                self.cancel_all_orders()
                order = MarketOrder(
                    trader_id=self.trader_id, volume=volume[1]
                )
                self.market.submit_order(order)

        if self.market.best_ask:
            if self.market.best_ask < self.fair_price:
                self.cancel_all_orders()
                order = MarketOrder(
                    trader_id=self.trader_id, volume=volume[0]
                )
                self.market.submit_order(order)


class InformedTraderTemplate:
    def __init__(
        self,
        name: str,
        price_strategy: Callable,
        volume_strategy: Callable,
        max_inventory: int,
    ):
        self.name = name
        self.price_strategy = price_strategy
        self.volume_strategy = volume_strategy
        self.max_inventory = max_inventory
    
    def create(self, market: ContinuousDoubleAuction):
        return BaseInformedTrader(
            market=market,
            fair_price_strategy=self.price_strategy,
            volume_strategy=self.volume_strategy,
            max_inventory=self.max_inventory,
            name=self.name
        )
    
# Predefined templates

class DummyInformedTrader(InformedTraderTemplate):
    def __init__(self):
        super().__init__(
            name="Dummy Informed Trader",
            price_strategy=ConstantFairPrice(1050),
            volume_strategy=MaxAllowedVolume(),
            max_inventory=1000
        )
    
class TWAPInformedTrader(InformedTraderTemplate):
    def __init__(self):
        super().__init__(
            name="TWAP Informed Trader",
            price_strategy=ConstantFairPrice(1050),
            volume_strategy=TimeWeightedVolume(),
            max_inventory=1000
        )

class NewsInformedTrader(InformedTraderTemplate):
    def __init__(self):
        super().__init__(
            name="News Informed Trader",
            price_strategy=NewsImpactExponentialFairPrice(10, 5),
            volume_strategy=TimeWeightedVolume(),
            max_inventory=1000
        )
