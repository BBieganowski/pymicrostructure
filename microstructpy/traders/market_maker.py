from microstructpy.traders.base import Trader
from microstructpy.orders.limit import LimitOrder
from microstructpy.markets.base import Market
import numpy as np

class MarketMaker(Trader):
    """
    Dummy market maker that places a bid and ask at a fixed price and volume.
    """
    def __init__(
        self, trader_id: int, market: Market, price: int, spread: int, volume: int
    ) -> None:
        super().__init__(trader_id, market)
        self.price = price
        self.spread = spread
        self.volume = volume

    def update(self) -> None:
        active_orders = [
            order
            for order in self.orders
            if order.status == "active" or order.status == "partial"
        ]
        active_bids = [order for order in active_orders if order.quantity > 0]
        active_asks = [order for order in active_orders if order.quantity < 0]

        active_bid_volume = sum([order.quantity for order in active_bids])
        active_ask_volume = sum([order.quantity for order in active_asks])

        if active_bid_volume < self.volume:
            bid = LimitOrder(
                trader_id=self.trader_id,
                quantity=self.volume - active_bid_volume,
                price=self.price - self.spread // 2,
            )
            self.market.submit_order(bid)
        if active_ask_volume > -self.volume:
            ask = LimitOrder(
                trader_id=self.trader_id,
                quantity=-self.volume - active_ask_volume,
                price=self.price + self.spread // 2,
            )
            self.market.submit_order(ask)


class BayesianMarketMaker(Trader):
    """
    Market maker that uses a Bayesian model to set prices.
    """
    def __init__(self, trader_id: int, market: Market, name: str = None,
                 initial_fair_value:int=100, initial_uncertainty:float=1) -> None:
        super().__init__(trader_id, market, name)
        self.fair_value = initial_fair_value
        self.uncertainty = initial_uncertainty

    def update(self) -> None:
        if self.market.trade_history:
            participant_count = len(self.market.participants)
            last_trades = self.market.trade_history[-participant_count:]
            signs = [trade["agressor_side"] for trade in last_trades]
            mean_sign = np.median(signs)

            self.fair_value += mean_sign
        
        self.cancel_all_orders()

        bid = LimitOrder(
            trader_id=self.trader_id,
            quantity=100,
            price=int(self.fair_value - 5),
        )

        
        ask = LimitOrder(
            trader_id=self.trader_id,
            quantity=-100,
            price=int(self.fair_value + 5),
        )
        self.market.submit_order([bid, ask])
    


        
