from microstructpy.traders.base import Trader
from microstructpy.orders.market import MarketOrder
from microstructpy.orders.limit import LimitOrder
from microstructpy.markets.base import Market


class InformedTrader(Trader):
    def __init__(self, trader_id: int, market: Market, position_limit: int, target_price: int) -> None: 
        super().__init__(trader_id, market)
        self.position_limit = position_limit
        self.target_price   = target_price

    def update(self) -> None:
        # Submit a predefined order, for example:
        if self.position < abs(self.position_limit):
            order = LimitOrder(trader_id=self.trader_id, quantity=min(self.position_limit - self.position, 10), price=self.target_price)
            self.market.submit_order(order)