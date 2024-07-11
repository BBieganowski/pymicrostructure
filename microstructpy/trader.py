# trader.py
import numpy as np
from typing import Type
from microstructpy.market import Market
from microstructpy.order import MarketOrder, LimitOrder

class Trader:
    def __init__(self, trader_id: int, market: Market) -> None:
        self.trader_id = trader_id
        self.market    = market
        self.orders    = []
        self.market.participants.append(self)

    def submit_order(self) -> None:
        raise NotImplementedError("This method should be overridden by subclasses")

class LiquidityTrader(Trader):
    def __init__(self, trader_id: int, market: Market, submission_rate = 1.00, volume_size = 1) -> None:
        super().__init__(trader_id, market)
        self.submission_rate = submission_rate
        self.volume_size     = volume_size

    def update(self) -> None:
        # Submit a predefined order, for example:
        if np.random.rand() < self.submission_rate:
            order = MarketOrder(trader_id=self.trader_id, quantity=self.volume_size*np.random.choice([-1, 1]))
            self.market.submit_order(order)

class ConstantPriceDealer(Trader):
    def __init__(self, trader_id: int, market: Market, price: int, spread: int, volume:int) -> None:
        super().__init__(trader_id, market)
        self.price  = price
        self.spread = spread
        self.volume = volume

    def update(self) -> None:
        active_orders = [order for order in self.orders if order.status == "active" or order.status == "partial"]
        active_bids = [order for order in active_orders if order.quantity > 0]
        active_asks = [order for order in active_orders if order.quantity < 0]

        active_bid_volume = sum([order.quantity for order in active_bids])
        active_ask_volume = sum([order.quantity for order in active_asks])

        if active_bid_volume < self.volume:
            bid = LimitOrder(trader_id=self.trader_id, quantity=self.volume - active_bid_volume, price=self.price-self.spread//2)
            self.market.submit_order(bid)
        if active_ask_volume > -self.volume:
            ask = LimitOrder(trader_id=self.trader_id, quantity=-self.volume - active_ask_volume, price=self.price+self.spread//2)
            self.market.submit_order(ask)