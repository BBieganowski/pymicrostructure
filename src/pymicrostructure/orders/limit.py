"""Limit order class."""

from pymicrostructure.orders.base import Order


class LimitOrder(Order):
    """
    Represents a limit order.

    A limit order is an order to buy or sell a security at a specific price or better.

    Attributes:
    -----------
    trader_id : int
        The ID of the trader submitting the order.
    volume : int
        The volume of the order.
    price : int
        The price at which the order is submitted.
    """

    def __init__(self, trader_id: int, volume: int, price: int) -> None:
        """Initialize a new LimitOrder."""
        super().__init__(trader_id, volume)
        self.price = price

    def __repr__(self) -> str:
        """Return a string representation of the order."""
        return f"LMT P: {self.price} V: {self.volume:+}, FROM: {self.trader_id}"
