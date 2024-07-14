# trader.py
import numpy as np
import random
from typing import Type
from microstructpy.markets.base import Market
from microstructpy.orders.market import MarketOrder
from microstructpy.orders.limit import LimitOrder
from microstructpy.traders.base import Trader
from typing import Union, Type, Callable


class NoiseTrader(Trader):
    def __init__(
        self, trader_id: int, market: Market, submission_rate: float = 1.00, 
        volume_size: Union[int, Callable[[], int]] = 1) -> None:
        super().__init__(trader_id, market)
        self.submission_rate = submission_rate
        self.volume_size = volume_size

    def _get_volume(self) -> int:
        if callable(self.volume_size):
            return self.volume_size()
        else:
            return self.volume_size

    def update(self) -> None:
        # Submit a predefined order, for example:
        volume = abs(int(self._get_volume()))
    
        if np.random.rand() < self.submission_rate and volume > 0:
            order = MarketOrder(
                trader_id=self.trader_id,
                quantity=volume * random.choice([-1, 1]),
            )
            self.market.submit_order(order)
