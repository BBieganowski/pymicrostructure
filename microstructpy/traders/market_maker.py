from microstructpy.traders.base import Trader
from microstructpy.orders.limit import LimitOrder
from microstructpy.markets.base import Market


class MarketMaker(Trader):
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