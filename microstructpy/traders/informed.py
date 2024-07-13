from microstructpy.traders.base import Trader
from microstructpy.orders.market import MarketOrder
from microstructpy.orders.limit import LimitOrder
from microstructpy.markets.base import Market

import numpy as np


class InformedTrader(Trader):
    """
    Dummy informed trader that immediately submits a limit order to reach a target position.
    """

    def __init__(
        self, trader_id: int, market: Market, position_target: int, target_price: int
    ) -> None:
        super().__init__(trader_id, market)
        self.position_target = position_target
        self.target_price = target_price

    def update(self) -> None:
        # Submit a predefined order, for example:
        if self.position < abs(self.position_target):
            order = LimitOrder(
                trader_id=self.trader_id,
                quantity=self.position_target - self.position,
                price=self.target_price,
            )
            self.market.submit_order(order)


class TWAPTrader(InformedTrader):
    """
    Informed trader that submits a TWAP order to reach a target position.
    """

    def __init__(
        self, trader_id: int, market: Market, position_target: int, target_price: int
    ) -> None:
        super().__init__(trader_id, market, position_target, target_price)

    def update(self) -> None:
        ticks_remaining = self.market.duration - self.market.current_tick
        volume_remaining = self.position_target - self.position
        volume_per_tick = volume_remaining / ticks_remaining

        if abs(volume_per_tick) < 1:
            if np.random.rand() < abs(volume_per_tick):
                order = LimitOrder(
                    trader_id=self.trader_id,
                    quantity=np.sign(volume_per_tick),
                    price=self.target_price,
                )
                self.market.submit_order(order)
        else:
            volume_per_tick = int(volume_per_tick)
            order = LimitOrder(
                trader_id=self.trader_id,
                quantity=volume_per_tick,
                price=self.target_price,
            )
            self.market.submit_order(order)
