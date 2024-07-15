# trader.py
"""Base classes for noise traders."""
import numpy as np
import random
from typing import Type
from microstructpy.markets.base import Market
from microstructpy.orders.market import MarketOrder
from microstructpy.orders.limit import LimitOrder
from microstructpy.traders.base import Trader
from typing import Union, Type, Callable


class NoiseTrader(Trader):
    """
    Noise trader that submits random market orders at a fixed rate.

    Noise traders are traders that submit random orders to the market, providing liquidity and
    adding noise to the price process.

    Attributes:
    -----------
    market : Market
        The market instance in which the trader participates.
    submission_rate : float
        The rate at which the trader submits orders.
    volume_size : int or Callable[[], int]
        The size of the orders submitted by the trader.
    """

    def __init__(
        self,
        market: Market,
        submission_rate: float = 1.00,
        volume_size: Union[int, Callable[[], int]] = 1,
    ) -> None:
        """Initialize a new NoiseTrader."""
        super().__init__(market)
        self.submission_rate = submission_rate
        self.volume_size = volume_size

    def _get_volume(self) -> int:
        """Get the volume of the next order."""
        if callable(self.volume_size):
            return self.volume_size()
        else:
            return self.volume_size

    def update(self) -> None:
        """Update the trader's orders."""
        # Submit a predefined order, for example:
        volume = abs(int(self._get_volume()))

        if np.random.rand() < self.submission_rate and volume > 0:
            order = MarketOrder(
                trader_id=self.trader_id,
                volume=volume * random.choice([-1, 1]),
            )
            self.market.submit_order(order)


class TrendFollower(NoiseTrader):
    """
    Noise trader that submits market orders in the direction of the trend.

    A trend-follower is a noise trader that submits market orders in the direction of the trend.
    The trend is determined by the sign of last few trades.

    Attributes:
    -----------
    market : Market
        The market instance in which the trader participates.
    submission_rate : float
        The rate at which the trader submits orders.
    volume_size : int or Callable[[], int]
        The size of the orders submitted by the trader.
    """

    def __init__(
        self,
        market: Market,
        submission_rate: float = 1.00,
        volume_size: Union[int, Callable[[], int]] = 1,
        trend_window: int = 20,
    ) -> None:
        """Initialize a new TrendFollower."""
        super().__init__(market, submission_rate, volume_size)
        self.trend_window = trend_window

    def update(self) -> None:
        """Update the trader's orders."""
        # Submit a predefined order, for example:
        volume = abs(int(self._get_volume()))

        if np.random.rand() < self.submission_rate and volume > 0:
            recent_trades = self.market.trade_history[-self.trend_window :]
            trend_signal = np.sign(sum([x["agressor_side"] for x in recent_trades]))
            sign = (
                np.sign(trend_signal) if trend_signal != 0 else random.choice([-1, 1])
            )
            order = MarketOrder(
                trader_id=self.trader_id,
                volume=volume * sign,
            )
            self.market.submit_order(order)


class MeanReverter(NoiseTrader):
    """
    Noise trader that submits market orders against the trend.

    A mean-reverter is a noise trader that submits market orders against the trend.
    The trend is determined by the sign of last few trades.

    Attributes:
    -----------
    market : Market
        The market instance in which the trader participates.
    submission_rate : float
        The rate at which the trader submits orders.
    volume_size : int or Callable[[], int]
        The size of the orders submitted by the trader.
    """

    def __init__(
        self,
        market: Market,
        submission_rate: float = 1.00,
        volume_size: Union[int, Callable[[], int]] = 1,
        last_n_trades: int = 20,
    ) -> None:
        """Initialize a new MeanReverter."""
        super().__init__(market, submission_rate, volume_size)
        self.last_n_trades = last_n_trades

    def update(self) -> None:
        """Update the trader's orders."""
        # Submit a predefined order, for example:
        volume = abs(int(self._get_volume()))

        if np.random.rand() < self.submission_rate and volume > 0:
            recent_trades = self.market.trades[-self.last_n_trades :]
            sign = np.sign(sum([x["agressor_side"] for x in recent_trades]))
            order = MarketOrder(
                trader_id=self.trader_id,
                volume=volume * -sign,
            )
            self.market.submit_order(order)


class FatFinger(NoiseTrader):
    """
    Noise trader that submits market orders at extreme prices.

    A fat-finger trader is a noise trader submits large orders on rare interval.
    The price is determined by a random factor.

    Attributes:
    -----------
    market : Market
        The market instance in which the trader participates.
    submission_rate : float
        The rate at which the trader submits orders.
    volume_size : int or Callable[[], int]
        The size of the orders submitted by the trader.
    """

    def __init__(
        self,
        market: Market,
        submission_rate: float = 0.01,
        volume_size: Union[int, Callable[[], int]] = lambda: np.random.lognormal(2, 2),
    ) -> None:
        """Initialize a new FatFinger."""
        super().__init__(market, submission_rate, volume_size)

    def update(self) -> None:
        """Update the trader's orders."""
        # Submit a predefined order, for example:
        volume = abs(int(self._get_volume()))

        if np.random.rand() < self.submission_rate and volume > 0:
            order = MarketOrder(
                trader_id=self.trader_id, volume=volume * random.choice([-1, 1])
            )
            self.market.submit_order(order)
