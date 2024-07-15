"""Informed traders that know the future price of a security."""

from microstructpy.traders.base import Trader
from microstructpy.orders.market import MarketOrder
from microstructpy.orders.limit import LimitOrder
from microstructpy.markets.base import Market

import numpy as np


class InformedTrader(Trader):
    """
    Dummy informed trader that immediately submits a limit order to reach a target position.

    Informed traders are traders that have some information about the future price of a security.

    Attributes:
    -----------
    market : Market
        The market instance in which the trader participates.
    position_target : int
        The target position of the trader.
    target_price : int
        The price at which to submit the order.

    Methods:
    --------
    update()
        Submit a predefined order to reach the target position.
    """

    def __init__(self, market: Market, position_target: int, target_price: int) -> None:
        """Initialize a new InformedTrader."""
        super().__init__(market)
        self.position_target = position_target
        self.target_price = target_price

    def update(self) -> None:
        """Submit a predefined order to reach the target position."""
        # Submit a predefined order, for example:
        if self.position < abs(self.position_target):
            order = LimitOrder(
                trader_id=self.trader_id,
                volume=self.position_target - self.position,
                price=self.target_price,
            )
            self.market.submit_order(order)


class TWAPTrader(InformedTrader):
    """Informed trader that submits a TWAP order to reach a target position."""

    def __init__(self, market: Market, position_target: int, target_price: int) -> None:
        """Initialize a new TWAPTrader."""
        super().__init__(market, position_target, target_price)

    def update(self) -> None:
        """Submit a TWAP order to reach the target position."""
        ticks_remaining = self.market.duration - self.market.current_tick
        volume_remaining = self.position_target - self.position
        volume_per_tick = volume_remaining / ticks_remaining

        if abs(volume_per_tick) < 1:
            if np.random.rand() < abs(volume_per_tick):
                order = LimitOrder(
                    trader_id=self.trader_id,
                    volume=np.sign(volume_per_tick),
                    price=self.target_price,
                )
                self.market.submit_order(order)
        else:
            volume_per_tick = int(volume_per_tick)
            order = LimitOrder(
                trader_id=self.trader_id,
                volume=volume_per_tick,
                price=self.target_price,
            )
            self.market.submit_order(order)
