"""Informed traders that have an opinion on the future price of a security."""

from pymicrostructure.traders.base import Trader
from pymicrostructure.orders.market import MarketOrder
from pymicrostructure.orders.limit import LimitOrder
from pymicrostructure.markets.continuous import ContinuousDoubleAuction
from typing import Tuple, Callable
from pymicrostructure.traders.strategy import *

import numpy as np


class BaseInformedTrader(Trader):
    """
    A base class for informed traders who have an opinion on the future price of a security.

    This trader uses strategies to determine fair price and trading volume, and
    places market orders based on these strategies and current market conditions.

    Attributes:
        fair_price_strategy (Callable): A strategy to determine the fair price.
        volume_strategy (Callable): A strategy to determine the trading volume.
        max_inventory (int): The maximum inventory the trader can hold.
        fair_price (float): The current fair price as determined by the strategy.
    """

    def __init__(
        self,
        market: ContinuousDoubleAuction,
        fair_price_strategy: Callable,
        volume_strategy: Callable,
        max_inventory: int = 1000,
        name: str = None,
        include_in_results: bool = True,
    ) -> None:
        """
        Initialize the BaseInformedTrader.

        Args:
            market (ContinuousDoubleAuction): The market in which the trader operates.
            fair_price_strategy (Callable): A strategy to determine the fair price.
            volume_strategy (Callable): A strategy to determine the trading volume.
            max_inventory (int, optional): The maximum inventory the trader can hold. Defaults to 1000.
            name (str, optional): The name of the trader. Defaults to None.
            include_in_results (bool, optional): Whether to include this trader in results. Defaults to True.
        """
        super().__init__(market, name, include_in_results)
        self.fair_price_strategy = fair_price_strategy
        self.volume_strategy = volume_strategy
        self.max_inventory = max_inventory

    def update(self) -> None:
        """
        Update the trader's state and potentially place orders.

        This method updates the fair price, calculates the trading volume,
        and places market orders if the current market price is favorable
        compared to the fair price.
        """
        self.fair_price = self.fair_price_strategy(self)
        volume = self.volume_strategy(self)

        if self.market.best_bid:
            if self.market.best_bid > self.fair_price and volume[1] != 0:
                self.cancel_all_orders()
                order = MarketOrder(trader_id=self.trader_id, volume=volume[1])
                self.market.submit_order(order)

        if self.market.best_ask:
            if self.market.best_ask < self.fair_price and volume[0] != 0:
                self.cancel_all_orders()
                order = MarketOrder(trader_id=self.trader_id, volume=volume[0])
                self.market.submit_order(order)


# Predefined templates


class DummyInformedTrader(BaseInformedTrader):
    """
    A dummy informed trader with constant fair price and maximum allowed volume.

    This trader uses a constant fair price of 1050 and always trades the maximum allowed volume.
    """

    def __init__(self, market: ContinuousDoubleAuction):
        """Initialize the DummyInformedTrader with predefined strategies."""
        super().__init__(
            market=market,
            name="Dummy Informed Trader",
            fair_price_strategy=ConstantFairPrice(1050),
            volume_strategy=MaxAllowedVolume(),
            max_inventory=1000,
        )


class TWAPInformedTrader(BaseInformedTrader):
    """
    A Time-Weighted Average Price (TWAP) informed trader.

    This trader uses a constant fair price of 1050 and a time-weighted volume strategy.
    """

    def __init__(self, market: ContinuousDoubleAuction):
        """Initialize the TWAPInformedTrader with predefined strategies."""
        super().__init__(
            market=market,
            name="TWAP Informed Trader",
            fair_price_strategy=ConstantFairPrice(1050),
            volume_strategy=TimeWeightedVolume(),
            max_inventory=1000,
        )


class NewsInformedTrader(BaseInformedTrader):
    """
    A news-informed trader that reacts to market news.

    This trader uses a news impact exponential fair price strategy and a time-weighted volume strategy.
    """

    def __init__(self, market: ContinuousDoubleAuction):
        """Initialize the NewsInformedTrader with predefined strategies."""
        super().__init__(
            market=market,
            name="News Informed Trader",
            fair_price_strategy=NewsImpactExponentialFairPrice(10, 5),
            volume_strategy=TimeWeightedVolume(),
            max_inventory=1000,
        )
