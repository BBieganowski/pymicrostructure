# trader.py
import numpy as np
import random
from typing import Type
from microstructpy.markets.base import Market
from microstructpy.orders.market import MarketOrder
from microstructpy.orders.limit import LimitOrder
from microstructpy.traders.base import Trader


class NoiseTrader(Trader):
    def __init__(
        self, trader_id: int, market: Market, submission_rate=1.00, volume_size=1
    ) -> None:
        super().__init__(trader_id, market)
        self.submission_rate = submission_rate
        self.volume_size = volume_size

    def update(self) -> None:
        # Submit a predefined order, for example:
        if np.random.rand() < self.submission_rate:
            order = MarketOrder(
                trader_id=self.trader_id,
                quantity=self.volume_size * random.choice([-1, 1]),
            )
            self.market.submit_order(order)
