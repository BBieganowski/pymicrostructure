# trader.py
"""Base classes for noise traders."""
import numpy as np
import random
from typing import Type
from pymicrostructure.markets.base import Market
from pymicrostructure.orders.market import MarketOrder
from pymicrostructure.orders.limit import LimitOrder
from pymicrostructure.traders.base import Trader
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
