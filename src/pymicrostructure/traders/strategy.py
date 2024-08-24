"""
Strategy module for market making algorithms.

This module provides abstract base classes and concrete implementations
for various strategies used in market making, including fair price calculation,
volume determination, and spread setting.
"""

from pymicrostructure.traders.base import Trader
from functools import partial
from typing import Tuple, Callable
import numpy as np
from abc import ABC, abstractmethod

##### Base Strategy Classes #####


class Strategy(ABC):
    """
    Abstract base class for all strategies.
    """

    @abstractmethod
    def __call__(self, trader):
        """
        Execute the strategy.

        Args:
            trader: The trader object implementing this strategy.

        Returns:
            Strategy-specific return value.
        """
        pass


class FairPriceStrategy(Strategy):
    """
    Abstract base class for fair price calculation strategies.
    """

    @abstractmethod
    def __call__(self, trader) -> int:
        """
        Calculate the fair price.

        Args:
            trader: The trader object implementing this strategy.

        Returns:
            int: The calculated fair price.
        """
        pass


class VolumeStrategy(Strategy):
    """
    Abstract base class for volume determination strategies.
    """

    @abstractmethod
    def __call__(self, trader) -> Tuple[int, int]:
        """
        Determine the bid and ask volumes.

        Args:
            trader: The trader object implementing this strategy.

        Returns:
            Tuple[int, int]: The bid and ask volumes.
        """
        pass


class SpreadStrategy(Strategy):
    """
    Abstract base class for spread setting strategies.
    """

    @abstractmethod
    def __call__(self, trader) -> Tuple[int, int]:
        """
        Determine the bid and ask spreads.

        Args:
            trader: The trader object implementing this strategy.

        Returns:
            Tuple[int, int]: The bid and ask spreads.
        """
        pass


##### Fair Price Strategies #####


class ConstantFairPrice(FairPriceStrategy):
    """
    A strategy that returns a constant fair price.
    """

    def __init__(self, fair_price: int):
        """
        Initialize the strategy with a constant fair price.

        Args:
            fair_price (int): The constant fair price to be used.
        """
        self.fair_price = fair_price

    def __call__(self, trader) -> int:
        """
        Return the constant fair price.

        Args:
            trader: The trader object (unused in this strategy).

        Returns:
            int: The constant fair price.
        """
        return self.fair_price


class OrderFlowSignFairPrice(FairPriceStrategy):
    """
    A strategy that adjusts the fair price based on the sign of recent order flow.
    """

    def __init__(self, window: int, aggressiveness: int):
        """
        Initialize the strategy.

        Args:
            window (int): The number of recent trades to consider.
            aggressiveness (int): The magnitude of price adjustment.
        """
        self.window = window
        self.aggressiveness = aggressiveness

    def __call__(self, trader) -> int:
        """
        Calculate the fair price based on recent order flow sign.

        Args:
            trader: The trader object implementing this strategy.

        Returns:
            int: The calculated fair price.
        """
        orderflow = trader.market.get_recent_trades(self.window)
        orderflow = sum(
            [trade["volume"] * trade["aggressor_side"] for trade in orderflow]
        )
        return trader.fair_price + self.aggressiveness * int(np.sign(orderflow))


class OrderFlowMagnitudeFairPrice(FairPriceStrategy):
    """
    A strategy that adjusts the fair price based on the magnitude of recent order flow.
    """

    def __init__(self, window: int, aggressiveness: int):
        """
        Initialize the strategy.

        Args:
            window (int): The number of recent trades to consider.
            aggressiveness (int): The magnitude of price adjustment.
        """
        self.window = window
        self.aggressiveness = aggressiveness

    def __call__(self, trader) -> int:
        """
        Calculate the fair price based on recent order flow magnitude.

        Args:
            trader: The trader object implementing this strategy.

        Returns:
            int: The calculated fair price.
        """
        trades = trader.market.get_recent_trades(self.window)
        orderflow = sum([trade["volume"] * trade["aggressor_side"] for trade in trades])
        total_volume = sum([trade["volume"] for trade in trades])
        indicator = orderflow / total_volume if total_volume != 0 else 0
        return trader.fair_price + int(indicator * self.aggressiveness * 3)


class NewsImpactFairPrice(FairPriceStrategy):
    """
    A strategy that adjusts the fair price based on the latest news impact.
    """

    def __init__(self, agressiveness: int):
        """
        Initialize the strategy.

        Args:
            agressiveness (int): The magnitude of price adjustment based on news.
        """
        self.agressiveness = agressiveness

    def __call__(self, trader) -> int:
        """
        Calculate the fair price based on the latest news impact.

        Args:
            trader: The trader object implementing this strategy.

        Returns:
            int: The calculated fair price.
        """
        news = trader.market.news_history[-1]
        if news == 0:
            return trader.fair_price
        return trader.fair_price + int(news * self.agressiveness)


class NewsImpactExponentialFairPrice(FairPriceStrategy):
    """
    A strategy that adjusts the fair price based on an exponential function of recent news.
    """

    def __init__(self, window: int, agressiveness: int):
        """
        Initialize the strategy.

        Args:
            window (int): The number of recent news items to consider.
            agressiveness (int): The magnitude of price adjustment based on news.
        """
        self.window = window
        self.agressiveness = agressiveness

    def __call__(self, trader) -> int:
        """
        Calculate the fair price based on an exponential function of recent news.

        Args:
            trader: The trader object implementing this strategy.

        Returns:
            int: The calculated fair price.
        """
        if trader.market.current_tick < self.window:
            return trader.fair_price
        news = sum(trader.market.news_history[-self.window :]) / self.window
        return trader.fair_price + int(np.exp(news * self.agressiveness))


