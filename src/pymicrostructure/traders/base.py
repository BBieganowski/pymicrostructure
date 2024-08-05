"""Base class for traders in a market simulation."""

import numpy as np
import random
from typing import Type
from pymicrostructure.markets.base import Market
from pymicrostructure.orders.market import MarketOrder
from pymicrostructure.orders.limit import LimitOrder


class Trader:
    """
    Represents a trader in a financial market.

    This class serves as a base class for specific trader implementations. It provides
    the basic structure for managing orders, trades, and interactions with the market.

    Attributes:
    -----------
    market : Market
        The market instance in which the trader participates.
    orders : list
        A list of orders submitted by the trader.
    filled_trades : list
        A list of trades that have been executed for the trader.
    position : int or float
        The current position of the trader in the market.
    include_in_results : bool
        Flag indicating whether to include this trader in result calculations.
    trader_id : int
        A unique identifier for the trader within the market.

    Methods:
    --------
    cancel_orders(side)
        Cancel active or partially filled orders on a specific side.
    cancel_all_orders()
        Cancel all active or partially filled orders.
    submit_order()
        A method to be implemented by subclasses for submitting orders to the market.
    """

    def __init__(
        self, market: Market, name: str = None, include_in_results=True
    ) -> None:
        """
        Initialize a new Trader instance.

        Parameters:
        -----------
        market : Market
            The market instance in which the trader will participate.
        name : str, optional
            The name of the trader (default is None).
        include_in_results : bool, optional
            Whether to include this trader in result calculations (default is True).
        """
        self.market = market
        self.orders = []
        self.filled_trades = []
        self.position = 0
        self.include_in_results = include_in_results
        self.fair_price = market.initial_fair_price
        self.market.participants.append(self)
        self.trader_id = self.market.participants.index(self)
        self.name = name

    def cancel_orders(self, side) -> None:
        """
        Cancel active or partially filled orders on a specific side.

        Parameters:
        -----------
        side : int
            The side of the orders to cancel (1 for buy, -1 for sell).
        """
        for order in self.orders:
            if (
                order.status == "active"
                or order.status == "partial"
                and np.sign(order.volume) == side
            ):
                order.status = "canceled"
                self.market.msg_history.append((self.trader_id, "CANCEL", order))
                self.market.cancellations.append(order)
        self.market.drop_cancelled_orders()

    def cancel_all_orders(self) -> None:
        """Cancel all active or partially filled orders for this trader."""
        for order in self.orders:
            if order.status == "active" or order.status == "partial":
                order.status = "canceled"
                self.market.cancellations.append(order)
        self.market.drop_cancelled_orders()

    def submit_order(self) -> None:
        """
        Submit an order to the market.

        This method should be overridden by subclasses to implement specific order
        submission logic.

        Raises:
        -------
        NotImplementedError
            If this method is not overridden by a subclass.
        """
        raise NotImplementedError("This method should be overridden by subclasses")
