"""
Module for market maker traders.

This module provides implementations of various market maker strategies
for trading in financial markets. It includes a base class for market makers
and several specific implementations with different pricing and volume strategies.
"""

from pymicrostructure.traders.base import Trader
from pymicrostructure.orders.limit import LimitOrder
from pymicrostructure.markets.base import Market
from typing import Callable
from pymicrostructure.traders.strategy import *


class BaseMarketMaker(Trader):
    """
    Base class for market maker traders.

    This class provides a foundation for implementing market maker strategies.
    It manages the core logic for updating orders based on fair price, spread, and volume strategies.

    Attributes:
        market (Market): The market in which the trader operates.
        fair_price_strategy (Callable): Strategy for determining the fair price.
        spread_strategy (Callable): Strategy for determining the bid-ask spread.
        volume_strategy (Callable): Strategy for determining the trading volume.
        max_inventory (int): Maximum inventory the market maker can hold.
        name (str): Name of the trader.
        include_in_results (bool): Whether to include this trader in results.

    """

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
        """
        Update the market maker's orders based on current market conditions.

        This method calculates the fair price, spread, and volumes, cancels existing orders,
        and submits new orders to the market.
        """
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
    """
    A simple market maker with constant fair price, volume, and spread.

    This market maker uses fixed values for its pricing and volume strategies,
    making it useful for testing and basic market simulations.

    Attributes:
        market (Market): The market in which the trader operates.
        name (str): Name of the trader.
        include_in_results (bool): Whether to include this trader in results.
    """

    def __init__(self, market: Market, name: str = None, include_in_results=True):
        super().__init__(
            market=market,
            fair_price_strategy=ConstantFairPrice(1000),
            volume_strategy=ConstantVolume(100),
            spread_strategy=ConstantSpread(5),
            max_inventory=1000,
            name=name,
            include_in_results=include_in_results,
        )


class KyleMarketMaker(BaseMarketMaker):
    """
    A market maker strategy based on Kyle's model.

    This market maker adjusts its fair price based on recent order flow,
    while maintaining constant volume and spread.

    Attributes:
        market (Market): The market in which the trader operates.
        name (str): Name of the trader.
        include_in_results (bool): Whether to include this trader in results.
    """

    def __init__(self, market: Market, name: str = None, include_in_results=True):
        super().__init__(
            market=market,
            fair_price_strategy=OrderFlowSignFairPrice(window=5, aggressiveness=2),
            volume_strategy=ConstantVolume(100),
            spread_strategy=ConstantSpread(5),
            max_inventory=1000,
            name=name,
            include_in_results=include_in_results,
        )


class AdaptiveMarketMaker(BaseMarketMaker):
    """
    An adaptive market maker that adjusts its strategy based on market conditions.

    This market maker uses order flow to adjust its fair price and spread,
    and sets its volume as a fraction of the market volume.

    Attributes:
        market (Market): The market in which the trader operates.
        name (str): Name of the trader.
        include_in_results (bool): Whether to include this trader in results.
    """

    def __init__(self, market: Market, name: str = None, include_in_results=True):
        super().__init__(
            market=market,
            fair_price_strategy=OrderFlowMagnitudeFairPrice(
                window=10, aggressiveness=1
            ),
            volume_strategy=MaxFractionVolume(0.1),
            spread_strategy=OrderFlowImbalanceSpread(
                window=10, aggressiveness=5, min_halfspread=5
            ),
            max_inventory=1000,
            name=name,
            include_in_results=include_in_results,
        )
