"""Market order class."""

import numpy as np
from pymicrostructure.orders.base import Order


class MarketOrder(Order):
    """
    Represents a market order.

    A market order is an order to buy or sell a security at the best available price.

    Attributes:
    -----------
    trader_id : int
        The ID of the trader submitting the order.
    volume : int
        The volume of the order.
    price : float
        The price at which the order is submitted - infinity for buy orders and negative infinity for sell orders.

    Methods:
    --------
    __repr__()
        Return a string representation of the order.
    """

    def __init__(self, trader_id: int, volume) -> None:
        """Initialize a new MarketOrder."""
        super().__init__(trader_id, volume)
        self.price = np.inf if volume > 0 else -np.inf

    def __repr__(self) -> str:
        """Return a string representation of the order."""
        return f"MKT V: {self.volume:+} FROM: {self.trader_id}"