##### Volume Strategies #####


class MaxAllowedVolume(VolumeStrategy):
    """
    A strategy that sets the maximum allowed volume based on inventory limits.
    """

    def __call__(self, trader) -> Tuple[int, int]:
        """
        Determine the maximum allowed bid and ask volumes.

        Args:
            trader: The trader object implementing this strategy.

        Returns:
            Tuple[int, int]: The bid and ask volumes.
        """
        bid_volume = trader.max_inventory - trader.position
        ask_volume = trader.max_inventory + trader.position
        return bid_volume, -ask_volume


class ConstantVolume(VolumeStrategy):
    """
    A strategy that sets a constant volume, limited by inventory constraints.
    """

    def __init__(self, volume: int):
        """
        Initialize the strategy with a constant volume.

        Args:
            volume (int): The constant volume to be used.
        """
        self.volume = volume

    def __call__(self, trader) -> Tuple[int, int]:
        """
        Determine the bid and ask volumes, limited by inventory constraints.

        Args:
            trader: The trader object implementing this strategy.

        Returns:
            Tuple[int, int]: The bid and ask volumes.
        """
        max_bid = trader.max_inventory - trader.position
        max_ask = trader.max_inventory + trader.position
        return min(self.volume, max_bid), -min(self.volume, max_ask)


class MaxFractionVolume(VolumeStrategy):
    """
    A strategy that sets the volume as a fraction of the maximum allowed volume.
    """

    def __init__(self, fraction: float):
        """
        Initialize the strategy with a fraction.

        Args:
            fraction (float): The fraction of maximum allowed volume to use.
        """
        self.fraction = fraction

    def __call__(self, trader) -> Tuple[int, int]:
        """
        Determine the bid and ask volumes as a fraction of maximum allowed volume.

        Args:
            trader: The trader object implementing this strategy.

        Returns:
            Tuple[int, int]: The bid and ask volumes.
        """
        bid_volume = int((trader.max_inventory - trader.position) * self.fraction)
        ask_volume = int((trader.max_inventory + trader.position) * self.fraction)
        return bid_volume, -ask_volume


class TimeWeightedVolume(VolumeStrategy):
    """
    A strategy that adjusts volume based on remaining time and current market conditions.
    """

    def __call__(self, trader) -> Tuple[int, int]:
        """
        Determine the bid and ask volumes based on time and market conditions.

        Args:
            trader: The trader object implementing this strategy.

        Returns:
            Tuple[int, int]: The bid and ask volumes.
        """
        self.duration = trader.market.duration
        fairprice = trader.fair_price
        if fairprice is None:
            return 0, 0

        if trader.market.best_bid:
            if fairprice < trader.market.best_bid:
                volume_left = -trader.max_inventory - trader.position
                time_left = self.duration - trader.market.current_tick
                return 0, int(volume_left / time_left)
        if trader.market.best_ask:
            if fairprice > trader.market.best_ask:
                volume_left = trader.max_inventory - trader.position
                time_left = self.duration - trader.market.current_tick
                return int(volume_left / time_left), 0
        return 0, 0


##### Spread Strategies #####


class ConstantSpread(SpreadStrategy):
    """
    A strategy that sets a constant spread around the fair price.
    """

    def __init__(self, halfspread: int):
        """
        Initialize the strategy with a constant halfspread.

        Args:
            halfspread (int): The constant halfspread to be used.
        """
        self.halfspread = halfspread

    def __call__(self, trader) -> Tuple[int, int]:
        """
        Determine the bid and ask spreads.

        Args:
            trader: The trader object implementing this strategy.

        Returns:
            Tuple[int, int]: The bid and ask spreads.
        """
        return -self.halfspread, self.halfspread


class OrderFlowImbalanceSpread(SpreadStrategy):
    """
    A strategy that adjusts the spread based on order flow imbalance.
    """

    def __init__(self, window: int, aggressiveness: int, min_halfspread: int):
        """
        Initialize the strategy.

        Args:
            window (int): The number of recent trades to consider.
            aggressiveness (int): The magnitude of spread adjustment.
            min_halfspread (int): The minimum halfspread to maintain.
        """
        self.window = window
        self.aggressiveness = aggressiveness
        self.min_halfspread = min_halfspread

    def __call__(self, trader) -> Tuple[int, int]:
        """
        Determine the bid and ask spreads based on order flow imbalance.

        Args:
            trader: The trader object implementing this strategy.

        Returns:
            Tuple[int, int]: The bid and ask spreads.
        """
        trades = trader.market.get_recent_trades(self.window)
        orderflow = sum([trade["volume"] * trade["aggressor_side"] for trade in trades])

        total_volume = sum([trade["volume"] for trade in trades])
        indicator = orderflow / total_volume if total_volume != 0 else 0
        bid_offset = min(int(indicator * self.aggressiveness), -self.min_halfspread)
        ask_offset = max(int(indicator * self.aggressiveness), self.min_halfspread)

        return bid_offset, ask_offset
