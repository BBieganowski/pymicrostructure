"""Module for market maker traders."""

from microstructpy.traders.base import Trader
from microstructpy.orders.limit import LimitOrder
from microstructpy.markets.base import Market
from typing import Tuple, Callable
from functools import partial
import numpy as np
from microstructpy.traders.strategy import *


class BaseMarketMaker(Trader):
    def __init__(
        self,
        market: Market,
        fair_price_strategy: Callable,
        volume_strategy: Callable,
        spread_strategy: Callable,
        max_inventory: int,
        name: str = None,
        include_in_results: bool = True,
    ):
        super().__init__(market, name, include_in_results)
        self.fair_price_strategy = fair_price_strategy
        self.spread_strategy = spread_strategy
        self.volume_strategy = volume_strategy
        self.max_inventory = max_inventory

    def update(self) -> None:
        self.fair_price = self.fair_price_strategy(self)
        bid_offset, ask_offset = self.spread_strategy(self)
        bid_volume, ask_volume = self.volume_strategy(self)
        self.cancel_all_orders()
        bid_price = self.fair_price + bid_offset
        ask_price = self.fair_price + ask_offset

        orders = []
        if bid_volume > 0:
            bid = LimitOrder(
                trader_id=self.trader_id, volume=bid_volume, price=bid_price
            )
            orders.append(bid)

        if ask_volume < 0:
            ask = LimitOrder(
                trader_id=self.trader_id, volume=ask_volume, price=ask_price
            )
            orders.append(ask)

        self.market.submit_order(orders)



class DummyMarketMaker(BaseMarketMaker):
    def __init__(self, market: Market, name: str = None, include_in_results=True):
        super().__init__(
            market=market,
            fair_price_strategy=ConstantFairPrice(1000),
            volume_strategy=ConstantVolume(100),
            spread_strategy=ConstantSpread(5),
            max_inventory=1000,
            name=name,
            include_in_results=include_in_results
        )
    
class KyleMarketMaker(BaseMarketMaker):
    def __init__(self, market: Market, name: str = None, include_in_results=True):
        super().__init__(
            market=market,
            fair_price_strategy=OrderFlowSignFairPrice(window=10, aggressiveness=2),
            volume_strategy=ConstantVolume(100),
            spread_strategy=ConstantSpread(5),
            max_inventory=1000,
            name=name,
            include_in_results=include_in_results
        )

class AdaptiveMarketMaker(BaseMarketMaker):
    def __init__(self, market: Market, name: str = None, include_in_results=True):
        super().__init__(
            market=market,
            fair_price_strategy=OrderFlowMagnitudeFairPrice(window=10, aggressiveness=1),
            volume_strategy=MaxFractionVolume(0.1),
            spread_strategy=OrderFlowImbalanceSpread(window=10, aggressiveness=5, min_halfspread=5),
            max_inventory=1000,
            name=name,
            include_in_results=include_in_results
        )