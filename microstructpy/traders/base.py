# trader.py
import numpy as np
import random
from typing import Type
from microstructpy.markets.base import Market
from microstructpy.orders.market import MarketOrder
from microstructpy.orders.limit import LimitOrder

class Trader:
    def __init__(self, trader_id: int, market: Market, name: str = None) -> None:
        self.trader_id = trader_id
        self.market    = market
        self.orders    = []
        self.filled_trades = []
        self.position  = 0
        self.market.participants.append(self)

    def submit_order(self) -> None:
        raise NotImplementedError("This method should be overridden by subclasses")