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
        self.market = market
        self.orders = []
        self.filled_trades = []
        self.position = 0
        self.market.participants.append(self)

    def cancel_orders(self, side) -> None:
        for order in self.orders:
            if (
                order.status == "active"
                or order.status == "partial"
                and np.sign(order.quantity) == side
            ):
                order.status = "canceled"
                self.market.cancellations.append(order)
        self.market.drop_cancelled_orders()

    def cancel_all_orders(self) -> None:
        for order in self.orders:
            if order.status == "active" or order.status == "partial":
                order.status = "canceled"
                self.market.cancellations.append(order)
        self.market.drop_cancelled_orders()

    def submit_order(self) -> None:
        raise NotImplementedError("This method should be overridden by subclasses")
