"""Module for market maker traders."""

from microstructpy.traders.base import Trader
from microstructpy.orders.limit import LimitOrder
from microstructpy.markets.base import Market
import numpy as np


class MarketMaker(Trader):
    """
    Dummy market maker that places a bid and ask at a fixed price and volume.

    Market makers are traders that provide liquidity to a market by placing orders on both sides of the order book.

    Attributes:
    -----------
    trader_id : int
        The ID of the trader.
    market : Market
        The market in which the trader participates.
    price : int
        The fair price around which to place the orders.
    spread : int
        The spread between the bid and ask prices.
    volume : int
        The volume of the orders.

    Methods:
    --------
    update()
        Update the trader's orders.
    """

    def __init__(
        self, trader_id: int, market: Market, price: int, spread: int, volume: int
    ) -> None:
        """Initialize a new MarketMaker."""
        super().__init__(trader_id, market)
        self.price = price
        self.spread = spread
        self.volume = volume

    def update(self) -> None:
        """Update the trader's orders."""
        active_orders = [
            order
            for order in self.orders
            if order.status == "active" or order.status == "partial"
        ]
        active_bids = [order for order in active_orders if order.volume > 0]
        active_asks = [order for order in active_orders if order.volume < 0]

        active_bid_volume = sum([order.volume for order in active_bids])
        active_ask_volume = sum([order.volume for order in active_asks])

        if active_bid_volume < self.volume:
            bid = LimitOrder(
                trader_id=self.trader_id,
                volume=self.volume - active_bid_volume,
                price=self.price - self.spread // 2,
            )
            self.market.submit_order(bid)
        if active_ask_volume > -self.volume:
            ask = LimitOrder(
                trader_id=self.trader_id,
                volume=-self.volume - active_ask_volume,
                price=self.price + self.spread // 2,
            )
            self.market.submit_order(ask)


class BayesianMarketMaker(Trader):
    """Market maker that uses a Bayesian model to set prices."""

    def __init__(
        self,
        market: Market,
        name: str = None,
        spread: int = 3,
        initial_fair_value: int = 100,
        initial_uncertainty: float = 1,
        max_inventory: int = 1000,
    ) -> None:
        """Initialize a new BayesianMarketMaker."""
        super().__init__(market, name)
        self.fair_value = initial_fair_value
        self.uncertainty = initial_uncertainty
        self.spread = spread
        self.max_inventory = max_inventory

    def update(self) -> None:
        """Update the trader's orders."""
        if self.market.trade_history:
            participant_count = len(self.market.participants)
            last_trades = self.market.trade_history[-10:]
            signs = [trade["agressor_side"] for trade in last_trades]
            mean_sign = np.median(signs)

            self.fair_value += mean_sign

        self.cancel_all_orders()

        orders = []
        bid_size = self.max_inventory - self.position
        if bid_size != 0:
            bid = LimitOrder(
                trader_id=self.trader_id,
                volume=min(self.max_inventory - self.position, 100),
                price=int(self.fair_value - self.spread // 2),
            )
            orders.append(bid)

        ask_size = -self.max_inventory - self.position
        if ask_size != 0:
            ask = LimitOrder(
                trader_id=self.trader_id,
                volume=max(-self.max_inventory - self.position, -100),
                price=int(self.fair_value + self.spread // 2),
            )
            orders.append(ask)
        self.market.submit_order(orders)
